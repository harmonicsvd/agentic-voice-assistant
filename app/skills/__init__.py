"""
Skills loader - Discovers and loads available skills dynamically.
"""

from pathlib import Path
import importlib.util

# Module-level cache for skills
_skills_cache = None

def load_skills(force_reload=False):
    """Load all available skills from the skills directory.
    
    Args:
        force_reload: If True, reload skills even if cached.
    
    Returns:
        Dictionary of skills with tools and prompts.
    """
    global _skills_cache
    
    if _skills_cache is not None and not force_reload:
        print("DEBUG: Using cached skills")
        return _skills_cache
    
    print("DEBUG: Loading skills from disk")
    skills_dir = Path(__file__).parent
    skills = {}
    
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
            skill_name = skill_dir.name
            # Load tools
            tools_path = skill_dir / "tools.py"
            if tools_path.exists():
                spec = importlib.util.spec_from_file_location(f"{skill_name}.tools", tools_path)
                tools_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(tools_module)
                # Load prompt
                prompt_path = skill_dir / "prompt.md"
                prompt = ""
                if prompt_path.exists():
                    with open(prompt_path, "r") as f:
                        prompt = f.read()
                
                skills[skill_name] = {
                    "tools": tools_module.tools,
                    "prompt": prompt
                }
    
    _skills_cache = skills
    print("DEBUG: Skills cached")
    return skills

def reload_skills():
    """Force reload skills from disk."""
    global _skills_cache
    _skills_cache = None
    return load_skills(force_reload=True)

def get_all_tools():
    """Get all tools from all skills."""
    skills = load_skills()
    all_tools = []
    for skill_data in skills.values():
        all_tools.extend(skill_data["tools"])
    return all_tools

def get_skill_prompts():
    """Get all skill prompts combined."""
    skills = load_skills()
    prompts = []
    for skill_name, skill_data in skills.items():
        prompts.append(f"## {skill_name.upper()}\n{skill_data['prompt']}")
    return "\n\n".join(prompts)
