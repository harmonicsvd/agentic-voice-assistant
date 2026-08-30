"""
Proxy skill - Delegates all skill execution to weather agent.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
import httpx
import os

BACKEND_AGENT_URL = os.getenv("BACKEND_AGENT_URL", "http://127.0.0.1:9000")
INTERNAL_API_KEY = os.getenv("BACKEND_INTERNAL_API_KEY", "")
BACKEND_AGENT_TIMEOUT = float(os.getenv("BACKEND_AGENT_TIMEOUT_SECONDS", "20"))

class ProxySkillInput(BaseModel):
    """Input schema for proxy skill."""
    skill_name: str = Field(description="Name of the skill to execute")
    parameters: dict = Field(description="Parameters for the skill")
    user_sub: str = Field(default="", description="User identifier for skill access control")

@tool
async def proxy_skill(
    skill_name: str,
    parameters: dict,
    user_sub: str = ""
) -> str:
    """Execute a skill on the backend agent. All skill execution is delegated to the backend agent."""
    url = f"{BACKEND_AGENT_URL}/internal/skills/{skill_name}"
    headers = {
        "X-Internal-API-Key": INTERNAL_API_KEY,
    }
    # Backend expects: parameters (dict) and user_sub (str) as form fields
    # skill_name comes from URL path, not form data - remove it from parameters if present
    if "skill_name" in parameters:
        del parameters["skill_name"]
    
    # Send as JSON body with parameters and user_sub
    headers["Content-Type"] = "application/json"
    json_body = {
        "parameters": parameters,
        "user_sub": user_sub
    }
    try:
        async with httpx.AsyncClient(timeout=BACKEND_AGENT_TIMEOUT) as client:
            response = await client.post(url, json=json_body, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data.get("result", "Skill executed successfully")
                # Format result to include skill name for better tracking
                return f"[{skill_name}] {result}"
            else:
                return f"[{skill_name}] Skill execution failed: {data.get('error', 'Unknown error')}"
        elif response.status_code == 403:
            # User doesn't have this skill installed
            return f"[{skill_name}] I don't have the capability to perform this action. You need to install the {skill_name} skill first."
        elif response.status_code == 404:
            # Skill not found in registry
            return f"[{skill_name}] I don't have the capability to perform this action. The {skill_name} skill is not available."
        elif response.status_code == 422:
            # Unprocessable entity - likely parameter format issue
            return f"[{skill_name}] Skill execution failed: Invalid parameters format. Backend returned: {response.text}"
        else:
            return f"[{skill_name}] Failed to execute skill: {response.status_code} - {response.text}"
    except Exception as e:
        return f"[{skill_name}] Failed to execute skill: {str(e)}"

skills = [proxy_skill]