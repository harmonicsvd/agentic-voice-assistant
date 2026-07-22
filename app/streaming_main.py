"""
Streaming WebSocket handler for real-time voice interaction using Pipecat.

This module uses Pipecat's FastAPIWebsocketTransport for seamless WebSocket integration.
Pipecat handles the entire voice pipeline: Audio → STT → LLM → TTS → Audio
"""

import logging
from fastapi import WebSocket, WebSocketDisconnect
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.workers.runner import WorkerRunner
from app.pipecat_agent import create_voice_agent_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamingWebSocketHandler:
    """
    Handles streaming WebSocket connections using Pipecat's FastAPIWebsocketTransport.
    """
    
    def __init__(self):
        """Initialize the handler."""
        logger.info("StreamingWebSocketHandler initialized")
    
    async def handle_connection(self, websocket: WebSocket, session_id: str, user_sub: str):
        """
        Handle a streaming WebSocket connection using Pipecat.
        
        Args:
            websocket: The WebSocket connection
            session_id: Unique identifier for this session
            user_sub: User identifier
        """
        await websocket.accept()
        logger.info(f"WebSocket connected: session_id={session_id}, user_sub={user_sub}")
        
        try:
            # Create Pipecat transport for FastAPI WebSocket
            transport = FastAPIWebsocketTransport(
                websocket,
                params=FastAPIWebsocketParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                )
            )
            
            # Create voice agent pipeline
            task, runner = create_voice_agent_pipeline(transport)
            
            # Add worker to runner
            await runner.add_workers(task)
            
            # Run the pipeline
            await runner.run()
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: session_id={session_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)


# Global handler instance
streaming_handler = StreamingWebSocketHandler()