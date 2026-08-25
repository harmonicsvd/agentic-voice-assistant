"""
Skills loader - Discovers and loads available skills dynamically.
"""

from pathlib import Path
import importlib.util
from app.db.db import get_db, db_execute

# Module-level cache for skills
_skills_cache = None
_filtered_skills_cache = {}  # Cache for filtered skills by user

def load_skills(force_reload=False, user_sub=None):
    """Load skills from database (for dynamic skill loading).
    
    Args:
        force_reload: If True, reload skills even if cached.
        user_sub: If provided, only load skills installed by this user.
    
    Returns:
        Dictionary of skills with skills and prompts.
    """
    global _skills_cache
    
    # If user_sub is provided, check filtered cache FIRST before any database calls
    if user_sub:
        # Check if we have cached filtered skills for this user
        if not force_reload and user_sub in _filtered_skills_cache:
            print(f"DEBUG: Using cached filtered skills for user {user_sub}")
            return _filtered_skills_cache[user_sub]
    
    # Load all skills from database (only if not cached or force_reload)
    if _skills_cache is not None and not force_reload:
        print("DEBUG: Using cached skills")
        skills = _skills_cache
    else:
        print("DEBUG: Loading skills from database")
        skills = {}
        
        # Map skill names to their prompts (matching skill_config.py skill names)
        skill_prompts = {
            "google_calendar": "You can help users schedule meetings and book calendar events.\n\nAvailable capabilities:\n- Create calendar events (book meetings): Ask for date, time, meeting mode (online/in-person), and optionally the meeting purpose/description\n- Note: For checking existing schedules or meeting summaries, the meeting_discussion skill is required\n\nWhen you need to perform an action, the system will handle the execution automatically. Focus on understanding what the user wants and gathering the necessary information.\n\nIMPORTANT CONVERSATION RULES:\n- Ask questions ONE AT A TIME - don't ask multiple questions in a single response\n- Wait for the user to finish speaking before responding\n- Let the user provide all information naturally before asking for confirmation\n- If the user is providing multiple details (date, time, purpose, etc.), let them finish before asking anything else\n",
            "meeting_discussion": "You can help users check their meeting schedule and get summaries of their calendar events.\n\nAvailable capabilities:\n- Get meetings summary: Show user's schedule for the specified date\n- Provide meeting details and context for discussions\n\nWhen you need to perform an action, the system will handle the execution automatically. Focus on understanding what the user wants and gathering the necessary information.\n\nIMPORTANT CONVERSATION RULES:\n- Ask questions ONE AT A TIME - don't ask multiple questions in a single response\n- Wait for the user to finish speaking before responding\n- Let the user provide all information naturally before asking for confirmation\n",
            "get_weather": "You can help users get weather information for specific locations.\n\nAvailable capabilities:\n- Get current weather conditions for a city\n- Get weather forecast for specific dates\n\nWhen you need to perform an action, the system will handle the execution automatically. Focus on understanding what the user wants and gathering the necessary information.\n\nIMPORTANT CONVERSATION RULES:\n- Ask questions ONE AT A TIME - don't ask multiple questions in a single response\n- Wait for the user to finish speaking before responding\n- Let the user provide all information naturally before asking for confirmation\n"
        }
        
        try:
            with get_db() as conn:
                # Load all available skills from skill_registry (all skills, not just installed)
                rows = db_execute(
                    conn,
                    "SELECT skill_name, display_name, description FROM skill_registry WHERE is_active = TRUE"
                ).fetchall()
                
                print(f"DEBUG: Found {len(rows)} available skills in database")
                
                for row in rows:
                    skill_name = row["skill_name"]
                    
                    # Get prompt for this skill from skill_prompts dict (for backward compatibility)
                    # In future, this should also come from database
                    prompt = skill_prompts.get(skill_name, f"You have access to the {skill_name} skill. This skill can help users with {skill_name.replace('_', ' ')} related tasks.")
                    
                    skills[skill_name] = {
                        "skills": [{"name": skill_name, "description": f"Skill for {skill_name}"}],
                        "prompt": prompt
                    }
                    
        except Exception as e:
            print(f"Error loading skills from database: {e}")
            # Fallback to loading from disk if database fails
            print("DEBUG: Falling back to disk loading")
            return _load_skills_from_disk()
        
        _skills_cache = skills
        print("DEBUG: Skills cached")
    
    # If user_sub is provided, filter skills and cache the result
    if user_sub:
        filtered = _filter_skills_by_user(skills, user_sub)
        _filtered_skills_cache[user_sub] = filtered
        return filtered
    
    return skills


def _load_skills_from_disk():
    """Fallback: Load skills from disk directories (for backward compatibility)."""
    skills_dir = Path(__file__).parent
    skills = {}
    
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
            skill_name = skill_dir.name
            # Load skills
            skills_path = skill_dir / "skills.py"
            if skills_path.exists():
                spec = importlib.util.spec_from_file_location(f"{skill_name}.skills", skills_path)
                skills_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(skills_module)
                
                # Load prompt
                prompt_path = skill_dir / "prompt.md"
                prompt = ""
                if prompt_path.exists():
                    with open(prompt_path, "r") as f:
                        prompt = f.read()

                skills[skill_name] = {
                    "skills": skills_module.skills,
                    "prompt": prompt
                }
    
    return skills


