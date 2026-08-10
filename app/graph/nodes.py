"""Node implementations for LangGraph planner - Optimized version with combined detection+extraction."""
from typing import Optional, List, Dict, Any
from app.graph.state import PlannerState
from app.skills import get_all_tools
from app.graph.tool_config import (
    TOOL_CONFIGS,
    get_tool_config, 
    get_state_key, 
    should_reset_state_on_cancel,
    get_required_fields,
    get_optional_fields,
    get_extraction_prompt_file,
    requires_confirmation,
    is_read_only_tool,
    get_confirmation_prompt_file,
    get_context_keywords,
    get_confirmation_phrases,
    get_name_extraction_patterns,
    get_continuation_words,
    get_default_value,
    get_corruption_indicators,
    get_time_pattern,
    get_valid_tools,
    get_date_keywords,
    get_success_indicators,
    get_failure_indicators,
    get_default_timezone,
    apply_fallback_rules
)
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


def build_collective_context(decision_type: str, state: PlannerState, user_input: str) -> dict:
    """
    Build collective context - only what affects the decision, nothing more.
    
    This implements the principle: pass only context that helps the LLM make the decision
    which can affect the decision. It should be collective, not random variables.
    
    Args:
        decision_type: "tool_detection", "parameter_extraction", "confirmation_detection"
        state: Current conversation state
        user_input: Current user speech
        
    Returns:
        Context dictionary specifically tailored for the decision type
    """
    if decision_type == "tool_detection":
        # Tool detection needs: available tools, discussion flow, previous decisions, current state
        return {
            "current_speech": user_input,
            "available_tools": get_valid_tools(),
            "discussion_flow": extract_discussion_flow(state),
            "previous_decisions": state.get("detected_tools", []),
            "current_state": extract_relevant_state(state)
        }
    
    elif decision_type == "parameter_extraction":
        # Parameter extraction needs: current speech, existing state, conversation stage, temporal context
        return {
            "current_speech": user_input,
            "existing_state": state.get("collected_params", {}),
            "conversation_stage": determine_conversation_stage(state),
            "temporal_context": {
                "current_date": datetime.now().strftime("%Y-%m-%d"),
                "current_day": datetime.now().strftime("%A"),
                "tomorrow": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            }
        }
    
    elif decision_type == "confirmation_detection":
        # Confirmation detection needs: current speech, collected state, conversation flow, previous questions
        return {
            "current_speech": user_input,
            "collected_state": state.get("collected_params", {}),
            "conversation_flow": extract_discussion_flow(state),
            "previous_questions": extract_previous_questions(state.get("conversation_history", [])),
            "confirmation_patterns": get_confirmation_phrases("create_event_tool")
        }
    
    else:
        # Fallback to minimal context
        return {
            "current_speech": user_input,
            "decision_type": decision_type
        }


def extract_discussion_flow(state: PlannerState) -> str:
    """Extract the discussion flow from conversation state."""
    conversation_history = state.get("conversation_history", [])
    detected_tools = state.get("detected_tools", [])
    
    if not detected_tools:
        return "idle"
    
    # Check if we're in the middle of a tool workflow
    if detected_tools[-1] == "create_event_tool":
        return "booking_meeting"
    elif detected_tools[-1] == "meetings_summary_tool":
        return "checking_calendar"
    elif detected_tools[-1] == "get_weather_tool":
        return "checking_weather"
    else:
        return "unknown"


def extract_relevant_state(state: PlannerState) -> dict:
    """Extract relevant state for tool detection (generic, not tool-specific)."""
    detected_tools = state.get("detected_tools", [])
    collected_params = state.get("collected_params", {})
    
    # Generic state that applies to any tool, not tool-specific
    return {
        "has_active_workflow": len(detected_tools) > 0,
        "current_workflow_type": detected_tools[-1] if detected_tools else None,
        "workflow_completion_status": determine_workflow_completion(state)
    }


def determine_workflow_completion(state: PlannerState) -> str:
    """Determine how complete the current workflow is (generic)."""
    detected_tools = state.get("detected_tools", [])
    collected_params = state.get("collected_params", {})
    
    if not detected_tools:
        return "none"
    
    current_tool = detected_tools[-1]
    
    # Check completion based on tool requirements (generic approach)
    required_fields = get_required_fields(current_tool)
    if required_fields:
        collected_fields = [field for field in required_fields if collected_params.get(field)]
        completion_ratio = len(collected_fields) / len(required_fields)
        
        if completion_ratio == 1.0:
            return "complete"
        elif completion_ratio > 0.5:
            return "mostly_complete"
        elif completion_ratio > 0:
            return "in_progress"
        else:
            return "started"
    else:
        return "complete"  # Tools with no required fields are complete


def determine_conversation_stage(state: PlannerState) -> str:
    """Determine the conversation stage."""
    collected_params = state.get("collected_params", {})
    detected_tools = state.get("detected_tools", [])
    
    if not detected_tools:
        return "idle"
    
    # Check if we have all required fields
    if detected_tools[-1] == "create_event_tool":
        required_fields = get_required_fields("create_event_tool")
        collected_fields = [field for field in required_fields if collected_params.get(field)]
        
        if len(collected_fields) == len(required_fields):
            return "confirming"
        elif len(collected_fields) > 0:
            return "gathering"
        else:
            return "starting"
    
    return "idle"


def extract_previous_questions(conversation_history: list) -> list:
    """Extract previous questions from conversation history."""
    questions = []
    for msg in conversation_history[-5:]:  # Last 5 messages
        if msg.get('role') == 'assistant':
            content = msg.get('content', '')
            # Check if this looks like a question
            if '?' in content or any(word in content.lower() for word in ['what', 'when', 'where', 'how', 'who', 'should']):
                questions.append(content)
    return questions


def get_tool_state(state: PlannerState, tool_name: str) -> list:
    """Get tool-specific state for a given tool (dynamic access)."""
    tool_state_key = get_state_key(tool_name)
    tool_specific_state = state.get("tool_specific_state", {})
    return tool_specific_state.get(tool_state_key, []) if tool_state_key else []


def set_tool_state(state: PlannerState, tool_name: str, data: Any) -> None:
    """Set tool-specific state for a given tool (dynamic access)."""
    tool_state_key = get_state_key(tool_name)
    if "tool_specific_state" not in state:
        state["tool_specific_state"] = {}
    state["tool_specific_state"][tool_state_key] = data


