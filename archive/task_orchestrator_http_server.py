#!/usr/bin/env python3
"""
HTTP wrapper for MCP Task Orchestrator
Provides HTTP API endpoints for the task orchestrator tools
Integrates with Ollama for LLM functionality using gpt-oss:latest model
Enhanced with intelligent MCP tools registry integration
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from typing import Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import aiohttp

# Determine project root (directory of this file)
PROJECT_ROOT = Path(__file__).parent.resolve()

# Allow override via env if needed
ATLAS_WORKING_DIR = Path(os.getenv("ATLAS_WORKING_DIR", str(PROJECT_ROOT)))

# Add task orchestrator to path (local vendored directory)
vendored_path = PROJECT_ROOT / "mcp-task-orchestrator"
if vendored_path.exists():
    sys.path.insert(0, str(vendored_path))

# Import task orchestrator components with fallback
try:
    from mcp_task_orchestrator.infrastructure.mcp.tool_definitions import get_all_tools  # type: ignore
    from mcp_task_orchestrator.infrastructure.mcp.tool_router import route_tool_call  # type: ignore
    from mcp_task_orchestrator.infrastructure.mcp.handlers.core_handlers import (  # type: ignore
        setup_logging,
        enable_dependency_injection
    )
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Task orchestrator imports failed: {e}")
    logger.warning("Running in minimal mode without orchestrator functionality")
    ORCHESTRATOR_AVAILABLE = False
    
    # Fallback implementations
    def get_all_tools():
        return []
    
    async def route_tool_call(tool_name: str, parameters: dict):
        return [{"error": "Task orchestrator not available"}]
    
    def setup_logging():
        return logging.getLogger(__name__)
    
    async def enable_dependency_injection():
        pass

# Configure logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(title="Task Orchestrator HTTP Server", version="1.0.0")

# Global state for task orchestrator
orchestrator_initialized = False

# Ollama configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:latest")

class OllamaLLMClient:
    """Client for calling Ollama LLM"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Ollama"""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": f"{context}\n\n{prompt}" if context else prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            logger.info(f"Calling Ollama with model {self.model}")
            
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama error: {response.status} {error_text}")
                        return f"Error calling LLM: {error_text}"
        except Exception as e:
            logger.error(f"Exception calling Ollama: {e}")
            return f"Error calling LLM: {str(e)}"

# Initialize LLM client
llm_client = OllamaLLMClient(OLLAMA_BASE_URL, OLLAMA_MODEL)

async def initialize_orchestrator():
    """Initialize the task orchestrator dependency injection"""
    global orchestrator_initialized
    if not orchestrator_initialized:
        try:
            # Set environment variables for orchestrator configuration
            # Use dynamic working directory instead of CI path
            os.environ.setdefault("MCP_TASK_ORCHESTRATOR_WORKING_DIR", str(ATLAS_WORKING_DIR))
            os.environ.setdefault("MCP_TASK_ORCHESTRATOR_USE_DI", "true")
            
            # Enable dependency injection
            await enable_dependency_injection()
            orchestrator_initialized = True
            logger.info("Task orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize task orchestrator: {e}")
            raise

async def get_mcp_tools_registry() -> Dict[str, Any]:
    """Отримати registry MCP інструментів з Atlas Core (порт 8000) або fallback."""
    candidate_urls = [
        "http://localhost:8000/tools",
        "http://localhost:8000/status"
    ]
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for url in candidate_urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, dict):
                                # /tools endpoint expected structure
                                if "tools" in data and isinstance(data["tools"], dict):
                                    logger.info(f"Retrieved tools registry from {url}: {len(data['tools'])} services")
                                    return data["tools"]
                                # /status might embed tools under mcp.tools
                                mcp = data.get("mcp") if isinstance(data.get("mcp"), dict) else None
                                if mcp and isinstance(mcp.get("tools"), dict):
                                    logger.info(f"Extracted tools registry from status: {len(mcp['tools'])} services")
                                    return mcp["tools"]
                except Exception:
                    continue
        logger.warning("Could not retrieve tools registry from Atlas, using fallback")
    except Exception as e:
        logger.error(f"Error getting tools registry: {e}")
    return {
        "task-orchestrator": ["orchestrator_plan_task", "orchestrator_execute_task", "orchestrator_get_status"],
        "tts": ["say_tts", "stop_tts"],
        "playwright": ["browserNavigate", "browserClick", "browserType", "browserScreenshot"],
        "applescript": ["run_applescript", "system_get_frontmost_app", "notifications_send_notification"]
    }

