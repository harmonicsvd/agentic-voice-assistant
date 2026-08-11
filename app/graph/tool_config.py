"""
Tool Configuration Registry

This file defines tool-specific configurations that drive dynamic behavior
across the generic workflow nodes. Each tool has its own configuration
that defines:
- Required vs optional fields
- State management keys
- Confirmation requirements
- Prompt file references
- State reset behavior

This makes the system extensible - adding new tools only requires adding
a configuration entry, not modifying core logic.
"""

# Global configuration (tool-independent)
GLOBAL_CONFIG = {
    "date_keywords": [
        "today", "tomorrow", "yesterday", "this week", "next week",
        "monday", "tuesday", "wednesday", "thursday", 
        "friday", "saturday", "sunday"
    ],
    "success_indicators": [
        "successfully", "completed", "done", "created", "updated", "deleted"
    ],
    "failure_indicators": [
        "failed", "error", "unable to", "cannot", "not found", "permission denied"
    ],
    "default_timezone": "Europe/Berlin"
}


def get_date_keywords() -> list:
    """Get global date keywords."""
    return GLOBAL_CONFIG["date_keywords"]


def get_success_indicators() -> list:
    """Get global success indicators."""
    return GLOBAL_CONFIG["success_indicators"]


def get_failure_indicators() -> list:
    """Get global failure indicators."""
    return GLOBAL_CONFIG["failure_indicators"]


def get_default_timezone() -> str:
    """Get global default timezone."""
    return GLOBAL_CONFIG["default_timezone"]


TOOL_CONFIGS = {
    "create_event_tool": {
        "required_fields": ["date", "time", "meeting_mode", "name"],
        "optional_fields": ["description", "duration", "location", "city"],
        "state_key": "meetings",  # Dynamic: meetings array for create_event_tool
        "requires_confirmation": True,
        "state_reset_on_cancel": True,
        "extraction_prompt": "create_event_extraction.txt",
        "confirmation_prompt": "create_event_confirmation.txt",
        "is_read_only": False,
        "context_formatter": "format_meeting_context",
        "fallback_rules": {
            "meeting_mode": [
                {"pattern": "online", "value": "online"},
                {"pattern": "in-person|in person|face-to-face", "value": "in_person"}
            ],
            "time": [
                {"pattern": r"(\d{1,2})(?:am|pm)", "extract": "time_24h"}
            ],
            "duration": {"default": "1 hour"}
        },
        "parameter_overrides": {
            "date": {"today": "current_date", "tomorrow": "tomorrow_date"}
        },
        "protection_rules": {
            "time": {"protect_from_fragments": True},
            "date": {"protect_from_fragments": True}
        },
        # Context keywords for detecting tool relevance
        "context_keywords": [
            "meeting", "book", "schedule", "appointment", 
            "call", "discuss", "talk"
        ],
        # Confirmation phrases for execution (tiered approach)
        # Tier 1: Natural confirmations (when all required fields present)
        # Tier 2: Explicit action phrases (for re-confirmation or uncertain situations)
        "confirmation_phrases": [
            # Tier 1: Natural confirmations
            "yes", "yeah", "yep", "correct", "right", "that's right", "that's correct",
            "sounds good", "perfect", "great", "exactly", "absolutely", "sure",
            "please do", "please proceed", "okay", "alright", "fine",
            
            # Tier 2: Explicit action phrases (for re-confirmation)
            "do it", "go ahead", "execute it", "proceed", "book it",
            "please book", "schedule it", "create it", "that's correct, do it",
            "book now", "you can book", "yes book it", "yes do it",
            "confirm", "proceed with booking", "proceed with scheduling"
        ],
        # Name extraction patterns
        "name_extraction_patterns": [
            r'\bwith\s+([A-Z][a-z]+)',  # "with Manish"
            r'\bdirector\s+(?:whose\s+name\s+is\s+)?([A-Z][a-z]+)',  # "director Smith" or "director whose name is Manish"
            r'\bmanager\s+([A-Z][a-z]+)',  # "manager Alex"
            r'\bmeeting\s+([A-Z][a-z]+)',  # "meeting John"
            r'\bto\s+([A-Z][a-z]+)',  # "to Smith" (as in "talk to Smith")
            r'\bnamed\s+([A-Z][a-z]+)',  # "named John"
        ],
        # Continuation words for description merging
        "continuation_words": ["as well as", "and also", "plus", "also", "and"],
        # Default values for fields (only for optional fields, not required ones)
        "default_values": {
            "timezone": "Europe/Berlin",
            "duration": "1 hour"
            # Removed defaults for required fields (name, meeting_mode) to prevent premature booking
        },
        # Corruption indicators for validation (specific phrases that indicate corrupted state)
        "corruption_indicators": [
            "book another meeting", "cancel this", "stop the booking", "never mind about this", "forget this meeting"
        ],
        # Time extraction pattern
        "time_pattern": r'(\d{1,2})(?:am|pm)'
    },
    "meetings_summary_tool": {
        "required_fields": ["date"],
        "optional_fields": [],
        "state_key": "meetings_summary",
        "requires_confirmation": False,
        "state_reset_on_cancel": False,
        "extraction_prompt": "meetings_summary_extraction.txt",
        "confirmation_prompt": None,
        "is_read_only": True,
        "context_formatter": "format_summary_context"
    },
    "get_weather_tool": {
        "required_fields": ["city"],
        "optional_fields": ["date"],
        "state_key": "weather_data",
        "requires_confirmation": False,
        "state_reset_on_cancel": False,
        "extraction_prompt": "weather_extraction.txt",
        "confirmation_prompt": None,
        "is_read_only": True,
        "context_formatter": "format_weather_context"
    },
    "general_conversation": {
        "required_fields": [],
        "optional_fields": [],
        "state_key": None,
        "requires_confirmation": False,
        "state_reset_on_cancel": False,
        "extraction_prompt": None,
        "confirmation_prompt": None,
        "is_read_only": True,
        "context_formatter": None
    },
    "cancel_event": {
        "required_fields": [],
        "optional_fields": [],
        "state_key": None,
        "requires_confirmation": False,
        "state_reset_on_cancel": True,
        "extraction_prompt": None,
        "confirmation_prompt": None,
        "is_read_only": False,
        "context_formatter": None
    }
}