async def analyze_and_extract_optimized(state: PlannerState, planning_llm) -> PlannerState:
    """
    COMBINED APPROACH: Tool detection + parameter extraction in ONE LLM call.
    
    This function:
    1. Detects which tool is needed AND extracts parameters in a single API call
    2. Updates state with both results
    3. Reduces LLM API calls by 50% (from 2 calls to 1 call per user input)
    
    PIPELINE TRANSPARENCY: Logs the current pipeline stage and decision
    - Helps with debugging and understanding system behavior
    - Provides clear feedback on what the system is doing
    
    WHY COMBINED: Eliminates redundant API calls while maintaining accuracy.
    - Original: Tool detection (call 1) → Parameter extraction (call 2) = 2 calls
    - Combined: Tool detection + extraction (call 1) = 1 call
    """
    user_input = state["user_input"]
    existing_params = state.get("collected_params", {})
    
    # Get temporal context for date/time overrides
    from datetime import datetime, timedelta
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_day = datetime.now().strftime("%A")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Build collective context for combined detection + extraction
    tool_context = build_collective_context("tool_detection", state, user_input)
    
    # Format context for prompt template
    context_hint = f"Discussion flow: {tool_context['discussion_flow']}. "
    context_hint += f"Available tools: {', '.join(tool_context['available_tools'])}. "
    context_hint += f"Active workflow: {tool_context['current_state']['has_active_workflow']}. "
    context_hint += f"Workflow type: {tool_context['current_state']['current_workflow_type']}. "
    context_hint += f"Workflow completion: {tool_context['current_state']['workflow_completion_status']}. "
    context_hint += f"Previous decisions: {tool_context['previous_decisions']}. "
    
    # Load combined detection + extraction prompt
    from app.prompts import get_combined_detection_extraction_prompt
    
    combined_prompt = get_combined_detection_extraction_prompt(
        user_input=user_input,
        existing_params=existing_params,
        current_date=current_date,
        current_day=current_day,
        tomorrow=tomorrow,
        context_hint=context_hint,
        conversation_history=state.get("conversation_history", [])
    )
    
    logger.info(f"🚀 OPTIMIZED: Using combined detection + extraction prompt")
    
    try:
        response = await planning_llm.ainvoke([
            {"role": "system", "content": "You are a tool detector and parameter extractor. Return ONLY valid JSON."},
            {"role": "user", "content": combined_prompt}
        ])
        
        response_content = response.content.strip()
        logger.info(f"🚀 OPTIMIZED: Combined LLM response={response_content}")
        
        # Parse JSON response
        try:
            # Clean up any markdown formatting
            if response_content.startswith("```json"):
                response_content = response_content[7:]
            if response_content.startswith("```"):
                response_content = response_content[3:]
            if response_content.endswith("```"):
                response_content = response_content[:-3]
            response_content = response_content.strip()
            
            result = json.loads(response_content)
            detected_tool = result.get("detected_tool", "none")
            extracted_params = result.get("extracted_params", {})
            
            logger.info(f"🚀 OPTIMIZED: Detected tool={detected_tool}, extracted_params={extracted_params}")
            
        except json.JSONDecodeError as e:
            logger.error(f"🚀 OPTIMIZED: JSON parsing error: {e}")
            logger.error(f"🚀 OPTIMIZED: Response content: {response_content}")
            detected_tool = "none"
            extracted_params = {}
        
    except Exception as e:
        logger.error(f"🚀 OPTIMIZED: Combined detection/extraction error: {e}")
        detected_tool = "none"
        extracted_params = {}
    
    if detected_tool == "none":
        logger.info(f"🚀 OPTIMIZED: No tool detected, keeping existing state")
        logger.info(f"🚀 PIPELINE: Early exit - no action needed for user input: '{user_input}'")
        state["detected_tools"] = []
        state["pipeline_status"] = "no_action_needed"
        return state
    
    # Parse tool name from response
    valid_tools = get_valid_tools()
    for tool in valid_tools:
        if tool in detected_tool:
            detected_tool = tool
            break
    else:
        detected_tool = "none"
    
    state["detected_tools"] = [detected_tool]
    
    # Handle cancellation - reset tool-specific state based on config
    if detected_tool == "cancel_event":
        logger.info(f"🚀 OPTIMIZED: LLM decided to cancel based on full conversation context")
        logger.info(f"🚀 OPTIMIZED: Respecting LLM's intelligent decision (user input: '{user_input}')")
        
        logger.info(f"🚀 OPTIMIZED: Resetting tool-specific state per LLM decision")
        state["collected_params"] = {}
        
        # Reset state for all tools that require it on cancellation
        for tool_name, config in TOOL_CONFIGS.items():
            if should_reset_state_on_cancel(tool_name):
                state_key = get_state_key(tool_name)
                if state_key and state_key in state:
                    state[state_key] = []
                    logger.info(f"🚀 OPTIMIZED: Reset state for {tool_name} (key: {state_key})")
        
        state["detected_tools"] = []
        state["pipeline_status"] = "cancelled_per_llm_decision"
        return state
    
    # Initialize tool-specific state based on config
    if detected_tool != "cancel_event":
        if not state.get("collected_params"):
            state["collected_params"] = {"action": detected_tool.replace("_tool", "")}
            logger.info(f"🚀 OPTIMIZED: Initialize collected_params for {detected_tool}")
        else:
            state["collected_params"]["action"] = detected_tool.replace("_tool", "")
        
        # Get tool state key for later use
        tool_state_key = get_state_key(detected_tool)
        
        # Initialize existing_tool_data for all tools
        existing_tool_data = get_tool_state(state, detected_tool)
        
        # Merge extracted parameters with existing params
        logger.info(f"🚀 OPTIMIZED: Merging extracted params: {extracted_params}")
        
        # Only update non-null parameters
        for key, value in extracted_params.items():
            if value is not None and value != "" and value != []:
                state["collected_params"][key] = value
                logger.info(f"🚀 OPTIMIZED: Updated {key} = {value}")
        
        logger.info(f"🚀 OPTIMIZED: Final collected_params: {state['collected_params']}")
        
        # Apply tool-specific parameter overrides and fallbacks
        parameters = extracted_params.copy()
        
        # Normalize time format from natural language to HH:MM
        if parameters.get("time") and isinstance(parameters["time"], str):
            time_str = parameters["time"].strip().lower()
            if "p.m." in time_str or "pm" in time_str:
                # Extract hour and convert to 24-hour format
                import re
                time_match = re.search(r'(\d+)\s*(?:p\.?m\.?|pm)', time_str)
                if time_match:
                    hour = int(time_match.group(1))
                    if hour != 12:
                        hour += 12
                    parameters["time"] = f"{hour:02d}:00"
                    logger.info(f"🚀 OPTIMIZED: Normalized time from '{extracted_params['time']}' to '{parameters['time']}'")
            elif "a.m." in time_str or "am" in time_str:
                import re
                time_match = re.search(r'(\d+)\s*(?:a\.?m\.?|am)', time_str)
                if time_match:
                    hour = int(time_match.group(1))
                    if hour == 12:
                        hour = 0
                    parameters["time"] = f"{hour:02d}:00"
                    logger.info(f"🚀 OPTIMIZED: Normalized time from '{extracted_params['time']}' to '{parameters['time']}'")
        
        # CRITICAL: Preserve time and duration from collected_params if LLM returned null
        if state.get("collected_params") and state["collected_params"].get("meetings"):
            existing_meeting = state["collected_params"]["meetings"][0] if state["collected_params"]["meetings"] else {}
            
            if (not parameters.get("time") or parameters.get("time") == "null") and existing_meeting.get("time"):
                parameters["time"] = existing_meeting["time"]
                logger.info(f"🚀 OPTIMIZED: PRESERVED - Restored time from collected_params: '{parameters['time']}'")
            
            if (not parameters.get("duration") or parameters.get("duration") == "null") and existing_meeting.get("duration"):
                parameters["duration"] = existing_meeting["duration"]
                logger.info(f"🚀 OPTIMIZED: PRESERVED - Restored duration from collected_params: '{parameters['duration']}'")
        
        # Get tool configuration for dynamic behavior
        tool_config = get_tool_config(detected_tool)
        required_fields = get_required_fields(detected_tool)
        optional_fields = get_optional_fields(detected_tool)
        
        # Apply critical overrides for date/time keywords (tools with date/time fields)
        if "date" in required_fields + optional_fields:
            if "today" in user_input.lower() and parameters.get("date"):
                parameters["date"] = current_date
                logger.info(f"🚀 OPTIMIZED: Overriding date to {current_date} (user said 'today')")
            if "tomorrow" in user_input.lower() and parameters.get("date"):
                parameters["date"] = tomorrow
                logger.info(f"🚀 OPTIMIZED: Overriding date to {tomorrow} (user said 'tomorrow')")
        
        # Tool-specific fallback logic
        if detected_tool == "create_event_tool":
            user_input_lower = user_input.lower()
            
            # Fallback for meeting_mode extraction
            if not parameters.get("meeting_mode"):
                fallback_result = apply_fallback_rules(detected_tool, parameters, user_input_lower)
                if fallback_result and fallback_result.get("meeting_mode"):
                    parameters["meeting_mode"] = fallback_result["meeting_mode"]
                    logger.info(f"🚀 OPTIMIZED: Fallback - extracted meeting_mode='{parameters['meeting_mode']}'")
            
            # CRITICAL: Protect existing critical values from fragment-based extraction errors
            if existing_tool_data and existing_tool_data[0]:
                existing_data = existing_tool_data[0]
            else:
                # Fallback: try to get from collected_params['meetings']
                if state.get("collected_params") and state["collected_params"].get("meetings"):
                    existing_data = state["collected_params"]["meetings"][0] if state["collected_params"]["meetings"] else {}
                    logger.info(f"🚀 OPTIMIZED: Using fallback from collected_params meetings for preservation: {existing_data}")
                else:
                    existing_data = None
            
            if existing_data:
                # CRITICAL: Preserve existing values when LLM returns null
                # This prevents losing previously extracted parameters
                for key in ["time", "date", "duration", "meeting_mode", "title", "description", "name", "location", "city"]:
                    if parameters.get(key) is None or parameters.get(key) == "" or parameters.get(key) == "null":
                        if existing_data.get(key) and existing_data[key] != "" and existing_data[key] != "null":
                            parameters[key] = existing_data[key]
                            logger.info(f"🚀 OPTIMIZED: PRESERVED - Restored existing {key}='{existing_data[key]}' (LLM returned null)")
                
                # Protect time from incorrect fragment extraction
                if parameters.get("time") and parameters["time"] != "" and parameters["time"] != "null":
                    if existing_data.get("time") and existing_data["time"] != "":
                        if parameters["time"] != existing_data["time"]:
                            logger.info(f"🚀 OPTIMIZED: PROTECTED - Preserving existing time '{existing_data['time']}' over fragment '{parameters['time']}'")
                            parameters["time"] = existing_data["time"]
                
                # Protect date from incorrect fragment extraction  
                if parameters.get("date") and parameters["date"] != "" and parameters["date"] != "null":
                    if existing_data.get("date") and existing_data["date"] != "":
                        if parameters["date"] != existing_data["date"]:
                            logger.info(f"🚀 OPTIMIZED: PROTECTED - Preserving existing date '{existing_data['date']}' over fragment '{parameters['date']}'")
                            parameters["date"] = existing_data["date"]
            
            # Fallback for time extraction
            if not parameters.get("time"):
                # Try to preserve existing time from collected_params first
                if state.get("collected_params") and state["collected_params"].get("meetings"):
                    existing_meeting = state["collected_params"]["meetings"][0] if state["collected_params"]["meetings"] else {}
                    if existing_meeting.get("time") and existing_meeting["time"] != "" and existing_meeting["time"] != "null":
                        parameters["time"] = existing_meeting["time"]
                        logger.info(f"🚀 OPTIMIZED: PRESERVED - Kept existing time='{existing_meeting['time']}' from collected_params")
                
                # If still no time, try regex extraction
                if not parameters.get("time"):
                    import re
                    time_pattern = get_time_pattern(detected_tool)
                    time_match = re.search(time_pattern, user_input_lower)
                    if time_match:
                        hour = int(time_match.group(1))
                        is_pm = "pm" in time_match.group(0).lower()
                        if is_pm and hour != 12:
                            hour += 12
                        elif not is_pm and hour == 12:
                            hour = 0
                        parameters["time"] = f"{hour:02d}:00"
                        logger.info(f"🚀 OPTIMIZED: Fallback - extracted time={parameters['time']}")
            
            # Default duration if not mentioned
            if not parameters.get("duration"):
                # Try to preserve existing duration from tool_state
                if existing_tool_data and existing_tool_data[0].get("duration"):
                    parameters["duration"] = existing_tool_data[0]["duration"]
                    logger.info(f"🚀 OPTIMIZED: Preserving existing duration from tool_state: {parameters['duration']}")
                # Fallback: try to preserve from collected_params
                elif state.get("collected_params") and state["collected_params"].get("meetings"):
                    existing_meeting = state["collected_params"]["meetings"][0] if state["collected_params"]["meetings"] else {}
                    if existing_meeting.get("duration") and existing_meeting["duration"] != "" and existing_meeting["duration"] != "null":
                        parameters["duration"] = existing_meeting["duration"]
                        logger.info(f"🚀 OPTIMIZED: PRESERVED - Kept existing duration='{existing_meeting['duration']}' from collected_params")
                else:
                    default_duration = get_default_value(detected_tool, "duration")
                    parameters["duration"] = default_duration
                    logger.info(f"🚀 OPTIMIZED: Default duration to {default_duration}")
            
            # Basic description cleanup
            if parameters.get("description") and parameters["description"] != "null":
                raw_desc = parameters["description"]
                cleaned_desc = raw_desc.strip()
                if cleaned_desc and cleaned_desc[0].islower():
                    cleaned_desc = cleaned_desc[0].upper() + cleaned_desc[1:]
                parameters["description"] = cleaned_desc
                logger.info(f"🚀 OPTIMIZED: Basic description cleanup: '{raw_desc}' → '{cleaned_desc}'")
            
            # Extract name from description if not provided directly
            if parameters.get("name") in [None, "", "null"] and parameters.get("description"):
                desc = parameters["description"]
                import re
                person_patterns = get_name_extraction_patterns(detected_tool)
                for pattern in person_patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        extracted_name = match.group(1)
                        if extracted_name:
                            parameters["name"] = extracted_name.capitalize()
                            logger.info(f"🚀 OPTIMIZED: Extracted name from description: '{extracted_name}'")
                            break
        
        # Merge with existing tool state
        if existing_tool_data:
            updated_data = {**existing_tool_data[0]}
            for key, value in parameters.items():
                if value is not None and value != "null" and value != "":
                    if key in updated_data and updated_data[key] == value:
                        logger.info(f"🚀 OPTIMIZED: Skipping {key} - value unchanged: '{value}'")
                        continue
                    
                    # Special handling for description - combine instead of overwrite
                    if key == "description" and updated_data.get("description"):
                        existing_desc = updated_data["description"].strip()
                        new_desc = value.strip()
                        
                        if new_desc.lower() in existing_desc.lower():
                            logger.info(f"🚀 OPTIMIZED: Skipping description - new is subset of existing")
                            continue
                        elif existing_desc.lower() in new_desc.lower():
                            updated_data[key] = new_desc
                            logger.info(f"🚀 OPTIMIZED: Updated description - existing is subset of new")
                        else:
                            existing_desc = existing_desc.rstrip("...")
                            new_desc = new_desc.lstrip("...")
                            
                            continuation_words = get_continuation_words(detected_tool)
                            new_desc_lower = new_desc.lower()
                            
                            has_continuation = any(new_desc_lower.startswith(word) for word in continuation_words)
                            if has_continuation:
                                for word in continuation_words:
                                    if new_desc_lower.startswith(word):
                                        new_desc = new_desc[len(word):].strip()
                                        new_desc = new_desc.lstrip(",.").strip()
                                        break
                                combined = f"{existing_desc} {new_desc}"
                            else:
                                if existing_desc and not existing_desc.endswith(".") and not existing_desc.endswith(","):
                                    combined = f"{existing_desc}. {new_desc}"
                                else:
                                    combined = f"{existing_desc} {new_desc}"
                            
                            combined = combined.strip()
                            words = combined.split()
                            seen = set()
                            unique_words = []
                            for word in words:
                                word_lower = word.lower().strip(".,")
                                if word_lower not in seen:
                                    seen.add(word_lower)
                                    unique_words.append(word)
                            
                            updated_data[key] = " ".join(unique_words)
                            logger.info(f"🚀 OPTIMIZED: Combined descriptions - old: '{existing_desc}', new: '{new_desc}', combined: '{updated_data[key]}'")
                    else:
                        updated_data[key] = value
                        logger.info(f"🚀 OPTIMIZED: Updated {key}: '{value}'")
            
            # Apply default values for missing required fields
            default_values = get_tool_config(detected_tool).get("default_values", {})
            for key, default_value in default_values.items():
                if key not in updated_data or updated_data[key] is None or updated_data[key] == "":
                    updated_data[key] = default_value
                    logger.info(f"🚀 OPTIMIZED: DEFAULT - Applied default {key}='{default_value}'")
            
            set_tool_state(state, detected_tool, [updated_data])
            logger.info(f"🚀 OPTIMIZED: Updated existing {tool_state_key} with new parameters")
        else:
            # Create new data, but preserve from collected_params and tool_state if available
            existing_meeting = {}
            
            # First try to get from tool_state
            if tool_state_key and tool_state_key in state and state[tool_state_key]:
                existing_meeting = state[tool_state_key][0] if state[tool_state_key] else {}
            
            # Fallback: try to get from collected_params['meetings']
            if not existing_meeting and state.get("collected_params") and state["collected_params"].get("meetings"):
                existing_meeting = state["collected_params"]["meetings"][0] if state["collected_params"]["meetings"] else {}
                logger.info(f"🚀 OPTIMIZED: Using fallback from collected_params meetings: {existing_meeting}")
            
            new_data = {}
            for key in ["date", "time", "duration", "meeting_mode", "title", "description", "name", "location", "city"]:
                # Use new value if provided and not null, otherwise use existing value
                new_value = parameters.get(key)
                if new_value is not None and new_value != "" and new_value != "null":
                    new_data[key] = new_value
                elif existing_meeting.get(key) and existing_meeting[key] != "" and existing_meeting[key] != "null":
                    new_data[key] = existing_meeting[key]
                    logger.info(f"🚀 OPTIMIZED: PRESERVED - Kept existing {key}='{existing_meeting[key]}' (LLM returned null)")
            
            # Apply default values for missing required fields
            default_values = get_tool_config(detected_tool).get("default_values", {})
            for key, default_value in default_values.items():
                if key not in new_data or new_data[key] is None or new_data[key] == "":
                    new_data[key] = default_value
                    logger.info(f"🚀 OPTIMIZED: DEFAULT - Applied default {key}='{default_value}'")
            
            set_tool_state(state, detected_tool, [new_data])
            logger.info(f"🚀 OPTIMIZED: Created new {tool_state_key} with parameters")
        
        # Update collected_params
        state["collected_params"].update(parameters)
        
        # Update tool state key reference
        if tool_state_key:
            state["collected_params"][tool_state_key] = get_tool_state(state, detected_tool)
    
    elif detected_tool in ["meetings_summary_tool", "get_weather_tool"]:
        # Clear collected params for non-booking tools
        state["collected_params"] = {}
        # Clear tool-specific state keys
        tool_state_key = get_state_key(detected_tool)
        if tool_state_key and tool_state_key in state:
            state[tool_state_key] = []
    
    logger.info(f"🚀 OPTIMIZED: Final state - detected_tools={state['detected_tools']}, collected_params={state.get('collected_params', {})}")
    return state


