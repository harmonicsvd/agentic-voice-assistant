"""
Proxy skill - Delegates all tool execution to weather agent.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
import httpx
import os

WEATHER_AGENT_URL = os.getenv("WEATHER_AGENT_URL", "http://127.0.0.1:9000")
INTERNAL_API_KEY = os.getenv("WEATHER_INTERNAL_API_KEY", "")

class ProxyToolInput(BaseModel):
    """Input schema for proxy tool."""
    tool_name: str = Field(description="Name of the tool to execute")
    parameters: dict = Field(description="Parameters for the tool")

@tool
async def proxy_tool(
    tool_name: str,
    parameters: dict
) -> str:
    """Execute a tool on the weather agent. All tool execution is delegated to the weather agent."""
    url = f"{WEATHER_AGENT_URL}/internal/tools/{tool_name}"
    headers = {
        "X-Internal-API-Key": INTERNAL_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=parameters, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("result", "Tool executed successfully")
            else:
                return f"Tool execution failed: {data.get('error', 'Unknown error')}"
        else:
            return f"Failed to execute tool: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Failed to execute tool: {str(e)}"

tools = [proxy_tool]
