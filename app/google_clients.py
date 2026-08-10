"""Google API client factories (Calendar service + OAuth config)."""

import json
from authlib.integrations.starlette_client import OAuth
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from app.config.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service(refresh_token: str | None = None):
    """
    Build Google Calendar service client.
    
    Args:
        refresh_token: User's OAuth refresh token for per-user access.
                      If None, uses shared service account credentials.
    """
    if refresh_token:
        # Use user's OAuth credentials
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
            scopes=SCOPES,
        )
        # Refresh the token to get a valid access token
        credentials.refresh(Request())
    else:
        # Use shared service account credentials
        if settings.service_account_json:
            service_account_info = json.loads(settings.service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=SCOPES,
            )
        else:
            credentials = service_account.Credentials.from_service_account_file(
                settings.service_account_file,
                scopes=SCOPES,
            )

    return build("calendar", "v3", credentials=credentials)


def build_oauth() -> OAuth:
    """Configure Google OAuth client used by `/auth/google/*` routes."""
    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile https://www.googleapis.com/auth/calendar",
            "prompt": "consent",  # Force consent to get refresh token
            "access_type": "offline",  # Request offline access for refresh token
            "approval_prompt": "force",  # Force approval prompt to ensure refresh token
        },
    )
    return oauth
