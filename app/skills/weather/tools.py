"""
Weather skill - Get weather information.
Tool definition and skill-specific instructions.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
import httpx

class GetWeatherInput(BaseModel):
    """Input schema for get-weather tool."""
    city: str = Field(description="City name")
    date: Optional[str] = Field(default="today", description="Date (default=today)")

@tool
async def get_weather_tool(
    city: str,
    date: str = "today"
) -> str:
    """Get weather information for a city. Ask for city if not provided."""
    # Mock weather response for testing
    weather_conditions = {
        "sunny": "sunny with clear skies",
        "cloudy": "cloudy with overcast conditions", 
        "rainy": "rainy with light precipitation",
        "stormy": "stormy with heavy rain"
    }
    
    # Simple mock based on city name hash
    import hashlib
    city_hash = int(hashlib.md5(city.encode()).hexdigest(), 16)
    condition = list(weather_conditions.values())[city_hash % len(weather_conditions)]
    
    return f"Weather in {city} for {date} is {condition}. Temperature is around 22°C."

tools = [get_weather_tool]