async def validate_execution_plan(plan: Dict[str, Any], tools_registry: Dict[str, Any]) -> Dict[str, Any]:
    """Валідуємо план виконання на відповідність registry інструментів"""
    validation_result = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "tool_coverage": 0
    }
    
    try:
        subtasks = plan.get("subtasks", [])
        valid_tools = []
        
        # Створюємо плоский список всіх доступних інструментів
        all_available_tools = []
        for service_tools in tools_registry.values():
            all_available_tools.extend(service_tools)
        
        for subtask in subtasks:
            tool_name = subtask.get("tool_name", "")
            tool_service = subtask.get("tool_service", "")
            
            # Перевіряємо існування інструменту
            if tool_name in all_available_tools:
                valid_tools.append(tool_name)
            else:
                validation_result["errors"].append(f"Tool '{tool_name}' not found in registry")
                validation_result["valid"] = False
            
            # Перевіряємо відповідність сервісу
            if tool_service in tools_registry:
                if tool_name not in tools_registry[tool_service]:
                    validation_result["warnings"].append(f"Tool '{tool_name}' not in service '{tool_service}'")
            else:
                validation_result["warnings"].append(f"Service '{tool_service}' not found in registry")
        
        # Розраховуємо покриття
        if subtasks:
            validation_result["tool_coverage"] = len(valid_tools) / len(subtasks)
        
        logger.info(f"Plan validation: {len(valid_tools)}/{len(subtasks)} tools valid, "
                   f"{len(validation_result['errors'])} errors, {len(validation_result['warnings'])} warnings")
        
    except Exception as e:
        validation_result["valid"] = False
        validation_result["errors"].append(f"Validation error: {str(e)}")
    
    return validation_result