def get_tool_config(tool_name: str) -> dict:
    """
    Get configuration for a specific tool.
    
    Args:
        tool_name: Name of the tool (e.g., "create_event_tool")
        
    Returns:
        Tool configuration dictionary, or empty dict if tool not found
    """
    return TOOL_CONFIGS.get(tool_name, {})


def get_required_fields(tool_name: str) -> list:
    """Get required fields for a tool."""
    config = get_tool_config(tool_name)
    return config.get("required_fields", [])


def get_optional_fields(tool_name: str) -> list:
    """Get optional fields for a tool."""
    config = get_tool_config(tool_name)
    return config.get("optional_fields", [])


def get_state_key(tool_name: str) -> str:
    """Get the state key for a tool's data."""
    config = get_tool_config(tool_name)
    return config.get("state_key", "collected_params")


def requires_confirmation(tool_name: str) -> bool:
    """Check if a tool requires user confirmation."""
    config = get_tool_config(tool_name)
    return config.get("requires_confirmation", True)


def should_reset_state_on_cancel(tool_name: str) -> bool:
    """Check if a tool should reset state on cancellation."""
    config = get_tool_config(tool_name)
    return config.get("state_reset_on_cancel", False)


def is_read_only_tool(tool_name: str) -> bool:
    """Check if a tool is read-only (no side effects)."""
    config = get_tool_config(tool_name)
    return config.get("is_read_only", False)


def get_extraction_prompt_file(tool_name: str) -> str:
    """Get the extraction prompt file for a tool."""
    config = get_tool_config(tool_name)
    return config.get("extraction_prompt", "")


def get_confirmation_prompt_file(tool_name: str) -> str:
    """Get the confirmation prompt file for a tool."""
    config = get_tool_config(tool_name)
    return config.get("confirmation_prompt", "")


def get_context_formatter(tool_name: str) -> str:
    """Get the context formatter function name for a tool."""
    config = get_tool_config(tool_name)
    return config.get("context_formatter", "")


def get_context_keywords(tool_name: str) -> list:
    """Get context keywords for detecting tool relevance."""
    config = get_tool_config(tool_name)
    return config.get("context_keywords", [])


def get_fresh_start_phrases(tool_name: str) -> list:
    """Get fresh start phrases for a tool.
    
    Note: This function is kept for backward compatibility but returns empty list
    since fresh start detection is now handled by the LLM with full context.
    """
    # Return empty list as fresh start detection is now LLM-based
    return []


