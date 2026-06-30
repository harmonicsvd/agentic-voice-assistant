"""
Orchestration layer for open-source voice stack.
Integrates Faster-Whisper STT, Mistral 7B (Ollama), and Piper TTS.
"""

from pathlib import Path
from typing import Optional
import tempfile

class VoiceOrchestrator:
    """Orchestrates the full voice pipeline: STT → LLM → Tools → TTS."""
    
    def __init__(
        self,
        stt_model_size: str = "base",
        llm_model: str = "mistral",
        tts_model_path: str = "voice_models/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        tts_config_path: str = "voice_models/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    ):
        """Initialize the orchestrator with model paths."""
        self.stt_model_size = stt_model_size
        self.llm_model = llm_model
        self.tts_model_path = tts_model_path
        self.tts_config_path = tts_config_path
        
        # Lazy-loaded components
        self._stt_model = None
        self._tts_voice = None
    
    def transcribe_audio(self, audio_bytes: bytes, suffix: str = ".wav") -> str:
        """Transcribe audio to text using Faster-Whisper."""
        from faster_whisper import WhisperModel
        
        # Lazy load the model
        if self._stt_model is None:
            self._stt_model = WhisperModel(self.stt_model_size, device="cpu")
        
        # Write audio to temp file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = Path(tmp.name)
        
        try:
            # Transcribe
            segments, info = self._stt_model.transcribe(str(tmp_path), language="en")
            text = " ".join(segment.text for segment in segments)
            return text.strip()
        finally:
            tmp_path.unlink(missing_ok=True)
        
    def process_with_llm(self, text: str) -> str:
        """Process text with Mistral via Ollama."""
        import ollama
        
        response = ollama.chat(
            model=self.llm_model,
            messages=[
                {'role': 'system', 'content': 'You are a helpful voice assistant for scheduling meetings. Be concise and friendly.'},
                {'role': 'user', 'content': text}
            ]
        )
        
        return response['message']['content']
    
    def execute_tools(self, llm_response: str) -> str:
        """Execute tool calls based on LLM response."""
        import httpx
        import json
        import re
        
        # For now, return the LLM response directly
        # Full tool execution will be implemented with LangChain later
        return llm_response
    
    def synthesize_speech(self, text: str) -> bytes:
        """Convert text to speech using Piper TTS with WAV headers."""
        from piper import PiperVoice
        import wave
        import io
        
        # Lazy load the voice model
        if self._tts_voice is None:
            self._tts_voice = PiperVoice.load(self.tts_model_path, self.tts_config_path)
        
        # Synthesize speech
        audio_generator = self._tts_voice.synthesize(text)
        audio_bytes = b''.join(chunk.audio_int16_bytes for chunk in audio_generator)
        
        # Create WAV file in memory with headers
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self._tts_voice.config.sample_rate)
            wav_file.writeframes(audio_bytes)
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def run_pipeline(self, audio_bytes: bytes) -> bytes:
        """Run the full pipeline: audio → text → LLM → tools → audio."""
        # Step 1: Transcribe audio to text
        text = self.transcribe_audio(audio_bytes)
        print(f"Transcribed: {text}")
        
        # Step 2: Process with LLM
        llm_response = self.process_with_llm(text)
        print(f"LLM Response: {llm_response}")
        
        # Step 3: Execute tools (placeholder for now)
        tool_result = self.execute_tools(llm_response)
        print(f"Tool Result: {tool_result}")
        
        # Step 4: Synthesize speech
        audio_output = self.synthesize_speech(tool_result)
        print(f"Synthesized audio: {len(audio_output)} bytes")
        
        return audio_output