#!/usr/bin/env python3
"""
Atlas Autonomous macOS Management System
=======================================

Core module for the Atlas system that provides autonomous computer management
capabilities for macOS systems using AI agents and modular MCP servers.

Features:
- Multi-agent AI system (LLM1: Interface, LLM2: Orchestrator, LLM3: Monitor)
- Native macOS automation via Automator and System Events
- Local LLM processing with Ollama for privacy
- Modular MCP (Model Context Protocol) architecture
- Voice interaction with TTS/STT
- Web-based control interface
- Autonomous decision-making and task execution

Author: Atlas AI Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import re
import platform
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Third-party imports (will be installed via requirements.txt)
try:
    import aiohttp
    import ollama
    from fastapi import FastAPI, HTTPException, Response
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from dotenv import load_dotenv
    # Prometheus metrics
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except ImportError as e:
    print(f"Missing required packages. Please run: pip install -r requirements.txt")
    print(f"Error: {e}")
    sys.exit(1)

# Optional imports for TTS functionality
UKRAINIAN_TTS_AVAILABLE = False
PYGAME_AVAILABLE = False

try:
    from ukrainian_tts.tts import TTS  # type: ignore
    UKRAINIAN_TTS_AVAILABLE = True
except ImportError:
    TTS = None

try:
    import pygame  # type: ignore
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('atlas.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Atlas')

# Load environment variables from .env only when running on host (not in Docker)
def _is_container() -> bool:
    try:
        if os.path.exists('/.dockerenv'):
            return True
        # cgroup hint (works on many distros)
        cgroup_path = '/proc/1/cgroup'
        if os.path.exists(cgroup_path):
            with open(cgroup_path, 'r') as f:
                data = f.read()
            if 'docker' in data or 'containerd' in data:
                return True
    except Exception:
        pass
    return False

try:
    if not _is_container() and os.getenv("ATLAS_IGNORE_DOTENV", "0") != "1":
        load_dotenv()
except Exception:
    # It's safe to proceed if dotenv isn't available or .env is missing
    pass

@dataclass
class AgentConfig:
    """Configuration for LLM agents"""
    name: str
    role: str
    model: str
    provider: str = "ollama"
    api_base: str = "http://localhost:11434"
    max_tokens: int = 1000
    temperature: float = 0.7

@dataclass
class SystemStatus:
    """System status information"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_tasks: int
    agent_status: Dict[str, str]

