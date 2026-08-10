"""Prompt loader for tool-specific extraction, confirmation, and detection prompts."""

import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent


def get_tool_detection_prompt(**kwargs) -> str:
    """
    Load tool detection prompt.
    
    Args:
        **kwargs: Variables to substitute in the prompt template
        
    Returns:
        The prompt string with variables substituted
    """
    prompt_path = PROMPTS_DIR / "tool_detection.txt"
    
    if not prompt_path.exists():
        logger.warning(f"Tool detection prompt file not found: {prompt_path}")
        # Fallback to basic prompt
        return f'Analyze this user request: "{kwargs.get("user_input", "")}"'
    
    # Read prompt template
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
    
    # Format conversation history using helper function
    conversation_history = kwargs.get('conversation_history', [])
    kwargs['conversation_history'] = format_conversation_history(conversation_history)
    
    # Substitute variables using %VAR% format
    result = prompt_template
    for key, value in kwargs.items():
        placeholder = f"%{key}%"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    # Check for any remaining unsubstituted placeholders
    import re
    remaining = re.findall(r'%(\w+)%', result)
    if remaining:
        logger.warning(f"Tool detection prompt template has unsubstituted variables: {remaining}")
        # Replace remaining placeholders with empty strings
        for var in remaining:
            result = result.replace(f"%{var}%", "")
    
    return result


def get_description_refinement_prompt(**kwargs) -> str:
    """
    Load description refinement prompt.
    
    Args:
        **kwargs: Variables to substitute in the prompt template
        
    Returns:
        The prompt string with variables substituted
    """
    prompt_path = PROMPTS_DIR / "description_refinement.txt"
    
    if not prompt_path.exists():
        logger.warning(f"Description refinement prompt file not found: {prompt_path}")
        # Fallback to basic prompt
        return f'Refine this description: "{kwargs.get("description", "")}"'
    
    # Read prompt template
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
    
    # Substitute variables using %VAR% format
    result = prompt_template
    for key, value in kwargs.items():
        placeholder = f"%{key}%"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    # Check for any remaining unsubstituted placeholders
    import re
    remaining = re.findall(r'%(\w+)%', result)
    if remaining:
        logger.warning(f"Description refinement prompt template has unsubstituted variables: {remaining}")
        # Replace remaining placeholders with empty strings
        for var in remaining:
            result = result.replace(f"%{var}%", "")
    
    return result


def format_conversation_history(conversation_history: list) -> str:
    """Format conversation history for LLM context."""
    if conversation_history:
        formatted_history = []
        for i, msg in enumerate(conversation_history[-5:]):  # Last 5 messages for context
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if role != 'system':  # Skip system messages
                formatted_history.append(f"  {role.upper()}: {content}")
        return "\n".join(formatted_history) if formatted_history else "  (no recent history)"
    else:
        return "  (no conversation history)"


def get_extraction_prompt(tool_name: str, **kwargs) -> str:
    """
    Load extraction prompt for a specific tool.
    
    Args:
        tool_name: Name of the tool (e.g., "create_event_tool", "meetings_summary_tool")
        **kwargs: Variables to substitute in the prompt template
        
    Returns:
        The prompt string with variables substituted
    """
    # Map tool names to prompt files
    prompt_files = {
        "create_event_tool": "create_event_extraction.txt",
        "meetings_summary_tool": "meetings_summary_extraction.txt",
        "get_weather_tool": "weather_extraction.txt",
    }
    
    # Default to generic if tool not found
    prompt_file = prompt_files.get(tool_name, "generic_extraction.txt")
    prompt_path = PROMPTS_DIR / prompt_file
    
    if not prompt_path.exists():
        logger.warning(f"Prompt file not found: {prompt_path}, using generic prompt")
        prompt_path = PROMPTS_DIR / "generic_extraction.txt"
        if not prompt_path.exists():
            # Fallback to basic prompt
            return f'Extract parameters from: "{kwargs.get("user_input", "")}"'
    
    # Read prompt template
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
    
    # Format existing parameters and meetings for better LLM context
    existing_params = kwargs.get('existing_params', {})
    existing_meetings = kwargs.get('existing_meetings', [])
    conversation_history = kwargs.get('conversation_history', [])
    
    # Format existing parameters in a clear, readable way
    if existing_params:
        formatted_params = "\n".join([f"  - {k}: {v}" for k, v in existing_params.items() if v])
        kwargs['existing_params'] = formatted_params
    else:
        kwargs['existing_params'] = "  (none yet)"
    
    # Format existing meetings in a clear, readable way
    if existing_meetings:
        formatted_meetings = []
        for i, meeting in enumerate(existing_meetings):
            if isinstance(meeting, dict):
                meeting_str = "\n    ".join([f"{k}: {v}" for k, v in meeting.items() if v])
                formatted_meetings.append(f"  Meeting {i+1}:\n    {meeting_str}")
        kwargs['existing_meetings'] = "\n".join(formatted_meetings) if formatted_meetings else "  (none yet)"
    else:
        kwargs['existing_meetings'] = "  (none yet)"
    
    # Format conversation history using helper function
    kwargs['conversation_history'] = format_conversation_history(conversation_history)
    
    # Format context hint for better LLM understanding
    context_hint = kwargs.get('context_hint', '')
    if context_hint:
        kwargs['context_hint'] = context_hint
    else:
        kwargs['context_hint'] = "No additional context provided"
    
    # Substitute variables using %VAR% format to avoid JSON conflicts
    result = prompt_template
    for key, value in kwargs.items():
        placeholder = f"%{key}%"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    # Check for any remaining unsubstituted placeholders
    import re
    remaining = re.findall(r'%(\w+)%', result)
    if remaining:
        logger.warning(f"Extraction prompt template has unsubstituted variables: {remaining}")
        # Replace remaining placeholders with empty strings
        for var in remaining:
            result = result.replace(f"%{var}%", "")
    
    return result
    
    # Substitute variables using %VAR% format to avoid JSON conflicts
    result = prompt_template
    for key, value in kwargs.items():
        placeholder = f"%{key}%"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    # Check for any remaining unsubstituted placeholders
    import re
    remaining = re.findall(r'%(\w+)%', result)
    if remaining:
        logger.warning(f"Prompt template has unsubstituted variables: {remaining}")
        # Replace remaining placeholders with empty strings
        for var in remaining:
            result = result.replace(f"%{var}%", "")
    
    return result


