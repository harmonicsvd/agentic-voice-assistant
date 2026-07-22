"""
LangChain tool definitions for calendar operations.
Defines tools for create-event and meetings-summary with authentication.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
import httpx
import os

# Get internal API key from environment
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


class CreateEventInput(BaseModel):
    """Input schema for create-event tool."""
    name: str = Field(description="Name of the person for the meeting")
    date: str = Field(description="Date in YYYY-MM-DD format")
    time: str = Field(description="Time in HH:MM format (24-hour)")
    title: str = Field(default="Meeting", description="Meeting title")
    duration: str = Field(default="1 hour", description="Meeting duration")
    meeting_mode: str = Field(default="online", description="online or in_person")
    location: Optional[str] = Field(default=None, description="Location for in-person meetings")
    city: Optional[str] = Field(default=None, description="City for in-person meetings")
    user_sub: str = Field(description="User identifier")


class MeetingsSummaryInput(BaseModel):
    """Input schema for meetings-summary tool."""
    date: str = Field(default=None, description="Date in YYYY-MM-DD format")
    timezone: str = Field(default="Europe/Berlin", description="IANA timezone")
    user_sub: str = Field(description="User identifier")


@tool
async def create_event_tool(
    name: str,
    date: str,
    time: str,
    title: str = "Meeting",
    duration: str = "1 hour",
    meeting_mode: str = "online",
    location: Optional[str] = None,
    city: Optional[str] = None,
    user_sub: str = ""
) -> str:
    """
    Create a calendar event via the /create-event endpoint.
    Use this when the user wants to schedule a meeting.
    """
    url = "http://localhost:8000/create-event"
    
    payload = {
        "message": {
            "toolCalls": [
                {
                    "id": "call_123",
                    "function": {
                        "arguments": {
                            "name": name,
                            "date": date,
                            "time": time,
                            "title": title,
                            "duration": duration,
                            "meeting_mode": meeting_mode,
                            "location": location,
                            "city": city,
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
        return f"Successfully created event: {title} on {date} at {time}"
    else:
        return f"Failed to create event: {response.text}"


@tool
async def meetings_summary_tool(
    date: Optional[str] = None,
    timezone: str = "Europe/Berlin",
    user_sub: str = ""
) -> str:
    """
    Get meetings summary via the /meetings-weather-summary endpoint.
    Use this when the user asks about their meetings or schedule.
    """
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


# Export tools list
tools = [create_event_tool, meetings_summary_tool]