def get_confirmation_phrases(tool_name: str) -> list:
    """Get confirmation phrases for tool execution."""
    config = get_tool_config(tool_name)
    return config.get("confirmation_phrases", [])


def get_name_extraction_patterns(tool_name: str) -> list:
    """Get name extraction patterns for a tool."""
    config = get_tool_config(tool_name)
    return config.get("name_extraction_patterns", [])


def get_continuation_words(tool_name: str) -> list:
    """Get continuation words for description merging."""
    config = get_tool_config(tool_name)
    return config.get("continuation_words", [])


def get_default_value(tool_name: str, field_name: str) -> any:
    """Get default value for a specific field of a tool."""
    config = get_tool_config(tool_name)
    defaults = config.get("default_values", {})
    return defaults.get(field_name)


def get_corruption_indicators(tool_name: str) -> list:
    """Get corruption indicators for validation."""
    config = get_tool_config(tool_name)
    return config.get("corruption_indicators", [])


def get_time_pattern(tool_name: str) -> str:
    """Get time extraction pattern for a tool."""
    config = get_tool_config(tool_name)
    return config.get("time_pattern", r'(\d{1,2})(?:am|pm)')


def get_valid_tools() -> list:
    """Dynamically get all registered tools from TOOL_CONFIGS."""
    return list(TOOL_CONFIGS.keys())


def format_meeting_context(params: dict) -> str:
    """
    Format meeting parameters into readable context for the main LLM.
    
    Args:
        params: Accumulated parameters from conversation
        
    Returns:
        Formatted context string describing what meeting details have been collected
    """
    if not params:
        return ""
    
    # Focus on the most relevant meeting parameters (dynamic state access)
    tool_specific_state = params.get("tool_specific_state", {})
    meetings = tool_specific_state.get("meetings", [])
    if meetings and isinstance(meetings, list) and len(meetings) > 0:
        meeting = meetings[0]
        context_parts = []
        
        # Format key meeting details
        if meeting.get("date"):
            context_parts.append(f"Date: {meeting['date']}")
        if meeting.get("time"):
            context_parts.append(f"Time: {meeting['time']}")
        if meeting.get("duration"):
            context_parts.append(f"Duration: {meeting['duration']}")
        if meeting.get("meeting_mode"):
            context_parts.append(f"Mode: {meeting['meeting_mode']}")
        if meeting.get("description"):
            context_parts.append(f"Description: {meeting['description']}")
        if meeting.get("name"):
            context_parts.append(f"With: {meeting['name']}")
        
        if context_parts:
            return f"Meeting details collected so far: {', '.join(context_parts)}. If user is providing more details, acknowledge them. If details are complete, ask for confirmation."
    
    return ""


def format_summary_context(params: dict) -> str:
    """
    Format meetings summary parameters into readable context for the main LLM.
    
    Args:
        params: Accumulated parameters from conversation
        
    Returns:
        Formatted context string describing what summary parameters have been collected
    """
    if not params:
        return ""
    
    if params.get("date"):
        return f"Summary request for date: {params['date']}. If user provides more details, acknowledge them."
    
    return ""


def format_weather_context(params: dict) -> str:
    """
    Format weather parameters into readable context for the main LLM.
    
    Args:
        params: Accumulated parameters from conversation
        
    Returns:
        Formatted context string describing what weather parameters have been collected
    """
    if not params:
        return ""
    
    context_parts = []
    if params.get("city"):
        context_parts.append(f"City: {params['city']}")
    if params.get("date"):
        context_parts.append(f"Date: {params['date']}")
    
    if context_parts:
        return f"Weather query collected: {', '.join(context_parts)}. If user provides more details, acknowledge them."
    
    return ""


# Map formatter function names to actual functions
CONTEXT_FORMATTERS = {
    "format_meeting_context": format_meeting_context,
    "format_summary_context": format_summary_context,
    "format_weather_context": format_weather_context
}


def get_formatted_context(tool_name: str, params: dict) -> str:
    """
    Get formatted context for a specific tool using its configured formatter.
    
    Args:
        tool_name: Name of the tool
        params: Accumulated parameters from conversation
        
    Returns:
        Formatted context string, or empty string if no formatter configured
    """
    formatter_name = get_context_formatter(tool_name)
    if not formatter_name:
        return ""
    
    formatter_func = CONTEXT_FORMATTERS.get(formatter_name)
    if not formatter_func:
        return ""
    
    return formatter_func(params)


