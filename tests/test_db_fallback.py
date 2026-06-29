"""Regression tests for database fallback behavior."""

import sqlite3
from types import SimpleNamespace

from app import db as db_module


class _FailingPsycopg:
    """Minimal psycopg stand-in that simulates a dead Postgres host."""

    @staticmethod
    def connect(*_args, **_kwargs):
        raise OSError("failed to resolve host")


def test_init_db_falls_back_to_sqlite_when_postgres_connect_fails(monkeypatch, tmp_path):
    """A configured but unreachable DATABASE_URL should not crash startup."""
    db_path = tmp_path / "fallback.db"
    monkeypatch.setattr(db_module, "DATABASE_URL", "postgresql://missing-host/db")
    monkeypatch.setattr(db_module, "_POSTGRES_DISABLED", False)
    monkeypatch.setattr(db_module, "psycopg", _FailingPsycopg())
    monkeypatch.setattr(db_module, "settings", SimpleNamespace(app_db_path=str(db_path)))

    db_module.init_db()

    assert db_module.using_postgres() is False
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'user_profiles'"
        ).fetchone()
    assert row is not None


def test_db_execute_uses_sqlite_placeholders_after_postgres_fallback(monkeypatch, tmp_path):
    """Queries written with Postgres placeholders should still work after fallback."""
    db_path = tmp_path / "fallback.db"
    monkeypatch.setattr(db_module, "DATABASE_URL", "postgresql://missing-host/db")
    monkeypatch.setattr(db_module, "_POSTGRES_DISABLED", False)
    monkeypatch.setattr(db_module, "psycopg", _FailingPsycopg())
    monkeypatch.setattr(db_module, "settings", SimpleNamespace(app_db_path=str(db_path)))

    db_module.init_db()

    with db_module.get_db() as conn:
        db_module.db_execute(
            conn,
            """
            INSERT INTO user_profiles (
                sub, email, default_city, timezone, updated_at
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                "user-1",
                "user@example.com",
                "Berlin",
                "Europe/Berlin",
                "2026-06-29T00:00:00+00:00",
            ),
        )
        row = db_module.db_execute(
            conn,
            "SELECT default_city FROM user_profiles WHERE sub = %s",
            ("user-1",),
        ).fetchone()

    assert row["default_city"] == "Berlin"
