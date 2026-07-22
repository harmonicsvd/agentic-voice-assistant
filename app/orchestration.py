"""
Orchestration layer for open-source voice stack.
Integrates Faster-Whisper STT, Mistral 7B (Ollama), and Piper TTS using LangGraph.
"""

from pathlib import Path
from typing import Optional
import tempfile
import wave
import io

class VoiceOrchestrator:
    """Orchestrates the full voice pipeline using LangGraph: STT → LLM → Tools → TTS."""
    
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
        self._tools = None
        self._skill_prompts = None
        
        # Preload skills at initialization
        self._preload_skills()

    def _preload_skills(self):
        """Preload skills and tools to avoid loading during pipeline."""
        try:
            from app.skills import get_all_tools, get_skill_prompts
            self._tools = get_all_tools()
            self._skill_prompts = get_skill_prompts()
            print("Skills preloaded successfully")
        except Exception as e:
            print(f"Error preloading skills: {e}")
            self._tools = []
            self._skill_prompts = ""

    def transcribe_audio_streaming(self, audio_bytes: bytes):
        """Stream transcribe audio to text using mlx-whisper.
        
        Yields partial transcriptions as they become available.
        """
        import mlx_whisper
        import io
        import tempfile
        from pathlib import Path
        import subprocess
        
        # Check if audio has WAV header by checking first 4 bytes
        is_wav = audio_bytes[:4] == b'RIFF'
        
        if is_wav:
            # Already has WAV headers, use as-is
            wav_path = None
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                wav_path = Path(tmp.name)
        else:
            # Convert webm to WAV using ffmpeg
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as webm_file:
                webm_file.write(audio_bytes)
                webm_path = webm_file.name
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
                wav_path = Path(wav_file.name)
            
            try:
                subprocess.run([
                    "ffmpeg", "-i", webm_path,
                    "-ar", "16000",
                    "-ac", "1",
                    "-y",  # Overwrite output file
                    str(wav_path)
                ], check=True, capture_output=True)
            finally:
                Path(webm_path).unlink(missing_ok=True)
        
        try:
            # Use mlx-whisper for transcription
            result = mlx_whisper.transcribe(str(wav_path))
            yield result["text"]
        finally:
            wav_path.unlink(missing_ok=True)
    
    def transcribe_audio(self, audio_bytes: bytes, suffix: str = ".wav") -> str:
        """Transcribe audio to text using Faster-Whisper."""
        from faster_whisper import WhisperModel
        import io
        
        # Lazy load the model
        if self._stt_model is None:
            self._stt_model = WhisperModel(self.stt_model_size, device="cpu")
        
        # Add WAV headers if the audio doesn't have them
        try:
            # Try to detect if it's already a valid WAV file
            wav_buffer = io.BytesIO(audio_bytes)
            wav_buffer.seek(0)
            try:
                with wave.open(wav_buffer, 'rb') as wav_file:
                    # It's a valid WAV file, use as-is
                    wav_buffer.seek(0)
                    audio_to_process = audio_bytes
            except:
                # Not a valid WAV, assume raw audio and add headers
                # Default to 16kHz mono 16-bit (Whisper standard)
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(16000)  # 16kHz
                    wav_file.writeframes(audio_bytes)
                audio_to_process = wav_buffer.getvalue()
        except Exception as e:
            print(f"Audio processing error: {e}")
            # Fallback: try to process as-is
            audio_to_process = audio_bytes
        
        # Write audio to temp file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_to_process)
            tmp_path = Path(tmp.name)
        
        try:
            # Transcribe
            segments, info = self._stt_model.transcribe(str(tmp_path), language="en")
            text = " ".join(segment.text for segment in segments)
            return text.strip()
        finally:
            tmp_path.unlink(missing_ok=True)
    
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

    def synthesize_speech_streaming(self, text: str):
        """Stream synthesize speech using Piper TTS.
        
        Yields audio chunks with WAV headers as they are generated.
        """
        from piper import PiperVoice
        import wave
        import io
        
        # Lazy load the voice model
        if self._tts_voice is None:
            self._tts_voice = PiperVoice.load(self.tts_model_path, self.tts_config_path)
        
        # First, yield WAV header
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self._tts_voice.config.sample_rate)
            # Write empty data to create header
            wav_file.writeframes(b'')
        
        wav_buffer.seek(0)
        wav_header = wav_buffer.read(44)  # WAV header is 44 bytes
        yield wav_header
        
        # Stream audio chunks from Piper
        audio_generator = self._tts_voice.synthesize(text)
        for chunk in audio_generator:
            yield chunk.audio_int16_bytes
    
    def run_pipeline(self, audio_bytes: bytes, user_sub: Optional[str] = None, session_id: Optional[str] = None) -> bytes:
        """Run the full pipeline using LangGraph: audio → text → LLM → tools → audio.
        
        Args:
            audio_bytes: Input audio data
            user_sub: User identifier
            session_id: Session identifier for multi-turn conversations
        """
        from app.graph import voice_graph
        from app.skills import get_all_tools
        
        # Initialize state with conversation fields
        initial_state = {
            "audio_bytes": audio_bytes,
            "transcription": None,
            "llm_response": None,
            "tool_results": None,
            "final_audio": None,
            "user_sub": user_sub,
            "messages": [],
            "intent": None,
            "collected_params": {},
            "available_skills": [skill.name for skill in get_all_tools()]
        }
        
        # Configure thread for session management
        config = {"configurable": {"thread_id": session_id or "default"}}
        
        # Run the graph with session config
        result = voice_graph.invoke(initial_state, config=config)
        
        print(f"Transcribed: {result.get('transcription')}")
        print(f"LLM Response: {result.get('llm_response')}")
        print(f"Tool Results: {result.get('tool_results')}")
        print(f"Synthesized audio: {len(result.get('final_audio', b''))} bytes")
        
        return result.get("final_audio", b"")

    async def run_pipeline_streaming(self, audio_bytes: bytes, user_sub: Optional[str] = None, session_id: Optional[str] = None):
        """Run the full pipeline with streaming: audio → text → LLM → tools → audio.
        
        Uses voice_graph for proper tool handling, streams TTS output.
        """
        from app.graph import voice_graph
        from app.skills import get_all_tools
        
        # Step 1: Stream transcribe audio
        transcription = ""
        for partial_text in self.transcribe_audio_streaming(audio_bytes):
            transcription = partial_text
        
        print(f"Transcription: {transcription}")
        
        # Step 2: Use voice_graph for LLM + tools (non-streaming for now)
        initial_state = {
            "audio_bytes": audio_bytes,
            "transcription": transcription,
            "llm_response": None,
            "tool_results": None,
            "final_audio": None,
            "user_sub": user_sub,
            "messages": [],
            "intent": None,
            "collected_params": {},
            "available_skills": [skill.name for skill in get_all_tools()]
        }
        
        config = {"configurable": {"thread_id": session_id or "default"}}
        result = voice_graph.invoke(initial_state, config=config)
        
        print(f"LLM Response: {result.get('llm_response')}")
        print(f"Tool Results: {result.get('tool_results')}")
        
        # Step 3: Stream TTS audio
        text_to_speak = result.get("tool_results") or result.get("llm_response", "")
        
        try:
            chunk_count = 0
            for audio_chunk in self.synthesize_speech_streaming(text_to_speak):
                chunk_count += 1
                yield audio_chunk
            print(f"TTS: Sent {chunk_count} audio chunks")
        except Exception as e:
            print(f"TTS error: {e}")
            raise