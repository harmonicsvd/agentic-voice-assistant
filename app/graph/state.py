"""State definitions for LangGraph planner."""
from typing import TypedDict, Annotated, Optional, List, Dict, Any
import operator


class PlannerState(TypedDict):
    """State for the LangGraph planner."""
    user_input: str
    plan: List[Dict[str, Any]]
    current_step: int
    skill_results: List[Dict[str, Any]]  # Skill execution results
    collected_params: Dict[str, Any]
    is_complete: bool
    error: Optional[str]
    conversation_history: List[Dict[str, Any]]
    user_sub: Optional[str]
    confirmed: bool
    detected_skills: List[str]  # Skills detected by the planner
    skill_specific_state: Optional[Dict[str, Any]]  # Skill-specific data (dynamic per skill)
    pipeline_status: Optional[str]  # Track current pipeline stage
    pipeline_message: Optional[str]  # User-facing message about pipeline state
    missing_required_fields: Optional[List[str]]  # Track which required fields are missing for execution
    available_skills: List[str]  # List of ALL skills for detection
    installed_skills: List[str]  # List of installed skills for execution check
    skill_is_installed: bool  # Whether the detected skill is installed
    active_skill: Optional[str]  # Currently active skill (to skip re-detection when continuing)