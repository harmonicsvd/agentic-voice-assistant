import os
import sqlite3
import logging
from contextlib import contextmanager
from app.config.config import settings

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:
    psycopg = None
    dict_row = None

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
_POSTGRES_DISABLED = False
logger = logging.getLogger("uvicorn.error")


def using_postgres() -> bool:
    """Return whether new connections should target Postgres."""
    return bool(DATABASE_URL) and not _POSTGRES_DISABLED and psycopg is not None


def _sqlite_connect():
    conn = sqlite3.connect(settings.app_db_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    global _POSTGRES_DISABLED

    if using_postgres():
        try:
            conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        except Exception as exc:
            _POSTGRES_DISABLED = True
            logger.warning(
                "postgres_connect_failed_fallback_to_sqlite db_path=%s error=%r",
                settings.app_db_path,
                exc,
            )
            conn = _sqlite_connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    else:
        if DATABASE_URL and psycopg is None and not _POSTGRES_DISABLED:
            _POSTGRES_DISABLED = True
            logger.warning(
                "postgres_driver_missing_fallback_to_sqlite db_path=%s",
                settings.app_db_path,
            )
        conn = _sqlite_connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def init_db():
    db_target = "postgres" if using_postgres() else settings.app_db_path
    logger.info("init_db starting | using_postgres=%s | target=%s", using_postgres(), db_target)
    ddl = """
    CREATE TABLE IF NOT EXISTS user_profiles (
        sub TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        default_city TEXT NOT NULL,
        timezone TEXT NOT NULL DEFAULT 'Europe/Berlin',
        role TEXT,
        commute_mode TEXT,
        ppe_required BOOLEAN DEFAULT FALSE,
        risk_tolerance TEXT,
        google_refresh_token TEXT,
        updated_at TEXT NOT NULL
    )
    """
    knowledge_documents_ddl = """
    CREATE TABLE IF NOT EXISTS user_knowledge_documents (
        id TEXT PRIMARY KEY,
        user_sub TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        stored_filename TEXT NOT NULL,
        storage_path TEXT NOT NULL,
        markdown_path TEXT,
        size_bytes INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'uploaded',
        uploaded_at TEXT NOT NULL
    )
    """
    with get_db() as conn:
        conn.execute(ddl)
        conn.execute(knowledge_documents_ddl)
    logger.info("init_db complete | using_postgres=%s", using_postgres())


def adapt_sql(query: str) -> str:
    """Convert Postgres-style placeholders to SQLite placeholders when needed."""
    if using_postgres():
        return query
    return query.replace("%s", "?")


def db_execute(conn, query: str, params=()):
    """Execute SQL with placeholder style adapted for active DB backend."""
    return conn.execute(adapt_sql(query), params)
