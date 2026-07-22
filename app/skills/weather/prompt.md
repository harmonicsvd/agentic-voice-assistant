## WEATHER

TRIGGER: User asks about weather ("what's the weather", "how's the weather", "weather forecast")
TOOL: get_weather_tool
REQUIRED: city
OPTIONAL: date (default=today)
FLOW: Ask for city if not provided, then call tool
RESPONSE: Provide weather information naturally
