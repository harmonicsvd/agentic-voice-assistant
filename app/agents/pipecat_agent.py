"""
Pipecat Voice Agent Pipeline

This module uses the Pipecat framework to handle real-time voice interactions.
Following the official Pipecat architecture with Pipeline, PipelineWorker, and proper transport.
"""

import os
import logging
import asyncio
import difflib
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineWorker
from pipecat.workers.runner import WorkerRunner
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.workers.llm.llm_context_worker import LLMContext, LLMContextAggregatorPair, LLMUserAggregatorParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from app.skills import get_skill_prompts
from app.graph.tool_config import get_formatted_context
from pipecat.frames.frames import (
    AudioRawFrame, TextFrame, TranscriptionFrame,
    UserStartedSpeakingFrame, UserStoppedSpeakingFrame,
    BotStartedSpeakingFrame, BotStoppedSpeakingFrame,
    TTSSpeakFrame, TTSStartedFrame, TTSStoppedFrame,
    LLMFullResponseStartFrame, LLMFullResponseEndFrame,
    LLMRunFrame, Frame, StartFrame
)
from pipecat.processors.frame_processor import FrameDirection

from app.graph.state import PlannerState
from app.graph.planner import LangGraphPlanner
from app.graph.tool_config import is_read_only_tool, is_write_enabled_tool
import time
from datetime import datetime
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
    
    def __init__(self, log_file="conversations.txt", tool_executor=None, wake_word_processor=None):
        super().__init__()
        self.speech_start_time = None
        self.stt_start_time = None
        self.llm_start_time = None
        self.tts_start_time = None
        self.audio_buffer = []
        self.log_file = log_file
        self.wake_word_processor = wake_word_processor
        self.tool_executor=tool_executor
        self.last_bot_speech_time = None
        self.sleep_timeout = 10  # seconds of silence before sleep
        self.wake_up_latency_start = None  # Track wake-up latency

        # Create log file with timestamp header
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n{'='*60}\n")
            f.write(f"NEW CONVERSATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n")  

    async def process_frame(self, frame, direction):
        frame_name = frame.__class__.__name__

        # Check for timeout-based sleep
        if not self.wake_word_processor.is_sleeping and self.last_bot_speech_time:
            time_since_last_speech = time.time() - self.last_bot_speech_time
            if time_since_last_speech > self.sleep_timeout:
                logger.info(f"💤 Timeout: No user response for {time_since_last_speech:.0f}s - putting agent to sleep")
                self.wake_word_processor.set_sleep_state(True)  # Automatic sleep
                self.last_bot_speech_time = None
            
        # Track user speech
        if isinstance(frame, UserStartedSpeakingFrame):
            self.last_bot_speech_time = None 
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
                
        # Track STT - save to file
        elif isinstance(frame, TranscriptionFrame):
            if self.stt_start_time:
                latency = (time.time() - self.stt_start_time) * 1000
                logger.info(f"\n📝 TRANSCRIPTION: \"{frame.text}\" (STT latency: {latency:.0f}ms)")
                self.stt_start_time = None
            else:
                logger.info(f"\n📝 TRANSCRIPTION: \"{frame.text}\"")
            
            # Save to file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"USER: {frame.text}\n")
        
        elif isinstance(frame, TextFrame):
            if self.stt_start_time:
                latency = (time.time() - self.stt_start_time) * 1000
                logger.info(f"\n📝 TEXT: \"{frame.text}\" (STT latency: {latency:.0f}ms)")
                self.stt_start_time = None
            else:
                logger.info(f"\n📝 TEXT: \"{frame.text}\"")
            
            # Save to file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"USER: {frame.text}\n")
                
        # Track LLM
        elif isinstance(frame, LLMFullResponseStartFrame):
            self.llm_start_time = time.time()
            
            # Check if this is a wake-up response and measure latency
            if self.wake_word_processor.wake_start_time:
                wake_to_llm_latency = (time.time() - self.wake_word_processor.wake_start_time) * 1000
                logger.info(f"⏱️ WAKE-UP LATENCY: Wake word → LLM start: {wake_to_llm_latency:.0f}ms")
                self.wake_up_latency_start = self.wake_word_processor.wake_start_time
                self.wake_word_processor.wake_start_time = None  # Reset after measuring
            
            logger.info("\n" + "=" * 50)
            logger.info("🤖 LLM PROCESSING")
            logger.info("=" * 50)
        
        elif isinstance(frame, LLMFullResponseEndFrame):
            if self.llm_start_time:
                latency = (time.time() - self.llm_start_time) * 1000
                logger.info(f"\n🤖 LLM COMPLETE (latency: {latency:.0f}ms)")
                self.llm_start_time = None
        
        # Track TTS - save bot response to file
        elif isinstance(frame, TTSSpeakFrame):
            self.tts_start_time = time.time()
            logger.info(f"\n🔊 TTS STARTED: \"{frame.text}\"")
            
            # Save bot response to file
            if frame.text:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"RAM: {frame.text}\n")
                    f.flush()  # Ensure immediate write
        
        elif isinstance(frame, TTSStartedFrame):
            # Check if this is a wake-up response and measure total latency
            if self.wake_up_latency_start:
                wake_to_tts_latency = (time.time() - self.wake_up_latency_start) * 1000
                logger.info(f"⏱️ WAKE-UP LATENCY: Wake word → TTS audio start: {wake_to_tts_latency:.0f}ms")
                self.wake_up_latency_start = None  # Reset after measuring
            
            logger.info("🔊 TTS AUDIO STARTED")
        
        elif isinstance(frame, TTSStoppedFrame):
            if self.tts_start_time:
                duration = time.time() - self.tts_start_time
                logger.info(f"🔊 TTS FINISHED (duration: {duration:.2f}s)")
                self.tts_start_time = None
        
        # Track bot speech
        elif isinstance(frame, BotStoppedSpeakingFrame):
            # Check if this is a wake-up response and measure end-to-end latency
            if self.wake_up_latency_start:
                wake_to_speech_latency = (time.time() - self.wake_up_latency_start) * 1000
                logger.info(f"⏱️ WAKE-UP LATENCY: Wake word → Bot stopped speaking (END-TO-END): {wake_to_speech_latency:.0f}ms")
                self.wake_up_latency_start = None  # Reset after measuring
            
            # Track last bot speech time for timeout
            self.last_bot_speech_time = time.time()
            logger.info("\n🤖 BOT STOPPED SPEAKING")
            
            # Sleep is now only handled by timeout inactivity, not by response content
            # Track last bot speech time for timeout
            self.last_bot_speech_time = time.time()
            logger.info("\n🤖 BOT STOPPED SPEAKING")
            
            # Sleep is now only handled by timeout inactivity, not by response content
                
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)