class MacOSAutomation:
    """Handle native macOS automation tasks"""
    
    def __init__(self):
        self.verify_macos()
        
    def verify_macos(self):
        """Verify we're running on macOS"""
        if platform.system() != "Darwin":
            logger.warning("This system is optimized for macOS but can run on other platforms with limited functionality")
    
    async def execute_applescript(self, script: str) -> str:
        """Execute AppleScript for macOS automation"""
        try:
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                logger.error(f"AppleScript error: {stderr.decode()}")
                return ""
        except Exception as e:
            logger.error(f"Failed to execute AppleScript: {e}")
            return ""
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        info = {
            "platform": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        
        if platform.system() == "Darwin":
            # Get macOS-specific information
            script = '''
            tell application "System Information"
                return computer name
            end tell
            '''
            computer_name = await self.execute_applescript(script)
            info["computer_name"] = computer_name
            
        return info
    
    async def manage_applications(self, action: str, app_name: str) -> bool:
        """Manage applications (open, close, minimize)"""
        if platform.system() != "Darwin":
            logger.warning("Application management requires macOS")
            return False
            
        try:
            if action == "open":
                script = f'tell application "{app_name}" to activate'
            elif action == "close":
                script = f'tell application "{app_name}" to quit'
            elif action == "minimize":
                script = f'''
                tell application "System Events"
                    tell process "{app_name}"
                        set visible to false
                    end tell
                end tell
                '''
            else:
                return False
                
            result = await self.execute_applescript(script)
            return True
        except Exception as e:
            logger.error(f"Failed to {action} {app_name}: {e}")
            return False

class LLMAgent:
    """Base class for LLM agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = None
        self.setup_client()

    def setup_client(self):
        """Setup the LLM client based on provider"""
        if self.config.provider == "ollama":
            # Allow both OLLAMA_URL (with scheme) and OLLAMA_HOST (host:port)
            api_base = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST") or self.config.api_base
            if api_base and not api_base.startswith("http"):
                api_base = f"http://{api_base}"
            try:
                self.client = ollama.Client(host=api_base)
                logger.info(f"Initialized LLM client for {self.config.name} with provider={self.config.provider}, api_base={api_base}, model={self.config.model}")
            except Exception as e:
                self.client = None
                logger.error(f"Failed to initialize LLM client for {self.config.name}: {e}")
        else:
            logger.warning(f"Provider {self.config.provider} not yet implemented")

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response from the LLM"""
        try:
            # Lazy init if needed
            if self.client is None:
                logger.warning(f"LLM client was not initialized for {self.config.name}. Attempting to initialize now...")
                self.setup_client()
            if self.client is None:
                logger.error(f"LLM client is not initialized for {self.config.name} (provider={self.config.provider})")
                return f"Error: LLM client not initialized for {self.config.name}"
            full_prompt = f"{context}\n\nКористувач: {prompt}\nВідповідь:" if context else prompt

            response = await self.client.generate(
                model=self.config.model,
                prompt=full_prompt,
                options={
                    'temperature': self.config.temperature,
                    'num_predict': self.config.max_tokens,
                },
            )
            return response['response']
        except Exception as e:
            logger.error(f"Failed to generate response for {self.config.name}: {e}")
            return f"Error: Unable to generate response from {self.config.name}"

class AtlasCore:
    """Main Atlas system orchestrator"""
    
    def __init__(self):
        self.agents = {}
        self.macos_automation = MacOSAutomation()
        self.task_queue = asyncio.Queue()
        self.system_status = None
        self.app = FastAPI(title="Atlas Autonomous System", version="1.0.0")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # MCP config store
        self.mcp_endpoints: Dict[str, Dict[str, str]] = {}
        
        # MCP Proxy support (Variant B)
        self.mcp_proxy_mode = os.getenv('ATLAS_MCP_PROXY_MODE', 'false').lower() == 'true'
        self.mcp_proxy_url = os.getenv('ATLAS_MCP_PROXY_URL', 'http://127.0.0.1:9090')
        self.mcp_tools_cache = {}
        # Список клієнтів для proxy (name[:type]) напр.: "tts:sse,playwright:streamable-http,automation:stdio"
        self.mcp_proxy_clients_raw = os.getenv('ATLAS_MCP_PROXY_CLIENTS', 'tts,automation,playwright,task-orchestrator')
        self.mcp_proxy_clients = {}
        
        # LLM1 log monitoring and feedback system
        self.log_monitor_task = None
        self.last_feedback_time = datetime.now()
        self.monitoring_enabled = True
        self.log_buffer = []
        self.max_log_buffer_size = 100
        
        self.setup_agents()
        self.setup_web_interface()
        if self.mcp_proxy_mode:
            logger.info("Atlas MCP Proxy mode enabled (Variant B)")
        else:
            self.load_mcp_config()
    
    @staticmethod
    def _normalize_model(name: str) -> str:
        """Normalize known model aliases to valid Ollama tags.
        Keeps original if unknown.
        """
        if not name:
            return name
        aliases = {
            # Common external aliases -> Ollama tags
            "mistral-medium-latest": "mistral:latest",
            "mistral-medium": "mistral:latest",
            "llama3.1:8b-instruct": "llama3.1:8b",
            "llama3-instruct": "llama3:latest",
        }
        return aliases.get(name, name)
        
    def setup_agents(self):
        """Initialize the three main LLM agents"""
        # Resolve common settings from env
        default_provider = os.getenv("ATLAS_LLM_PROVIDER", "ollama")
        # Prefer per-agent model envs, then common, then sensible defaults available in repo
        llm1_model = os.getenv("ATLAS_LLM1_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "gpt-oss:latest"
        llm2_model = os.getenv("ATLAS_LLM2_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "gpt-oss:latest"
        llm3_model = os.getenv("ATLAS_LLM3_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "gpt-oss:latest"
        # Normalize any known aliases to valid Ollama tags
        llm1_model = self._normalize_model(llm1_model)
        llm2_model = self._normalize_model(llm2_model)
        llm3_model = self._normalize_model(llm3_model)
        api_base = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        if api_base and not str(api_base).startswith("http"):
            api_base = f"http://{api_base}"

        # LLM1 - Interface & Memory Agent
        llm1_config = AgentConfig(
            name="LLM1_Interface",
            role="User interface and memory management",
            model=llm1_model,
            provider=os.getenv("ATLAS_LLM1_PROVIDER", default_provider),
            api_base=str(api_base)
        )
        
        # LLM2 - Orchestrator Agent  
        llm2_config = AgentConfig(
            name="LLM2_Orchestrator", 
            role="Task orchestration and planning",
            model=llm2_model,
            provider=os.getenv("ATLAS_LLM2_PROVIDER", default_provider),
            api_base=str(api_base)
        )
        
        # LLM3 - Monitor Agent
        llm3_config = AgentConfig(
            name="LLM3_Monitor",
            role="System monitoring and security",
            model=llm3_model,
            provider=os.getenv("ATLAS_LLM3_PROVIDER", default_provider),
            api_base=str(api_base)
        )
        
        self.agents = {
            "interface": LLMAgent(llm1_config),
            "orchestrator": LLMAgent(llm2_config),
            "monitor": LLMAgent(llm3_config)
        }
        # Log effective agent configs for troubleshooting
        logger.info(
            "LLM agent configs: LLM1(provider=%s, model=%s, api=%s), LLM2(provider=%s, model=%s), LLM3(provider=%s, model=%s)",
            llm1_config.provider, llm1_config.model, llm1_config.api_base,
            llm2_config.provider, llm2_config.model,
            llm3_config.provider, llm3_config.model,
        )
        # Warn if non-ollama provider requested but not implemented
        for key, agent in self.agents.items():
            if agent.config.provider != "ollama":
                logger.warning("Provider %s for %s is not implemented; fallback to ollama is not automatic.", agent.config.provider, key)
        logger.info("Initialized all three LLM agents")
    
    def setup_web_interface(self):
        """Setup FastAPI web interface"""
        # Basic Prometheus metrics for requests
        REQUEST_COUNT = Counter(
            "atlas_requests_total", "Total HTTP requests", ["method", "path", "status"]
        )
        REQUEST_LATENCY = Histogram(
            "atlas_request_latency_seconds", "Request latency in seconds", ["method", "path"]
        )

        @self.app.middleware("http")
        async def metrics_middleware(request, call_next):
            method = request.method
            path = request.url.path
            start = asyncio.get_event_loop().time()
            try:
                response = await call_next(request)
                status = str(response.status_code)
                REQUEST_COUNT.labels(method, path, status).inc()
                REQUEST_LATENCY.labels(method, path).observe(asyncio.get_event_loop().time() - start)
                return response
            except Exception:
                REQUEST_COUNT.labels(method, path, "500").inc()
                REQUEST_LATENCY.labels(method, path).observe(asyncio.get_event_loop().time() - start)
                raise
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return """
            <!DOCTYPE html>
            <html>
           
            </html>
            """
        
        @self.app.post("/chat")
        async def chat(request: dict):
            message = request.get("message", "")
            response = await self.process_user_message(message)
            return {"response": response}
        
        @self.app.post("/action")
        async def action(request: dict):
            action = request.get("action", "")
            result = await self.execute_action(action)
            return {"result": result}
        
        @self.app.post("/tts")
        async def tts(request: dict):
            text = request.get("text", "")
            rate = request.get("rate", 200)
            if not text:
                raise HTTPException(status_code=400, detail="Text is required")
            
            try:
                # Use direct TTS implementation
                result = await self.call_mcp_tool_via_proxy("say_tts", {"text": text, "rate": rate})
                return result
            except Exception as e:
                logger.error(f"TTS error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status")
        async def status():
            return await self.get_system_status()

        @self.app.get("/metrics")
        async def metrics():
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    async def process_user_message(self, message: str) -> str:
        """Process user message through the 3-agent system"""
        logger.info(f"🔵 [LLM1] Received user message: {repr(message)}")
        
        try:
            # 🔵 PHASE 1: LLM1 - Interface Agent (Ukrainian communication)
            llm1_context = """Ти - LLM1 (Interface Agent) системи Atlas. 
Твоя роль: спілкуватися з користувачем ТІЛЬКИ українською мовою і звітувати про стан.

ПРАВИЛА:
- Розмовляй ТІЛЬКИ українською мовою  
- НІКОЛИ не використовуй російську або англійську
- Відповідай КОРОТКО (1-2 речення)
- Якщо користувач просить щось ВИКОНАТИ - скажи що передаєш завдання до системи
- Постійно звітуй про прогрес виконання"""

            # LLM1 дає початкову відповідь користувачу
            initial_response = await self.agents["interface"].generate_response(message, llm1_context)
            cleaned_response = self._clean_response(initial_response)
            
            # 🔵 LLM1 звітує про початок
            logger.info(f"🔵 [LLM1] Initial response: {cleaned_response}")
            
            # Перевірка чи потрібно виконання задач
            action_keywords = ['open', 'close', 'run', 'execute', 'launch', 'start', 'stop', 
                             'відкрий', 'закрий', 'запусти', 'виконай', 'розгорни', 'запуск', 'стоп']
            
            needs_execution = any(keyword in message.lower() for keyword in action_keywords)
            
            if needs_execution:
                # 🔵 LLM1 звітує про передачу завдання
                progress_report = f"{cleaned_response}\n🔄 Передаю завдання до системи виконання..."
                logger.info(f"🔵 [LLM1] Transferring task to LLM2")
                
                # 🟡 PHASE 2: LLM1 транслює завдання для LLM2 англійською
                translation_prompt = f"""Translate this Ukrainian user request to detailed English task description for LLM2 Orchestrator:

User request (Ukrainian): "{message}"

Provide ONLY the English translation as a clear, detailed task description that LLM2 can understand and execute using MCP tools."""

                english_task = await self.agents["interface"].generate_response(translation_prompt, "Translate to English for LLM2. Return ONLY the English task description.")
                english_task = english_task.strip().replace("English task description:", "").strip()
                
                logger.info(f"🔵 [LLM1] Translated task for LLM2: {english_task}")
                
                # 🟠 PHASE 3: Task Orchestrator - Планування і виконання через MCP Task Orchestrator
                execution_results = await self.execute_task_with_task_orchestrator(english_task, message)
                
                # 🔵 PHASE 4: LLM1 звітує про результати
                final_report = await self.generate_final_report_llm1(cleaned_response, execution_results)
                
                # Озвучуємо фінальний звіт
                try:
                    await self.call_mcp_tool_via_proxy("say_tts", {"text": final_report})
                except Exception as e:
                    logger.warning(f"TTS failed: {e}")
                
                return final_report
            
            else:
                # Простий діалог без виконання дій
                try:
                    await self.call_mcp_tool_via_proxy("say_tts", {"text": cleaned_response})
                except Exception as e:
                    logger.warning(f"TTS failed: {e}")
                
                return cleaned_response
                
        except Exception as e:
            logger.error(f"🔴 [LLM1] Error processing message: {e}")
            error_msg = f"Вибачте, сталася помилка при обробці запиту: {str(e)}"
            return error_msg
    
    def _clean_response(self, response: str) -> str:
        """Clean response from English translations and system prefixes"""
        import re
        
        # Remove common system prefixes at the beginning
        cleaned = re.sub(r'^(Atlas Interface:|Interface Agent:|Atlas:|LLM1:|LLM1,|Assistant:)\s*', '', response.strip())
        
        # Remove English translations in parentheses (case insensitive)
        cleaned = re.sub(r'\s*\([^)]*\b(?:Hello|Everything|good|how are you|thank you|please|sorry)\b[^)]*\)', '', cleaned, flags=re.IGNORECASE)
        
        # Remove any remaining full English parenthetical expressions
        cleaned = re.sub(r'\s*\([A-Za-z\s,!?.-]+\)', '', cleaned)
        
        # Remove excessive context that might be leaked from prompts
        cleaned = re.sub(r'^.*?User:.*?Assistant:\s*', '', cleaned, flags=re.DOTALL)
        
        # Clean up extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'^\s*\n+', '', cleaned)
        
        return cleaned
    
    async def execute_task_with_task_orchestrator(self, english_task: str, original_message: str) -> List[Dict]:
        """🟠 Task Orchestrator - планує і виконує завдання через MCP Task Orchestrator"""
        logger.info(f"🟠 [Task Orchestrator] Starting task orchestration: {english_task}")
        
        # 🔴 LLM3 Security Check
        security_check = await self.security_check_llm3(english_task)
        if not security_check["approved"]:
            logger.warning(f"🔴 [LLM3] Task rejected: {security_check['reason']}")
            return [{"success": False, "error": f"Відхилено з міркувань безпеки: {security_check['reason']}"}]
        
        logger.info(f"🔴 [LLM3] Task approved")
        
        try:
            # Call Task Orchestrator via MCP to initialize session and plan task
            execution_results = []
            
            # Step 1: Initialize orchestration session
            logger.info(f"🟠 [Task Orchestrator] Initializing session")
            # Determine working directory dynamically (fallback to current file's parent)
            working_dir = os.getenv("ATLAS_WORKING_DIR") or os.getcwd()
            init_result = await self.call_task_orchestrator_tool("orchestrator_initialize_session", {
                "working_directory": working_dir
            })
            
            if not init_result.get("success", False):
                logger.error(f"🟠 [Task Orchestrator] Failed to initialize: {init_result}")
                return [{"success": False, "error": "Failed to initialize task orchestrator"}]
            
            # Step 2: Plan the task
            logger.info(f"🟠 [Task Orchestrator] Planning task")
            plan_result = await self.call_task_orchestrator_tool("orchestrator_plan_task", {
                "task_description": english_task,
                "context": f"Original Ukrainian request: {original_message}. Available tools: macOS automation, applescript, browser automation, TTS, file operations."
            })
            
            if not plan_result.get("success", False):
                logger.error(f"🟠 [Task Orchestrator] Failed to plan: {plan_result}")
                return [{"success": False, "error": "Failed to plan task"}]
            
            execution_results.append(plan_result)
            
            # Step 3: Execute the task if planning was successful
            if plan_result.get("task_id"):
                logger.info(f"🟠 [Task Orchestrator] Executing task {plan_result['task_id']}")
                
                # Execute each subtask
                task_data = plan_result.get("task_data", {})
                subtasks = task_data.get("subtasks", [])
                
                for i, subtask in enumerate(subtasks):
                    logger.info(f"🟠 [Task Orchestrator] Executing subtask {i+1}/{len(subtasks)}: {subtask.get('title', 'Unknown')}")
                    
                    # 🔵 LLM1 звітує про прогрес
                    await self.llm1_progress_report(f"Виконую підзавдання {i+1} з {len(subtasks)}: {subtask.get('title', 'Unknown')}")
                    
                    # Execute the subtask
                    exec_result = await self.call_task_orchestrator_tool("orchestrator_execute_task", {
                        "task_id": subtask.get("id"),
                        "specialist_context": "You have access to macOS automation tools, AppleScript, browser automation, and TTS. Use these tools to accomplish the task."
                    })
                    
                    execution_results.append(exec_result)
                    
                    if exec_result.get("success", False):
                        # Mark subtask as complete
                        complete_result = await self.call_task_orchestrator_tool("orchestrator_complete_task", {
                            "task_id": subtask.get("id"),
                            "result": exec_result.get("result", ""),
                            "artifacts": exec_result.get("artifacts", [])
                        })
                        execution_results.append(complete_result)
                
                # Step 4: Synthesize results
                logger.info(f"🟠 [Task Orchestrator] Synthesizing results")
                synthesis_result = await self.call_task_orchestrator_tool("orchestrator_synthesize_results", {
                    "session_id": plan_result.get("session_id"),
                    "summary_request": "Provide a summary of what was accomplished"
                })
                execution_results.append(synthesis_result)
            
            logger.info(f"🟠 [Task Orchestrator] Task completed: {len(execution_results)} operations executed")
            return execution_results
            
        except Exception as e:
            logger.error(f"🟠 [Task Orchestrator] Task execution error: {e}")
            return [{"success": False, "error": f"Task orchestration failed: {str(e)}"}]

    async def execute_task_with_llm2(self, english_task: str, original_message: str) -> List[Dict]:
        """🟠 LLM2 Orchestrator - планує і виконує завдання з MCP tools (Legacy, replaced by task orchestrator)"""
        logger.info(f"🟠 [LLM2] Starting task orchestration: {english_task}")
        
        # 🔴 LLM3 Security Check
        security_check = await self.security_check_llm3(english_task)
        if not security_check["approved"]:
            logger.warning(f"🔴 [LLM3] Task rejected: {security_check['reason']}")
            return [{"success": False, "error": f"Відхилено з міркувань безпеки: {security_check['reason']}"}]
        
        logger.info(f"🔴 [LLM3] Task approved")
        
        try:
            # LLM2 створює план виконання
            llm2_context = f"""You are LLM2 (Orchestrator Agent) in the Atlas system.
Your role: Plan and execute tasks using available MCP tools through proxy.

AVAILABLE MCP TOOLS (via proxy at {self.mcp_proxy_url}):
- tts: say_tts, elevenlabs_tts, google_tts, openai_tts
- automation: mouseClick, mouseMove, screenshot, type, keyControl, systemCommand
- applescript: run_applescript  
- automator: run_workflow
- playwright: browser_navigate, browser_click, browser_type, browser_screenshot
- vnc: vnc_screenshot, vnc_control

TASK: {english_task}

Create a detailed step-by-step execution plan. Return ONLY valid JSON format:
{{
  "steps": [
    {{"service": "automation", "tool": "mouseClick", "params": {{"x": 100, "y": 200}}}},
    {{"service": "applescript", "tool": "run_applescript", "params": {{"script": "tell application \\"Safari\\" to activate"}}}}
  ]
}}

Focus on the most direct approach to accomplish the task."""

            plan_response = await self.agents["orchestrator"].generate_response(english_task, llm2_context)
            logger.info(f"🟠 [LLM2] Raw plan: {plan_response}")
            
            # Парсинг JSON плану
            execution_results = []
            try:
                # Знаходимо JSON в відповіді
                json_start = plan_response.find('{')
                json_end = plan_response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = plan_response[json_start:json_end]
                    plan = json.loads(json_text)
                    
                    logger.info(f"🟠 [LLM2] Parsed plan: {len(plan.get('steps', []))} steps")
                    
                    # Виконання кожного кроку
                    for i, step in enumerate(plan.get("steps", [])):
                        logger.info(f"🟠 [LLM2] Executing step {i+1}: {step}")
                        
                        # 🔵 LLM1 звітує про прогрес
                        await self.llm1_progress_report(f"Виконую крок {i+1} з {len(plan['steps'])}")
                        
                        # Виконання через MCP Proxy
                        step_result = await self.execute_mcp_step_via_proxy(step, i+1)
                        execution_results.append(step_result)
                        
                        # Якщо крок провалився, LLM2 може спробувати альтернативу
                        if not step_result.get("success", False) and i < len(plan["steps"]) - 1:
                            logger.info(f"🟠 [LLM2] Step {i+1} failed, attempting recovery")
                            recovery_result = await self.llm2_error_recovery(step, step_result["error"])
                            if recovery_result:
                                execution_results.append(recovery_result)
                    
                else:
                    # Fallback якщо JSON не знайдено
                    logger.warning("🟠 [LLM2] No JSON found, using fallback execution")
                    fallback_result = await self.execute_simple_task(english_task)
                    execution_results.append(fallback_result)
                    
            except json.JSONDecodeError as e:
                logger.error(f"🟠 [LLM2] JSON parse error: {e}")
                fallback_result = await self.execute_simple_task(english_task) 
                execution_results.append(fallback_result)
                
            logger.info(f"🟠 [LLM2] Task completed: {len(execution_results)} steps executed")
            return execution_results
            
        except Exception as e:
            logger.error(f"🟠 [LLM2] Task execution error: {e}")
            return [{"success": False, "error": str(e)}]
    
    async def generate_final_report_llm1(self, initial_response: str, execution_results: List[Dict]) -> str:
        """🔵 LLM1 генерує фінальний звіт українською"""
        logger.info(f"🔵 [LLM1] Generating final report")
        
        # Підрахунок результатів
        successful_steps = [r for r in execution_results if r.get("success", False)]
        failed_steps = [r for r in execution_results if not r.get("success", False)]
        
        # Формування контексту для LLM1
        results_context = f"""Результати виконання:
Успішно: {len(successful_steps)} кроків
Помилки: {len(failed_steps)} кроків

Деталі успішних кроків:
{json.dumps(successful_steps[:3], indent=2, ensure_ascii=False)}

Деталі помилок:
{json.dumps(failed_steps[:2], indent=2, ensure_ascii=False)}"""

        llm1_final_context = f"""Ти - LLM1 (Interface Agent). Створи ФІНАЛЬНИЙ ЗВІТ українською мовою.

Початкова відповідь: "{initial_response}"

{results_context}

Створи короткий і зрозумілий звіт для користувача українською мовою про те, що було виконано."""

        final_response = await self.agents["interface"].generate_response(
            "Створи фінальний звіт про виконання завдання",
            llm1_final_context
        )
        
        cleaned_final = self._clean_response(final_response)
        logger.info(f"🔵 [LLM1] Final report: {cleaned_final}")
        
        return cleaned_final
    
    async def execute_action(self, action: str) -> str:
        """Execute predefined actions"""
        try:
            if action == "system_info":
                info = await self.macos_automation.get_system_info()
                return f"System Information:\n{json.dumps(info, indent=2)}"
            
            elif action == "open_app":
                success = await self.macos_automation.manage_applications("open", "Safari")
                return "Safari opened successfully" if success else "Failed to open Safari"
            
            elif action == "monitor_system":
                monitor_context = "You are LLM3, the monitoring agent. Analyze current system status and report any issues."
                response = await self.agents["monitor"].generate_response("Analyze current system status", monitor_context)
                return f"System Monitor Report:\n{response}"
            
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            return f"Error executing action: {str(e)}"
    
    async def execute_orchestrated_task(self, task_description: str):
        """Execute tasks orchestrated by LLM2 using gpt-oss:latest model"""
        logger.info(f"LLM2 orchestrating task: {task_description}")
        
        # Add to log buffer for LLM1 monitoring
        self.add_log_entry("INFO", f"Starting task orchestration: {task_description}", "atlas-orchestrator")
        
        try:
            # Use LLM2 to create detailed execution plan
            orchestration_prompt = f"""You are LLM2, a task orchestrator. Create a detailed execution plan for: "{task_description}"
            
Return a JSON plan with steps using available MCP tools. Each step should have:
- service: "macos-automator" | "automation" | "tts" | "playwright"  
- tool: specific tool name from the service
- params: parameters for the tool

Available MCP tools:
- macos-automator: app_control, applescript, shortcuts, window_control
- automation: read_file, write_file, execute_command, http_request, system_info
- playwright: open_page, goto, click, fill, eval, screenshot, get_title, close
- tts: speak

Example format:
{{"steps": [
  {{"service": "macos-automator", "tool": "app_control", "params": {{"action": "open", "app_name": "Safari"}}}},
  {{"service": "playwright", "tool": "open_page", "params": {{"url": "https://example.com"}}}}
]}}

Task: {task_description}"""

            # Get execution plan from LLM2
            execution_plan_text = await self.agents["orchestrator"].generate_response(
                orchestration_prompt, 
                "You are LLM2. Return ONLY valid JSON execution plan."
            )
            
            logger.info(f"LLM2 execution plan: {execution_plan_text}")
            
            # Parse and execute the plan
            execution_results = []
            try:
                # Extract JSON from response
                json_start = execution_plan_text.find('{')
                json_end = execution_plan_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = execution_plan_text[json_start:json_end]
                    execution_plan = json.loads(json_text)
                    
                    logger.info(f"Parsed execution plan: {execution_plan}")
                    
                    # Add to log buffer for LLM1 monitoring
                    steps_count = len(execution_plan.get("steps", []))
                    self.add_log_entry("INFO", f"LLM2 created execution plan with {steps_count} steps", "atlas-orchestrator")
                    
                    # Execute each step in the plan
                    for i, step in enumerate(execution_plan.get("steps", [])):
                        step_result = await self.execute_mcp_step(step, i+1)
                        execution_results.append(step_result)
                        
                else:
                    logger.warning("Could not extract JSON from LLM2 response, attempting direct execution")
                    # Fallback: try to execute based on keywords
                    fallback_result = await self.execute_fallback_task(task_description)
                    execution_results.append(fallback_result)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM2 execution plan: {e}")
                # Fallback execution
                fallback_result = await self.execute_fallback_task(task_description)
                execution_results.append(fallback_result)
            
            return execution_results
            
        except Exception as e:
            logger.error(f"Error in task orchestration: {e}")
            return [{"success": False, "error": str(e)}]
    
    def add_log_entry(self, level: str, message: str, source: str = "atlas-core"):
        """Add log entry to buffer for LLM1 analysis"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "source": source, 
            "message": message
        }
        
        self.log_buffer.append(log_entry)
        
        # Keep buffer size manageable
        if len(self.log_buffer) > self.max_log_buffer_size:
            self.log_buffer = self.log_buffer[-self.max_log_buffer_size:]
    
    async def start_log_monitoring(self):
        """Start LLM1 log monitoring and feedback system"""
        if self.log_monitor_task is not None:
            return
            
        logger.info("🔍 Starting LLM1 log monitoring and feedback system")
        self.log_monitor_task = asyncio.create_task(self._log_monitoring_loop())
    
    async def stop_log_monitoring(self):
        """Stop log monitoring"""
        if self.log_monitor_task:
            self.log_monitor_task.cancel()
            try:
                await self.log_monitor_task
            except asyncio.CancelledError:
                pass
            self.log_monitor_task = None
    
    async def _log_monitoring_loop(self):
        """Main loop for LLM1 log monitoring and feedback"""
        try:
            while self.monitoring_enabled:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                # Check if enough time has passed since last feedback
                time_since_feedback = datetime.now() - self.last_feedback_time
                if time_since_feedback.total_seconds() < 15:  # Minimum 15 seconds between feedback
                    continue
                
                # Get recent logs for analysis
                recent_logs = self.log_buffer[-20:] if self.log_buffer else []
                if not recent_logs:
                    continue
                
                # Check MCP service status
                mcp_status = await self.check_mcp_status()
                
                # Analyze logs and system status with LLM1
                await self._analyze_and_provide_feedback(recent_logs, mcp_status)
                
        except asyncio.CancelledError:
            logger.info("Log monitoring stopped")
        except Exception as e:
            logger.error(f"Error in log monitoring loop: {e}")
    
    async def _analyze_and_provide_feedback(self, recent_logs: List[Dict], mcp_status: Dict[str, bool]):
        """Analyze logs and provide verbal feedback through LLM1"""
        try:
            # Create analysis prompt for LLM1
            logs_text = "\n".join([
                f"[{log['timestamp']}] [{log['level']}] [{log['source']}] {log['message']}"
                for log in recent_logs[-10:]  # Last 10 logs
            ])
            
            online_services = [name for name, status in mcp_status.items() if status]
            offline_services = [name for name, status in mcp_status.items() if not status]
            
            analysis_prompt = f"""Ти LLM1 - інтерфейсний агент Atlas системи. Твоє завдання - аналізувати логи та надавати короткі голосові коментарі українською мовою про стан системи.

Поточні логи системи:
{logs_text}

Статус MCP сервісів:
- Онлайн: {', '.join(online_services) if online_services else 'Немає'}
- Офлайн: {', '.join(offline_services) if offline_services else 'Немає'}

Дай короткий (1-2 речення) голосовий коментар про:
1. Що відбувається в системі зараз
2. Чи є проблеми що потребують уваги
3. Загальний стан виконання завдань

Відповідай ТІЛЬКИ українською мовою, коротко і зрозуміло."""

            # Get analysis from LLM1
            if "interface" in self.agents:
                feedback = await self.agents["interface"].generate_response(
                    analysis_prompt,
                    "Ти LLM1. Аналізуй логи і давай короткі голосові коментарі українською мовою."
                )
                
                # Provide verbal feedback via TTS
                await self._provide_verbal_feedback(feedback)
                
                self.last_feedback_time = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in log analysis: {e}")
    
    async def _provide_verbal_feedback(self, feedback_text: str):
        """Provide verbal feedback using TTS service"""
        try:
            if 'tts' not in self.mcp_endpoints:
                logger.warning("TTS service not available for feedback")
                return
            
            # Clean up the feedback text
            cleaned_feedback = self._clean_response(feedback_text)
            
            # Make TTS request
            endpoint = self.mcp_endpoints['tts']['base_url']
            mcp_payload = {
                "tool": "speak",
                "parameters": {
                    "text": cleaned_feedback,
                    "provider": "ukrainian_tts"
                }
            }
            
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(f"{endpoint}/execute", json=mcp_payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"🔊 LLM1 feedback: {cleaned_feedback}")
                        # Also add to log buffer for monitoring
                        self.add_log_entry("INFO", f"LLM1 feedback: {cleaned_feedback}", "atlas-llm1")
                    else:
                        logger.warning(f"TTS feedback failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error providing verbal feedback: {e}")
    
    async def execute_mcp_step(self, step: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Execute a single step from the LLM2 execution plan"""
        try:
            service = step.get("service", "")
            tool = step.get("tool", "")
            params = step.get("params", {})
            
            logger.info(f"Executing step {step_number}: {service}.{tool} with params {params}")
            
            # Get the MCP endpoint for this service
            if service not in self.mcp_endpoints:
                logger.error(f"MCP service '{service}' not configured")
                return {
                    "step": step_number,
                    "service": service,
                    "tool": tool,
                    "success": False,
                    "error": f"Service {service} not available"
                }
            
            endpoint = self.mcp_endpoints[service]["base_url"]
            execute_url = f"{endpoint}/execute"
            
            # Prepare MCP request payload in the correct format
            mcp_payload = {
                "tool": tool,
                "parameters": params
            }
            
            # Prepare headers with proper Accept headers for different services
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Special handling for Playwright service which may need event-stream support
            if service == "playwright":
                headers["Accept"] = "application/json, text/event-stream"
            
            # Execute the MCP tool
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.post(execute_url, json=mcp_payload, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Step {step_number} completed successfully")
                            
                            # Add to log buffer for LLM1 monitoring
                            self.add_log_entry("INFO", f"Step {step_number}: {service}.{tool} completed successfully", "atlas-executor")
                            
                            return {
                                "step": step_number,
                                "service": service,
                                "tool": tool,
                                "success": True,
                                "result": result,
                                "description": f"Successfully executed {service}.{tool}"
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"Step {step_number} failed: HTTP {response.status} - {error_text}")
                            
                            # Add to log buffer for LLM1 monitoring
                            self.add_log_entry("ERROR", f"Step {step_number}: {service}.{tool} failed - HTTP {response.status}: {error_text}", "atlas-executor")
                            
                            return {
                                "step": step_number,
                                "service": service,
                                "tool": tool,
                                "success": False,
                                "error": f"HTTP {response.status}: {error_text}"
                            }
                            
                except asyncio.TimeoutError:
                    logger.error(f"Step {step_number} timed out")
                    return {
                        "step": step_number,
                        "service": service,
                        "tool": tool,
                        "success": False,
                        "error": "Request timed out"
                    }
                    
        except Exception as e:
            logger.error(f"Error executing step {step_number}: {e}")
            return {
                "step": step_number,
                "success": False,
                "error": str(e)
            }
    
    async def execute_fallback_task(self, task_description: str) -> Dict[str, Any]:
        """Execute task using simple keyword matching when JSON parsing fails"""
        logger.info(f"Executing fallback task: {task_description}")
        
        task_lower = task_description.lower()
        
        try:
            if any(word in task_lower for word in ['safari', 'сафар', 'browser', 'браузер']):
                if 'macos-automator' in self.mcp_endpoints:
                    endpoint = self.mcp_endpoints['macos-automator']['base_url']
                    headers = {"Content-Type": "application/json", "Accept": "application/json"}
                    mcp_payload = {
                        "tool": "app_control",
                        "parameters": {"action": "open", "app_name": "Safari"}
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f"{endpoint}/execute", 
                                                json=mcp_payload, headers=headers) as response:
                            if response.status == 200:
                                return {
                                    "success": True,
                                    "description": "Opened Safari browser",
                                    "fallback": True
                                }
            
            return {
                "success": False,
                "error": "Could not determine appropriate action",
                "fallback": True
            }
            
        except Exception as e:
            logger.error(f"Fallback execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": True
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        # Check MCP status based on mode
        if self.mcp_proxy_mode:
            mcp_proxy_status = await self.check_mcp_proxy_status()
            mcp_info = {
                "mode": "proxy",
                "proxy_url": self.mcp_proxy_url,
                "proxy_status": mcp_proxy_status,
                "tools": self.get_available_mcp_tools()
            }
        else:
            mcp_status = await self.check_mcp_status()
            mcp_info = {
                "mode": "direct",
                "configured": list(self.mcp_endpoints.keys()),
                "endpoints": {k: v.get("base_url") for k, v in self.mcp_endpoints.items()},
                "online": mcp_status,
                "count_online": sum(1 for v in mcp_status.values() if v),
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "agents_online": len(self.agents),
            "task_queue_size": self.task_queue.qsize(),
            "automation_ready": True,
            "mcp": mcp_info
        }

    def load_mcp_config(self) -> None:
        """Load MCP servers configuration.
        In proxy mode (ATLAS_MCP_PROXY_MODE=true): Use single proxy endpoint
        In direct mode: Use individual server endpoints
        """
        # If proxy mode is enabled, use proxy for all MCP calls
        if self.mcp_proxy_mode:
            logger.info(f"🔗 MCP Proxy mode enabled - using {self.mcp_proxy_url}")
            # In proxy mode, we don't need individual endpoints
            # All calls go through call_mcp_tool_via_proxy()
            self.mcp_endpoints = {
                "proxy": {
                    "base_url": self.mcp_proxy_url,
                    "health_url": f"{self.mcp_proxy_url}/tts/sse"  # Use working endpoint for health check
                }
            }
            return

        # Direct mode: Load individual server endpoints
        servers_str = os.getenv("ATLAS_MCP_SERVERS", "").strip()
        if not servers_str:
            self.mcp_endpoints = {}
            return
        names = [s.strip() for s in servers_str.split(",") if s.strip()]
        endpoints: Dict[str, Dict[str, str]] = {}
        for name in names:
            upper = name.upper().replace("-", "_")
            # Specific shorthands
            if name == "tts":
                base = os.getenv("ATLAS_MCP_TTS_URL")
            elif name == "playwright":
                base = os.getenv("ATLAS_MCP_PLAYWRIGHT_URL")
            else:
                base = None
            # Generic override
            base = os.getenv(f"ATLAS_MCP_{upper}_URL", base)
            # Defaults by name
            if not base:
                if name == "automation":
                    base = "http://mcp-automation:4002"
                elif name in ("macos-automator", "macos_automator"):
                    base = "http://mcp-automator:4003"
                elif name == "tts":
                    base = "http://mcp-tts:4004"
                elif name == "playwright":
                    base = "http://mcp-playwright:4005/mcp"
                elif name in ("task-orchestrator", "task_orchestrator", "orchestrator"):
                    base = "http://localhost:4006"
                else:
                    # Unknown - skip
                    continue
            # Determine health URL
            health_url = base if base.endswith("/mcp") else base.rstrip("/") + "/health"
            endpoints[name] = {"base_url": base, "health_url": health_url}
        self.mcp_endpoints = endpoints

    async def check_mcp_status(self) -> Dict[str, bool]:
        """Check MCP endpoints quickly; playwright (/mcp) treats 200/400 as up."""
        result: Dict[str, bool] = {}
        if not self.mcp_endpoints:
            return result
        timeout = aiohttp.ClientTimeout(total=2)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = []
            names = list(self.mcp_endpoints.keys())
            for name in names:
                url = self.mcp_endpoints[name]["health_url"]
                tasks.append(self._probe(session, name, url))
            probe_results = await asyncio.gather(*tasks, return_exceptions=True)
            for item in probe_results:
                # Ignore exceptions; just treat as down
                if isinstance(item, BaseException):
                    continue
                # Expect (name, bool)
                if isinstance(item, tuple) and len(item) == 2:
                    name, ok = item
                    result[name] = bool(ok)
        return result

    async def _probe(self, session: aiohttp.ClientSession, name: str, url: str):
        try:
            async with session.get(url) as resp:
                if url.endswith("/mcp"):
                    return name, (resp.status in (200, 400))
                return name, (resp.status == 200)
        except Exception:
            return name, False

    async def load_mcp_config_proxy_mode(self):
        """Load MCP configuration in proxy mode - parse clients and discover tools (Variant B)"""
        proxy_url = self.mcp_proxy_url.rstrip('/')
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                test_url = f"{proxy_url}/"
                async with session.get(test_url) as resp:
                    if resp.status not in [200, 404, 405, 500]:
                        logger.error(f"MCP Proxy не доступний (HTTP {resp.status})")
                        return False
                    logger.info(f"🔗 MCP Proxy доступний: {proxy_url} (HTTP {resp.status})")
                
                # Парсинг списку клієнтів з env
                raw_items = [c.strip() for c in self.mcp_proxy_clients_raw.split(',') if c.strip()]
                if not raw_items:
                    logger.warning("Не задано клієнтів в ATLAS_MCP_PROXY_CLIENTS")
                    return False
                
                for item in raw_items:
                    if ':' in item:
                        name, ctype = item.split(':', 1)
                        ctype = ctype.strip().lower()
                    else:
                        name, ctype = item, 'sse'
                    name = name.strip()
                    if not name:
                        continue
                    
                    if ctype not in ('sse', 'streamable-http', 'stdio'):
                        logger.warning(f"Невідомий тип клієнта '{ctype}' для {name}, використовую sse")
                        ctype = 'sse'
                    
                    # stdio через проксі експонується як sse
                    eff_type = 'sse' if ctype == 'stdio' else ctype
                    if eff_type == 'sse':
                        health_url = f"{proxy_url}/{name}/sse"
                        execute_base = f"{proxy_url}/{name}"
                    else:  # streamable-http
                        health_url = f"{proxy_url}/{name}/mcp"
                        execute_base = f"{proxy_url}/{name}/mcp"
                    
                    self.mcp_proxy_clients[name] = {
                        'type': eff_type,
                        'declared_type': ctype,
                        'health_url': health_url,
                        'execute_base': execute_base
                    }
                
                # Спроба автовизначення доступних інструментів
                discovered = {}
                for svc, meta in self.mcp_proxy_clients.items():
                    tools_candidates = [
                        f"{meta['execute_base']}/tools",
                        f"{proxy_url}/{svc}/tools"
                    ]
                    for candidate in tools_candidates:
                        try:
                            async with session.get(candidate) as t_resp:
                                if t_resp.status == 200:
                                    data = await t_resp.json()
                                    tools = []
                                    if isinstance(data, dict) and 'tools' in data:
                                        tools = [t.get('name', t.get('id', str(t))) for t in data['tools'] if isinstance(t, dict)]
                                    elif isinstance(data, list):
                                        tools = [t.get('name', t.get('id', str(t))) if isinstance(t, dict) else str(t) for t in data]
                                    if tools:
                                        discovered[svc] = tools
                                        logger.info(f"� Знайдено {len(tools)} інструментів для {svc}: {tools[:3]}{'...' if len(tools)>3 else ''}")
                                        break
                        except Exception:
                            continue
                
                # Fallback для відомих сервісів
                if not discovered:
                    logger.warning("Автовизначення інструментів не вдалося, використовую статичний набір")
                    discovered = {
                        "tts": ["say_tts"],
                        "automation": ["mouseClick", "mouseMove", "screenshot", "type"],
                        "playwright": ["browser_navigate", "browser_click", "browser_type"],
                        "task-orchestrator": ["call_tool"]
                    }
                
                self.mcp_tools_cache = discovered
                logger.info(f"📦 Загалом proxy інструментів: {sum(len(v) for v in self.mcp_tools_cache.values())}")
                return True
                
        except Exception as e:
            logger.error(f"Помилка ініціалізації MCP proxy: {e}")
            return False

    async def call_mcp_tool_via_proxy(self, tool_name: str, args: dict):
        """Call MCP tool through proxy with error handling and logging"""
        if not hasattr(self, 'mcp_proxy_url'):
            raise Exception("MCP Proxy not initialized")
        
        # Use direct Ukrainian TTS for TTS calls
        if tool_name == "say_tts":
            text = args.get("text", "")
            voice = args.get("voice", "mykyta") 
            rate = args.get("rate", 200)  # Default rate 
            
            try:
                # Спробувати прямий виклик українського TTS
                logger.info(f"🎙️ Using Ukrainian TTS for: {text[:50]}...")
                
                # Перевірка наявності необхідних модулів
                if not UKRAINIAN_TTS_AVAILABLE:
                    logger.warning("Ukrainian TTS not available, falling back to system TTS")
                    await self.call_mcp_tool_via_proxy("say_tts", {"text": text, "rate": rate})
                    return {"success": True, "message": "Used fallback TTS"}
                
                if not PYGAME_AVAILABLE:
                    logger.warning("Pygame not available, falling back to system TTS")
                    await self.call_mcp_tool_via_proxy("say_tts", {"text": text, "rate": rate})
                    return {"success": True, "message": "Used fallback TTS"}
                
                # Import локально з перевіркою
                import tempfile
                
                # Ініціалізація TTS
                tts = TTS(device='cpu')  # type: ignore
                
                # Генерація аудіо
                temp_path = tempfile.mktemp(suffix='.wav')
                with open(temp_path, 'wb') as output_file:
                    tts.tts(text, voice, "dictionary", output_file)  # type: ignore
                
                # Відтворення через pygame
                pygame.mixer.init()  # type: ignore
                pygame.mixer.music.load(temp_path)  # type: ignore
                pygame.mixer.music.play()  # type: ignore
                
                # Чекаємо закінчення
                while pygame.mixer.music.get_busy():  # type: ignore
                    await asyncio.sleep(0.1)
                
                # Очищення
                import os
                os.unlink(temp_path)
                
                logger.info(f"✅ Ukrainian TTS completed for: {text[:50]}...")
                return {"status": "success", "message": f"Ukrainian TTS: {text}"}
                
            except Exception as e:
                logger.warning(f"⚠️ Ukrainian TTS failed: {e}, falling back to macOS say")
                
                # Fallback на macOS say
                process = await asyncio.create_subprocess_exec(
                    'say', '-r', str(args.get("rate", 200)), text,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"Fallback TTS: Successfully spoke text: {text[:50]}...")
                    return {"status": "success", "message": f"Fallback TTS: {text}"}
                else:
                    logger.error(f"All TTS methods failed: {stderr.decode()}")
                    return {"status": "error", "message": stderr.decode()}
        
        # For other tools, return placeholder
        logger.warning(f"MCP Tool '{tool_name}' not yet implemented via proxy")
        return {"status": "pending", "message": f"Tool {tool_name} via proxy not yet implemented"}

    def get_available_mcp_tools(self):
        """Get list of available MCP tools grouped by namespace"""
        if hasattr(self, 'mcp_tools_cache'):
            return self.mcp_tools_cache
        return {}

    async def check_mcp_proxy_status(self):
        """Check MCP proxy health and return status"""
        if not self.mcp_proxy_mode:
            return {"status": "disabled", "mode": "direct"}
        
        try:
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test TTS SSE endpoint
                test_url = f"{self.mcp_proxy_url}/tts/sse"
                async with session.get(test_url) as resp:
                    if resp.status == 200:
                        tools_count = sum(len(tools) for tools in self.mcp_tools_cache.values())
                        return {
                            "status": "online",
                            "mode": "proxy", 
                            "url": self.mcp_proxy_url,
                            "tools_count": tools_count,
                            "namespaces": list(self.mcp_tools_cache.keys())
                        }
                    else:
                        return {"status": "error", "mode": "proxy", "http_status": resp.status}
        except Exception as e:
            return {"status": "offline", "mode": "proxy", "error": str(e)}

    async def initialize_mcp(self):
        """Initialize MCP system (proxy or direct mode)"""
        if self.mcp_proxy_mode:
            success = await self.load_mcp_config_proxy_mode()
            if not success:
                logger.warning("Failed to initialize MCP proxy, falling back to direct mode")
                self.mcp_proxy_mode = False
                self.load_mcp_config()
        else:
            self.load_mcp_config()
    
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        logger.info("Starting system monitoring...")
        
        while True:
            try:
                # LLM3 monitors system periodically
                monitor_context = "You are LLM3, continuously monitoring system health. Report any anomalies."
                await self.agents["monitor"].generate_response("Check system status", monitor_context)
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the Atlas system"""
        logger.info("Starting Atlas Autonomous System...")
        
        # Initialize MCP system (proxy or direct mode)
        await self.initialize_mcp()
        
        # Start LLM1 log monitoring and feedback
        await self.start_log_monitoring()
        
        # Start background monitoring
        monitoring_task = asyncio.create_task(self.start_monitoring())
        
        # Start web server
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        try:
            await server.serve()
        finally:
            monitoring_task.cancel()
    
    # ======= ДОПОМІЖНІ МЕТОДИ ДЛЯ НОВОЇ АРХІТЕКТУРИ =======
    
    async def security_check_llm3(self, task: str) -> Dict[str, Any]:
        """🔴 LLM3 - перевірка безпеки завдання"""
        logger.info(f"🔴 [LLM3] Security check for: {task}")
        
        try:
            llm3_context = """You are LLM3 (Monitor Agent) - security and safety monitor.
Analyze the task for potential security risks. 

REJECT if task involves:
- System damage or deletion
- Unauthorized access
- Malicious activities
- Privacy violations
- Network attacks

APPROVE safe automation tasks like:
- Opening applications
- File management
- Web browsing
- System information

Return JSON: {"approved": true/false, "reason": "explanation"}"""

            response = await self.agents["monitor"].generate_response(task, llm3_context)
            
            # Спроба парсингу JSON
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(response[json_start:json_end])
                    return result
            except:
                pass
            
            # Fallback: аналіз за ключовими словами
            dangerous_keywords = ['delete', 'remove', 'format', 'erase', 'destroy', 'hack', 'crack']
            is_dangerous = any(word in task.lower() for word in dangerous_keywords)
            
            return {
                "approved": not is_dangerous,
                "reason": "Blocked dangerous keywords" if is_dangerous else "Task approved"
            }
            
        except Exception as e:
            logger.error(f"🔴 [LLM3] Security check error: {e}")
            return {"approved": False, "reason": f"Security check failed: {str(e)}"}
    
    async def llm1_progress_report(self, progress: str):
        """🔵 LLM1 звітує про прогрес"""
        logger.info(f"🔵 [LLM1] Progress: {progress}")
        # Тут можна додати відправку прогресу до frontend через websockets
    
    async def call_task_orchestrator_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the task orchestrator MCP server"""
        try:
            # Check if task orchestrator is configured
            if "task-orchestrator" not in self.mcp_endpoints and "orchestrator" not in self.mcp_endpoints:
                logger.error("Task orchestrator not configured in MCP endpoints")
                return {"success": False, "error": "Task orchestrator not available"}
            
            # Get the endpoint
            endpoint_name = "task-orchestrator" if "task-orchestrator" in self.mcp_endpoints else "orchestrator"
            endpoint = self.mcp_endpoints[endpoint_name]["base_url"]
            
            # Prepare the request
            url = f"{endpoint}/call_tool"
            payload = {
                "tool_name": tool_name,
                "parameters": parameters
            }
            
            logger.info(f"🟠 [Task Orchestrator] Calling {tool_name} at {url}")
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"🟠 [Task Orchestrator] Tool {tool_name} success: {result}")
                        return {"success": True, **result}
                    else:
                        error_text = await response.text()
                        logger.error(f"🟠 [Task Orchestrator] Tool {tool_name} failed: {response.status} {error_text}")
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"🟠 [Task Orchestrator] Tool {tool_name} exception: {e}")
            return {"success": False, "error": str(e)}

    async def execute_mcp_step_via_proxy(self, step: Dict, step_number: int) -> Dict[str, Any]:
        """Виконання кроку через MCP Proxy"""
        logger.info(f"🔧 [PROXY] Step {step_number}: {step}")
        
        try:
            service = step.get("service", "")
            tool = step.get("tool", "")
            params = step.get("params", {})
            
            # Спеціальна обробка для різних типів інструментів
            if service == "applescript" and tool == "run_applescript":
                # AppleScript через MCP Proxy
                script = params.get("script", "")
                if "safari" in script.lower():
                    # Прямий виклик AppleScript для Safari
                    result = await self.macos_automation.execute_applescript(script)
                    return {
                        "success": True,
                        "description": f"Executed AppleScript: {script[:50]}...",
                        "result": result
                    }
            
            elif service == "automation" and tool == "systemCommand":
                # Команди системи
                command = params.get("command", "")
                if command:
                    # Виконання через subprocess
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    return {
                        "success": process.returncode == 0,
                        "description": f"Executed command: {command}",
                        "result": stdout.decode() if stdout else stderr.decode()
                    }
            
            # Загальний виклик через HTTP до MCP Proxy
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.mcp_proxy_url}/{service}/{tool}"
                async with session.post(url, json=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "description": f"Executed {service}/{tool}",
                            "result": result
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"🔧 [PROXY] Step {step_number} error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def llm2_error_recovery(self, failed_step: Dict, error: str) -> Optional[Dict]:
        """🟠 LLM2 намагається відновитися після помилки"""
        logger.info(f"🟠 [LLM2] Attempting error recovery for: {failed_step}")
        
        try:
            recovery_prompt = f"""The step failed: {failed_step}
Error: {error}

Suggest an alternative approach or simpler method to achieve the same goal.
Return JSON with alternative step format or null if no recovery possible."""

            recovery_response = await self.agents["orchestrator"].generate_response(
                f"Recover from error: {error}",
                recovery_prompt
            )
            
            # Парсинг альтернативного кроку
            try:
                json_start = recovery_response.find('{')
                json_end = recovery_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    alternative_step = json.loads(recovery_response[json_start:json_end])
                    return await self.execute_mcp_step_via_proxy(alternative_step, 0)
            except:
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"🟠 [LLM2] Recovery error: {e}")
            return None
    
    async def execute_simple_task(self, task: str) -> Dict[str, Any]:
        """Простий fallback для виконання основних завдань"""
        logger.info(f"🔄 [FALLBACK] Executing simple task: {task}")
        
        task_lower = task.lower()
        
        try:
            # Safari
            if any(word in task_lower for word in ['safari', 'browser', 'web']):
                success = await self.macos_automation.manage_applications("open", "Safari")
                return {
                    "success": success,
                    "description": "Opened Safari browser" if success else "Failed to open Safari"
                }
            
            # Finder
            elif any(word in task_lower for word in ['finder', 'files', 'folder']):
                success = await self.macos_automation.manage_applications("open", "Finder")
                return {
                    "success": success,
                    "description": "Opened Finder" if success else "Failed to open Finder"
                }
            
            # System Info
            elif any(word in task_lower for word in ['info', 'system', 'status']):
                info = await self.macos_automation.get_system_info()
                return {
                    "success": True,
                    "description": "Retrieved system information",
                    "result": info
                }
            
            else:
                return {
                    "success": False,
                    "error": "Task not recognized by fallback system"
                }
                
        except Exception as e:
            logger.error(f"🔄 [FALLBACK] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def main():
    """Main entry point"""
    print("🤖 Atlas Autonomous macOS Management System")
    print("==========================================")
    
    # Check if Ollama is available
    try:
        import ollama
        # Respect environment configuration for Ollama endpoint
        api_base = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        if api_base and not str(api_base).startswith("http"):
            api_base = f"http://{api_base}"
        client = ollama.Client(host=str(api_base))
        models_response = client.list()
        models_count = len(models_response.get('models', [])) if isinstance(models_response, dict) else 0
        print(f"✅ Ollama available with {models_count} models")
    except Exception as e:
        print(f"❌ Ollama not available: {e}")
        print("Please install Ollama and ensure it's running: https://ollama.ai")
        return
    
    # Initialize and run Atlas
    atlas = AtlasCore()
    
    try:
        asyncio.run(atlas.run())
    except KeyboardInterrupt:
        print("\n🛑 Atlas system stopped by user")
    except Exception as e:
        print(f"❌ Error starting Atlas: {e}")

if __name__ == "__main__":
    main()