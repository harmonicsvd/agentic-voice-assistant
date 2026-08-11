"""Main LangGraph planner class."""
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from app.graph.state import PlannerState
from app.graph.nodes import analyze_request, create_plan, execute_plan, validate_results, should_retry, extract_parameters, confirm_action, analyze_and_extract_optimized
from app.skills import get_skill_prompts
import os
from dotenv import load_dotenv
import time
import logging 

load_dotenv()
logger = logging.getLogger(__name__)

from functools import partial

class LangGraphPlanner:
    """LangGraph planner for multi-step workflow orchestration."""
    
    def __init__(self, user_sub: Optional[str] = None, use_optimized: bool = True):
        self.user_sub = user_sub

        self.tool_cache = {}  # Cache for recent tool executions: {(tool_name, params_hash): (result, timestamp)}
        self.cache_ttl = 30  # Cache time-to-live in seconds
        
        # Use OmniRoute for multi-provider routing with free tier optimization
        # When REQUIRE_API_KEY=false in OmniRoute config, no API key needed
        # Otherwise use "free" placeholder for no-auth providers
        omniroute_api_key = os.getenv("OMNIROUTE_API_KEY", "free")  # Can be empty string if REQUIRE_API_KEY=false
        omniroute_base_url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
        
        # If API key is empty, use a placeholder for OpenAI client compatibility
        if not omniroute_api_key:
            omniroute_api_key = "free"
        
        self.planning_llm = ChatOpenAI(
            api_key=omniroute_api_key,
            base_url=omniroute_base_url,
            model="groq/llama-3.3-70b-versatile",  # Fast Groq model for better performance
            temperature=0.1,
        )
        self.skill_prompts = get_skill_prompts()
        
        # Use optimized graph by default to reduce LLM calls
        if use_optimized:
            self.graph = self._build_optimized_graph()
            logger.info("🚀 Using OPTIMIZED graph (combined analyze+extract)")
        else:
            self.graph = self._build_planning_graph()
            logger.info("Using LEGACY graph (separate analyze+extract)")
            
        self.compiled_graph = self.graph.compile()

    
    async def _analyze_request_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for analyze_request node."""
        return await analyze_request(state, self.planning_llm)

    async def _extract_parameters_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for extract_parameters node."""
        return await extract_parameters(state, self.planning_llm)

    async def _analyze_and_extract_optimized_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for optimized combined analyze and extract node."""
        return await analyze_and_extract_optimized(state, self.planning_llm)

    async def _create_plan_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for create_plan node to pass planning_llm."""
        return await create_plan(state, self.planning_llm)

    async def _confirm_action_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for confirm_action node to pass planning_llm."""
        return await confirm_action(state, self.planning_llm)

    async def _execute_plan_wrapper(self, state: PlannerState) -> PlannerState:
        """Async Wrapper to pass cache methods to execute_plan."""
        return await execute_plan(
            state,
            cache_get=self._get_cached_result,
            cache_set=self._cache_result
        )

    def _build_planning_graph(self) -> StateGraph:
        workflow = StateGraph(PlannerState)
        workflow.add_node("analyze_request", self._analyze_request_wrapper)
        workflow.add_node("extract_parameters", self._extract_parameters_wrapper)
        workflow.add_node("create_plan", self._create_plan_wrapper)
        workflow.add_node("confirm_action", self._confirm_action_wrapper)
        workflow.add_node("execute_plan", self._execute_plan_wrapper)
        workflow.add_node("validate_results", validate_results)
        workflow.set_entry_point("analyze_request")
        workflow.add_edge("analyze_request", "extract_parameters")
        workflow.add_edge("extract_parameters", "create_plan")
        workflow.add_edge("create_plan", "confirm_action")
        workflow.add_edge("confirm_action", "execute_plan")
        workflow.add_edge("execute_plan", "validate_results")
        workflow.add_conditional_edges("validate_results", should_retry, {"retry": "execute_plan", "complete": END})
        return workflow

    def _build_optimized_graph(self) -> StateGraph:
        """Optimized graph using combined analyze_and_extract to reduce LLM calls."""
        workflow = StateGraph(PlannerState)
        workflow.add_node("analyze_and_extract_optimized", self._analyze_and_extract_optimized_wrapper)
        workflow.add_node("create_plan", self._create_plan_wrapper)
        workflow.add_node("confirm_action", self._confirm_action_wrapper)
        workflow.add_node("execute_plan", self._execute_plan_wrapper)
        workflow.add_node("validate_results", validate_results)
        workflow.set_entry_point("analyze_and_extract_optimized")
        workflow.add_edge("analyze_and_extract_optimized", "create_plan")
        workflow.add_edge("create_plan", "confirm_action")
        workflow.add_edge("confirm_action", "execute_plan")
        workflow.add_edge("execute_plan", "validate_results")
        workflow.add_conditional_edges("validate_results", should_retry, {"retry": "execute_plan", "complete": END})
        return workflow

    def _get_cache_key(self, tool_name: str, params: dict) -> tuple:
        """Generate a cache key from tool name and parameters."""
        import hashlib
        import json
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return (tool_name, params_hash)

    def _get_cached_result(self, tool_name: str, params: dict) -> Optional[Any]:
        """Check cache for recent tool execution result."""
        # Skip caching for read-only tools to get fresh data
        if "meetings_summary" in tool_name.lower() or "get_events" in tool_name.lower() or "get_meetings" in tool_name.lower():
            logger.info(f"🔍 Skipping cache for read-only tool: {tool_name}")
            return None

        cache_key = self._get_cache_key(tool_name, params)
        if cache_key in self.tool_cache:
            result, timestamp = self.tool_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"🔍 Cache hit for {tool_name}")
                return result
            else:
                del self.tool_cache[cache_key]
        return None

    def _cache_result(self, tool_name: str, params: dict, result: Any):
        """Cache a tool execution result."""
        cache_key = self._get_cache_key(tool_name, params)
        self.tool_cache[cache_key] = (result, time.time())
        
    async def plan_and_execute(self, user_input: str, conversation_history: list = None, accumulated_params: dict = None) -> Dict[str, Any]:
        initial_state: PlannerState = {
            "user_input": user_input,
            "plan": [],
            "current_step": 0,
            "tool_results": [],
            "collected_params": accumulated_params or {},
            "is_complete": False,
            "error": None,
            "conversation_history": conversation_history or [],
            "user_sub": self.user_sub,
            "confirmed": False,
            "detected_tools": [],
            "tool_specific_state": accumulated_params.get("tool_specific_state") if accumulated_params and "tool_specific_state" in accumulated_params else {},
            "pipeline_status": "started",
            "pipeline_message": "Pipeline started"
        }
        
        final_state = await self.compiled_graph.ainvoke(initial_state)
        
        # Add pipeline status for debugging
        pipeline_status = final_state.get("pipeline_status", "unknown")
        logger.info(f"🚀 PIPELINE COMPLETED: status={pipeline_status}, tools_executed={len(final_state['tool_results'])}")
        
        return {
            "tool_results": final_state["tool_results"],
            "is_complete": final_state["is_complete"],
            "error": final_state["error"],
            "collected_params": final_state["collected_params"],
            "plan": final_state["plan"],
            "pipeline_status": pipeline_status,
            "pipeline_message": final_state.get("pipeline_message", ""),
            "detected_tools": final_state.get("detected_tools", [])
        }