def get_combined_detection_extraction_prompt(**kwargs) -> str:
    """
    Load combined tool detection and parameter extraction prompt.
    
    This function provides a single prompt that combines both tool detection
    and parameter extraction to reduce LLM API calls by 50%.
    
    Args:
        **kwargs: Variables to substitute in the prompt template
        
    Returns:
        The prompt string with variables substituted
    """
    prompt_path = PROMPTS_DIR / "combined_detection_extraction.txt"
    
    if not prompt_path.exists():
        logger.warning(f"Combined detection/extraction prompt file not found: {prompt_path}")
        # Fallback to basic prompt
        return f'Analyze this user request and extract parameters: "{kwargs.get("user_input", "")}"'
    
    # Read prompt template
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
    
    # Format existing parameters for better LLM context
    existing_params = kwargs.get('existing_params', {})
    conversation_history = kwargs.get('conversation_history', [])
    
    # Format existing parameters in a clear, readable way
    if existing_params:
        formatted_params = "\n".join([f"  - {k}: {v}" for k, v in existing_params.items() if v])
        kwargs['existing_params'] = formatted_params
    else:
        kwargs['existing_params'] = "  (none yet)"
    
    # Format conversation history using helper function
    kwargs['conversation_history'] = format_conversation_history(conversation_history)
    
    # Format context hint for better LLM understanding
    context_hint = kwargs.get('context_hint', '')
    if context_hint:
        kwargs['context_hint'] = context_hint
    else:
        kwargs['context_hint'] = "No additional context provided"
    
    # Substitute variables using %VAR% format to avoid JSON conflicts
    result = prompt_template
    for key, value in kwargs.items():
        placeholder = f"%{key}%"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    # Check for any remaining unsubstituted placeholders
    import re
    remaining = re.findall(r'%(\w+)%', result)
    if remaining:
        logger.warning(f"Combined detection/extraction prompt template has unsubstituted variables: {remaining}")
        # Replace remaining placeholders with empty strings
        for var in remaining:
            result = result.replace(f"%{var}%", "")
    
    return result


def get_confirmation_prompt(tool_name: str, **kwargs) -> str:
    """
    Load confirmation prompt for a specific tool.
    
    Args:
        tool_name: Name of the tool (e.g., "create_event_tool", "meetings_summary_tool")
        **kwargs: Variables to substitute in the prompt template
        
    Returns:
        The prompt string with variables substituted
    """
    # Map tool names to confirmation prompt files
    prompt_files = {
        "create_event_tool": "create_event_confirmation.txt",
        "meetings_summary_tool": "generic_confirmation.txt",
        "get_weather_tool": "generic_confirmation.txt",
    }
    
    # Default to generic if tool not found
    prompt_file = prompt_files.get(tool_name, "generic_confirmation.txt")
    prompt_path = PROMPTS_DIR / prompt_file
    
    if not prompt_path.exists():
        logger.warning(f"Confirmation prompt file not found: {prompt_path}, using generic")
        prompt_path = PROMPTS_DIR / "generic_confirmation.txt"
        if not prompt_path.exists():
            # Fallback to basic prompt
            return f'Does user want to proceed with "{tool_name}"? Input: "{kwargs.get("user_input", "")}"'
    
    # Read prompt template
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
    
    # Substitute variables using %VAR% format
    result = prompt_template
    for key, value in kwargs.items():
        placeholder = f"%{key}%"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    # Check for any remaining unsubstituted placeholders
    import re
    remaining = re.findall(r'%(\w+)%', result)
    if remaining:
        logger.warning(f"Confirmation prompt template has unsubstituted variables: {remaining}")
        # Replace remaining placeholders with empty strings
        for var in remaining:
            result = result.replace(f"%{var}%", "")
    
    return result
