"""Ram backend: auth, voice calendar skills, and delegation to Sham intelligence."""

import hmac
import json
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, Query, Header, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import JSONResponse, Response, RedirectResponse, FileResponse

from app.config.config import settings
from app.google_clients import get_calendar_service, build_oauth




from pydantic import BaseModel, Field, ValidationError
from typing import Literal, Any

from app.db.db import init_db, get_db, db_execute, using_postgres
from uuid import uuid4
from app.skills import clear_user_cache
import httpx
import os

BACKEND_AGENT_URL = os.getenv("BACKEND_AGENT_URL", "http://127.0.0.1:9000")
BACKEND_INTERNAL_API_KEY = os.getenv("BACKEND_INTERNAL_API_KEY", "your-internal-api-key")

async def clear_backend_cache(user_sub: str):
    """Clear the skills cache in the backend service."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_AGENT_URL}/internal/skills/cache/clear",
                data={"user_sub": user_sub},
                headers={"X-Internal-API-Key": BACKEND_INTERNAL_API_KEY},
                timeout=5.0
            )
            if response.status_code == 200:
                logger.info(f"Successfully cleared backend cache for user {user_sub}")
            else:
                logger.warning(f"Failed to clear backend cache: {response.status_code}")
    except Exception as e:
        logger.error(f"Error clearing backend cache: {e}")

from datetime import datetime, timedelta, timezone
import httpx
import time


import re
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Header
import jwt

from app.agents.pipecat_websocket import pipecat_websocket_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize persistent resources once at process startup."""
    init_db()   # runs once when server starts

   


    yield       # app serves requests here
    # optional cleanup when server stops

app = FastAPI(lifespan=lifespan)
logger = logging.getLogger("uvicorn.error")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://emo-personal-agentic-voice-assistan.vercel.app",
        "https://voice-scheduling-agent-pi.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.app_secret_key,
    same_site="lax",  # Changed back to lax for better compatibility
    https_only=settings.environment == "production",  # HTTPS only for production, allow HTTP for local dev
    max_age=None,  # Session cookie (expires when browser closes)
)


oauth = build_oauth()

