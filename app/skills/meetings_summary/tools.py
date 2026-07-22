"""
Meetings Summary skill - Fetch meetings and weather summary.
Tool definition and skill-specific instructions.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
import httpx
import os

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

class MeetingsSummaryInput(BaseModel):
    """Input schema for meetings-summary tool."""
    date: str = Field(default=None, description="Date in YYYY-MM-DD format")
    timezone: str = Field(default="Europe/Berlin", description="IANA timezone")
    user_sub: str = Field(description="User identifier")

@tool
async def meetings_summary_tool(
    date: Optional[str] = None,
    timezone: str = "Europe/Berlin",
    user_sub: str = ""
) -> str:
    """Get meetings summary. Use when user asks about schedule, meetings, or calendar. Default date=today, timezone=Europe/Berlin."""
    url = "http://localhost:8000/meetings-weather-summary"
    payload = {
        "message": {
            "toolCalls": [
                {
                    "id": "call_456",
                    "function": {
                        "arguments": {
                            "date": date,
                            "timezone": timezone,
                            "user_sub": user_sub
                        }
                    }
                }
            ]
        }
    }
    headers = {
        "X-Internal-API-Key": INTERNAL_API_KEY,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return f"Meetings summary: {data}"
    else:
        return f"Failed to get meetings summary: {response.text}"

tools = [meetings_summary_tool]
