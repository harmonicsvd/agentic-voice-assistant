"""
Pipecat WebSocket Transport Layer

This module provides a WebSocket transport for the Pipecat voice pipeline,
enabling real-time bidirectional voice communication using the open source stack
(Gemini LLM + Whisper MLX STT + Piper TTS).
"""

import logging
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.workers.runner import WorkerRunner, WorkerParams
from pipecat.frames.frames import LLMRunFrame
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
        
        # Create voice agent pipeline (pipeline-level event handlers are in pipecat_agent.py)
        logger.info("Creating voice agent pipeline")
        worker, runner, context, planner = create_voice_agent_pipeline(transport, user_sub)
        logger.info("Pipecat voice agent pipeline created successfully")

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, websocket):
            logger.info("Client disconnected - cancelling pipeline")
            await worker.cancel()

        # Explicit RTVI handling
        @worker.rtvi.event_handler("on_client_ready")
        async def on_client_ready(rtvi):
            logger.info("Client ready - setting bot ready")
            await rtvi.set_bot_ready()
            
            # Kick off the conversation with an introduction
            current_hour = datetime.now().hour
            greeting = "good morning" if current_hour < 12 else "good afternoon" if current_hour < 18 else "good evening"
            context.add_message(
    {"role": "system", "content": f"For this first response only: Say '{greeting}, I'm Ram. How can I help?' - keep it very brief."}
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