def get_fallback_rules(tool_name: str) -> dict:
    """Get fallback extraction rules for a tool."""
    config = get_tool_config(tool_name)
    return config.get("fallback_rules", {})


def get_parameter_overrides(tool_name: str) -> dict:
    """Get parameter override rules for a tool."""
    config = get_tool_config(tool_name)
    return config.get("parameter_overrides", {})


def get_protection_rules(tool_name: str) -> dict:
    """Get field protection rules for a tool."""
    config = get_tool_config(tool_name)
    return config.get("protection_rules", {})


def apply_fallback_rules(tool_name: str, parameters: dict, user_input: str, existing_data: dict = None) -> dict:
    """
    Apply dynamic fallback rules for parameter extraction.
    
    Args:
        tool_name: Name of the tool
        parameters: Currently extracted parameters
        user_input: Original user input string
        existing_data: Existing tool data for preservation
        
    Returns:
        Updated parameters with fallback values applied
    """
    import re
    fallback_rules = get_fallback_rules(tool_name)
    user_input_lower = user_input.lower()
    
    updated_params = parameters.copy()
    
    for field, rules in fallback_rules.items():
        if updated_params.get(field):
            continue  # Skip if already extracted
            
        if isinstance(rules, list):
            # Pattern-based fallback rules
            for rule in rules:
                pattern = rule.get("pattern")
                value = rule.get("value")
                extract_type = rule.get("extract")
                
                if extract_type == "time_24h":
                    match = re.search(pattern, user_input_lower)
                    if match:
                        hour = int(match.group(1))
                        is_pm = "pm" in match.group(0).lower()
                        if is_pm and hour != 12:
                            hour += 12
                        elif not is_pm and hour == 12:
                            hour = 0
                        updated_params[field] = f"{hour:02d}:00"
                        break
                elif value and re.search(pattern, user_input_lower, re.IGNORECASE):
                    updated_params[field] = value
                    break
        elif isinstance(rules, dict) and "default" in rules:
            # Default value fallback
            if existing_data and existing_data.get(field):
                # Preserve existing value if available
                updated_params[field] = existing_data[field]
            else:
                updated_params[field] = rules["default"]
    
    return updated_params


def apply_parameter_overrides(tool_name: str, parameters: dict, user_input: str, current_date: str = None, tomorrow_date: str = None) -> dict:
    """
    Apply dynamic parameter overrides based on keywords.
    
    Args:
        tool_name: Name of the tool
        parameters: Currently extracted parameters
        user_input: Original user input string
        current_date: Current date in YYYY-MM-DD format
        tomorrow_date: Tomorrow's date in YYYY-MM-DD format
        
    Returns:
        Updated parameters with overrides applied
    """
    override_rules = get_parameter_overrides(tool_name)
    user_input_lower = user_input.lower()
    
    updated_params = parameters.copy()
    
    for field, overrides in override_rules.items():
        if not updated_params.get(field):
            continue
            
        if isinstance(overrides, dict):
            for keyword, replacement in overrides.items():
                if keyword in user_input_lower:
                    if replacement == "current_date" and current_date:
                        updated_params[field] = current_date
                    elif replacement == "tomorrow_date" and tomorrow_date:
                        updated_params[field] = tomorrow_date
                    else:
                        updated_params[field] = replacement
                    break
    
    return updated_params


def apply_protection_rules(tool_name: str, parameters: dict, existing_data: dict = None) -> dict:
    """
    Apply field protection rules to prevent fragment-based corruption.
    
    Args:
        tool_name: Name of the tool
        parameters: Currently extracted parameters
        existing_data: Existing tool data to protect
        
    Returns:
        Updated parameters with protection applied
    """
    protection_rules = get_protection_rules(tool_name)
    
    if not existing_data or not protection_rules:
        return parameters
    
    updated_params = parameters.copy()
    
    for field, rules in protection_rules.items():
        if rules.get("protect_from_fragments") and existing_data.get(field):
            if updated_params.get(field) and updated_params[field] != existing_data[field]:
                # Protect existing value from fragment-based changes
                updated_params[field] = existing_data[field]
    
    return updated_params