async def analyze_request(state: PlannerState, planning_llm) -> PlannerState:
    """
    Analyze user request to determine intent and required tools using LLM.

    Uses LLM to detect which tool is needed based on natural language input.
    This is more flexible than keyword matching and handles variations better.

    Clears collected_params when switching from booking to viewing to prevent
    incorrect parameter context.
    """
    user_input = state["user_input"]
    analysis = {"required_tools": [], "parameters": {}}

    # Check if there's existing meeting context (dynamic state access)
    existing_meetings = get_tool_state(state, "create_event_tool")
    context_hint = ""
    if existing_meetings:
        context_hint = f"\n\nIMPORTANT: User has {len(existing_meetings)} existing meeting(s) in progress. If user is providing updates (like meeting mode, location, time, etc.), use create_event_tool."

    tool_detection_prompt = f"""Analyze this user request to determine which tool is needed.

User input: "{user_input}"{context_hint}

Available tools:
1. create_event_tool - Use when user wants to book/schedule/create a meeting or appointment, OR when user is providing updates to existing meetings (like meeting mode "online/in-person", location, time, etc.), OR when user confirms to execute booking (phrases like "yes book it", "do it", "go ahead", "proceed", "schedule it", "create it")
2. meetings_summary_tool - Use when user wants to view/check/see/tell/show their meetings, schedule, calendar, or what meetings they have (including variations like "what am I having today or any specific date", "what do I have", "tell me my meetings")
3. get_weather_tool - Use when user asks about weather

IMPORTANT: If user says things like "it's online", "it's in-person", "online meeting", "in-person meeting" when there are existing meetings, use create_event_tool to update the meeting mode.
IMPORTANT: If user says confirmation phrases like "yes book it", "do it", "go ahead", "proceed", "schedule it", "create it", "that's correct do it" when there are existing meetings, use create_event_tool to execute the booking.

Return ONLY the tool name (one of: {', '.join(get_valid_tools())}) or "none" if no tool is needed."""

    try:
        response = await planning_llm.ainvoke([
            {"role": "system", "content": "You are a tool detector. Return only the tool name or 'none'."},
            {"role": "user", "content": tool_detection_prompt}
        ])
        
        detected_tool = response.content.strip().lower()
        logger.info(f"🔍 analyze_request: LLM detected tool={detected_tool}")
        
        # Parse tool name from response (LLM might return explanation instead of just name)
        valid_tools = get_valid_tools()
        for tool in valid_tools:
            if tool in detected_tool:
                detected_tool = tool
                break
        else:
            detected_tool = "none"

        if detected_tool in valid_tools:
            analysis["required_tools"] = [detected_tool]
    except Exception as e:
        logger.error(f"🔍 analyze_request: LLM detection error: {e}")
        # Fallback to keyword matching on error
        user_input_lower = user_input.lower()
        if any(keyword in user_input_lower for keyword in ["book", "schedule"]):
            analysis["required_tools"] = ["create_event_tool"]
        elif any(keyword in user_input_lower for keyword in ["what are my", "show my", "my meetings", "my schedule", "meetings today", "what meetings", "see my meetings", "my meeting", "what am i meeting", "tell me my", "what do i have", "my calendar", "check my", "do i have"]):
            analysis["required_tools"] = ["meetings_summary_tool"]
        elif any(keyword in user_input_lower for keyword in ["weather"]):
            analysis["required_tools"] = ["get_weather_tool"]
    
    state["detected_tools"] = analysis["required_tools"]

    # Reset collected_params for meetings_summary_tool and get_weather_tool
    if analysis["required_tools"] == ["meetings_summary_tool"]:
        state["collected_params"] = {}
    elif analysis["required_tools"] == ["get_weather_tool"]:
        state["collected_params"] = {}
    # Initialize collected_params for create_event_tool
    elif analysis["required_tools"] == ["create_event_tool"]:
        if not state.get("collected_params"):
            state["collected_params"] = {"action": "create_event"}
        else:
            state["collected_params"]["action"] = "create_event"

    logger.info(f"🔍 analyze_request: detected tools={analysis['required_tools']}")
    return state


