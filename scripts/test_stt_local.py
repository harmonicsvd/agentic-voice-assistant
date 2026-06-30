import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.stt import transcribe_audio_bytes

AUDIO_PATH = PROJECT_ROOT / "test_audio.wav"

audio_bytes = AUDIO_PATH.read_bytes()
transcript = transcribe_audio_bytes(audio_bytes, suffix=AUDIO_PATH.suffix)

print("Transcript:")
print(transcript)