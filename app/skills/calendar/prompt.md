## CALENDAR

TRIGGER: User wants to book/schedule meeting ("book a meeting", "schedule something", "set up a call")
TOOL: create_event_tool
REQUIRED: name, date, time, meeting_mode (online/in_person)
OPTIONAL: title (default="Meeting"), duration (default="1 hour"), location, city, user_sub (from session)
FLOW: Ask one question at a time naturally, confirm details, then call tool
FORMAT: date=YYYY-MM-DD, time=HH:MM (24-hour), meeting_mode="online" or "in_person"