def _load_proxy_skill():
    """Load the proxy skill from disk - this is the actual executable tool."""
    proxy_dir = Path(__file__).parent / "proxy"
    skills_path = proxy_dir / "skills.py"
    if skills_path.exists():
        spec = importlib.util.spec_from_file_location("proxy.skills", skills_path)
        skills_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(skills_module)
        return skills_module.skills
    return []


# Module-level cache for user installed skills to avoid repeated DB calls
_user_installed_skills_cache = {}  # {user_sub: {skill_names}} - NO TIME LIMIT, only cleared on install/uninstall

def _filter_skills_by_user(skills, user_sub):
    """Filter skills to only include those installed by the user."""
    global _user_installed_skills_cache
    
    try:
        # Check cache first for user's installed skills (NO TIME LIMIT)
        if user_sub in _user_installed_skills_cache:
            installed_skill_names = _user_installed_skills_cache[user_sub]
            print(f"DEBUG: Using cached installed skills for user {user_sub}")
        else:
            # Cache miss - load from DB (only happens once per user or after install/uninstall)
            print(f"DEBUG: Cache miss for user {user_sub}, loading from DB")
            with get_db() as conn:
                print(f"DEBUG: Database connection established")
                rows = db_execute(
                    conn,
                    "SELECT skill_name FROM user_installed_skills WHERE user_sub = %s AND status = 'active'",
                    (user_sub,)
                ).fetchall()
                
                print(f"DEBUG: User has {len(rows)} installed skills")
                installed_skill_names = {row["skill_name"] for row in rows}
                print(f"DEBUG: Installed skill names from DB: {installed_skill_names}")
                
                # Cache the result indefinitely (until cleared on install/uninstall)
                _user_installed_skills_cache[user_sub] = installed_skill_names
        
        print(f"DEBUG: Available skill names from database: {list(skills.keys())}")
        
        # Filter skills to only include installed ones (DB now stores tool names directly)
        filtered_skills = {}
        for tool_name, skill_data in skills.items():
            if tool_name in installed_skill_names:
                filtered_skills[tool_name] = skill_data
                print(f"DEBUG: Matched skill: {tool_name}")
            else:
                print(f"DEBUG: No match for available skill: {tool_name}")
        
        print(f"DEBUG: Filtered to {len(filtered_skills)} skills")
        return filtered_skills
    except Exception as e:
        print(f"Error filtering skills by user: {e}")
        # Return empty dict if filtering fails
        return {}


def reload_skills():
    """Force reload skills from disk."""
    global _skills_cache, _filtered_skills_cache
    _skills_cache = None
    _filtered_skills_cache = {}  # Clear all user caches as well
    return load_skills(force_reload=True)

def clear_user_cache(user_sub):
    """Clear the cached skills for a specific user (called when skills are installed/uninstalled)."""
    global _skills_cache, _filtered_skills_cache, _user_installed_skills_cache
    
    # Clear user-specific filtered skills cache
    if user_sub in _filtered_skills_cache:
        del _filtered_skills_cache[user_sub]
        print(f"DEBUG: Cleared filtered skills cache for user {user_sub}")
    
    # Clear user installed skills cache (this will force reload on next call)
    if user_sub in _user_installed_skills_cache:
        del _user_installed_skills_cache[user_sub]
        print(f"DEBUG: Cleared installed skills cache for user {user_sub}")
    
    # Clear global skills cache since available skills might have changed (new skills added/removed)
    _skills_cache = None
    print(f"DEBUG: Cleared global skills cache")
    
    # The next load_skills() call will automatically reload from DB since caches are cleared

def get_all_skills(user_sub=None):
    """Get all skills from all skills. If user_sub provided, only from user-installed skills."""
    skills = load_skills(user_sub=user_sub)
    all_skills = []
    for skill_data in skills.values():
        all_skills.extend(skill_data["skills"])
    
    # Only load proxy skill if not filtering by user (for execution, not for LLM context)
    # proxy_skill is an internal execution tool, not a user-installable skill
    if user_sub is None:
        proxy_skills = _load_proxy_skill()
        all_skills.extend(proxy_skills)
    
    return all_skills

def get_all_tools(user_sub=None):
    """Get all tools (alias for get_all_skills for compatibility)."""
    return get_all_skills(user_sub=user_sub)


def get_skill_prompts(user_sub=None):
    """Get all skill prompts combined. If user_sub provided, only from user-installed skills."""
    skills = load_skills(user_sub=user_sub)
    prompts = []
    for skill_name, skill_data in skills.items():
        prompts.append(f"## {skill_name.upper()}\n{skill_data['prompt']}")
    return "\n\n".join(prompts)

def get_all_skills_with_status(user_sub=None):
    """Get all skills with their installation status. Returns dict with skill names and whether they're installed."""
    # Get all available skills (without user filter)
    all_skills_data = load_skills(user_sub=None)
    all_skill_names = set(all_skills_data.keys())
    
    # Get installed skills for this user
    installed_skills_data = load_skills(user_sub=user_sub)
    installed_skill_names = set(installed_skills_data.keys())
    
    # Build status dict
    skills_status = {}
    for skill_name in all_skill_names:
        skills_status[skill_name] = skill_name in installed_skill_names
    
    return skills_status