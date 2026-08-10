"""
Pipecat Voice Agent Pipeline

This module uses the Pipecat framework to handle real-time voice interactions.
Following the official Pipecat architecture with Pipeline, PipelineWorker, and proper transport.
"""

import os
import logging
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
    
    def __init__(self, log_file="conversations.txt"):
        super().__init__()
        self.speech_start_time = None
        self.stt_start_time = None
        self.llm_start_time = None
        self.tts_start_time = None
        self.audio_buffer = []
        self.log_file = log_file
        # Create log file with timestamp header
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n{'='*60}\n")
            f.write(f"NEW CONVERSATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n")
    
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
        # Use Groq API for summarization
        import httpx
        import os
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            logger.error("❌ GROQ_API_KEY not set")
            return _generate_param_summary(params)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
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


class ToolExecutionProcessor(FrameProcessor):
    """Ram passes user input to Sham for tool decisions."""

    def __init__(self, planner: LangGraphPlanner, context: LLMContext, llm):
        super().__init__()
        self.planner = planner
        self.context = context
        self.llm = llm  # LLM for summarization
        self.accumulated_params = {}  # Persist params across conversation turns
        self.active_tool = None  # Track which tool is currently active

    async def process_frame(self, frame, direction):
        frame_name = frame.__class__.__name__

        # Process transcription frames - check if tool execution is needed
        if isinstance(frame, TranscriptionFrame):
            user_input = frame.text
            logger.info(f"� Received transcription: {user_input}")

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

            # Check if no tool was detected - this means the planner decided no action is needed
            # In this case, we should NOT add fake tool results to the context
            detected_tools = result.get("detected_tools", [])
            if not detected_tools and not result["tool_results"]:
                logger.info(f"🚫 No tool detected and no tool results - skipping fake result injection")
                # Clear any accumulated params since no action is being taken
                self.accumulated_params = {}
                self.active_tool = None
                # Add a system message to inform the LLM that no action was taken
                self.context.add_message({
                    "role": "system",
                    "content": "No action was taken. The user's input did not require any tool execution. Respond naturally to continue the conversation."
                })
                logger.info(f"📥 Added 'no action taken' message to context")
                # Skip the rest of the tool result handling
                return

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
                    # Check if this is a read-only tool by looking at the tool name in the result
                    # Tools are wrapped by proxy_tool, so we need to check the parameters for the actual tool name
                    is_read_only = False
                    for r in result["tool_results"]:
                        tool_name = r.get("tool", "")
                        logger.info(f"📥 Debug tool_name from result: {tool_name}")
                        
                        # If it's proxy_tool, check the parameters for the actual tool name
                        if tool_name == "proxy_tool":
                            params = r.get("parameters", {})
                            # The actual tool name might be in parameters.tool_name or parameters.parameters.tool_name
                            actual_tool_name = params.get("tool_name", "")
                            if not actual_tool_name:
                                # Try nested parameters
                                nested_params = params.get("parameters", {})
                                actual_tool_name = nested_params.get("tool_name", "")
                            logger.info(f"📥 Debug actual_tool_name from proxy_tool params: {actual_tool_name}")
                            if actual_tool_name:
                                tool_name = actual_tool_name
                        
                        # Check if it's a read-only tool (meetings_summary, get_events, etc.)
                        if "meetings_summary" in tool_name.lower() or "get_events" in tool_name.lower() or "get_meetings" in tool_name.lower():
                            is_read_only = True
                            break
                        # Also check the result content for meeting-related keywords
                        result_content = r.get("result", "")
                        if "meetings on" in result_content.lower() or "your meetings" in result_content.lower():
                            is_read_only = True
                            break

                    logger.info(f"📥 is_read_only check: {is_read_only}")

                    if is_read_only:
                        confirmation_msg = f"TOOL EXECUTION RESULTS:\n{tool_result_text}\n\nYour task: Share this information with the user in a brief, natural way. Do NOT mention 'tool results' or 'Sham'. Just tell the user what you found in a conversational manner."
                    else:
                        num_meetings = len(result.get("tool_results", []))
                        if num_meetings > 1:
                            confirmation_msg = f"Sham's tool results:\n{tool_result_text}\n\nIMPORTANT: All {num_meetings} meetings have been successfully booked. Confirm this to the user in a brief, natural way (e.g., 'Great, I've booked both meetings for you.'). Do NOT ask if anything else is needed - just confirm the bookings."
                        else:
                            confirmation_msg = f"Sham's tool results:\n{tool_result_text}\n\nIMPORTANT: The meeting has been successfully booked. Confirm this to the user in a brief, natural way (e.g., 'Great, I've booked your meeting for today at 7 PM.'). Do NOT ask if anything else is needed - just confirm the booking."

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
                logger.info(f"� No tool execution - passing transcription to LLM")
                
                # Add context about collected parameters to help Ram understand the conversation state
                if self.accumulated_params and self.active_tool:
                    # Use dynamic context formatter from tool config
                    context_msg = get_formatted_context(self.active_tool, self.accumulated_params)
                    
                    if context_msg:
                        # Add as system message to give Ram visibility into what's been collected
                        self.context.add_messages([{"role": "system", "content": context_msg}])
                        logger.info(f"🧠 Added parameter context to Ram ({self.active_tool}): {context_msg[:100]}...")
                # No tool executed - this is just conversation
                logger.info(f"� No tool execution - passing transcription to LLM")
                
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


def create_voice_agent_pipeline(transport, user_sub: str = None):
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
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    # Initialize STT service (Whisper)
    stt = WhisperSTTService(
        model="base",
        language="en"
    )
    logger.info("Whisper STT service initialized")


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

    # Initialize LLM service with Groq (using OpenAI-compatible interface)
    llm = OpenAILLMService(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        settings=OpenAILLMService.Settings(
            model="llama-3.3-70b-versatile",
            temperature=0,
            system_instruction=system_prompt,
        ),
    )
    logger.info("Groq LLM service initialized with llama-3.3-70b-versatile")
    
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
                    stop_secs=0.8,  # Wait 0.8 seconds of silence before considering user finished (prevents premature triggers on natural pauses)
                ),
            ),
            # Disable filter_incomplete_user_turns to prevent Smart Turn from sending extra API calls for incomplete detection
            filter_incomplete_user_turns=False,
        ),
    )

   # Build the pipeline with ConversationLogger and ToolExecutionProcessor
    conversation_logger = ConversationLogger()
    tool_executor = ToolExecutionProcessor(planner, context, llm)

    pipeline = Pipeline(
    [
        transport.input(),  # Transport user input
        stt,  # STT
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
    return worker, runner, context, planner
