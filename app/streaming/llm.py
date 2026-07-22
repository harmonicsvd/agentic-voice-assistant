"""Streaming LLM service using Ollama."""

from typing import AsyncGenerator, Callable
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
import asyncio

class StreamingLLM:
    """Real-time streaming LLM with Ollama."""
    
    def __init__(self, model: str = "ollama:mistral", temperature: float = 0):
        self.model = model
        self.temperature = temperature
        self.llm = init_chat_model(model, temperature=temperature)
        
    async def stream_response(
        self,
        messages: list,
        on_token: Callable[[str], None] = None
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response token by token."""
        try:
            # Use streaming mode
            async for chunk in self.llm.astream(messages):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    if on_token:
                        on_token(content)
                    yield content
        except Exception as e:
            print(f"LLM streaming error: {e}")
            raise
    
    def bind_tools(self, tools: list):
        """Bind tools to the LLM for function calling."""
        self.llm = self.llm.bind_tools(tools)
        return self.llm