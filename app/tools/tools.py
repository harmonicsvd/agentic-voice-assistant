"""
LangChain tool definitions for calendar operations.
Voice agent calls weather agent via HTTP endpoints for production deployment.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
import httpx
import os

# Get internal API key from environment
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
WEATHER_AGENT_BASE_URL = os.getenv("WEATHER_AGENT_BASE_URL", "http://127.0.0.1:9000")


class CreateEventInput(BaseModel):
    """Input schema for create-event tool."""
    name: str = Field(description="Name of the person for the meeting")
    date: str = Field(description="Date in YYYY-MM-DD format")
    time: str = Field(description="Time in HH:MM format (24-hour)")
    title: Optional[str] = Field(default="Meeting", description="Meeting title")
    description: Optional[str] = Field(default=None, description="Meeting description/purpose")
    duration: Optional[str] = Field(default="1 hour", description="Meeting duration")
    meeting_mode: str = Field(default="online", description="online or in_person")
    location: Optional[str] = Field(default=None, description="Location for in-person meetings")
    city: Optional[str] = Field(default=None, description="City for in-person meetings")
    user_sub: str = Field(description="User identifier")
    timezone: Optional[str] = Field(default="Europe/Berlin", description="User timezone")


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
    title: Optional[str] = "Meeting",
    description: Optional[str] = None,
    duration: Optional[str] = "1 hour",
    meeting_mode: str = "online",
    location: Optional[str] = None,
    city: Optional[str] = None,
    user_sub: str = "",
    timezone: str = "Europe/Berlin"
) -> str:
    """
    Create a calendar event via the weather agent HTTP endpoint.
    Use this when the user wants to schedule a meeting.
    """
    url = f"{WEATHER_AGENT_BASE_URL}/internal/tools/create_event_tool"

    parameters = {
        "name": name,
        "date": date,
        "time": time,
        "title": title,
        "description": description,
        "duration": duration,
        "meeting_mode": meeting_mode,
        "location": location,
        "city": city,
        "user_sub": user_sub,
        "calendar_id": None,
        "timezone": timezone
    }

    headers = {
        "X-Internal-API-Key": INTERNAL_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=parameters, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("result", "Event created successfully")
    else:
        return f"Failed to create event: {response.text}"


@tool
async def meetings_summary_tool(
    date: Optional[str] = None,
    timezone: str = "Europe/Berlin",
    user_sub: str = ""
) -> str:
    """
    Get meetings summary via the weather agent HTTP endpoint.
    Use this when the user asks about their meetings or schedule.
    """
    url = f"{WEATHER_AGENT_BASE_URL}/internal/tools/meetings_summary_tool"

    parameters = {
        "date": date,
        "timezone": timezone,
        "user_sub": user_sub
    }

    headers = {
        "X-Internal-API-Key": INTERNAL_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=parameters, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("result", "Meetings summary retrieved")
    else:
        return f"Failed to get meetings summary: {response.text}"


# Export tools list
tools = [create_event_tool, meetings_summary_tool]