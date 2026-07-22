"""
LangGraph workflow for voice orchestration.
Defines the graph nodes and edges for STT → LLM → Tools → TTS pipeline.
"""

from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from app.skills import get_all_tools, get_skill_prompts
from langgraph.checkpoint.memory import MemorySaver
import operator

# Module-level cache for tools and prompts
_tools_cache = None
_prompts_cache = None


class VoiceState(TypedDict):
    """State for the voice orchestration graph."""
    audio_bytes: bytes
    transcription: Optional[str]
    llm_response: Optional[str]
    tool_results: Optional[str]
    final_audio: Optional[bytes]
    user_sub: Optional[str]
    messages: Annotated[list, operator.add]
    # Conversation state for natural multi-turn flow
    intent: Optional[str]  # "booking", "summary", or None
    collected_params: dict  # Parameters collected so far
    available_skills: list[str]  # Skills installed by user


def transcribe_node(state: VoiceState) -> VoiceState:
    """Transcribe audio to text."""
    from app.orchestration import VoiceOrchestrator
    
    orchestrator = VoiceOrchestrator()
    transcription = orchestrator.transcribe_audio(state["audio_bytes"])
    
    return {
        **state,
        "transcription": transcription,
        "messages": [HumanMessage(content=transcription)]
    }


def llm_node(state: VoiceState) -> VoiceState:
    """Process with LLM using tools."""
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import SystemMessage
    
    global _tools_cache, _prompts_cache
    
    # Use cached tools and prompts
    if _tools_cache is None:
        _tools_cache = get_all_tools()
        print("DEBUG: Tools cached in graph module")
    if _prompts_cache is None:
        _prompts_cache = get_skill_prompts()
        print("DEBUG: Skill prompts cached in graph module")
    
    tools = _tools_cache
    skill_prompts = _prompts_cache
    
    # Use the correct format: "provider:model" (like weather agent)
    llm = init_chat_model("ollama:mistral", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    # System prompt with technical skill instructions
    base_prompt = """You are a friendly, energetic, and professional Voice Assistant who helps users with their calendar and meetings.

Current date: 2026-07-01

GENERAL STYLE:
- Keep responses short, warm, and clear
- Ask one question at a time
- Never mention technical details, tool names, or JSON to the user
- Always remain conversational and helpful

INTERNAL INSTRUCTIONS (do not repeat to user):
"""

    # Add technical skill instructions for tool decision rules
    system_prompt = base_prompt + skill_prompts
    
    messages_with_system = [
        SystemMessage(content=system_prompt),
        *state["messages"]
    ]
    
    response = llm_with_tools.invoke(messages_with_system)
    
    return {
        **state,
        "llm_response": response.content,
        "messages": [response]
    }

async def tool_execution_node(state: VoiceState) -> VoiceState:
    """Execute tool calls from LLM response."""
    import json
    import re
    
    last_message = state["messages"][-1]
    
    tool_calls_to_execute = []
    
    # Check for structured tool_calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_calls_to_execute = last_message.tool_calls
    else:
        # Try to parse tool calls from content (JSON format)
        content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        print(f"DEBUG: Content to parse: {repr(content)}")
        # Look for JSON array in content
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            try:
                tool_calls_to_execute = json.loads(json_match.group())
                print(f"DEBUG: Parsed tool calls: {tool_calls_to_execute}")
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON parse error: {e}")
        else:
            print(f"DEBUG: No JSON match found")
    
    if not tool_calls_to_execute:
        return {
            **state,
            "tool_results": "No tool calls needed"
        }
    
    # Execute tool calls
    tool_results = []
    # Load tools dynamically from skills
    from app.skills import get_all_tools
    tools = get_all_tools()
    
    for tool_call in tool_calls_to_execute:
        if isinstance(tool_call, dict):
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})
        else:
            continue
        
        # Add user_sub to args
        tool_args["user_sub"] = state.get("user_sub", "")
        
        # Find and execute the tool
        for tool in tools:
            if tool.name == tool_name:
                # Use await instead of asyncio.run since we're in async context
                result = await tool.ainvoke(tool_args)
                tool_results.append(result)
                break
    
    return {
        **state,
        "tool_results": "\n".join(tool_results),
        "messages": [AIMessage(content="\n".join(tool_results))]
    }


def synthesize_node(state: VoiceState) -> VoiceState:
    """Convert final response to audio."""
    from app.orchestration import VoiceOrchestrator
    
    orchestrator = VoiceOrchestrator()
    
    # Use tool results if available, otherwise use LLM response
    text_to_speak = state.get("tool_results") or state.get("llm_response", "")
    
    audio = orchestrator.synthesize_speech(text_to_speak)
    
    return {
        **state,
        "final_audio": audio
    }


def should_execute_tools(state: VoiceState) -> str:
    """Determine if tools should be executed."""
    import re
    last_message = state["messages"][-1]
    
    # Check for structured tool_calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "execute_tools"
    
    # Check for JSON tool calls in content
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
    if re.search(r'\[.*?"name".*?\]', content, re.DOTALL):
        return "execute_tools"
    
    return "synthesize"


# Build the graph
def build_graph():
    """Build and return the voice orchestration graph with checkpointer for session management."""
    # Create memory checkpointer for multi-turn conversations
    checkpointer = MemorySaver()
    
    workflow = StateGraph(VoiceState)
    
    # Add nodes
    workflow.add_node("transcribe", transcribe_node)
    workflow.add_node("llm_process", llm_node)
    workflow.add_node("execute_tools", tool_execution_node)
    workflow.add_node("synthesize", synthesize_node)
    
    # Add edges
    workflow.set_entry_point("transcribe")
    workflow.add_edge("transcribe", "llm_process")
    workflow.add_conditional_edges(
        "llm_process",
        should_execute_tools,
        {
            "execute_tools": "execute_tools",
            "synthesize": "synthesize"
        }
    )
    workflow.add_edge("execute_tools", "synthesize")
    workflow.add_edge("synthesize", END)
    
    # Compile with checkpointer for session management
    return workflow.compile(checkpointer=checkpointer)
    
# Create the graph instance
voice_graph = build_graph()