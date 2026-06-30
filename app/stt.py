"""Local speech-to-text helpers for Ram's open-source voice stack."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any


_TRANSCRIBER: Any | None = None


def get_transcriber() -> Any:
    """
    Lazily load Whisper so normal app startup does not download/load the model.

    This keeps the existing Ram backend usable even when optional STT
    dependencies are not installed yet.
    """
    global _TRANSCRIBER

    if _TRANSCRIBER is not None:
        return _TRANSCRIBER

    try:
        import torch
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError(
            "Local STT dependencies are missing. Install requirements-stt.txt first."
        ) from exc

    device = "mps" if torch.backends.mps.is_available() else "cpu"

    _TRANSCRIBER = pipeline(
        task="automatic-speech-recognition",
        model="openai/whisper-small",
        device=device,
    )
    return _TRANSCRIBER


def transcribe_audio_bytes(file_bytes: bytes, suffix: str = ".webm") -> str:
    """Write uploaded browser audio to a temp file and transcribe it with Whisper."""
    if not file_bytes:
        raise ValueError("Audio file is empty.")

    transcriber = get_transcriber()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        result = transcriber(
            str(tmp_path),
            return_timestamps=True,
            generate_kwargs={
                "language": "en",
                "task": "transcribe",
            },
        )
        return (result.get("text") or "").strip()
    finally:
        tmp_path.unlink(missing_ok=True)
