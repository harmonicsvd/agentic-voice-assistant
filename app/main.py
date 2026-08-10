"""Ram backend: auth, voice calendar tools, and delegation to Sham intelligence."""

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

from datetime import datetime, timedelta, timezone
import httpx
import time


import re
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

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
    same_site="lax",
    https_only=False,  # local dev
)


oauth = build_oauth()

BASE_DIR = Path(__file__).resolve().parent.parent
LOGIN_HTML = BASE_DIR / "login.html"
SETUP_HTML = BASE_DIR / "setup.html"
VOICE_HTML = BASE_DIR / "index.html"


class ProfileUpdate(BaseModel):
    """Validated payload for updating user profile preferences."""
    role: str = Field(min_length=2, max_length=80)
    default_city: str = Field(min_length=2, max_length=80)
    timezone: str = Field(default="Europe/Berlin", min_length=3, max_length=80)
    commute_mode: str = Field(min_length=2, max_length=40)
    risk_tolerance: str = Field(min_length=2, max_length=20)
    ppe_required: bool = False


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


@app.get("/profile")
async def get_profile(request: Request):
    """Return current user profile from SQLite for authenticated browser user."""
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

@app.put("/profile")
async def put_profile(payload: ProfileUpdate, request: Request):
    """Upsert current user profile preferences."""
    user, error = get_current_user_or_401(request)
    if error:
        return error

    updated_at = datetime.now(timezone.utc).isoformat()

    try:
        with get_db() as conn:
            # Get existing refresh token to preserve it
            existing = db_execute(
                conn,
                "SELECT google_refresh_token FROM user_profiles WHERE sub = %s",
                (user["sub"],)
            ).fetchone()
            existing_refresh_token = existing["google_refresh_token"] if existing else None
            
            # Use different upsert syntax based on database type
            if using_postgres():
                db_execute(
                    conn,
                    """
                    INSERT INTO user_profiles (
                        sub, email, default_city, timezone, role, commute_mode,
                        ppe_required, risk_tolerance, google_refresh_token, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(sub) DO UPDATE SET
                        email = excluded.email,
                        default_city = excluded.default_city,
                        timezone = excluded.timezone,
                        role = excluded.role,
                        commute_mode = excluded.commute_mode,
                        ppe_required = excluded.ppe_required,
                        risk_tolerance = excluded.risk_tolerance,
                        google_refresh_token = COALESCE(excluded.google_refresh_token, user_profiles.google_refresh_token),
                        updated_at = excluded.updated_at
                    """,
                    (
                        user["sub"],
                        user.get("email", ""),
                        payload.default_city.strip(),
                        payload.timezone.strip(),
                        payload.role.strip(),
                        payload.commute_mode.strip(),
                        payload.ppe_required,
                        payload.risk_tolerance.strip(),
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
                        sub, email, default_city, timezone, role, commute_mode,
                        ppe_required, risk_tolerance, google_refresh_token, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user["sub"],
                        user.get("email", ""),
                        payload.default_city.strip(),
                        payload.timezone.strip(),
                        payload.role.strip(),
                        payload.commute_mode.strip(),
                        payload.ppe_required,
                        payload.risk_tolerance.strip(),
                        existing_refresh_token,
                        updated_at,
                    ),
                )
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
            SELECT sub, email, default_city, timezone, role, commute_mode, ppe_required, risk_tolerance, google_refresh_token, updated_at
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

    user_sub = request.session["user"].get("sub", "")
    
    # Save refresh token to database if available
    refresh_token = token.get("refresh_token")
    logger.info(f"OAuth callback - refresh_token in token: {refresh_token is not None}")
    if refresh_token:
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
                    (refresh_token, datetime.utcnow().isoformat(), user_sub)
                )
                logger.info(f"OAuth callback - updated refresh_token for existing profile: {user_sub}")
            else:
                # Profile will be created during setup, but save refresh token for later
                # Insert a minimal profile with the refresh token and required fields
                db_execute(
                    conn,
                    "INSERT INTO user_profiles (sub, email, default_city, timezone, google_refresh_token, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_sub, user_info.get("email"), "", "Europe/Berlin", refresh_token, datetime.utcnow().isoformat())
                )
                logger.info(f"OAuth callback - created minimal profile with refresh_token: {user_sub}")
    else:
        logger.warning(f"OAuth callback - no refresh_token returned by Google. Token keys: {list(token.keys())}")
    
    destination = "/assistant" if _is_profile_complete(_get_profile_row(user_sub)) else "/setup"
    # Redirect to React dev server for development
    react_url = getattr(settings, 'react_dev_url', 'http://localhost:5173')
    return RedirectResponse(url=f"{react_url}{destination}?user_sub={user_sub}", status_code=302)


@app.get("/auth/me")
async def auth_me(request: Request):
    """Return current session user data for frontend bootstrapping."""
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

    if not settings.weather_agent_knowledge_upload_url:
        return JSONResponse(
            {"error": "Weather-agent knowledge upload URL is not configured"},
            status_code=500,
        )

    async with httpx.AsyncClient(
        timeout=settings.weather_agent_timeout_seconds
    ) as client:
        response = await client.post(
            settings.weather_agent_knowledge_upload_url,
            data={"user_sub": user["sub"]},
            files={
                "file": (
                    file.filename or "upload.pdf",
                    file_bytes,
                    "application/pdf",
                )
            },
            headers={
                "X-Internal-API-Key": settings.weather_agent_internal_api_key,
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
    user = request.session.get("user")
    if not user:
        return None, JSONResponse({"error": "authentication required"}, status_code=401)
    return user, None


def _get_profile_row(sub: str):
    """Load one profile row used by page routing and profile APIs."""
    with get_db() as conn:
        return db_execute(
            conn,
            """
            SELECT sub, email, default_city, timezone, role, commute_mode, ppe_required, risk_tolerance, google_refresh_token, updated_at
            FROM user_profiles
            WHERE sub = %s
            """,
            (sub,),
        ).fetchone()


def _is_profile_complete(row) -> bool:
    """Treat setup as complete only when all onboarding-required fields are present."""
    if not row:
        return False

    required_fields = [
        row["role"],
        row["default_city"],
        row["timezone"],
        row["commute_mode"],
        row["risk_tolerance"],
    ]
    return all(isinstance(value, str) and value.strip() for value in required_fields)


def _lookup_profile_city(sub: str | None) -> str | None:
    """Read default city from local profile DB for fallback event city logic."""
    if not sub:
        return None

    with get_db() as conn:
        row = db_execute(
            conn,
            "SELECT default_city FROM user_profiles WHERE sub = %s",
            (sub,),
        ).fetchone()
    city = (row["default_city"] or "").strip() if row else ""
    return city or None


def _lookup_profile_timezone(sub: str | None) -> str | None:
    """Read timezone from local profile DB for event scheduling."""
    if not sub:
        return None

    with get_db() as conn:
        row = db_execute(
            conn,
            "SELECT timezone FROM user_profiles WHERE sub = %s",
            (sub,),
        ).fetchone()
    tz = (row["timezone"] or "").strip() if row else ""
    return tz or None


# Mount static files for frontend (must be after all route definitions)
# Only for production when serving built React app
if Path("frontend/dist").exists():
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
