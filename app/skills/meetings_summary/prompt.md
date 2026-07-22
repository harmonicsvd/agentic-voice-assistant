## MEETINGS_SUMMARY

TRIGGER: User asks about schedule/meetings ("what are my meetings", "show my schedule", "do I have any meetings")
TOOL: meetings_summary_tool
PARAMETERS: user_sub (from session), date (default=today), timezone (default=Europe/Berlin)
ACTION: Call tool immediately with available parameters
RESPONSE: Explain results naturally - total meetings, in-person vs online, weather for in-person