async def _generate_concise_summary(conversation_history: list, params: dict, llm) -> str:
    """
    Generate a concise summary from conversation history and parameters using LLM.
    
    This avoids long repetitive confirmations by asking the LLM to summarize
    the conversation context in 1-2 sentences. Works for all tools, not just events.
    
    Only calls LLM if context is large (>500 chars), otherwise uses parameter-based summary.
    """
    if not conversation_history and not params:
        return ""
    
    # Calculate context size (character count)
    context_size = sum(len(msg.get('content', '')) for msg in conversation_history if msg.get('role') != 'system')
    
    # If context is small, use parameter-based summary (faster, no LLM call)
    if context_size < 500:
        logger.info(f"📝 Context small ({context_size} chars), using param-based summary")
        return _generate_param_summary(params)
    
    # Context is large, use LLM summarization
    logger.info(f"📝 Context large ({context_size} chars), using LLM summarization")
    
    # Build context from params if available
    params_text = ""
    if params:
        params_text = f"\nCollected parameters: {params}"
    
    # Get recent conversation history (last 10 messages)
    recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
    
    # Format history for LLM
    history_text = "\n".join([
        f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
        for msg in recent_history
        if msg.get('role') != 'system'  # Skip system messages
    ])
    
    summarization_prompt = f"""Summarize this conversation in 1-2 sentences maximum for confirmation purposes.

Conversation history:
{history_text}
{params_text}

CRITICAL RULES:
- DO NOT say "booked", "scheduled", "created", "done", or claim any action was completed
- ONLY describe what was discussed/requested, not what was done
- Say "User wants to book..." or "User requested to book..." NOT "User confirmed to book..." or "Booked..."
- Focus on the request/intent, not the execution
- Use neutral language about the request status

Rules:
- Be extremely concise (1-2 sentences max)
- Focus on the key action/request
- Don't repeat unnecessary details
- Output ONLY the summary, no other text

Example outputs:
- "User wants to book a meeting with Alex today at 3PM for 4 hours online."
- "User wants to book two meetings for today."
- "Check meetings for tomorrow."
- "Weather in Berlin."

Summary:"""

    try:
        # Use Groq API directly for summarization
        import httpx
        import os
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not set - using fallback summarization")
            raise Exception("GROQ_API_KEY not set")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",  # Use Groq's Llama 3.3 70B model
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Summarize the following meeting parameters in a single sentence. Be concise."},
                        {"role": "user", "content": summarization_prompt}
                    ],
                    "temperature": 0.1
                },
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            logger.info(f"📝 LLM-generated summary: {summary}")
            return summary
    except Exception as e:
        logger.error(f"❌ Summarization error: {str(e)}")
        # Fallback to parameter-based summary
        return _generate_param_summary(params)


