"""
Pipecat WebSocket Transport Layer

This module provides a WebSocket transport for the Pipecat voice pipeline,
enabling real-time bidirectional voice communication using the open source stack
(Gemini LLM + Whisper MLX STT + Piper TTS).
"""

import logging
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.workers.runner import WorkerRunner, WorkerParams
from pipecat.frames.frames import LLMRunFrame, TextFrame
from pipecat.processors.frame_processor import FrameDirection
from app.agents.pipecat_agent import create_voice_agent_pipeline


logger = logging.getLogger(__name__)


async def pipecat_websocket_handler(websocket: WebSocket):
    """
    FastAPI WebSocket endpoint handler for Pipecat voice pipeline.
    
    This endpoint handles real-time bidirectional voice communication:
    - Receives audio from client
    - Processes through Pipecat pipeline (STT -> LLM -> TTS)
    - Sends audio back to client
    
    Args:
        websocket: FastAPI WebSocket connection
    """
    await websocket.accept()
    logger.info("Pipecat WebSocket connection accepted")
    
    # Track incoming messages
    message_count = 0

    user_sub = websocket.query_params.get("user_sub") or (websocket.session.get("user_sub") if hasattr(websocket, "session") else None)
    
    try:
        # Create Pipecat FastAPI WebSocket transport
        logger.info("Creating FastAPIWebsocketTransport with ProtobufFrameSerializer")
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                audio_in_enabled=True,
                audio_in_sample_rate=16000,
                audio_out_sample_rate=24000,
                add_wav_header=False,
                serializer=ProtobufFrameSerializer(),
            )
        )
        logger.info("FastAPIWebsocketTransport created successfully")





        async def send_sleep_state_to_frontend(websocket: WebSocket, status: str):
            """Send sleep state update to frontend via RTVI server message."""
            try:
                # Use RTVI protocol to send sleep state updates
                # This avoids protobuf deserialization issues
                if hasattr(worker, 'rtvi'):
                    if status == "Sleeping":
                        await worker.rtvi.send_server_message({
                            "sleep_state": "Sleeping",
                            "sleeping": True
                        })
                        logger.info(f"📤 Sent sleep state to frontend via RTVI: sleeping")
                    elif status == "Awake":
                        await worker.rtvi.send_server_message({
                            "sleep_state": "Awake",
                            "sleeping": False
                        })
                        logger.info(f"📤 Sent awake state to frontend via RTVI: awake")
                    elif status == "Waking up":
                        await worker.rtvi.send_server_message({
                            "sleep_state": "Waking up",
                            "sleeping": False
                        })
                        logger.info(f"📤 Sent wake state to frontend via RTVI: waking up")
                    elif status == "NoWakeWord":
                        await worker.rtvi.send_server_message({
                            "sleep_state": "NoWakeWord",
                            "sleeping": True
                        })
                        logger.info(f"📤 Sent no wake word to frontend via RTVI")
            except Exception as e:
                logger.error(f"Error sending sleep state to frontend via RTVI: {e}")
        
        # Create a wrapper that handles the async callback properly
        async def sleep_state_callback_wrapper(status: str):
            await send_sleep_state_to_frontend(websocket, status)
                
        # Create voice agent pipeline (pipeline-level event handlers are in pipecat_agent.py)
        logger.info("Creating voice agent pipeline")
        worker, runner, context, planner, wake_word_processor = create_voice_agent_pipeline(
            transport, 
            user_sub,
            sleep_state_callback=sleep_state_callback_wrapper
        )
        logger.info("Pipecat voice agent pipeline created successfully")

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, websocket):
            logger.info("Client disconnected - cancelling pipeline")
            await worker.cancel()

        # Handle custom sleep/wake control via RTVI text messages
        # RTVI allows sending text messages from client to server
        @worker.rtvi.event_handler("on_client_message")
        async def on_client_message(rtvi, message):
            try:
                logger.info(f"📥 Received RTVI message from frontend: {message}")
                
                # Check if this is a sleep/wake command
                if isinstance(message, dict):
                    message_type = message.get("type")
                    if message_type == "send-text":
                        text_content = message.get("data", {}).get("content", "")
                        if isinstance(text_content, str):
                            if "sleep" in text_content.lower():
                                wake_word_processor.set_sleep_state(True, manual=True)
                                logger.info("💤 Frontend requested sleep via sendText - agent going to sleep (manual)")
                                # Send back immediate response to prevent passing to LLM
                                return {"type": "sleep_control", "status": "success"}
                            elif "wake" in text_content.lower():
                                wake_word_processor.set_sleep_state(False, manual=True)
                                logger.info("🎯 Frontend requested wake via sendText - agent waking up (manual)")
                                # Send back immediate response to prevent passing to LLM
                                return {"type": "sleep_control", "status": "success"}
                    # Let normal text messages pass through
            except Exception as e:
                logger.error(f"Error handling sleep/wake message: {e}")

        # Explicit RTVI handling
        @worker.rtvi.event_handler("on_client_ready")
        async def on_client_ready(rtvi):
            logger.info("Client ready - setting bot ready")
            await rtvi.set_bot_ready()
            
            # Set initial sleep state to awake so the agent is ready to respond
            wake_word_processor.set_sleep_state(False)
            logger.info("🎯 Setting initial sleep state to awake")
            
            # Add a small delay before the first speech for natural feel
            import asyncio
            await asyncio.sleep(1.0)  # 1 second delay for natural pause
            
            # Kick off the conversation with an introduction
            current_hour = datetime.now().hour
            greeting = "good morning" if current_hour < 12 else "good afternoon" if current_hour < 18 else "good evening"
            context.add_message(
    {"role": "system", "content": f"For this first response only: Say '{greeting}. I am EMO. Ready to help.' - Speak in short phrases with natural pauses. Use periods and commas to create gaps. Keep it slow and gentle."}
)
            await worker.queue_frames([LLMRunFrame()])
            
        # Run the pipeline
        logger.info("Starting pipeline runner")
        await runner.run(worker)
        logger.info("Pipeline runner completed")
        
    except WebSocketDisconnect:
        logger.info("Pipecat WebSocket disconnected")
    except Exception as e:
        logger.exception("Pipecat WebSocket error")
        await websocket.close()