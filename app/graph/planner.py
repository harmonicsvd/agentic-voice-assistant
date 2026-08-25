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

class LangGraphPlanner:
    """LangGraph planner for multi-step workflow orchestration."""
    
    def __init__(self, user_sub: Optional[str] = None, use_optimized: bool = True):
        self.user_sub = user_sub

        self.skill_cache = {}  # Cache for recent skill executions: {(skill_name, params_hash): (result, timestamp)}
        self.cache_ttl = 30  # Cache time-to-live in seconds
        
        # Rate limiting to avoid Groq API 429 errors
        self.last_llm_call_time = 0
        self.min_llm_call_interval = 1.0  # Minimum 500ms between LLM calls
        
        # Use Groq API directly for planning
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required but not set. Please get your API key from https://console.groq.com/keys and add it to your .env file.")
        
        self.planning_llm = ChatOpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            model="openai/gpt-oss-120b",  # Use Groq's GPT OSS 120B model (replacement for discontinued Llama 3.3 70B)
            temperature=0.1,
        )
        
        # Load skill prompts with error handling and logging
        logger.info(f"Loading skill prompts for user_sub: {user_sub}")
        try:
            self.skill_prompts = get_skill_prompts(user_sub=user_sub)
            logger.info(f"Skill prompts loaded successfully, length: {len(self.skill_prompts)}")
        except Exception as e:
            logger.error(f"Failed to load skill prompts: {e}")
            self.skill_prompts = ""  # Fallback to empty prompts
        
        # Use optimized graph by default to reduce LLM calls
        if use_optimized:
            self.graph = self._build_optimized_graph()
            logger.info("🚀 Using OPTIMIZED graph (combined analyze+extract)")
        else:
            self.graph = self._build_planning_graph()
            logger.info("Using LEGACY graph (separate analyze+extract)")
            
        self.compiled_graph = self.graph.compile()
    
    def _rate_limit_llm_call(self):
        """Enforce minimum interval between LLM calls to avoid rate limiting."""
        import time as time_module
        current_time = time_module.time()
        time_since_last_call = current_time - self.last_llm_call_time
        
        if time_since_last_call < self.min_llm_call_interval:
            sleep_time = self.min_llm_call_interval - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f}s before LLM call")
            time_module.sleep(sleep_time)
        
        self.last_llm_call_time = time_module.time()

    
    async def _analyze_request_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for analyze_request node."""
        return await analyze_request(state, self.planning_llm)

    async def _extract_parameters_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for extract_parameters node."""
        return await extract_parameters(state, self.planning_llm)

    async def _analyze_and_extract_optimized_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for optimized combined analyze and extract node."""
        self._rate_limit_llm_call()
        return await analyze_and_extract_optimized(state, self.planning_llm)

    async def _create_plan_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for create_plan node to pass planning_llm."""
        self._rate_limit_llm_call()
        return await create_plan(state, self.planning_llm)

    async def _confirm_action_wrapper(self, state: PlannerState) -> PlannerState:
        """Async wrapper for confirm_action node to pass planning_llm."""
        self._rate_limit_llm_call()
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

    def _get_cache_key(self, skill_name: str, params: dict) -> tuple:
        """Generate a cache key from skill name and parameters."""
        import hashlib
        import json
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return (skill_name, params_hash)

    def _get_cached_result(self, skill_name: str, params: dict) -> Optional[Any]:
        """Check cache for recent skill execution result."""
        # Skip caching for read-only skills to get fresh data
        if "meetings_summary" in skill_name.lower() or "get_events" in skill_name.lower() or "get_meetings" in skill_name.lower():
            logger.info(f"🔍 Skipping cache for read-only skill: {skill_name}")
            return None

        cache_key = self._get_cache_key(skill_name, params)
        if cache_key in self.skill_cache:
            result, timestamp = self.skill_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"🔍 Cache hit for {skill_name}")
                return result
            else:
                del self.skill_cache[cache_key]
        return None

    def _cache_result(self, skill_name: str, params: dict, result: Any):
        """Cache a skill execution result."""
        cache_key = self._get_cache_key(skill_name, params)
        self.skill_cache[cache_key] = (result, time.time())
        
    async def plan_and_execute(self, user_input: str, conversation_history: list = None, accumulated_params: dict = None, available_skills: list = None, installed_skills: list = None) -> Dict[str, Any]:
        initial_state: PlannerState = {
            "user_input": user_input,
            "plan": [],
            "current_step": 0,
            "skill_results": [],
            "collected_params": accumulated_params or {},
            "is_complete": False,
            "error": None,
            "conversation_history": conversation_history or [],
            "user_sub": self.user_sub,
            "confirmed": False,
            "detected_skills": [],
            "skill_specific_state": accumulated_params.get("skill_specific_state") if accumulated_params and "skill_specific_state" in accumulated_params else {},
            "pipeline_status": "started",
            "pipeline_message": "Pipeline started",
            "missing_required_fields": None,
            "available_skills": available_skills or [],
            "installed_skills": installed_skills or [],
            "skill_is_installed": False,  # Default to False for safety - assume not installed unless confirmed
            "active_skill": None  # No active skill initially
        }
        
        final_state = await self.compiled_graph.ainvoke(initial_state)
        
        # Add pipeline status for debugging
        pipeline_status = final_state.get("pipeline_status", "unknown")
        skill_results = final_state.get("skill_results", [])
        logger.info(f"🚀 PIPELINE COMPLETED: status={pipeline_status}, skills_executed={len(skill_results)}")
        
        return {
            "skill_results": final_state.get("skill_results", []),
            "is_complete": final_state.get("is_complete", False),
            "error": final_state.get("error"),
            "collected_params": final_state.get("collected_params", {}),
            "plan": final_state.get("plan", []),
            "pipeline_status": pipeline_status,
            "active_skills": final_state.get("detected_skills", []),
            "pipeline_message": final_state.get("pipeline_message", ""),
            "detected_skills": final_state.get("detected_skills", []),
            "missing_required_fields": final_state.get("missing_required_fields"),
            "available_skills": final_state.get("available_skills", []),
            "skill_is_installed": final_state.get("skill_is_installed", False)
        }