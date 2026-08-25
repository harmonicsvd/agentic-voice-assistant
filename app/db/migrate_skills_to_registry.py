"""
Migration script to populate skill_registry table with existing skill configurations.
This should be run once to migrate hardcoded skill_config.py data to the database.
"""

import json
from datetime import datetime
from app.db.db import get_db, db_execute

def migrate_skills_to_registry():
    """Migrate existing skill configurations from skill_config.py to database."""
    
    # Skill configurations from skill_config.py
    skills_to_migrate = [
        {
            "skill_name": "google_calendar",
            "display_name": "Google Calendar",
            "description": "Book, schedule, and manage calendar events",
            "required_fields": ["date", "time", "meeting_mode", "description", "name"],
            "optional_fields": ["duration", "location", "city", "title"],
            "state_key": "meetings",
            "extraction_prompt_file": "create_event_extraction.txt",
            "confirmation_prompt_file": "create_event_confirmation.txt",
            "detection_keywords": ["meeting", "book", "schedule", "appointment", "call", "discuss", "talk"],
            "is_active": True
        },
        {
            "skill_name": "meeting_discussion",
            "display_name": "Meeting Discussion",
            "description": "View and discuss meeting schedules and calendar events",
            "required_fields": ["date"],
            "optional_fields": [],
            "state_key": "meetings_summary",
            "extraction_prompt_file": "meeting_discussion_extraction.txt",
            "confirmation_prompt_file": None,
            "detection_keywords": ["what are my", "show my", "my meetings", "my schedule", "meetings today", "what meetings", "see my meetings", "my meeting", "what am i meeting", "tell me my", "what do i have", "my calendar", "check my", "do i have"],
            "is_active": True
        },
        {
            "skill_name": "get_weather",
            "display_name": "Get Weather",
            "description": "Get weather information for a location",
            "required_fields": ["city"],
            "optional_fields": ["date"],
            "state_key": "weather_data",
            "extraction_prompt_file": "weather_extraction.txt",
            "confirmation_prompt_file": None,
            "detection_keywords": ["weather"],
            "is_active": True
        }
    ]
    
    with get_db() as conn:
        for skill in skills_to_migrate:
            skill_name = skill["skill_name"]
            
            # Check if skill already exists
            existing = db_execute(
                conn,
                "SELECT skill_name FROM skill_registry WHERE skill_name = %s",
                (skill_name,)
            ).fetchone()
            
            if existing:
                print(f"Skill {skill_name} already exists, skipping...")
                continue
            
            # Insert skill into registry
            now = datetime.now().isoformat()
            db_execute(
                conn,
                """INSERT INTO skill_registry 
                   (skill_name, display_name, description, required_fields, optional_fields, 
                    state_key, extraction_prompt_file, confirmation_prompt_file, detection_keywords, 
                    is_active, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    skill["skill_name"],
                    skill["display_name"],
                    skill["description"],
                    json.dumps(skill["required_fields"]),
                    json.dumps(skill["optional_fields"]),
                    skill["state_key"],
                    skill["extraction_prompt_file"],
                    skill["confirmation_prompt_file"],
                    json.dumps(skill["detection_keywords"]),
                    skill["is_active"],
                    now,
                    now
                )
            )
            print(f"Migrated skill: {skill_name}")
    
    print("Migration complete!")

if __name__ == "__main__":
    migrate_skills_to_registry()
