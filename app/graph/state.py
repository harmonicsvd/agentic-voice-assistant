"""State definitions for LangGraph planner."""
from typing import TypedDict, Annotated, Optional, List, Dict, Any
import operator


class PlannerState(TypedDict):
    """State for the LangGraph planner."""
    user_input: str
    plan: List[Dict[str, Any]]
    current_step: int
    tool_results: List[Dict[str, Any]]
    collected_params: Dict[str, Any]
    is_complete: bool
    error: Optional[str]
    conversation_history: List[Dict[str, Any]]
    user_sub: Optional[str]
    confirmed: bool
    detected_tools: List[str]
    tool_specific_state: Optional[Dict[str, Any]]  # Generic: tool-specific data (dynamic per tool)
    pipeline_status: Optional[str]  # Track current pipeline stage
    pipeline_message: Optional[str]  # User-facing message about pipeline state
    missing_required_fields: Optional[List[str]]  # Track which required fields are missing for execution