async def handle_plan_task_with_llm(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle task planning with intelligent LLM assistance using dynamic tools registry"""
    try:
        task_description = parameters.get("task_description", "")
        context = parameters.get("context", "")
        
        # Отримуємо актуальний registry інструментів
        tools_registry = await get_mcp_tools_registry()
        
        # Формуємо детальний список можливостей
        capabilities_text = "Available MCP Tools by Category:\n"
        for service, tools in tools_registry.items():
            capabilities_text += f"\n{service.upper()}:\n"
            for tool in tools:
                capabilities_text += f"  - {tool}\n"
        
        # Побудова переліку дозволених інструментів
        all_available_tools = []
        for service, tools in tools_registry.items():
            all_available_tools.extend(tools)
        allowed_tools_line = ", ".join(sorted(set(all_available_tools))) or "system_launch_app"

        # Інтелектуальний планувальний prompt (заборона вигаданих інструментів)
        planning_prompt = f"""You are an intelligent task orchestrator with access to real MCP tools. 

TASK: {task_description}
CONTEXT: {context}

{capabilities_text}

INSTRUCTIONS:
1. Break down the task into 3-7 concrete subtasks
2. For each subtask, specify the EXACT tool name from the registry above (allowed tools ONLY): {allowed_tools_line}
    - Do NOT invent tools. If no perfect match exists for launching an app use system_launch_app or run_applescript.
3. Include tool parameters where possible
4. Consider dependencies between subtasks
5. Prioritize efficiency and reliability
6. Reject any invented tool names (e.g. macos_run_shell_command) – they are invalid.

RESPONSE FORMAT (JSON only):
{{
  "plan": {{
    "title": "Main task title",
    "estimated_duration": "5-10 minutes",
    "complexity": "medium",
    "subtasks": [
      {{
        "id": "subtask_1",
        "title": "Specific action description",
        "tool_name": "exact_tool_name_from_registry",
        "tool_service": "service_category",
        "parameters": {{"param1": "value1"}},
        "complexity": "low|medium|high",
        "dependencies": ["subtask_id_if_any"],
        "timeout": 30,
        "retry_policy": "once|multiple|none"
      }}
    ]
  }}
}}

Respond with ONLY the JSON, no other text."""

        # Get LLM response
        llm_response = await llm_client.generate_response(planning_prompt)
        
        # Try to parse JSON from LLM response
        try:
            # Find JSON in response
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = llm_response[json_start:json_end]
                plan_data = json.loads(json_text)
                
                # Валідуємо план
                validation_result = await validate_execution_plan(plan_data.get("plan", {}), tools_registry)
                
                # Створюємо задачу через orchestrator
                result = await route_tool_call("orchestrator_plan_task", {
                    "task_description": task_description,
                    "context": context
                })
                
                # Комбінуємо результати
                return {
                    "success": True,
                    "task_id": f"task_{uuid.uuid4().hex[:8]}",
                    "task_data": plan_data.get("plan", {}),
                    "intelligent_plan": plan_data,
                    "validation": validation_result,
                    "tools_used": len(tools_registry),
                    "orchestrator_result": result,
                    "tool_name": "orchestrator_plan_task"
                }
            else:
                raise ValueError("No valid JSON found in LLM response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse LLM response as JSON: {e}")
            # Fallback: базовий orchestrator
            result = await route_tool_call("orchestrator_plan_task", parameters)
            return {
                "success": True,
                "result": result,
                "fallback": True,
                "error": "LLM parsing failed",
                "tool_name": "orchestrator_plan_task"
            }
            
    except Exception as e:
        logger.error(f"Error in intelligent LLM planning: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": "orchestrator_plan_task"
        }

async def handle_execute_task_with_llm(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle task execution with intelligent LLM assistance"""
    try:
        task_id = parameters.get("task_id", "")
        specialist_context = parameters.get("specialist_context", "")
        
        # Отримуємо актуальний registry інструментів
        tools_registry = await get_mcp_tools_registry()
        
        # Create execution prompt for the LLM
        execution_prompt = f"""You are executing a task with ID: {task_id}

Context: {specialist_context}

Available Tools:
{chr(10).join([f"{service}: {', '.join(tools)}" for service, tools in tools_registry.items()])}

Execute the next step and report results in JSON format:
{{
  "action": "tool_name_to_call",
  "parameters": {{"param": "value"}},
  "reasoning": "Why this action",
  "expected_outcome": "What should happen"
}}"""

        # Get LLM response
        llm_response = await llm_client.generate_response(execution_prompt)
        
        # Use orchestrator to execute
        result = await route_tool_call("orchestrator_execute_task", parameters)
        
        return {
            "success": True,
            "task_id": task_id,
            "execution_details": llm_response,
            "orchestrator_result": result,
            "tool_name": "orchestrator_execute_task"
        }
        
    except Exception as e:
        logger.error(f"Error in intelligent LLM execution: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": "orchestrator_execute_task"
        }

@app.on_event("startup")
async def startup_event():
    """Initialize the task orchestrator on startup"""
    await initialize_orchestrator()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Intelligent Task Orchestrator HTTP Server", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "orchestrator_initialized": orchestrator_initialized}

@app.get("/tools")
async def list_tools():
    """List available tools"""
    if not ORCHESTRATOR_AVAILABLE:
        return {"error": "Task orchestrator not available"}
    
    try:
        tools = get_all_tools()
        tools_data = []
        for tool in tools:
            tools_data.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        return {"tools": tools_data}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return {"error": str(e)}

@app.post("/call_tool")
async def call_tool(request: dict):
    """Call a specific tool with enhanced intelligence"""
    try:
        # Accept both 'name' (current) and legacy 'tool_name'
        tool_name = request.get("name") or request.get("tool_name", "")
        parameters = request.get("parameters", {})
        
        logger.info(f"🔧 Intelligent tool call: {tool_name} with params: {parameters}")
        
        # Enhanced routing with intelligence
        if tool_name == "orchestrator_plan_task":
            result = await handle_plan_task_with_llm(parameters)
        elif tool_name == "orchestrator_execute_task":
            result = await handle_execute_task_with_llm(parameters)
        else:
            # Standard routing for other tools
            result = await route_tool_call(tool_name, parameters)
        
        logger.info(f"🎯 Tool call result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4006))
    uvicorn.run(app, host="0.0.0.0", port=4006)
