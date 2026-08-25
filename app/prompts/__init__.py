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
        tool_name: Name of the tool (e.g., "google_calendar", "meeting_discussion")
        **kwargs: Variables to substitute in the prompt template
        
    Returns:
        The prompt string with variables substituted
    """
    # Get prompt file from database
    from app.db.db import get_db, db_execute
    
    try:
        with get_db() as conn:
            row = db_execute(
                conn,
                "SELECT extraction_prompt_file FROM skill_registry WHERE skill_name = %s",
                (tool_name,)
            ).fetchone()
            
            if not row or not row['extraction_prompt_file']:
                logger.warning(f"No extraction prompt file found for tool: {tool_name}")
                prompt_file = "generic_extraction.txt"
            else:
                prompt_file = row['extraction_prompt_file']
    except Exception as e:
        logger.error(f"Failed to get extraction prompt file from database: {e}")
        prompt_file = "generic_extraction.txt"
    
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
        skip_detection: If True, skip skill detection and only extract parameters
        
    Returns:
        The prompt string with variables substituted
    """
    prompt_path = PROMPTS_DIR / "combined_detection_extraction.txt"
    
    if not prompt_path.exists():
        logger.warning(f"Combined detection/extraction prompt file not found: {prompt_path}")
        # Fallback to basic prompt
        skip_detection = kwargs.get('skip_detection', False)
        if skip_detection:
            return f'Extract parameters for the active skill from this user request: "{kwargs.get("user_input", "")}"'
        return f'Analyze this user request and extract parameters: "{kwargs.get("user_input", "")}"'
    
    # Read prompt template
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
    
    # Check if we should skip detection (extraction-only mode)
    skip_detection = kwargs.get('skip_detection', False)
    if skip_detection:
        # In extraction-only mode, modify the prompt to focus only on parameter extraction
        # Remove the detection section and focus on extraction
        prompt_template = """
You are extracting parameters for an already-active skill. The user is continuing a conversation about a specific task.

%existing_params%

User's latest input: %user_input%

Extract ONLY the parameters for the active skill from the user's input. Return JSON with this format:
{
  "extracted_params": {
    "param1": "value1",
    "param2": "value2"
  }
}

Focus on extracting NEW information. If a parameter was already provided, don't re-extract it unless the user is correcting it.
"""
    
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
    
    # Build available skills list with descriptions based on user's installed skills
    available_skills = kwargs.get('available_skills', [])
    
    # Get skill descriptions dynamically from database
    from app.skills import load_skills
    all_skills_data = load_skills(force_reload=False, user_sub=None)
    
    # Build skill descriptions from actual skill data
    skill_descriptions = {}
    for skill_name, skill_data in all_skills_data.items():
        # Extract a brief description from the skill prompt
        prompt = skill_data.get('prompt', '')
        # Take first line or first sentence as description
        first_line = prompt.split('\n')[0] if prompt else "Unknown skill"
        skill_descriptions[skill_name] = first_line
    
    if available_skills:
        formatted_skills = []
        for skill in available_skills:
            desc = skill_descriptions.get(skill, "Unknown skill")
            formatted_skills.append(f"- {skill}: {desc}")
        # Always include 'none' as an option (only if not skipping detection)
        if not skip_detection:
            formatted_skills.append("- none: Input is casual conversation, greeting, or unrelated to available skills")
        kwargs['available_skills'] = "\n".join(formatted_skills)
    else:
        # No skills installed - only general conversation
        kwargs['available_skills'] = "- none: Input is casual conversation, greeting, or unrelated to available skills"
    
    # Substitute variables using %VAR% format to avoid JSON conflicts
    result = prompt_template
    for key, value in kwargs.items():
        placeholder = f"%{key}%"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    # Remove parameter extraction rules for tools that are not in available_skills
    # This prevents the LLM from detecting tools that aren't installed
    if available_skills:
        import re
        from app.skills import load_skills
        
        # Get all available skills from database (dynamic, not hardcoded)
        all_skills_data = load_skills(force_reload=False, user_sub=None)
        tools_to_remove = list(all_skills_data.keys())
        
        for tool in tools_to_remove:
            if tool not in available_skills:
                # Remove the parameter extraction rules section for this tool
                pattern = rf'PARAMETER EXTRACTION RULES FOR {tool.upper()}:(.*?)(?=PARAMETER EXTRACTION RULES FOR|INTELLIGENT BEHAVIOR|USER INPUT|$)'
                result = re.sub(pattern, '', result, flags=re.DOTALL)
                logger.info(f"Removed parameter extraction rules for {tool} (not installed)")
    
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
        tool_name: Name of the tool (e.g., "google_calendar", "meeting_discussion")
        **kwargs: Variables to substitute in the prompt template
        
    Returns:
        The prompt string with variables substituted
    """
    # Get confirmation prompt file from database
    from app.db.db import get_db, db_execute
    
    try:
        with get_db() as conn:
            row = db_execute(
                conn,
                "SELECT confirmation_prompt_file FROM skill_registry WHERE skill_name = %s",
                (tool_name,)
            ).fetchone()
            
            if not row or not row['confirmation_prompt_file']:
                logger.warning(f"No confirmation prompt file found for tool: {tool_name}")
                prompt_file = "generic_confirmation.txt"
            else:
                prompt_file = row['confirmation_prompt_file']
    except Exception as e:
        logger.error(f"Failed to get confirmation prompt file from database: {e}")
        prompt_file = "generic_confirmation.txt"
    
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
