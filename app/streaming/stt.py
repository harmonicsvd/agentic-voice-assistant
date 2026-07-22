"""Streaming Speech-to-Text service using Deepgram with VAD."""

import os
import threading
from typing import Callable
from deepgram import DeepgramClient
from deepgram.core.events import EventType

# Get Deepgram API key from environment
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

class StreamingSTT:
    """Real-time streaming STT with Deepgram."""
    
    def __init__(self):
        if not DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in environment variables")
        
        # Initialize Deepgram client with keyword argument
        self.client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
        self.context_manager = None
        self.connection = None
        self.is_listening = False
        self.on_transcript_callback = None
        self.on_speech_started_callback = None
        self.on_speech_ended_callback = None
        
    def start_streaming(
        self, 
        on_transcript: Callable[[str], None],
        on_speech_started: Callable[[], None] = None,
        on_speech_ended: Callable[[], None] = None
    ) -> None:
        """Start streaming audio and transcribing in real-time."""
        if self.is_listening:
            return
            
        self.is_listening = True
        
        # Store callbacks
        self.on_transcript_callback = on_transcript
        self.on_speech_started_callback = on_speech_started
        self.on_speech_ended_callback = on_speech_ended
        
        # Create connection with v7.x API using with statement
        self.context_manager = self.client.listen.v1.connect(
            model="nova-3",
            language="en-US",
            smart_format=True,
            interim_results=True,
            vad_events=True,
            encoding="linear16",  # WAV uses linear16 PCM
            sample_rate=16000,  # Common sample rate for WAV
        )
        self.connection = self.context_manager.__enter__()
        
        # Register event handlers
        self.connection.on(EventType.MESSAGE, self._handle_message)
        self.connection.on(EventType.OPEN, lambda _: print("Deepgram connection opened"))
        self.connection.on(EventType.CLOSE, lambda _: print("Deepgram connection closed"))
        self.connection.on(EventType.ERROR, lambda error: print(f"Deepgram error: {error}"))
        
        # Start listening in a separate thread
        self.listen_thread = threading.Thread(target=self.connection.start_listening, daemon=True)
        self.listen_thread.start()
        print("Deepgram streaming STT started")
    
    def send_audio(self, audio_data: bytes) -> None:
        """Send audio chunk to Deepgram for transcription."""
        if self.connection and self.is_listening:
            self.connection.send_media(audio_data)
            print(f"Sent {len(audio_data)} bytes to Deepgram")
        else:
            print(f"Cannot send audio: connection={self.connection is not None}, listening={self.is_listening}")
    
    def stop_streaming(self) -> None:
        """Stop streaming and close connection."""
        if self.context_manager:
            try:
                self.context_manager.__exit__(None, None, None)
            except:
                pass
            self.context_manager = None
            self.connection = None
        self.is_listening = False
        print("Deepgram streaming STT stopped")
    
    def _handle_message(self, message) -> None:
        """Handle messages from Deepgram."""
        msg_type = getattr(message, "type", "Unknown")
        
        if msg_type == "Results":
            # Get the transcript text
            if hasattr(message, 'channel') and hasattr(message.channel, 'alternatives'):
                transcript = message.channel.alternatives[0].transcript
                is_final = message.is_final
                
                if transcript and is_final:
                    # Final transcript - send to callback
                    if self.on_transcript_callback:
                        self.on_transcript_callback(transcript)
                elif transcript:
                    # Interim result (partial transcription)
                    # Could be used for real-time display
                    pass
        
        elif msg_type == "SpeechStarted":
            if self.on_speech_started_callback:
                self.on_speech_started_callback()
        
        elif msg_type == "SpeechEnded":
            if self.on_speech_ended_callback:
                self.on_speech_ended_callback()