def _format_date_for_speech(date_str: str) -> str:
    """Convert ISO date (2026-08-01) to natural language for TTS."""
    if not date_str:
        return ""
    
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Check if it's today
        today = datetime.now().date()
        if date_obj.date() == today:
            return "today"
        
        # Format as "August 1st" or "August 1"
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        month = month_names[date_obj.month - 1]
        day = date_obj.day
        
        # Add ordinal suffix (1st, 2nd, 3rd, etc.)
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        
        return f"{month} {day}{suffix}"
    except:
        return date_str


def _format_time_for_speech(time_str: str) -> str:
    """Convert 24h time (16:00) to natural language for TTS."""
    if not time_str:
        return ""
    
    try:
        # Handle "null" string
        if time_str.lower() == "null":
            return ""
        
        hour = int(time_str.split(":")[0])
        
        # Convert to 12-hour format
        if hour == 0:
            return "12 AM"
        elif hour < 12:
            return f"{hour} AM"
        elif hour == 12:
            return "12 PM"
        else:
            return f"{hour - 12} PM"
    except:
        return time_str


def _generate_param_summary(params: dict) -> str:
    """
    Fallback: Generate summary from parameters only (no LLM).
    """
    if not params:
        return ""
    
    parts = []
    
    # Meeting title/name
    if params.get("title"):
        parts.append(params["title"])
    elif params.get("name"):
        parts.append(f"Meeting with {params['name']}")
    
    # Date and time - convert to natural language
    date = params.get("date")
    time = params.get("time")
    formatted_date = _format_date_for_speech(date) if date else ""
    formatted_time = _format_time_for_speech(time) if time else ""
    
    if formatted_date and formatted_time:
        parts.append(f"on {formatted_date} at {formatted_time}")
    elif formatted_date:
        parts.append(f"on {formatted_date}")
    elif formatted_time:
        parts.append(f"at {formatted_time}")
    
    # Duration
    if params.get("duration"):
        parts.append(f"for {params['duration']}")
    
    # Meeting mode
    if params.get("meeting_mode") == "online":
        parts.append("online")
    elif params.get("meeting_mode") == "in_person":
        parts.append("in-person")
    
    # Description (truncate if too long)
    if params.get("description"):
        desc = params["description"]
        if len(desc) > 30:
            desc = desc[:30] + "..."
        parts.append(f"about {desc}")
    
    return " ".join(parts) + "." if parts else ""