async def extract_parameters(state: PlannerState, planning_llm) -> PlannerState:
    """
    Extract meeting parameters from user input using LLM.
    
    This function:
    - Uses LLM to extract structured parameters from natural language
    - Handles multiple meetings by returning an array
    - Preserves existing parameters across turns
    - Stores tool-specific state for proper multi-meeting handling
    
    WHY THIS HELPER FUNCTION:
    - Keeps parameter extraction logic separate from planning
    - Allows flexible LLM-based extraction
    - Handles edge cases like confirmation and multi-meeting scenarios
    """
    user_input = state["user_input"]
    existing_params = state.get("collected_params", {})
    detected_tools = state.get("detected_tools", [])
    
    # Get temporal context for date/time overrides
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_day = datetime.now().strftime("%A")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    if not detected_tools:
        logger.info(f"🔍 extract_parameters: no tools detected, skipping extraction")
        return state
    
    detected_tool = detected_tools[0]
    
    # For meetings_summary_tool and get_weather_tool, use simple extraction
    if detected_tool == "meetings_summary_tool":
        user_input_lower = user_input.lower()
        date_keywords = get_date_keywords()
        
        # Check for explicit date mention
        date_to_use = None
        for keyword in date_keywords:
            if keyword in user_input_lower:
                if keyword == "today":
                    date_to_use = current_date
                elif keyword == "tomorrow":
                    date_to_use = tomorrow
                break
        
        if date_to_use:
            state["collected_params"]["date"] = date_to_use
            logger.info(f"🔍 extract_parameters: extracted date={date_to_use} for meetings_summary_tool")
        else:
            # Default to today if no date mentioned
            state["collected_params"]["date"] = current_date
            logger.info(f"🔍 extract_parameters: defaulting to today for meetings_summary_tool")
        
        return state
    
    elif detected_tool == "get_weather_tool":
        # Extract city for weather
        import re
        # Simple city extraction - look for capitalized words or common city patterns
        words = user_input.split()
        city = None
        for word in words:
            if word[0].isupper() and len(word) > 2:
                city = word
                break
        
        if city:
            state["collected_params"]["city"] = city
            logger.info(f"🔍 extract_parameters: extracted city={city} for get_weather_tool")
        
        # Default date to today
        state["collected_params"]["date"] = current_date
        logger.info(f"🔍 extract_parameters: defaulting to today for get_weather_tool")
        
        return state
    
    # For create_event_tool, use LLM-based extraction
    elif detected_tool == "create_event_tool":
        tool_state_key = get_state_key(detected_tool)
        existing_tool_data = get_tool_state(state, detected_tool)
        
        # Build extraction context
        extraction_context = build_collective_context("parameter_extraction", state, user_input)
        
        # Load extraction prompt
        from app.prompts import get_extraction_prompt
        extraction_prompt_file = get_extraction_prompt_file(detected_tool)
        
        if extraction_prompt_file:
            extraction_prompt = get_extraction_prompt(
                detected_tool,
                user_input=user_input,
                existing_params=existing_params,
                conversation_history=state.get("conversation_history", []),
                current_date=current_date,
                current_day=current_day,
                tomorrow=tomorrow
            )
            
            try:
                response = await planning_llm.ainvoke([
                    {"role": "system", "content": "You are a parameter extractor. Return ONLY valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ])
                
                response_content = response.content.strip()
                logger.info(f"🔍 extract_parameters: LLM response={response_content}")
                
                # Parse JSON response
                try:
                    # Clean up any markdown formatting
                    if response_content.startswith("```json"):
                        response_content = response_content[7:]
                    if response_content.startswith("```"):
                        response_content = response_content[3:]
                    if response_content.endswith("```"):
                        response_content = response_content[:-3]
                    response_content = response_content.strip()
                    
                    extracted_params = json.loads(response_content)
                    logger.info(f"🔍 extract_parameters: extracted_params={extracted_params}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"🔍 extract_parameters: JSON parsing error: {e}")
                    extracted_params = {}
                
            except Exception as e:
                logger.error(f"🔍 extract_parameters: LLM extraction error: {e}")
                extracted_params = {}
        else:
            # Fallback to keyword-based extraction
            extracted_params = {}
            user_input_lower = user_input.lower()
            
            # Simple date extraction
            if "today" in user_input_lower:
                extracted_params["date"] = current_date
            elif "tomorrow" in user_input_lower:
                extracted_params["date"] = tomorrow
            
            # Simple time extraction
            import re
            time_pattern = get_time_pattern(detected_tool)
            time_match = re.search(time_pattern, user_input_lower)
            if time_match:
                hour = int(time_match.group(1))
                is_pm = "pm" in time_match.group(0).lower()
                if is_pm and hour != 12:
                    hour += 12
                elif not is_pm and hour == 12:
                    hour = 0
                extracted_params["time"] = f"{hour:02d}:00"
            
            # Simple meeting_mode extraction
            if "online" in user_input_lower:
                extracted_params["meeting_mode"] = "online"
            elif "in-person" in user_input_lower or "in person" in user_input_lower:
                extracted_params["meeting_mode"] = "in-person"
        
        # Merge extracted parameters with existing params
        for key, value in extracted_params.items():
            if value is not None and value != "" and value != []:
                state["collected_params"][key] = value
                logger.info(f"🔍 extract_parameters: Updated {key} = {value}")
        
        # Update tool-specific state
        if tool_state_key:
            if existing_tool_data:
                updated_data = {**existing_tool_data[0]}
                for key, value in extracted_params.items():
                    if value is not None and value != "null" and value != "":
                        updated_data[key] = value
                state[tool_state_key] = [updated_data]
            else:
                new_data = {k: v for k, v in extracted_params.items() if v is not None and v != "null"}
                state[tool_state_key] = [new_data]
            
            state["collected_params"][tool_state_key] = state[tool_state_key]
        
        logger.info(f"🔍 extract_parameters: Final collected_params={state['collected_params']}")
        return state
    
    return state


async def create_plan(state: PlannerState, planning_llm) -> PlannerState:
    """
    Create execution plan using LLM-extracted parameters.

    This function decides WHEN to execute tools based on:
    - Detected tools from analyze_request
    - Required parameters presence
    - User confirmation for booking actions

    Architecture:
    - Uses detected_tools from state to know which tool to execute
    - meetings_summary_tool executes immediately (no required params)
    - create_event_tool requires date, time, meeting_mode AND user confirmation
    - Uses LLM for confirmation detection (flexible natural language)
    """
    user_input = state["user_input"]
    plan = []
    params = state.get("collected_params", {})
    conversation_history = state.get("conversation_history", [])
    detected_tools = state.get("detected_tools", [])
    user_input_lower = user_input.lower()

    # Handle meetings_summary_tool - defaults to "today" if no date specified
    if "meetings_summary_tool" in detected_tools:
        logger.info(f"🔍 create_plan: handling meetings_summary_tool")
        date_keywords = get_date_keywords()
        has_explicit_date = any(keyword in user_input_lower for keyword in date_keywords)
        
        # Default to "today" if no explicit date mentioned
        date_to_use = params.get("date", "today")
        if not has_explicit_date:
            date_to_use = "today"
            logger.info(f"🔍 create_plan: no explicit date, defaulting to today")
        
        # Convert relative dates to YYYY-MM-DD format
        date_lower = date_to_use.lower()
        if date_lower == "today":
            date_to_use = datetime.now().strftime("%Y-%m-%d")
        elif date_lower == "tomorrow":
            date_to_use = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif date_lower == "yesterday":
            date_to_use = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        logger.info(f"🔍 create_plan: converted date to {date_to_use}")
        
        plan.append({
            "step": 1,
            "tool": "proxy_tool",
            "description": "Get meetings summary",
            "parameters": {
                "tool_name": "meetings_summary_tool",
                "parameters": {
                    "user_sub": state.get("user_sub", ""),
                    "date": date_to_use,
                    "timezone": params.get("timezone", get_default_timezone())
                }
            }
        })
        logger.info(f"🔍 create_plan: adding proxy_tool for meetings_summary_tool with date={date_to_use}")

    # Handle create_event_tool - requires explicit confirmation
    # Only create plan if user explicitly says "do it", "go ahead", "book it", etc. (using dynamic config)
    execution_confirmation_phrases = get_confirmation_phrases("create_event_tool")
    has_explicit_confirmation = any(phrase in user_input_lower for phrase in execution_confirmation_phrases)
    
    if "create_event_tool" in detected_tools or (params.get("date") and params.get("time") and params.get("meeting_mode")) or state.get("tool_specific_state", {}).get("meetings"):
        logger.info(f"🔍 create_plan: handling create_event_tool")
        logger.info(f"🔍 create_plan: meetings={state.get('tool_specific_state', {}).get('meetings')}")
        logger.info(f"🔍 create_plan: params={params}")
        logger.info(f"🔍 create_plan: detected_tools={detected_tools}")
        logger.info(f"🔍 create_plan: has_explicit_confirmation={has_explicit_confirmation}")
        
        # Check if all required fields are present (dynamic state access)
        meetings = get_tool_state(state, "create_event_tool")
        has_all_required_fields = False
        
        # Use config-based required fields
        required_fields = get_required_fields("create_event_tool")
        
        if len(meetings) == 1:
            meeting_params = meetings[0]
            has_all_required_fields = all(meeting_params.get(field) for field in required_fields)
        elif len(meetings) > 1:
            has_all_required_fields = all(
                all(meeting.get(field) for field in required_fields)
                for meeting in meetings
            )
        elif all(params.get(field) for field in required_fields):
            has_all_required_fields = True
        
        logger.info(f"🔍 create_plan: has_all_required_fields={has_all_required_fields}")
        
        # Only create plan steps if user explicitly confirmed to book AND all fields are present
        if not has_explicit_confirmation or not has_all_required_fields:
            logger.info(f"🔍 create_plan: missing confirmation or required fields, skipping tool execution")
            # Don't add any plan steps - just return empty plan
            # The LLM will continue gathering information or ask for confirmation
        else:
            logger.info(f"🔍 create_plan: explicit booking confirmation detected, creating plan")
            # Check if we have multiple meetings to book
            meetings = get_tool_state(state, "create_event_tool")
            
            if len(meetings) > 1:
                # Multiple meetings - create plan for each
                for idx, meeting in enumerate(meetings):
                    meeting_params = meeting.copy()
                    # Add default name if missing (required by backend)
                    if not meeting_params.get("name"):
                        meeting_params["name"] = f"Meeting {idx + 1}"
                        logger.info(f"🔍 create_plan: added default name 'Meeting {idx + 1}' for meeting {idx}")
                    
                    plan.append({
                        "step": len(plan) + 1,
                        "tool": "proxy_tool",
                        "description": f"Book meeting {idx + 1}",
                        "parameters": {
                            "tool_name": "create_event_tool",
                            "parameters": {
                                "user_sub": state.get("user_sub", ""),
                                **meeting_params
                            }
                        }
                    })
                logger.info(f"🔍 create_plan: creating plan for {len(meetings)} meetings")
            elif len(meetings) == 1:
                # Single meeting
                meeting_params = meetings[0].copy()
                # Add default name if missing (required by backend)
                if not meeting_params.get("name"):
                    meeting_params["name"] = "Meeting"
                    logger.info(f"🔍 create_plan: added default name 'Meeting' (name was missing)")
                
                plan.append({
                    "step": len(plan) + 1,
                    "tool": "proxy_tool",
                    "description": "Book meeting",
                    "parameters": {
                        "tool_name": "create_event_tool",
                        "parameters": {
                            "user_sub": state.get("user_sub", ""),
                            **meeting_params
                        }
                    }
                })
                logger.info(f"🔍 create_plan: creating plan for single meeting")
            elif params.get("date") and params.get("time") and params.get("meeting_mode") and params.get("description"):
                # Fallback to collected_params if no tool-specific state
                params_copy = params.copy()
                # Add default name if missing (required by backend)
                if not params_copy.get("name"):
                    params_copy["name"] = "Meeting"
                    logger.info(f"🔍 create_plan: added default name 'Meeting' (name was missing)")
                
                plan.append({
                    "step": len(plan) + 1,
                    "tool": "proxy_tool",
                    "description": "Book meeting",
                    "parameters": {
                        "tool_name": "create_event_tool",
                        "parameters": {
                            "user_sub": state.get("user_sub", ""),
                            **params_copy
                        }
                    }
                })
                logger.info(f"🔍 create_plan: creating plan from collected_params")

    # Handle get_weather_tool
    if "get_weather_tool" in detected_tools:
        logger.info(f"🔍 create_plan: handling get_weather_tool")
        city = params.get("city", "Unknown")
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        plan.append({
            "step": len(plan) + 1,
            "tool": "proxy_tool",
            "description": "Get weather",
            "parameters": {
                "tool_name": "get_weather_tool",
                "parameters": {
                    "city": city,
                    "date": date
                }
            }
        })
        logger.info(f"🔍 create_plan: adding proxy_tool for get_weather_tool with city={city}, date={date}")

    state["plan"] = plan
    logger.info(f"🔍 create_plan: created plan with {len(plan)} steps")
    return state


async def confirm_action(state: PlannerState, planning_llm) -> PlannerState:
    """
    Generic confirmation detection node for all tools using file-based prompts.
    
    Detect if user has confirmed the action before execution.
    Skip confirmation for read-only operations (meetings_summary_tool).
    
    NOW USES FILE-BASED PROMPTS for tool-specific confirmation logic.
    """
    user_input = state.get("user_input", "")
    params = state.get("collected_params", {})
    plan = state.get("plan", [])
    
    # If no plan, nothing to confirm
    if not plan:
        logger.info(f"🔍 confirm_action: no plan to confirm, skipping")
        state["confirmed"] = True
        return state
    
    # Get the tool name from the plan
    tool_name = plan[0].get("tool", "unknown") if plan else "unknown"
    
    # For proxy_tool, check the nested tool_name parameter to determine if it's read-only
    actual_tool_name = tool_name
    if tool_name == "proxy_tool":
        actual_tool_name = plan[0].get("parameters", {}).get("tool_name", "unknown")
    
    # Skip confirmation for read-only tools using config
    if is_read_only_tool(actual_tool_name):
        logger.info(f"🔍 confirm_action: read-only tool {actual_tool_name} (via {tool_name}), auto-confirming")
        state["confirmed"] = True
        return state
    
    # CRITICAL FIX: If we already detected explicit confirmation in create_plan, skip LLM check
    # BUT ONLY if we also have all required fields - otherwise use LLM to detect if user is confirming
    # or still providing information
    user_input_lower = user_input.lower()
    execution_confirmation_phrases = get_confirmation_phrases(actual_tool_name)
    has_explicit_confirmation = any(phrase in user_input_lower for phrase in execution_confirmation_phrases)
    
    # Generic confirmation words (yes, right, correct, please) should ALWAYS go through LLM
    # because the LLM needs to check the bot's previous question to determine intent
    generic_confirmation_words = ["yes", "yeah", "yep", "right", "correct", "please"]
    has_generic_confirmation = any(word in user_input_lower for word in generic_confirmation_words)
    
    # Explicit action phrases (book it, do it, proceed) can skip LLM if all fields present
    explicit_action_phrases = ["book it", "do it", "go ahead", "proceed", "schedule it", "create it", "execute it"]
    has_explicit_action = any(phrase in user_input_lower for phrase in explicit_action_phrases)
    
    # Check if all required fields are present
    required_fields = get_required_fields(actual_tool_name)
    tool_details = state.get("collected_params", {})
    has_all_required = all(tool_details.get(field) for field in required_fields) if required_fields else True
    
    # Only skip LLM if we have explicit ACTION confirmation (not just "yes") AND all required fields
    if has_explicit_action and has_all_required:
        logger.info(f"🔍 confirm_action: explicit action confirmation detected AND all required fields present, skipping LLM check")
        state["confirmed"] = True
        return state
    
    # If user said generic "yes" but all fields present, still use LLM to check bot's previous question
    if has_generic_confirmation and has_all_required:
        logger.info(f"🔍 confirm_action: generic 'yes' detected with all fields present, using LLM to check bot's previous question")
    
    if has_explicit_confirmation and not has_all_required:
        logger.info(f"🔍 confirm_action: explicit confirmation detected but missing required fields, using LLM to verify")
    elif not has_explicit_confirmation:
        logger.info(f"🔍 confirm_action: no explicit confirmation keyword, using LLM to detect")
    
    # Build collective context for confirmation detection
    user_input = state.get("user_input", "")
    confirmation_context = build_collective_context("confirmation_detection", state, user_input)
    
    # Get required fields for the tool
    required_fields = get_required_fields(actual_tool_name)
    
    # Use collective context for tool details
    tool_details = confirmation_context['collected_state']
    
    # Check if all required fields are present (dynamic based on tool config)
    has_all_required = all(tool_details.get(field) for field in required_fields) if required_fields else True
    
    # Build confirmation prompt variables - using collective context
    confirmation_vars = {
        "user_input": user_input,
        "collected_params": json.dumps(tool_details, indent=2),
        "all_required_present": str(has_all_required),
        "conversation_flow": confirmation_context['conversation_flow'],
        "previous_questions": confirmation_context['previous_questions']
    }
    
    # Add dynamic field statuses based on tool config
    all_fields = required_fields + get_optional_fields(actual_tool_name)
    for field in all_fields:
        field_status = tool_details.get(field, 'MISSING')
        confirmation_vars[f"{field}_status"] = field_status
    
    # Use tool-specific confirmation prompt file from config
    from app.prompts import get_confirmation_prompt
    
    confirmation_prompt_file = get_confirmation_prompt_file(actual_tool_name)
    if confirmation_prompt_file:
        confirmation_text = get_confirmation_prompt(actual_tool_name, **confirmation_vars)
    else:
        # Fallback to generic confirmation if no prompt file configured
        confirmation_text = f"User said: '{user_input}'. Are they confirming the action? Reply 'yes' or 'no'."
    
    try:
        response = await planning_llm.ainvoke([
            {"role": "system", "content": "You are a confirmation detector. Return only 'yes' or 'no'."},
            {"role": "user", "content": confirmation_text}
        ])
        user_confirmed = response.content.strip().lower() == "yes"
        logger.info(f"🔍 confirm_action: LLM confirmation detection result={user_confirmed} (input: '{response.content.strip()}')")
        state["confirmed"] = user_confirmed
    except Exception as e:
        logger.error(f"🔍 confirm_action: confirmation detection error: {e}")
        state["confirmed"] = False
    
    return state


def get_user_timezone(user_sub: str) -> str:
    """
    Get user timezone from SQLite database.
    Returns default timezone from config if not found.
    """
    import sqlite3
    from pathlib import Path
    
    default_timezone = get_default_timezone()
    
    if not user_sub:
        return default_timezone
    
    try:
        db_path = Path(__file__).parent.parent.parent / "data" / "app.db"
        if not db_path.exists():
            logger.warning(f"get_user_timezone: database not found at {db_path}")
            return default_timezone
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT timezone FROM user_profiles WHERE sub = ?",
                (user_sub,)
            )
            row = cursor.fetchone()
            if row and row["timezone"]:
                logger.info(f"get_user_timezone: found timezone {row['timezone']} for user {user_sub}")
                return row["timezone"]
    except Exception as e:
        logger.error(f"get_user_timezone: error retrieving timezone: {e}")
    
    return default_timezone


async def execute_plan(state: PlannerState, cache_get=None, cache_set=None) -> PlannerState:
    """Execute planned steps."""
    plan = state["plan"]
    current_step = state["current_step"]
    tool_results = state.get("tool_results", [])
    user_confirmed = state.get("confirmed", False)
    
    logger.info(f"🔍 execute_plan: current_step={current_step}, plan_length={len(plan)}, confirmed={user_confirmed}")
    
    if current_step >= len(plan):
        logger.info(f"🔍 execute_plan: plan complete")
        state["is_complete"] = True
        return state
    
    # Check if user has confirmed before executing
    if not user_confirmed:
        logger.info(f"🔍 execute_plan: user not confirmed, skipping tool execution")
        state["is_complete"] = True  # Mark as complete to avoid infinite loop
        return state
    
    step = plan[current_step]
    tool_name = step["tool"]
    parameters = step.get("parameters", {})
    
    # Add user_sub to parameters if available
    # For proxy_tool, add to nested parameters; for direct tools, add to top-level
    if state.get("user_sub"):
        if tool_name == "proxy_tool":
            if "parameters" not in parameters:
                parameters["parameters"] = {}
            parameters["parameters"]["user_sub"] = state["user_sub"]
        else:
            parameters["user_sub"] = state["user_sub"]
    
    # Add timezone for create_event_tool
    if tool_name == "proxy_tool" and parameters.get("tool_name") == "create_event_tool":
        user_timezone = get_user_timezone(state.get("user_sub", ""))
        if "parameters" not in parameters:
            parameters["parameters"] = {}
        parameters["parameters"]["timezone"] = user_timezone
        logger.info(f"🔍 execute_plan: Added timezone to create_event_tool: {user_timezone}")
        
        # Validate meeting parameters before execution
        tool_params = parameters.get("parameters", {})
        description = tool_params.get("description", "")
        duration = tool_params.get("duration", "")
        
        # Check for corrupted state indicators (using dynamic config)
        corruption_indicators = get_corruption_indicators("create_event_tool")
        is_corrupted = any(indicator in description.lower() for indicator in corruption_indicators)
        
        # Check for invalid duration
        is_invalid_duration = duration in ["0 hours", "0 minutes", "0"] or duration == "0 hours"
        
        if is_corrupted:
            logger.warning(f"🔍 execute_plan: Detected corrupted state in description: '{description}'")
            logger.warning(f"🔍 execute_plan: Skipping execution due to corrupted state")
            tool_results.append({
                "step": current_step,
                "tool": tool_name,
                "result": "Skipped: Corrupted meeting state detected",
                "success": False,
                "success_message": "Meeting state appears corrupted, please start fresh"
            })
            state["tool_results"] = tool_results
            state["current_step"] = current_step + 1
            state["is_complete"] = True
            return state
        
        if is_invalid_duration:
            logger.warning(f"🔍 execute_plan: Invalid duration detected: '{duration}'")
            logger.warning(f"🔍 execute_plan: Skipping execution due to invalid duration")
            tool_results.append({
                "step": current_step,
                "tool": tool_name,
                "result": "Skipped: Invalid duration specified",
                "success": False,
                "success_message": "Please specify a valid meeting duration"
            })
            state["tool_results"] = tool_results
            state["current_step"] = current_step + 1
            state["is_complete"] = True
            return state
    
    logger.info(f"🔍 execute_plan: executing tool={tool_name}, params={parameters}")
       
    # Check cache before executing tool
    if cache_get:
        cached_result = cache_get(tool_name, parameters)
        if cached_result is not None:
            logger.info(f"🔍 execute_plan: using cached result for {tool_name}")
            tool_results.append({"step": current_step, "tool": tool_name, "result": cached_result, "success": True})
            state["tool_results"] = tool_results
            state["current_step"] = current_step + 1
            return state


    tools = get_all_tools()
    tool = next((t for t in tools if t.name == tool_name), None)
    
    if not tool:
        logger.error(f"🔍 execute_plan: tool {tool_name} not found")
        tool_results.append({
            "step": current_step,
            "tool": tool_name,
            "result": f"Tool {tool_name} not found",
            "success": False
        })
        state["tool_results"] = tool_results
        state["current_step"] = current_step + 1
        return state
    
    try:
        result = await tool.ainvoke(parameters)
        logger.info(f"🔍 execute_plan: tool {tool_name} executed successfully")
        
        # Cache the result if cache_set is provided
        if cache_set:
            cache_set(tool_name, parameters, result)
        
        tool_results.append({
            "step": current_step,
            "tool": tool_name,
            "result": result,
            "success": True
        })
    except Exception as e:
        logger.error(f"🔍 execute_plan: tool {tool_name} execution error: {e}")
        tool_results.append({
            "step": current_step,
            "tool": tool_name,
            "result": str(e),
            "success": False
        })
    
    state["tool_results"] = tool_results
    state["current_step"] = current_step + 1
    return state


async def validate_results(state: PlannerState) -> PlannerState:
    """Validate execution results."""
    plan = state["plan"]
    current_step = state["current_step"]
    tool_results = state.get("tool_results", [])
    user_confirmed = state.get("confirmed", False)
    
    # If user didn't confirm, respect the is_complete flag from execute_plan
    if not user_confirmed:
        logger.info(f"🔍 validate_results: user not confirmed, respecting is_complete={state.get('is_complete')}")
        return state
    
    if current_step >= len(plan):
        state["is_complete"] = True
    else:
        if tool_results and not tool_results[-1]["success"]:
            state["error"] = f"Step {current_step} failed: {tool_results[-1]['result']}"
            state["is_complete"] = False
        else:
            state["is_complete"] = False
    
    return state


def should_retry(state: PlannerState) -> str:
    """Determine if execution should retry or complete."""
    return "retry" if not state["is_complete"] else "complete"