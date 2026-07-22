"""Streaming Text-to-Speech service using Deepgram."""

import os
from typing import AsyncGenerator
from deepgram import DeepgramClient
import asyncio

# Get Deepgram API key from environment
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

class StreamingTTS:
    """Real-time streaming TTS with Deepgram."""
    
    def __init__(self):
        if not DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in environment variables")
        
        self.client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
        
    async def synthesize_streaming(
        self, 
        text: str,
        voice: str = "aura-asteria-en"
    ) -> AsyncGenerator[bytes, None]:
        """Stream audio chunks for the given text."""
        try:
            # Stream the audio using v7.x API
            response = self.client.speak.v("1").stream_async(
                text=text,
                model=voice,
                encoding="linear16",
                sample_rate=24000,
                container="none"
            )
            
            # Yield chunks as they arrive
            for chunk in response:
                yield chunk
        except Exception as e:
            print(f"TTS streaming error: {e}")
            raise