class WakeWordProcessor(FrameProcessor):
    """Processes wake word detection when agent is sleeping."""
    
    def __init__(self, sleep_state_callback=None):
        super().__init__()
        self.is_sleeping = False  # Start in awake state - agent is ready to respond
        self.wake_phrases = ["wake up emo", "hey emo", "hey emo, are you there?", "wake up", "emo"]  # Wake word phrases
        # Add phonetic variations for accent tolerance
        self.phonetic_variations = [
            "ve cop", "veckop", "ve cop i'm on", "wake ip", "way up", 
            "vake up", "weck up", "wak up", "wakeup", "wake-ip",
            "hey eemo", "hey imo", "hey emmo", "a emo", "e mo",
            "lemo", "immo", "eemo", "emmo",
            # Additional variations for wake up
            "vekabimo", "vecopément", "vekab", "vek op", "vekkop",
            "vécop", "vécopé", "vécopé ment", "ve copa", "ve copa ment",
            "way cop", "way cop", "wey cop", "wei cop",
            # Phonetic variations for "hey emo, are you there?"
            "hey mo are you there", "hey mo are you there?", "hey mo are u there",
            "hey imo are you there", "hey emmo are you there", "hey eemo are you there",
            "hey mo r u there", "hey mo r u there?", "hey emo r u there",
            "hey em are you there", "hey em are u there", "hey emo are u there",
            # Additional variations for are you there
            "are you there", "are u there", "r u there", "you there",
            "hey you there", "hey are you there", "hey r u there"
        ]
        self.sleep_state_callback = sleep_state_callback  # Callback to notify frontend
        self.wake_start_time = None  # Track when wake word was detected
        self.sleep_audio_start_time = None  # Track when audio started while sleeping
        self.max_sleep_audio_duration = 15.0  # Max seconds to buffer audio while sleeping (prevents queue buildup)
    
    def set_sleep_state(self, sleeping: bool):
        """Set the sleep state of the agent.
        
        Args:
            sleeping: Whether the agent should be sleeping
        """
        self.is_sleeping = sleeping
        logger.info(f"💤 Agent sleep state set to: {'sleeping' if sleeping else 'awake'}")
        
        # Notify frontend via callback (both when going to sleep and waking up)
        if self.sleep_state_callback:
            try:
                status = "Sleeping" if sleeping else "Awake"
                if asyncio.iscoroutinefunction(self.sleep_state_callback):
                    asyncio.create_task(self.sleep_state_callback(status))
                else:
                    def sync_wrapper():
                        try:
                            self.sleep_state_callback(status)
                        except Exception as e:
                            logger.error(f"Error in sync callback: {e}")
                    asyncio.create_task(sync_wrapper())
            except Exception as e:
                logger.error(f"Error calling sleep state callback: {e}")

    def _extract_wake_word_phrase(self, text: str) -> str:
        """Extract just the wake word phrase from mixed transcriptions.
        
        Example: "Hey pass the salt wake up" → "wake up"
        """
        text_lower = text.lower().strip()
        
        # Find the wake word in the text
        for phrase in self.wake_phrases + self.phonetic_variations:
            if phrase in text_lower:
                # Extract the phrase and a bit of context around it
                start_idx = text_lower.find(phrase)
                # Get 50 chars before and after for context
                context_start = max(0, start_idx - 50)
                context_end = min(len(text), start_idx + len(phrase) + 50)
                extracted = text[context_start:context_end].strip()
                
                # If the extracted text is much longer than the wake word,
                # try to extract just the wake word part
                if len(extracted) > len(phrase) * 3:
                    # Try to find sentence boundaries
                    words = extracted.split()
                    phrase_words = phrase.split()
                    
                    # Find the wake word in the extracted words
                    for i, word in enumerate(words):
                        if phrase_words[0] in word.lower():
                            # Extract from this word onwards
                            result = ' '.join(words[i:i+len(phrase_words)+2])  # +2 for buffer
                            return result if result else phrase
                
                return extracted if extracted else phrase
        
        return text  # Return original if no wake word found
    
    def is_wake_word(self, text: str) -> bool:
        """Check if the text contains a wake word using exact and fuzzy matching."""
        text_lower = text.lower().strip()
        
        # First try exact matching (fastest)
        for phrase in self.wake_phrases:
            if phrase in text_lower:
                logger.info(f"🔊 Wake word detected (exact): '{phrase}' in '{text}'")
                return True
        
        # Then try fuzzy matching for phonetic variations (medium speed)
        for variation in self.phonetic_variations:
            if variation in text_lower:
                logger.info(f"🔊 Wake word detected (phonetic): '{variation}' in '{text}'")
                return True
        
        # Only do expensive fuzzy matching if text is reasonably short (optimization)
        if len(text_lower) < 30:  # Increased from 20 to handle longer wake phrases
            for phrase in self.wake_phrases + self.phonetic_variations:
                # Check if the text is similar to any wake word phrase
                similarity = difflib.SequenceMatcher(None, text_lower, phrase).ratio()
                if similarity > 0.70:  # Lowered threshold slightly for longer phrases
                    logger.info(f"🔊 Wake word detected (fuzzy {similarity:.2f}): '{phrase}' ~ '{text}'")
                    return True
        
        return False

    async def process_frame(self, frame, direction):
        # Always call parent's process_frame first to handle StartFrame properly
        await super().process_frame(frame, direction)
        
        # CRITICAL: Always let audio frames pass through to STT even when sleeping
        # This ensures wake words can be detected
        if isinstance(frame, AudioRawFrame):
            # Track audio duration when sleeping to prevent queue buildup
            if self.is_sleeping:
                if self.sleep_audio_start_time is None:
                    self.sleep_audio_start_time = time.time()
                else:
                    audio_duration = time.time() - self.sleep_audio_start_time
                    if audio_duration > self.max_sleep_audio_duration:
                        logger.warning(f"⚠️ Sleep audio buffer exceeded {self.max_sleep_audio_duration}s - resetting to prevent STT queue buildup")
                        self.sleep_audio_start_time = time.time()  # Reset timer
            
            await self.push_frame(frame, direction)
            return
        
        # Handle wake word logic for TranscriptionFrame
        if isinstance(frame, TranscriptionFrame):
            logger.info(f"📝 WakeWordProcessor received transcription: '{frame.text}', sleeping: {self.is_sleeping}")
            
            if self.is_sleeping:
                # Check for wake word
                if self.is_wake_word(frame.text):
                    # Wake word detected - wake up immediately and let transcription pass through
                    self.wake_start_time = time.time()
                    logger.info("🎯 Wake word detected - waking up agent immediately")
                    
                    # Reset sleep audio timer
                    self.sleep_audio_start_time = None
                    
                    # Extract just the wake word part for cleaner LLM response
                    cleaned_text = self._extract_wake_word_phrase(frame.text)
                    if cleaned_text != frame.text:
                        logger.info(f"🧹 Cleaned wake word transcription: '{frame.text}' → '{cleaned_text}'")
                        # Modify the existing frame's text instead of creating new one
                        frame.text = cleaned_text
                    
                    # Send "Waking up" state first for better UX
                    if self.sleep_state_callback:
                        try:
                            if asyncio.iscoroutinefunction(self.sleep_state_callback):
                                await self.sleep_state_callback("Waking up")
                            else:
                                self.sleep_state_callback("Waking up")
                        except Exception as e:
                            logger.error(f"Error sending Waking up state: {e}")
                    
                    # CRITICAL: Update sleep state BEFORE pushing frame through
                    # This prevents ToolExecutionProcessor from blocking the transcription
                    self.set_sleep_state(False)
                    
                    # Pass the (possibly cleaned) frame
                    await self.push_frame(frame, direction)
                    
                    logger.info(f"⏱️ Wake-up started at: {self.wake_start_time:.3f}s")
                else:
                    # No wake word - block the transcription when sleeping
                    logger.info(f"🔇 Agent sleeping - blocking transcription: '{frame.text}'")
                    # Don't push the frame - block it
                    return
            else:
                # Agent is awake - let all transcriptions pass through
                await self.push_frame(frame, direction)
        else:
            # Pass all other frames through (StartFrame, STTMetadataFrame, etc.)
            await self.push_frame(frame, direction)


