"""
Pipecat Voice Agent Pipeline

This module uses the Pipecat framework to handle real-time voice interactions.
Following the official Pipecat architecture with Pipeline, PipelineWorker, and proper transport.
"""

import os
import logging
from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineWorker
from pipecat.workers.runner import WorkerRunner
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.workers.llm.llm_context_worker import LLMContext, LLMContextAggregatorPair, LLMUserAggregatorParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from app.skills import get_skill_prompts
from pipecat.frames.frames import (
    AudioRawFrame, TextFrame, TranscriptionFrame,
    UserStartedSpeakingFrame, UserStoppedSpeakingFrame,
    BotStartedSpeakingFrame, BotStoppedSpeakingFrame,
    TTSSpeakFrame, TTSStartedFrame, TTSStoppedFrame,
    LLMFullResponseStartFrame, LLMFullResponseEndFrame,
    LLMRunFrame
)
import time
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable verbose Pipecat debug logging
# Temporarily enable DEBUG for serializers to see frame serialization/deserialization
logging.getLogger("pipecat").setLevel(logging.DEBUG)
logging.getLogger("pipecat.serializers").setLevel(logging.DEBUG)
logging.getLogger("pipecat.serializers.protobuf").setLevel(logging.DEBUG)

class ConversationLogger(FrameProcessor):
    """Clean, production-style logger for voice conversation lifecycle."""
    
    def __init__(self):
        super().__init__()
        self.speech_start_time = None
        self.stt_start_time = None
        self.llm_start_time = None
        self.tts_start_time = None
        self.audio_buffer = []
    
    async def process_frame(self, frame, direction):
        frame_name = frame.__class__.__name__
        
        # Track user speech
        if isinstance(frame, UserStartedSpeakingFrame):
            self.speech_start_time = time.time()
            self.audio_buffer = []
            logger.info("\n" + "=" * 50)
            logger.info("🎤 USER STARTED SPEAKING")
            logger.info("=" * 50)
        
        elif isinstance(frame, UserStoppedSpeakingFrame):
            if self.speech_start_time:
                duration = time.time() - self.speech_start_time
                avg_rms = np.mean(self.audio_buffer) if self.audio_buffer else 0
                logger.info(f"\n🎤 USER STOPPED SPEAKING (duration: {duration:.2f}s, avg RMS: {avg_rms:.0f})")
                self.speech_start_time = None
        
        # Track audio levels during speech
        elif isinstance(frame, AudioRawFrame) and self.speech_start_time:
            if hasattr(frame, "audio") and frame.audio:
                audio_data = np.frombuffer(frame.audio, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                self.audio_buffer.append(rms)
                
        # Track STT
        elif isinstance(frame, TranscriptionFrame):
            if self.stt_start_time:
                latency = (time.time() - self.stt_start_time) * 1000
                logger.info(f"\n📝 TRANSCRIPTION: \"{frame.text}\" (STT latency: {latency:.0f}ms)")
                self.stt_start_time = None
            else:
                logger.info(f"\n📝 TRANSCRIPTION: \"{frame.text}\"")
        
        elif isinstance(frame, TextFrame):
            if self.stt_start_time:
                latency = (time.time() - self.stt_start_time) * 1000
                logger.info(f"\n📝 TEXT: \"{frame.text}\" (STT latency: {latency:.0f}ms)")
                self.stt_start_time = None
            else:
                logger.info(f"\n📝 TEXT: \"{frame.text}\"")
        
        # Track LLM
        elif isinstance(frame, LLMFullResponseStartFrame):
            self.llm_start_time = time.time()
            logger.info("\n" + "=" * 50)
            logger.info("🤖 LLM PROCESSING")
            logger.info("=" * 50)
        
        elif isinstance(frame, LLMFullResponseEndFrame):
            if self.llm_start_time:
                latency = (time.time() - self.llm_start_time) * 1000
                logger.info(f"\n🤖 LLM COMPLETE (latency: {latency:.0f}ms)")
                self.llm_start_time = None
        
        # Track TTS
        elif isinstance(frame, TTSSpeakFrame):
            self.tts_start_time = time.time()
            logger.info(f"\n🔊 TTS STARTED: \"{frame.text}\"")
        
        elif isinstance(frame, TTSStartedFrame):
            logger.info("🔊 TTS AUDIO STARTED")
        
        elif isinstance(frame, TTSStoppedFrame):
            if self.tts_start_time:
                duration = time.time() - self.tts_start_time
                logger.info(f"🔊 TTS FINISHED (duration: {duration:.2f}s)")
                self.tts_start_time = None
        
        # Track bot speech
        elif isinstance(frame, BotStartedSpeakingFrame):
            logger.info("\n🤖 BOT STARTED SPEAKING")
        
        elif isinstance(frame, BotStoppedSpeakingFrame):
            logger.info("\n🤖 BOT STOPPED SPEAKING")
        
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)
def create_voice_agent_pipeline(transport):
    """
    Create a Pipecat voice agent pipeline.
    
    This follows the official Pipecat pattern:
    transport.input() -> stt -> user_aggregator -> llm -> tts -> transport.output() -> assistant_aggregator
    
    Args:
        transport: Pipecat transport (e.g., Daily, LiveKit, or custom)
    
    Returns:
        tuple: (PipelineWorker, WorkerRunner) ready to run
    """
    logger.info("Creating Pipecat voice agent pipeline")

    # Get API keys from environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")
        
    # Initialize STT service (Whisper with VAD support)
    stt = WhisperSTTService(
        settings=WhisperSTTService.Settings(
            model="base",
            language="en",
        )
    )
    logger.info("Whisper STT service initialized")
    
    # Get dynamic skills prompts
    skills_prompts = get_skill_prompts()
    logger.info(f"Loaded skills context with {len(skills_prompts)} characters")
    
    # Initialize LLM service with dynamic skills context
    llm = GroqLLMService(
        api_key=groq_api_key,
        settings=GroqLLMService.Settings(
            model="llama-3.3-70b-versatile",
            system_instruction=f"""You are Ram, a helpful voice scheduling assistant.

You can help users with the following capabilities:

{skills_prompts}

Your responses will be spoken aloud, so avoid emojis, bullet points, or other formatting that can't be spoken. Respond to what the user said in a creative, helpful, and brief way. Keep responses to 1-2 sentences maximum.""",
        ),
    )
    logger.info("Groq LLM service initialized")
    
    # Initialize TTS service (Piper - open source)
    tts = PiperTTSService(
        settings=PiperTTSService.Settings(
            voice="en_US-lessac-medium",
        )
    )
    logger.info("Piper TTS service initialized")
    
    # Create conversation context
    context = LLMContext()
    
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(),
            # Disable filter_incomplete_user_turns to prevent Smart Turn from sending unsupported frame types to JS SDK 1.5.0
            #filter_incomplete_user_turns=True,
        ),
    )

    # Build the pipeline with ConversationLogger
    conversation_logger = ConversationLogger()
    
    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            stt,  # STT
            user_aggregator,  # User responses (handles VAD internally)
            conversation_logger,  # Log conversation lifecycle (after VAD to see speech events)
            llm,  # LLM
            tts,  # TTS
            transport.output(),  # Transport bot output
            assistant_aggregator,  # Assistant spoken responses
        ]
    )
    
    # Create pipeline worker with pipeline
    worker = PipelineWorker(
        pipeline,
    )
    
    # Create runner
    runner = WorkerRunner(handle_sigint=False)
    
    logger.info("Pipecat pipeline created successfully")
    return worker, runner, context