# JWT Configuration
JWT_SECRET = settings.app_secret_key
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def create_jwt_token(user_data: dict) -> str:
    """Create a JWT token for the user."""
    payload = {
        "sub": user_data.get("sub"),
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "picture": user_data.get("picture"),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def get_user_from_token(authorization: str = Header(None)) -> Optional[dict]:
    """Extract and verify user from Authorization header."""
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    return verify_jwt_token(token)

BASE_DIR = Path(__file__).resolve().parent.parent
LOGIN_HTML = BASE_DIR / "login.html"
SETUP_HTML = BASE_DIR / "setup.html"
VOICE_HTML = BASE_DIR / "index.html"


class ProfileUpdate(BaseModel):
    """Validated payload for updating user profile preferences."""
    work_description: str = Field(default="", max_length=200)
    industry: str = Field(default="", max_length=100)
    responsibilities: str = Field(default="", max_length=500)
    company_name: str = Field(default="", max_length=100)
    work_environment: str = Field(default="", max_length=50)
    emo_avatar: str = Field(default="", max_length=255)  # Add this line


@app.get("/login")
async def login_page(request: Request):
    """Serve login UI entrypoint."""
    return FileResponse(LOGIN_HTML)

@app.get("/assistant")
async def assistant_page(request: Request):
    """Serve assistant UI only for authenticated sessions."""
    user, _ = get_current_user_or_401(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not user.get("sub"):
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)
    if not _is_profile_complete(_get_profile_row(user["sub"])):
        return RedirectResponse(url="/setup", status_code=302)
    return FileResponse(VOICE_HTML)


@app.get("/setup")
async def setup_page(request: Request):
    """Serve onboarding UI for authenticated users who still need profile setup."""
    user, _ = get_current_user_or_401(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not user.get("sub"):
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)
    if _is_profile_complete(_get_profile_row(user["sub"])):
        return RedirectResponse(url="/assistant", status_code=302)
    return FileResponse(SETUP_HTML)


@app.get("/api/profile")
async def get_profile(request: Request):
    """Return current user profile from database (SQLite or PostgreSQL) for authenticated browser user."""
    user, error = get_current_user_or_401(request)
    if error:
        return error

    row = _get_profile_row(user["sub"])

    if not row:
        return {"has_profile": False, "is_setup_complete": False, "profile": None}

    return {
        "has_profile": True,
        "is_setup_complete": _is_profile_complete(row),
        "profile": dict(row),
    }

@app.put("/api/profile")
async def put_profile(payload: ProfileUpdate, request: Request):
    """Upsert current user profile preferences."""
    user, error = get_current_user_or_401(request)
    if error:
        return error

    updated_at = datetime.now(timezone.utc).isoformat()

    try:
        with get_db() as conn:
            # Get existing profile data to preserve fields not being updated
            existing = db_execute(
                conn,
                "SELECT * FROM user_profiles WHERE sub = %s",
                (user["sub"],)
            ).fetchone()
            
            # Prepare values - use existing if payload field is empty, otherwise use payload
            work_description = payload.work_description.strip() if payload.work_description else (existing["work_description"] if existing else "")
            industry = payload.industry.strip() if payload.industry else (existing["industry"] if existing else "")
            responsibilities = payload.responsibilities.strip() if payload.responsibilities else (existing["responsibilities"] if existing else "")
            company_name = payload.company_name.strip() if payload.company_name else (existing["company_name"] if existing else "")
            work_environment = payload.work_environment.strip() if payload.work_environment else (existing["work_environment"] if existing else "")
            emo_avatar = payload.emo_avatar.strip() if payload.emo_avatar else (existing["emo_avatar"] if existing else "")
            existing_name = existing["name"] if existing and existing.get("name") else ""
            existing_refresh_token = existing["google_refresh_token"] if existing else None

            # Use different upsert syntax based on database type
            if using_postgres():
                db_execute(
                    conn,
                    """
                    INSERT INTO user_profiles (
                        sub, email, name, work_description, industry, responsibilities, company_name, work_environment, emo_avatar,
                        google_refresh_token, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(sub) DO UPDATE SET
                        email = excluded.email,
                        name = user_profiles.name,
                        work_description = CASE WHEN excluded.work_description = '' THEN user_profiles.work_description ELSE excluded.work_description END,
                        industry = CASE WHEN excluded.industry = '' THEN user_profiles.industry ELSE excluded.industry END,
                        responsibilities = CASE WHEN excluded.responsibilities = '' THEN user_profiles.responsibilities ELSE excluded.responsibilities END,
                        company_name = CASE WHEN excluded.company_name = '' THEN user_profiles.company_name ELSE excluded.company_name END,
                        work_environment = CASE WHEN excluded.work_environment = '' THEN user_profiles.work_environment ELSE excluded.work_environment END,
                        emo_avatar = CASE WHEN excluded.emo_avatar = '' THEN user_profiles.emo_avatar ELSE excluded.emo_avatar END,
                        google_refresh_token = COALESCE(excluded.google_refresh_token, user_profiles.google_refresh_token),
                        updated_at = excluded.updated_at
                    """,
                    (
                        user["sub"],
                        user.get("email", ""),
                        existing_name,  # preserve existing name from OAuth
                        work_description,
                        industry,
                        responsibilities,
                        company_name,
                        work_environment,
                        emo_avatar,
                        existing_refresh_token,
                        updated_at,
                    ),
                )
            else:
                # SQLite: Use INSERT OR REPLACE (upsert)
                db_execute(
                    conn,
                    """
                    INSERT OR REPLACE INTO user_profiles (
                        sub, email, name, work_description, industry, responsibilities, company_name, work_environment, emo_avatar,
                        google_refresh_token, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user["sub"],
                        user.get("email", ""),
                        existing_name,  # preserve existing name from OAuth
                        work_description,
                        industry,
                        responsibilities,
                        company_name,
                        work_environment,
                        emo_avatar,
                        existing_refresh_token,
                        updated_at,
                    ),
                )
            
            # Check if user has any installed skills - if not, install default skill
            existing_skills = db_execute(
                conn,
                "SELECT skill_name FROM user_installed_skills WHERE user_sub = %s AND status = 'active'",
                (user["sub"],)
            ).fetchall()
            
            if not existing_skills:
                # User has no skills - install default google_calendar
                if using_postgres():
                    db_execute(
                        conn,
                        """
                        INSERT INTO user_installed_skills (id, user_sub, skill_name, status, installed_at)
                        VALUES (%s, %s, %s, 'active', %s)
                        ON CONFLICT (user_sub, skill_name) DO NOTHING
                        """,
                        (str(uuid4()), user["sub"], "google_calendar", datetime.now(timezone.utc).isoformat())
                    )
                else:
                    db_execute(
                        conn,
                        """
                        INSERT OR IGNORE INTO user_installed_skills (id, user_sub, skill_name, status, installed_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (str(uuid4()), user["sub"], "google_calendar", "active", datetime.now(timezone.utc).isoformat())
                    )
                
                # Clear cache so the voice agent picks up the new skill
                clear_user_cache(user["sub"])
                logger.info(f"Installed default skill 'google_calendar' for new user {user['sub']}")
    except Exception as e:
        logger.error(f"Failed to save profile: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

    return {"ok": True}

def require_internal_api_key(x_internal_api_key: str | None):
    """Guard internal endpoints with constant-time API key comparison."""
    if not settings.internal_api_key:
        return JSONResponse({"error": "internal api key not configured"}, status_code=500)
    if not x_internal_api_key or not hmac.compare_digest(x_internal_api_key, settings.internal_api_key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return None

@app.get("/internal/profile/{sub}")
async def get_internal_profile(
    sub: str,
    x_internal_api_key: str | None = Header(default=None),
):
    err = require_internal_api_key(x_internal_api_key)
    if err:
        return err

    with get_db() as conn:
        row = db_execute(
            conn,
            """
            SELECT sub, email, name, work_description, industry, responsibilities, company_name, work_environment, google_refresh_token, updated_at
            FROM user_profiles
            WHERE sub = %s
            """,
            (sub,),
        ).fetchone()

    if not row:
        return JSONResponse({"error": "profile_not_found"}, status_code=404)

    return {"profile": dict(row)}



def _derive_city_from_location(location: str | None) -> str | None:
    """
    Best-effort extraction of a city token from a free-form venue string.
    Examples:
    - "Berlin Office" -> "Berlin"
    - "Friedrichstrasse 10, Berlin" -> "Berlin"
    """
    if not location:
        return None

    text = location.strip()
    if not text:
        return None

    # Prefer trailing segment in comma-separated addresses.
    candidate = text.split(",")[-1].strip() or text
    candidate = re.sub(
        r"\b(office|hq|headquarters|campus|site|building|floor|room|client)\b",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(r"[^A-Za-z\s\-']", " ", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip()

    if not candidate:
        return None

    # Preserve common city capitalization format.
    return candidate.title()




@app.get("/")
def root():
    """Default root route redirects users to login."""
    return RedirectResponse(url="/login", status_code=302)


@app.head("/")
def root_head():
    """HEAD probe for root path (used by some hosting health checks)."""
    return Response(status_code=200)


@app.get("/health")
def health():
    """Simple liveness endpoint."""
    return {"ok": True}


@app.head("/health")
def health_head():
    """HEAD variant for liveness checks."""
    return Response(status_code=200)


# Skill Management Endpoints
class SkillInstallRequest(BaseModel):
    skill_name: str = Field(..., description="Name of the skill to install")

# Predefined list of valid skills for UI database management (using skill names)
VALID_SKILLS = ["meeting_discussion", "google_calendar"]

@app.post("/api/skills/install")
async def install_skill(request: Request, payload: SkillInstallRequest):
    """Install a skill for the current user."""
    user, error = get_current_user_or_401(request)
    if error:
        return error

    try:
        from uuid import uuid4
        from datetime import datetime

        # Check if skill is in the predefined valid skills list
        if payload.skill_name not in VALID_SKILLS:
            return JSONResponse({"error": f"Skill '{payload.skill_name}' not found"}, status_code=404)

        with get_db() as conn:
            # Check if already installed
            existing = db_execute(
                conn,
                "SELECT * FROM user_installed_skills WHERE user_sub = %s AND skill_name = %s",
                (user["sub"], payload.skill_name)
            ).fetchone()

            if existing:
                # Update status to active if it exists but is inactive
                if existing["status"] != "active":
                    db_execute(
                        conn,
                        "UPDATE user_installed_skills SET status = 'active', installed_at = %s WHERE user_sub = %s AND skill_name = %s",
                        (datetime.now(timezone.utc).isoformat(), user["sub"], payload.skill_name)
                    )
            else:
                # Install the skill - use upsert to handle re-installation after uninstall
                from app.db.db import using_postgres
                if using_postgres():
                    db_execute(
                        conn,
                        """
                        INSERT INTO user_installed_skills (id, user_sub, skill_name, status, installed_at)
                        VALUES (%s, %s, %s, 'active', %s)
                        ON CONFLICT (user_sub, skill_name) 
                        DO UPDATE SET status = 'active', installed_at = %s
                        """,
                        (str(uuid4()), user["sub"], payload.skill_name, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat())
                    )
                else:
                    # SQLite: Use REPLACE (delete + insert) to handle re-installation
                    db_execute(
                        conn,
                        """
                        INSERT OR REPLACE INTO user_installed_skills (id, user_sub, skill_name, status, installed_at)
                        VALUES (%s, %s, %s, 'active', %s)
                        """,
                        (str(uuid4()), user["sub"], payload.skill_name, datetime.now(timezone.utc).isoformat())
                    )

        # Clear the skills cache for this user so they get fresh data on next request
        # This must happen outside the database transaction and after any DB changes
        clear_user_cache(user["sub"])
        
        # Also clear the backend cache
        await clear_backend_cache(user["sub"])

        return {"ok": True, "skill_name": payload.skill_name}
    except Exception as e:
        logger.error(f"Failed to install skill: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete("/api/skills/uninstall")
async def uninstall_skill(request: Request, skill_name: str = Query(..., description="Name of the skill to uninstall")):
    """Uninstall a skill for the current user."""
    user, error = get_current_user_or_401(request)
    if error:
        return error

    try:
        # Check if skill is in the predefined valid skills list
        if skill_name not in VALID_SKILLS:
            return JSONResponse({"error": f"Skill '{skill_name}' not found"}, status_code=404)

        with get_db() as conn:
            # Instead of deleting, set status to inactive
            db_execute(
                conn,
                "UPDATE user_installed_skills SET status = 'inactive' WHERE user_sub = %s AND skill_name = %s",
                (user["sub"], skill_name)
            )

        # Clear the skills cache for this user so they get fresh data on next request
        clear_user_cache(user["sub"])
        
        # Also clear the backend cache
        await clear_backend_cache(user["sub"])

        return {"ok": True, "skill_name": skill_name}
    except Exception as e:
        logger.error(f"Failed to uninstall skill: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/skills/available")
async def get_available_skills(request: Request):
    """Get all available skills with installation status for current user."""
    user, error = get_current_user_or_401(request)
    if error:
        return error

    try:
        # Get all available skills from predefined list
        available_skills = []

        # Get user's installed skills
        with get_db() as conn:
            installed_skills = db_execute(
                conn,
                "SELECT skill_name FROM user_installed_skills WHERE user_sub = %s AND status = 'active'",
                (user["sub"],)
            ).fetchall()

        installed_skill_names = {row["skill_name"] for row in installed_skills}

        # Build response with installation status from predefined skills list
        for skill_name in VALID_SKILLS:
            available_skills.append({
                "skill_name": skill_name,
                "installed": skill_name in installed_skill_names,
                "tools_count": 1  # Placeholder count
            })

        return {"available_skills": available_skills}
    except Exception as e:
        logger.error(f"Failed to get available skills: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)





@app.websocket("/ws/pipecat")
async def pipecat_websocket(websocket: WebSocket):
    """WebSocket endpoint for Pipecat real-time voice pipeline."""
    await pipecat_websocket_handler(websocket)


def _list_events_payload(from_iso: str, to_iso: str, user_sub: str | None = None) -> dict:
    """Unified event reader used by both public `/events` and internal `/internal/events`."""
    
    # Get user's refresh token if user_sub is provided
    refresh_token = None
    calendar_id = settings.calendar_id
    
    if user_sub:
        try:
            profile = _get_profile_row(user_sub)
            if profile:
                # sqlite3.Row object - access by column name directly
                refresh_token = profile["google_refresh_token"] if profile and "google_refresh_token" in profile.keys() else None
                calendar_id = "primary"  # Use user's primary calendar
                logger.info(f"📅 _list_events_payload: user_sub={user_sub}, has_refresh_token={bool(refresh_token)}")
            else:
                logger.warning(f"📅 _list_events_payload: no profile found for user_sub={user_sub}")
        except Exception as e:
            logger.error(f"📅 _list_events_payload: error getting profile: {e}")
    
    try:
        service = get_calendar_service(refresh_token=refresh_token)
    except Exception as e:
        logger.error(f"📅 _list_events_payload: error getting calendar service: {e}")
        # Fall back to shared calendar if user token fails
        service = get_calendar_service(refresh_token=None)
        calendar_id = settings.calendar_id
        logger.info("📅 _list_events_payload: falling back to shared calendar")
    
    try:
        response = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=from_iso,
                timeMax=to_iso,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
    except Exception as e:
        logger.error(f"📅 _list_events_payload: error listing events: {e}")
        return {"events": []}

    items = response.get("items", [])
    events = []
    for e in items:
        start = (e.get("start") or {}).get("dateTime") or (e.get("start") or {}).get("date")
        end = (e.get("end") or {}).get("dateTime") or (e.get("end") or {}).get("date")
        location = e.get("location")
        description_raw = e.get("description") or ""
        description = description_raw.lower()
        
        # Remove user_sub extraction since we're using per-user calendars
        weather_city_match = re.search(r"\bweather_city:([^;]+)", description_raw)
        weather_city = weather_city_match.group(1).strip() if weather_city_match else None
        city_source_match = re.search(r"\bcity_source:([^;]+)", description_raw)
        city_source = city_source_match.group(1).strip() if city_source_match else None

        meeting_mode = "unknown"
        if "meeting_mode:online" in description:
            meeting_mode = "online"
        elif "meeting_mode:in_person" in description:
            meeting_mode = "in_person"

        # Backward compatibility for old calendar events that were created
        # before weather_city metadata existed.
        if not weather_city and meeting_mode == "in_person" and location:
            legacy_city = _derive_city_from_location(location)
            if legacy_city:
                weather_city = legacy_city
                if not city_source:
                    city_source = "legacy_from_location"

        heuristic_virtual = (
            ("zoom" in (location or "").lower())
            or ("meet.google.com" in description)
            or ("teams" in description)
        )

        if meeting_mode == "online":
            is_virtual = True
        elif meeting_mode == "in_person":
            is_virtual = False
        else:
            is_virtual = heuristic_virtual

        summary = e.get("summary", "Untitled")

        events.append(
            {
                "title": summary,
                "start": start,
                "end": end,
                "location": location,
                "description": description_raw,
                "city": weather_city,
                "city_source": city_source,
                "meeting_mode": meeting_mode,
                "is_virtual": is_virtual,
            }
        )

    return {"events": events}


# Internal endpoints for weather-agent integration
@app.get("/internal/events")
async def list_events_internal(
    from_iso: str = Query(..., description="ISO start datetime"),
    to_iso: str = Query(..., description="ISO end datetime"),
    user_sub: str | None = Query(default=None, description="Filter by user sub"),
    x_internal_api_key: str | None = Header(default=None),
):
    """Internal calendar listing endpoint for backend callers."""
    err = require_internal_api_key(x_internal_api_key)
    if err:
        return err

    try:
        return _list_events_payload(from_iso, to_iso, user_sub=user_sub)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/auth/google/login")
async def auth_google_login(request: Request):
    """Start Google OAuth browser redirect flow."""
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        prompt="consent",
        access_type="offline"
    )


@app.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    """Handle Google OAuth callback and persist session identity."""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            user_info = await oauth.google.parse_id_token(request, token)

        request.session["user"] = {
            "sub": user_info.get("sub"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        }
        request.session["token"] = {
            "access_token": token.get("access_token"),
            "expires_at": token.get("expires_at"),
        }

        user_sub = user_info.get("sub", "")
        
        # Store user in session for local development (same-origin)
        request.session["user"] = {
            "sub": user_sub,
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        }
        
        # Create JWT token for frontend (for production cross-origin)
        jwt_token = create_jwt_token({
            "sub": user_sub,
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        })
        
        # Save refresh token to database if available
        refresh_token = token.get("refresh_token")
        logger.info(f"OAuth callback - refresh_token in token: {refresh_token is not None}")
        if refresh_token:
            try:
                with get_db() as conn:
                    # Check if profile exists
                    existing = db_execute(
                        conn,
                        "SELECT sub FROM user_profiles WHERE sub = %s",
                        (user_sub,)
                    ).fetchone()
                    
                    if existing:
                        # Update refresh token
                        db_execute(
                            conn,
                            "UPDATE user_profiles SET google_refresh_token = %s, updated_at = %s WHERE sub = %s",
                            (refresh_token, datetime.now(timezone.utc).isoformat(), user_sub)
                        )
                        logger.info(f"OAuth callback - updated refresh_token for existing profile: {user_sub}")
                    else:
                        # Profile will be created during setup, but save refresh token for later
                        # Insert a minimal profile with the refresh token and required fields
                        db_execute(
                            conn,
                            "INSERT INTO user_profiles (sub, email, name, work_description, industry, responsibilities, company_name, work_environment, google_refresh_token, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (user_sub, user_info.get("email"), user_info.get("name", ""), "", "", "", "", "", refresh_token, datetime.now(timezone.utc).isoformat())
                        )
                        logger.info(f"OAuth callback - created minimal profile with refresh_token: {user_sub}")
            except Exception as db_error:
                logger.error(f"OAuth callback - database error: {db_error}")
                # Continue without saving refresh token if DB fails
        else:
            logger.warning(f"OAuth callback - no refresh_token returned by Google. Token keys: {list(token.keys())}")
        
        destination = "/assistant" if _is_profile_complete(_get_profile_row(user_sub)) else "/setup"
        # Redirect to frontend URL (use environment variable in production, localhost for dev)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}{destination}?token={jwt_token}", status_code=302)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return JSONResponse({"error": f"OAuth callback failed: {str(e)}"}, status_code=500)


@app.get("/auth/me")
async def auth_me(request: Request, authorization: str = Header(None)):
    """Return current session user data for frontend bootstrapping."""
    # Try JWT token first
    if authorization:
        user_data = get_user_from_token(authorization)
        if user_data:
            return {"authenticated": True, "user": user_data}
    
    # Fallback to session
    user = request.session.get("user")
    if not user:
        return JSONResponse({"authenticated": False}, status_code=401)
    return {"authenticated": True, "user": user}

@app.post("/auth/logout")
async def auth_logout(request: Request):
    """Clear browser session data."""
    request.session.clear()
    return {"ok": True}

@app.post("/knowledge/upload")
async def upload_knowledge_pdf(
    request: Request,
    file: UploadFile = File(...),
):
    """Accept a Ram user PDF and forward it to Sham for RAG ingestion."""
    user, error = get_current_user_or_401(request)
    if error:
        return error

    if file.content_type != "application/pdf":
        return JSONResponse(
            {"error": "Only PDF files are supported"},
            status_code=400,
        )

    file_bytes = await file.read()
    
    if not file_bytes:
        return JSONResponse(
            {"error": "Uploaded file is empty"},
            status_code=400,
        )

    if not settings.backend_agent_knowledge_upload_url:
        return JSONResponse(
            {"error": "Backend Agent knowledge upload URL is not configured"},
            status_code=500,
        )

    async with httpx.AsyncClient(
        timeout=settings.backend_agent_timeout_seconds
    ) as client:
        response = await client.post(
            settings.backend_agent_knowledge_upload_url,
            data={"user_sub": user["sub"]},
            files={
                "file": (
                    file.filename,
                    file.file,
                    file.content_type
                )
            },
            headers={
                "X-Internal-API-Key": settings.backend_agent_internal_api_key,
            },
        )

    if response.status_code >= 400:
        logger.error(
            "knowledge_pdf_forward_failed user_sub=%s status=%s body=%s",
            user["sub"],
            response.status_code,
            response.text,
        )
        return JSONResponse(
            {"error": "Weather-agent PDF ingestion failed"},
            status_code=502,
        )

    logger.info(
        "knowledge_pdf_forwarded user_sub=%s filename=%s size_bytes=%s",
        user["sub"],
        file.filename,
        len(file_bytes),
    )

    return response.json()


def get_current_user_or_401(request: Request):
    """Small auth helper returning `(user, error_response)` tuple."""
    # Try JWT token first
    authorization = request.headers.get("Authorization")
    if authorization:
        user_data = get_user_from_token(authorization)
        if user_data:
            return user_data, None
    
    # Fallback to session
    user = request.session.get("user")
    if not user:
        return None, JSONResponse({"error": "authentication required"}, status_code=401)
    return user, None


def _get_profile_row(sub: str):
    """Load one profile row used by page routing and profile APIs."""
    try:
        with get_db() as conn:
            return db_execute(
                conn,
                """
                SELECT sub, email, name, work_description, industry, responsibilities, company_name, work_environment, emo_avatar, google_refresh_token, updated_at
                FROM user_profiles
                WHERE sub = %s
                """,
                (sub,),
            ).fetchone()
    except Exception as e:
        logger.error(f"Error getting profile row for sub {sub}: {e}")
        return None


def _is_profile_complete(row) -> bool:
    """Treat setup as complete only when all onboarding-required fields are present."""
    if not row:
        return False

    required_fields = [
        row.get("work_description", ""),
        row.get("industry", ""),
        row.get("responsibilities", ""),
        row.get("company_name", ""),
        row.get("work_environment", ""),
    ]
    return all(isinstance(value, str) and value.strip() for value in required_fields)


# Mount static files for frontend (must be after all route definitions)
# Only for production when serving built React app
if Path("frontend/dist").exists():
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