class ToolExecutionProcessor(FrameProcessor):
    """Ram passes user input to Sham for tool decisions."""

    def __init__(self, planner: LangGraphPlanner, context: LLMContext, llm, wake_word_processor):
        super().__init__()
        self.planner = planner
        self.context = context
        self.llm = llm  # LLM for summarization
        self.accumulated_params = {}  # Persist params across conversation turns
        self.active_tool = None  # Track which tool is currently active
        self.wake_word_processor = wake_word_processor  # Reference to wake word processor
        self._should_sleep_after_response = False  # Flag to sleep after unclear responses

    async def process_frame(self, frame, direction):
        frame_name = frame.__class__.__name__

        # Check if this is a wake word transcription - allow it through even if sleeping
        is_wake_word = False
        if isinstance(frame, TranscriptionFrame):
            text_lower = frame.text.lower().strip()
            wake_phrases = ["wake up emo", "hey emo", "hey emo, are you there?", "wake up", "emo"]
            is_wake_word = any(phrase in text_lower for phrase in wake_phrases)
            if is_wake_word:
                logger.info(f"🎯 ToolExecutionProcessor detected wake word - allowing through: '{frame.text}'")

        # CRITICAL: Always let audio frames pass through even when sleeping
        # This ensures wake words can be transcribed by STT
        if isinstance(frame, AudioRawFrame):
            await super().process_frame(frame, direction)
            await self.push_frame(frame, direction)
            return

        # Comprehensive sleep blocking - block ALL processing when sleeping
        # EXCEPT for wake word transcriptions which should pass through to LLM
        if self.wake_word_processor.is_sleeping and not is_wake_word:
            # Block all transcriptions when sleeping (except wake words)
            if isinstance(frame, TranscriptionFrame):
                logger.info(f"🔇 Agent sleeping - blocking ALL transcription processing: '{frame.text}'")
                return  # Don't process anything when sleeping
            # Block all other frames when sleeping (except critical control frames)
            elif not isinstance(frame, (StartFrame, Frame)):
                logger.info(f"🔇 Agent sleeping - blocking frame: {frame_name}")
                return  # Block all non-control frames when sleeping

        # Process transcription frames - check if tool execution is needed
        if isinstance(frame, TranscriptionFrame):
            user_input = frame.text
            logger.info(f"🎤 Received transcription: {user_input}")

            # Get conversation context
            messages = self.context.get_messages() if hasattr(self.context, 'get_messages') else []

            # Call planner to detect if tool is needed
            result = await self.planner.plan_and_execute(
                user_input,
                conversation_history=messages,
                accumulated_params=self.accumulated_params
            )

            # Update accumulated params from result
            if result.get("collected_params"):
                self.accumulated_params.update(result["collected_params"])
                logger.info(f"📤 Accumulated params updated: {self.accumulated_params}")
            
            # Store the active tool for context formatting
            if result.get("detected_tools"):
                self.active_tool = result["detected_tools"][0] if result["detected_tools"] else None
                logger.info(f"🎯 Active tool set: {self.active_tool}")

            # Check if general_conversation was detected - this means user wants general advice/chat
            detected_tools = result.get("detected_tools", [])
            if "general_conversation" in detected_tools:
                logger.info(f"💬 General conversation detected - switching to conversational mode")
                # Clear any accumulated params since this is not meeting-related
                self.accumulated_params = {}
                self.active_tool = None
                # Add a system message to inform the LLM this is general conversation
                self.context.add_message({
                    "role": "system",
                    "content": "The user is asking a general question or seeking advice. Respond naturally and helpfully without trying to force it into a meeting context. Just have a normal conversation."
                })
                logger.info(f"📥 Added 'general conversation' message to context")
                # Add the user's message to context for the LLM to respond
                self.context.add_message({
                    "role": "user",
                    "content": user_input
                })
                logger.info(f"📥 Added user message to context for general conversation")
                # Skip the rest of the tool result handling since there are no results
                # Continue to the end of the function to let the LLM respond normally
                result["tool_results"] = []  # Ensure tool_results is empty list to skip result processing
            
            # Check if no tool was detected - this means the planner decided no action is needed
            # In this case, we should NOT add fake tool results to the context
            elif not detected_tools and not result["tool_results"]:
                logger.info(f"🚫 No tool detected and no tool results - skipping fake result injection")
                
                # Clear params but don't sleep - keep agent awake for conversation
                was_in_task = self.active_tool is not None
                self.accumulated_params = {}
                self.active_tool = None
                
                # Don't automatically sleep - let the conversation continue naturally
                # Sleep should only happen via timeout or explicit user action
                logger.info(f"� General conversation - keeping agent awake")
                
                # Add a system message to inform the LLM that no action was taken
                self.context.add_message({
                    "role": "system",
                    "content": "No action was taken. The user's input did not require any tool execution. Respond naturally to continue the conversation."
                })
                logger.info(f"📥 Added 'no action taken' message to context")
                # Add the user's message to context for the LLM to respond
                self.context.add_message({
                    "role": "user",
                    "content": user_input
                })
                logger.info(f"📥 Added user message to context for conversational response")
                    
                # Skip the rest of the tool result handling since there are no results
                # Continue to the end of the function to let the LLM respond normally
                result["tool_results"] = []  # Ensure tool_results is empty list to skip result processing

            # Handle tool results or lack thereof
            if result["tool_results"]:
                tool_result_text = "\n".join([
                    f"Tool {r['tool']}: {r['result']}"
                    for r in result["tool_results"]
                ])

                # Check if any tool failed
                has_failure = any("failed" in r["result"].lower() or "error" in r["result"].lower() for r in result["tool_results"])

                if has_failure:
                    self.context.add_message({
                        "role": "system",
                        "content": f"CRITICAL: Tool execution FAILED. Sham's tool results:\n{tool_result_text}\n\nDO NOT say 'booked' or 'scheduled' or claim any action was taken. Inform the user there was an error and ask them to try again."
                    })
                    logger.info(f"📥 Tool failure detected - informing LLM")
                else:
                    # Use the active tool set to determine tool type instead of trying to extract from result
                    # The result structure doesn't preserve the original tool name, but we track it in active_tools
                    has_write_enabled_tool = False
                    has_read_only_tool = False
                    actual_tool_names = []
                    
                    # Get active tools from the result
                    active_tools = result.get("active_tools", [])
                    logger.info(f"📥 Active tools from result: {active_tools}")
                    
                    for tool_name in active_tools:
                        actual_tool_names.append(tool_name)
                        # Check if this tool is write-enabled or read-only
                        if is_write_enabled_tool(tool_name):
                            has_write_enabled_tool = True
                            logger.info(f"📥 Found write-enabled tool: {tool_name}")
                        elif is_read_only_tool(tool_name):
                            has_read_only_tool = True
                            logger.info(f"📥 Found read-only tool: {tool_name}")
                    
                    logger.info(f"📥 Tool analysis - names: {actual_tool_names}, has_write_enabled: {has_write_enabled_tool}, has_read_only: {has_read_only_tool}")

                    if has_write_enabled_tool:
                        # At least one write-enabled tool was executed - confirm the action
                        # Generic approach: works for create_event_tool and any future write-enabled tools
                        num_results = len(result.get("tool_results", []))
                        
                        if num_results > 1:
                            confirmation_msg = f"Sham's tool results:\n{tool_result_text}\n\nIMPORTANT: All {num_results} actions have been successfully completed. Confirm this to the user in a brief, natural way. Do NOT ask if anything else is needed - just confirm the completion."
                        else:
                            confirmation_msg = f"Sham's tool results:\n{tool_result_text}\n\nIMPORTANT: The action has been successfully completed. Confirm this to the user in a brief, natural way (e.g., 'Great, I've done that for you.'). Do NOT ask if anything else is needed - just confirm the completion."
                    elif has_read_only_tool:
                        # All tools are read-only - just share information
                        confirmation_msg = f"TOOL EXECUTION RESULTS:\n{tool_result_text}\n\nYour task: Share this information with the user in a brief, natural way. Do NOT mention 'tool results' or 'Sham'. Just tell the user what you found in a conversational manner. DO NOT claim any booking or scheduling happened - this is read-only information."
                    else:
                        # Fallback for unknown tools or tools not in config
                        confirmation_msg = f"TOOL EXECUTION RESULTS:\n{tool_result_text}\n\nYour task: Share this information with the user in a brief, natural way."

                    self.context.add_message({
                        "role": "system",
                        "content": confirmation_msg
                    })
                    logger.info(f"📥 Sham results added to Ram's context")
                    # Preserve all_meetings before reset
                    all_meetings_to_preserve = self.accumulated_params.get("all_meetings")
                    self.accumulated_params = {}
                    self.active_tool = None  # Reset active tool on cancellation
                    if all_meetings_to_preserve:
                        self.accumulated_params["all_meetings"] = all_meetings_to_preserve
            
            elif result.get("plan_complete"):
                # Tool execution completed successfully
                logger.info(f"✅ Tool execution completed, resetting active tool")
                self.active_tool = None  # Reset active tool after completion
            else:
                # No tool executed - this is just conversation
                logger.info(f"🚫 No tool execution - passing transcription to LLM")
                
                # Check if execution was skipped due to missing required fields
                missing_fields = result.get("missing_required_fields")
                logger.info(f"🔍 DEBUG: missing_required_fields from result: {missing_fields}")
                if missing_fields:
                    # Provide specific feedback to LLM about what's missing
                    missing_fields_msg = f"EMERGENCY: TOOL EXECUTION WAS SKIPPED. The action was NOT completed. Required fields are missing: {', '.join(missing_fields)}. DO NOT say 'booked', 'scheduled', 'done', 'completed', or claim any action was taken. Ask the user for the missing information: {', '.join(missing_fields)}. This is critical - the backend did NOT execute the tool."
                    self.context.add_message({
                        "role": "system",
                        "content": missing_fields_msg
                    })
                    logger.info(f"🚫 Added missing fields feedback to LLM: {missing_fields}")
                
                # Add context about collected parameters to help Ram understand the conversation state
                if self.accumulated_params and self.active_tool:
                    # Use dynamic context formatter from tool config
                    context_msg = get_formatted_context(self.active_tool, self.accumulated_params)
                    
                    if context_msg:
                        # Add as system message to give Ram visibility into what's been collected
                        self.context.add_messages([{"role": "system", "content": context_msg}])
                        logger.info(f"🧠 Added parameter context to Ram ({self.active_tool}): {context_msg[:100]}...")

        # Pass all frames through
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)


