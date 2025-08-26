#!/usr/bin/env python3
"""
HTTP wrapper for MCP Task Orchestrator
Provides HTTP API endpoints for the task orchestrator tools
Integrates with Ollama for LLM functionality using gpt-oss:latest model
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import aiohttp

# Add task orchestrator to path
sys.path.append(str(Path(__file__).parent / "mcp-task-orchestrator"))

# Import task orchestrator components
from mcp_task_orchestrator.infrastructure.mcp.tool_definitions import get_all_tools
from mcp_task_orchestrator.infrastructure.mcp.tool_router import route_tool_call
from mcp_task_orchestrator.infrastructure.mcp.handlers.core_handlers import (
    setup_logging,
    enable_dependency_injection
)

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
            os.environ.setdefault("MCP_TASK_ORCHESTRATOR_WORKING_DIR", "/home/runner/work/Atlas-mcp-1/Atlas-mcp-1")
            os.environ.setdefault("MCP_TASK_ORCHESTRATOR_USE_DI", "true")
            
            # Enable dependency injection
            await enable_dependency_injection()
            orchestrator_initialized = True
            logger.info("Task orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize task orchestrator: {e}")
            raise

@app.on_event("startup")
async def startup_event():
    """Initialize the task orchestrator on startup"""
    await initialize_orchestrator()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Task Orchestrator HTTP Server", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "orchestrator_initialized": orchestrator_initialized}

@app.get("/tools")
async def list_tools():
    """List available tools"""
    try:
        await initialize_orchestrator()
        tools = get_all_tools()
        return {"tools": [{"name": tool.name, "description": tool.description} for tool in tools]}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/call_tool")
async def call_tool(request: Dict[str, Any]):
    """Call a tool with parameters"""
    try:
        await initialize_orchestrator()
        
        tool_name = request.get("tool_name")
        parameters = request.get("parameters", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="tool_name is required")
        
        logger.info(f"Calling tool: {tool_name} with parameters: {parameters}")
        
        # For certain tools that need LLM assistance, we need to provide that capability
        if tool_name == "orchestrator_plan_task":
            return await handle_plan_task_with_llm(parameters)
        elif tool_name == "orchestrator_execute_task":
            return await handle_execute_task_with_llm(parameters)
        
        # Call the tool through the MCP router
        result = await route_tool_call(tool_name, parameters)
        
        # Convert MCP result to JSON-serializable format
        if result:
            # Extract text content from MCP response
            response_data = []
            for item in result:
                if hasattr(item, 'text'):
                    response_data.append(item.text)
                else:
                    response_data.append(str(item))
            
            return {
                "success": True,
                "result": response_data,
                "tool_name": tool_name
            }
        else:
            return {
                "success": True,
                "result": ["Tool executed successfully"],
                "tool_name": tool_name
            }
    
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name
        }

async def handle_plan_task_with_llm(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle task planning with LLM assistance"""
    try:
        task_description = parameters.get("task_description", "")
        context = parameters.get("context", "")
        
        # Create a planning prompt for the LLM
        planning_prompt = f"""You are a task orchestrator. Break down this task into manageable subtasks.

Task: {task_description}
Context: {context}

Available capabilities:
- macOS automation (mouse, keyboard, screenshots)
- AppleScript execution
- Browser automation
- Text-to-speech
- File operations

Create a detailed plan with 3-5 subtasks. For each subtask, specify:
1. Title (brief description)
2. Type (automation, applescript, browser, tts, or file)
3. Complexity (low, medium, high)
4. Dependencies (which other subtasks must complete first)

Respond in JSON format:
{{
  "plan": {{
    "title": "Main task title",
    "subtasks": [
      {{
        "id": "subtask_1",
        "title": "Subtask description",
        "type": "automation",
        "complexity": "medium",
        "dependencies": [],
        "details": "Specific steps to accomplish this subtask"
      }}
    ]
  }}
}}"""

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
                
                # Now use the orchestrator to create the task
                result = await route_tool_call("orchestrator_plan_task", {
                    "task_description": task_description,
                    "context": context
                })
                
                # Combine LLM planning with orchestrator result
                return {
                    "success": True,
                    "task_id": f"task_{uuid.uuid4().hex[:8]}",
                    "task_data": plan_data.get("plan", {}),
                    "llm_plan": plan_data,
                    "orchestrator_result": result,
                    "tool_name": "orchestrator_plan_task"
                }
            else:
                # Fallback to basic orchestrator
                result = await route_tool_call("orchestrator_plan_task", parameters)
                return {
                    "success": True,
                    "result": result,
                    "tool_name": "orchestrator_plan_task"
                }
                
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM response as JSON, falling back to basic orchestrator")
            result = await route_tool_call("orchestrator_plan_task", parameters)
            return {
                "success": True,
                "result": result,
                "tool_name": "orchestrator_plan_task"
            }
            
    except Exception as e:
        logger.error(f"Error in LLM-assisted planning: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": "orchestrator_plan_task"
        }

async def handle_execute_task_with_llm(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle task execution with LLM assistance"""
    try:
        task_id = parameters.get("task_id", "")
        specialist_context = parameters.get("specialist_context", "")
        
        # Create execution prompt for the LLM
        execution_prompt = f"""You are executing a task with ID: {task_id}

Context: {specialist_context}

Available tools for execution:
- automation: mouseClick, mouseMove, screenshot, type, keyControl, systemCommand
- applescript: run_applescript
- browser: navigate, click, type, screenshot
- tts: text-to-speech functions

Determine the specific actions needed and respond with implementation details.
Focus on practical, executable steps for macOS automation.

Provide specific implementation details for the task."""

        # Get LLM guidance
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
        logger.error(f"Error in LLM-assisted execution: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": "orchestrator_execute_task"
        }

@app.post("/orchestrate")
async def orchestrate_task(request: Dict[str, Any]):
    """High-level orchestration endpoint"""
    try:
        await initialize_orchestrator()
        
        task_description = request.get("task_description")
        if not task_description:
            raise HTTPException(status_code=400, detail="task_description is required")
        
        # Initialize session
        init_result = await route_tool_call("orchestrator_initialize_session", {
            "working_directory": request.get("working_directory", "/home/runner/work/Atlas-mcp-1/Atlas-mcp-1")
        })
        
        # Plan task with LLM assistance
        plan_result = await handle_plan_task_with_llm({
            "task_description": task_description,
            "context": request.get("context", "")
        })
        
        return {
            "success": True,
            "initialization": init_result,
            "plan": plan_result
        }
        
    except Exception as e:
        logger.error(f"Error orchestrating task: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point"""
    port = int(os.environ.get("TASK_ORCHESTRATOR_PORT", "4006"))
    host = os.environ.get("TASK_ORCHESTRATOR_HOST", "0.0.0.0")
    
    logger.info(f"Starting Task Orchestrator HTTP Server on {host}:{port}")
    logger.info(f"Using Ollama at {OLLAMA_BASE_URL} with model {OLLAMA_MODEL}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    import uuid  # Add missing import
    main()