def create_voice_agent_pipeline(transport, user_sub: str = None, sleep_state_callback=None):
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

    current_date = datetime.now().strftime("%B %d, %Y")
    current_day = datetime.now().strftime("%A")

    # Get API keys from environment
    # Use Groq API directly instead of OmniRoute
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is required but not set. Please get your API key from https://console.groq.com/keys and add it to your .env file.")

    # Initialize STT service (Whisper)
    # Using "base" model for speed - if you need better accent recognition, change to "small"
    # "base" = faster, "small" = better accents but slower, "medium" = best accuracy but slowest
    stt = WhisperSTTService(
        settings=WhisperSTTService.Settings(
            model="base",  # Changed back to base for speed - small was too slow
            language="en"
        )
    )
    logger.info("Whisper STT service initialized with base model for speed")


    # Initialize LangGraph planner for tool execution
    planner = LangGraphPlanner(user_sub=user_sub)
    logger.info("LangGraph planner initialized")



    # Get dynamic skills prompts
    skills_prompts = get_skill_prompts()
    logger.info(f"Loaded skills context with {len(skills_prompts)} characters")

    # Load system prompt (try full prompt first, fallback to simplified)
    try:
        with open("app/prompts/system_prompt_backup.txt", "r") as f:
            system_prompt = f.read().format(current_date=current_date, current_day=current_day, skills_prompts=skills_prompts)
        logger.info("Using full system prompt")
    except Exception as e:
        logger.warning(f"Could not load full prompt: {e}, using fallback")
        try:
            with open("app/prompts/system_prompt_simple.txt", "r") as f:
                system_prompt = f.read().format(current_date=current_date, current_day=current_day)
            logger.info("Using simplified system prompt")
        except Exception as e2:
            logger.warning(f"Could not load simplified prompt: {e2}, using fallback")
            system_prompt = f"""You are Ram, a helpful voice assistant. Today is {current_date} ({current_day}). Keep responses brief."""

    # Initialize LLM service with Groq API directly
    llm = OpenAILLMService(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        settings=OpenAILLMService.Settings(
            model="llama-3.3-70b-versatile",  # Use Groq's Llama 3.3 70B model
            temperature=0,
            system_instruction=system_prompt,
        ),
    )
    logger.info("Groq LLM service initialized with Llama 3.3 70B")
    
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
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    stop_secs=0.4,  # Wait 0.8 seconds of silence before considering user finished (prevents premature triggers on natural pauses)
                ),
            ),
            # Disable filter_incomplete_user_turns to prevent Smart Turn from sending extra API calls for incomplete detection
            filter_incomplete_user_turns=False,
        ),
    )


     # Create wake word processor for sleep/wake functionality
    wake_word_processor = WakeWordProcessor(sleep_state_callback=sleep_state_callback)
    tool_executor = ToolExecutionProcessor(planner, context, llm, wake_word_processor)


   # Build the pipeline with ConversationLogger and ToolExecutionProcessor
    conversation_logger = ConversationLogger(tool_executor=tool_executor, wake_word_processor=wake_word_processor)
    
   
    pipeline = Pipeline(
    [
        transport.input(),  # Transport user input
        stt,  # STT
        wake_word_processor,  # Check for wake word when sleeping AND intercept sleep/wake commands
        tool_executor,  # Execute tools via LangGraph (intercept transcriptions)
        user_aggregator,  # User responses (handles VAD internally)
        llm,  # LLM
        tts,  # TTS
        transport.output(),  # Transport bot output
        assistant_aggregator,  # Assistant spoken responses
        conversation_logger,  # Log conversation lifecycle (after TTS to capture bot responses)
    ]
)
    
    
    # Create pipeline worker with pipeline
    worker = PipelineWorker(
        pipeline,
    )
    
    # Create runner
    runner = WorkerRunner(handle_sigint=False)
    
    logger.info("Pipecat pipeline created successfully")
    return worker, runner, context, planner, wake_word_processor
