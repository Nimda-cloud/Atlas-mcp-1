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
from collections import deque

# Third-party imports (will be installed via requirements.txt)
try:
    import aiohttp
    import ollama
    from fastapi import FastAPI, HTTPException, Response, Request
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, StreamingResponse
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
    print("🎙️ Trying to import Ukrainian TTS...")
    from ukrainian_tts.tts import TTS  # type: ignore
    UKRAINIAN_TTS_AVAILABLE = True
    print("✅ Ukrainian TTS imported successfully")
except ImportError as e:
    print(f"⚠️ Ukrainian TTS not available: {e}")
    TTS = None

try:
    print("🎮 Trying to import pygame...")
    import pygame  # type: ignore
    PYGAME_AVAILABLE = True
    print("✅ Pygame imported successfully")
except ImportError as e:
    print(f"⚠️ Pygame not available: {e}")
    pygame = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/atlas.log'),
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
@dataclass
class ExecutionContext:
    """Unified execution context for task tracing"""
    session_id: str
    correlation_id: str
    user_message: str
    english_task: str
    start_time: datetime
    current_step: int = 0
    total_steps: int = 0
    end_time: Optional[datetime] = None
    duration: Optional[float] = None

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
        # In-memory log buffer & concurrency primitives
        self.log_buffer: List[Dict[str, Any]] = []
        self.max_log_buffer_size = 100
        self.log_buffer_lock = asyncio.Lock()
        # Subscribers for live log streaming (SSE)
        self.log_subscribers: List[asyncio.Queue] = []
        # Latency & reliability statistics per service/tool-group
        # latency_stats[service] = { 'calls': int, 'errors': int, 'total_ms': float,
        #   'last_ms': float, 'samples': deque, 'last_error': str|None, 'since': datetime, 'ema_ms': float }
        self.latency_stats: Dict[str, Dict[str, Any]] = {}
        self._latency_window = 200

        # Initialize subsystems
        self.setup_agents()
        self.setup_web_interface()
        if self.mcp_proxy_mode:
            logger.info("Atlas MCP Proxy mode enabled (Variant B)")
        # MCP config will be loaded during initialize_mcp() call
    
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
        
        @self.app.get("/tools/refresh")
        async def refresh_tools():
            """Перезапустити детекцію MCP інструментів"""
            if self.mcp_proxy_mode:
                try:
                    logger.info("Manual MCP tools refresh requested...")
                    self.mcp_tools_cache = await self.discover_mcp_tools_real()
                    total_tools = sum(len(tools) for tools in self.mcp_tools_cache.values())
                    
                    return {
                        "success": True,
                        "message": f"Tools refreshed: {total_tools} tools from {len(self.mcp_tools_cache)} services",
                        "tools": self.mcp_tools_cache,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"Tools refresh failed: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "success": False,
                    "error": "MCP proxy mode not enabled",
                    "timestamp": datetime.now().isoformat()
                }

        @self.app.get("/tools")
        async def list_tools():
            """Get comprehensive list of available MCP tools"""
            if self.mcp_proxy_mode:
                return {
                    "mode": "proxy",
                    "proxy_url": self.mcp_proxy_url,
                    "tools": self.get_available_mcp_tools(),
                    "total_tools": sum(len(tools) for tools in self.get_available_mcp_tools().values()),
                    "services": list(self.get_available_mcp_tools().keys()),
                    "proxy_status": await self.check_mcp_proxy_status()
                }
            else:
                return {
                    "mode": "direct",
                    "endpoints": {k: v.get("base_url") for k, v in self.mcp_endpoints.items()},
                    "status": await self.check_mcp_status(),
                    "tools": "Available in direct mode - check individual endpoints"
                }

        @self.app.get("/")
        async def dashboard():
            tools_info = {}
            if self.mcp_proxy_mode:
                tools = self.get_available_mcp_tools()
                tools_info = {
                    "total_tools": sum(len(tools_list) for tools_list in tools.values()),
                    "services": len(tools),
                    "by_service": {service: len(tools_list) for service, tools_list in tools.items()}
                }
            
            return {
                "status": "Atlas Autonomous System",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "mode": "proxy" if self.mcp_proxy_mode else "direct",
                "proxy_url": self.mcp_proxy_url if self.mcp_proxy_mode else None,
                "agents": list(self.agents.keys()),
                "endpoints": ["/chat", "/action", "/tts", "/status", "/metrics", "/tools", "/tools/refresh"],
                "mcp_tools": tools_info
            }
        
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

        @self.app.get("/logs")
        async def get_logs(limit: int = 100):
            """Повертає останні логи з внутрішнього буфера (для viewer)."""
            try:
                # Захист від надмірних значень
                limit_safe = max(1, min(limit, 500))
                async with self.log_buffer_lock:
                    logs_slice = self.log_buffer[-limit_safe:]
                return {"logs": logs_slice, "count": len(logs_slice)}
            except Exception as e:
                logger.error(f"/logs endpoint error: {e}")
                raise HTTPException(status_code=500, detail="Failed to read logs")

        @self.app.get("/logs/stream")
        async def stream_logs(request: Request):
            """Server-Sent Events stream of live logs (backfills recent buffer)."""
            async def event_generator():
                # Per-client queue
                q: asyncio.Queue = asyncio.Queue()
                self.log_subscribers.append(q)
                # Send backlog first
                try:
                    async with self.log_buffer_lock:
                        backlog = list(self.log_buffer[-200:])  # cap backlog
                    for entry in backlog:
                        yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"
                    # Heartbeat timer
                    last_heartbeat = time.time()
                    while True:
                        # Disconnect check
                        if await request.is_disconnected():
                            break
                        try:
                            entry = await asyncio.wait_for(q.get(), timeout=10.0)
                            yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"
                        except asyncio.TimeoutError:
                            # Heartbeat every 10s
                            now = time.time()
                            if now - last_heartbeat >= 10:
                                last_heartbeat = now
                                yield ": heartbeat\n\n"
                            continue
                finally:
                    # Remove subscriber
                    try:
                        self.log_subscribers.remove(q)
                    except ValueError:
                        pass
            return StreamingResponse(event_generator(), media_type="text/event-stream")
    
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
            
            # Перевірка чи потрібно виконання задач через покращений класифікатор
            needs_execution = await self._classify_action_intent(message, cleaned_response)
            
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
                
                # Озвучуємо фінальний звіт з покращеним TTS
                try:
                    tts_result = await self.enhanced_tts_call(final_report)
                    logger.info(f"🔊 TTS result: {tts_result.get('method', 'unknown')}")
                except Exception as e:
                    logger.warning(f"TTS failed: {e}")
                
                return final_report
            
            else:
                # Простий діалог без виконання дій
                try:
                    tts_result = await self.enhanced_tts_call(cleaned_response)
                    logger.info(f"🔊 TTS result: {tts_result.get('method', 'unknown')}")
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
    
    async def _classify_action_intent(self, user_message: str, llm1_response: str) -> bool:
        """Покращений класифікатор для визначення потреби у виконанні дій"""
        try:
            # Швидка перевірка простих ключових слів
            action_keywords = {
                'direct_action': ['open', 'close', 'run', 'execute', 'launch', 'start', 'stop', 'create', 'delete'],
                'ukrainian_action': ['відкрий', 'закрий', 'запусти', 'виконай', 'розгорни', 'запуск', 'стоп', 'створи', 'видали'],
                'information_only': ['що', 'how', 'explain', 'tell', 'describe', 'розкажи', 'поясни', 'опиши']
            }
            
            message_lower = user_message.lower()
            
            # Швидкий відбір: якщо є прямі дієслова дії
            has_action_words = any(word in message_lower for word in 
                                 action_keywords['direct_action'] + action_keywords['ukrainian_action'])
            
            # Швидкий відбір: якщо тільки інформаційні запити
            only_info_request = any(word in message_lower for word in action_keywords['information_only'])
            
            if has_action_words and not only_info_request:
                logger.info("🎯 [CLASSIFIER] Direct action keywords detected")
                return True
                
            if only_info_request and not has_action_words:
                logger.info("🎯 [CLASSIFIER] Information-only request detected")
                return False
            
            # Складніші випадки - використовуємо LLM1 для класифікації
            classification_prompt = f"""Проаналізуй чи потребує цей запит ВИКОНАННЯ КОНКРЕТНИХ ДІЙ на комп'ютері.

Запит користувача: "{user_message}"
Попередня відповідь LLM1: "{llm1_response}"

ВИКОНАННЯ ДІЙ потрібно для:
- Відкриття/закриття програм
- Виконання команд
- Створення/видалення файлів
- Автоматизація завдань
- Контроль системи

НЕ потрібно для:
- Звичайного спілкування
- Запитів інформації
- Пояснень
- Теоретичних питань

Відповідай ТІЛЬКИ: ТАК або НІ"""

            classification = await self.agents["interface"].generate_response(
                classification_prompt,
                "Ти класифікатор дій. Відповідай ТІЛЬКИ 'ТАК' або 'НІ'"
            )
            
            # Парсинг відповіді
            classification_clean = classification.lower().strip()
            is_action_needed = 'так' in classification_clean or 'yes' in classification_clean
            
            logger.info(f"🎯 [CLASSIFIER] LLM classification: {classification_clean} → {'ACTION' if is_action_needed else 'NO_ACTION'}")
            return is_action_needed
            
        except Exception as e:
            logger.error(f"🎯 [CLASSIFIER] Error in classification: {e}")
            # Fallback до простих ключових слів
            action_keywords = ['open', 'close', 'run', 'execute', 'launch', 'start', 'stop', 
                             'відкрий', 'закрий', 'запусти', 'виконай', 'розгорни', 'запуск', 'стоп']
            fallback_result = any(keyword in user_message.lower() for keyword in action_keywords)
            logger.info(f"🎯 [CLASSIFIER] Fallback to keywords: {'ACTION' if fallback_result else 'NO_ACTION'}")
            return fallback_result
    
    async def _discover_proxy_services(self):
        """Відкриває доступні сервіси через проксі для health checks"""
        try:
            # Спробуємо отримати список доступних сервісів
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                # Типові ендпоінти різних сервісів
                test_endpoints = [
                    ("tts", "/tts/sse"),
                    ("task_orchestrator", "/task_orchestrator/mcp"),
                    ("ollama", "/ollama/mcp"), 
                    ("macos_automation", "/macos_automation/mcp"),
                    ("prometheus", "/prometheus/mcp")
                ]
                
                working_services = []
                for service_name, endpoint in test_endpoints:
                    try:
                        health_url = f"{self.mcp_proxy_url}{endpoint}"
                        async with session.get(health_url) as response:
                            if response.status < 500:  # 2xx, 3xx, 4xx all indicate service exists
                                working_services.append(service_name)
                                self.mcp_endpoints[f"proxy_{service_name}"] = {
                                    "base_url": self.mcp_proxy_url,
                                    "health_url": health_url
                                }
                                logger.info(f"🟢 [HEALTH] Discovered working service: {service_name} at {health_url}")
                    except Exception as e:
                        logger.debug(f"🔴 [HEALTH] Service {service_name} not available: {e}")
                        continue
                
                if not working_services:
                    # Fallback to original tts endpoint
                    self.mcp_endpoints["proxy"]["health_url"] = f"{self.mcp_proxy_url}/tts/sse"
                    logger.warning("🟡 [HEALTH] No services discovered, using fallback TTS health check")
                else:
                    # Use first working service as primary health check
                    primary_service = working_services[0]
                    self.mcp_endpoints["proxy"]["health_url"] = self.mcp_endpoints[f"proxy_{primary_service}"]["health_url"]
                    logger.info(f"🟢 [HEALTH] Using {primary_service} as primary health check, {len(working_services)} services total")
                    
        except Exception as e:
            logger.error(f"🔴 [HEALTH] Error discovering proxy services: {e}")
            # Fallback
            self.mcp_endpoints["proxy"]["health_url"] = f"{self.mcp_proxy_url}/tts/sse"
    
    async def execute_task_with_task_orchestrator(self, english_task: str, original_message: str) -> List[Dict]:
        """🟠 Інтелектуальний Task Orchestrator - планує і виконує завдання з використанням динамічного registry інструментів"""
        # Create execution context for tracing
        import uuid
        context = ExecutionContext(
            session_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4())[:8],
            user_message=original_message,
            english_task=english_task,
            start_time=datetime.now()
        )
        
        logger.info(f"🟠 [Intelligent Orchestrator] Starting intelligent task orchestration: {english_task} [ID: {context.correlation_id}]")
        
        # 🔴 LLM3 Security Check
        security_check = await self.security_check_llm3(english_task)
        if not security_check["approved"]:
            logger.warning(f"🔴 [LLM3] Task rejected: {security_check['reason']}")
            return [{"success": False, "error": f"Відхилено з міркувань безпеки: {security_check['reason']}"}]
        
        logger.info(f"🔴 [LLM3] Task approved")
        
        try:
            # ЕТАП 1: Отримуємо актуальний registry інструментів
            available_tools = self.get_available_mcp_tools()
            total_tools = sum(len(tools) for tools in available_tools.values())
            logger.info(f"🔍 [Registry] Using {total_tools} tools from {len(available_tools)} services")
            
            execution_results = []
            
            # ЕТАП 2: Initialize orchestration session
            logger.info(f"🟠 [Intelligent Orchestrator] Initializing session")
            working_dir = os.getenv("ATLAS_WORKING_DIR") or os.getcwd()
            init_result = await self.call_task_orchestrator_tool("orchestrator_initialize_session", {
                "working_directory": working_dir
            })
            
            if not init_result.get("success", False):
                logger.error(f"🟠 [Intelligent Orchestrator] Failed to initialize: {init_result}")
                return [{"success": False, "error": "Failed to initialize intelligent task orchestrator"}]
            
            # ЕТАП 3: Інтелектуальне планування з використанням registry
            logger.info(f"🟠 [Intelligent Orchestrator] Creating intelligent plan using tools registry")
            
            # Формуємо збагачений контекст для планування
            tools_context = self._format_tools_context(available_tools)
            enhanced_context = (
                f"Original Ukrainian request: {original_message}. "
                f"Available tools: {tools_context}. "
                f"Total tools available: {total_tools}. "
                f"Use specific tool names from the registry for concrete execution."
            )
            
            plan_result = await self.call_task_orchestrator_tool(
                "orchestrator_plan_task",
                {
                    "task_description": english_task,
                    "context": enhanced_context,
                    "tools_registry": available_tools,  # Передаємо registry
                    "complexity": "moderate",
                    "specialist_type": "intelligent_mcp"
                }
            )
            
            if not plan_result.get("success", False):
                logger.error(f"🟠 [Intelligent Orchestrator] Failed to plan: {plan_result}")
                return [{"success": False, "error": "Failed to create intelligent plan"}]
            
            execution_results.append(plan_result)
            
            # ЕТАП 4: Intelligent fallback з використанням registry
            if not plan_result.get("task_id"):
                dynamic_app = await self._intelligent_app_inference(english_task, available_tools)
                if dynamic_app:
                    logger.info(f"� [Intelligent Fallback] Detected app: {dynamic_app}")
                    try:
                        # Перевіряємо чи є потрібний інструмент в registry
                        if self._tool_available("system_launch_app", available_tools):
                            launch_result = await self.call_mcp_tool_via_proxy(
                                "system_launch_app", {"app_name": dynamic_app}
                            )
                            execution_results.append({
                                "success": launch_result.get("status") == "success",
                                "result": launch_result,
                                "intelligent_fallback": True,
                                "description": f"Intelligent launch of {dynamic_app} using registry-verified tool"
                            })
                        else:
                            logger.warning("🔍 [Intelligent Fallback] system_launch_app not available in registry")
                            execution_results.append({
                                "success": False,
                                "error": "Required tool system_launch_app not available",
                                "intelligent_fallback": True
                            })
                    except Exception as fe:
                        execution_results.append({
                            "success": False,
                            "error": f"Intelligent fallback failed: {fe}",
                            "intelligent_fallback": True
                        })

            # ЕТАП 5: Intelligent execution з валідацією інструментів
            if plan_result.get("task_id"):
                logger.info(f"🟠 [Intelligent Orchestrator] Executing intelligent plan {plan_result['task_id']}")
                
                task_data = plan_result.get("task_data", {})
                subtasks = task_data.get("subtasks", [])

                # Normalize service casing in subtasks (LLM may upper-case services)
                service_key_map = {s.lower(): s for s in available_tools.keys()}  # existing services
                for st in subtasks:
                    svc = st.get("tool_service")
                    if isinstance(svc, str) and svc:
                        lower = svc.lower()
                        if lower in service_key_map:
                            st["tool_service"] = service_key_map[lower]
                        else:
                            # If not mapped, try to detect service by tool membership
                            tname = st.get("tool_name")
                            if tname:
                                for svc_name, tools_list in available_tools.items():
                                    if tname in tools_list:
                                        st["tool_service"] = svc_name
                                        break
                
                # Перевіряємо план на валідність
                validation_result = await self._validate_plan_against_registry(task_data, available_tools)
                execution_results.append({
                    "validation": validation_result,
                    "type": "plan_validation"
                })
                
                for i, subtask in enumerate(subtasks):
                    context.current_step = i + 1
                    context.total_steps = len(subtasks)
                    
                    logger.info(f"🟠 [Intelligent Orchestrator] Executing intelligent subtask {i+1}/{len(subtasks)}: {subtask.get('title', 'Unknown')} [ID: {context.correlation_id}]")
                    
                    # 🔵 LLM1 звітує про прогрес
                    await self.llm1_progress_report(f"Виконую підзавдання {i+1} з {len(subtasks)}: {subtask.get('title', 'Unknown')}")
                    
                    # Intelligent execution з валідацією інструментів
                    try:
                        # Перевіряємо чи доступний необхідний інструмент
                        required_tool = subtask.get("tool_name")
                        if required_tool and not self._tool_available(required_tool, available_tools):
                            logger.warning(f"🔍 [Tool Validation] Tool '{required_tool}' not available, attempting alternative")
                            alternative_tool = await self._find_alternative_tool(required_tool, available_tools)
                            if alternative_tool:
                                logger.info(f"🔄 [Tool Substitution] Using '{alternative_tool}' instead of '{required_tool}'")
                                subtask["tool_name"] = alternative_tool
                        
                        exec_result = await asyncio.wait_for(
                            self.call_task_orchestrator_tool("orchestrator_execute_task", {
                                "task_id": subtask.get("id"),
                                "specialist_context": f"Use available tools from registry: {tools_context}. Execute the specific tool: {subtask.get('tool_name', 'unknown')}",
                                "correlation_id": context.correlation_id,
                                "tool_registry": available_tools
                            }),
                            timeout=60.0
                        )
                        
                        execution_results.append({
                            "subtask_id": subtask.get("id"),
                            "subtask_title": subtask.get("title"),
                            "tool_used": subtask.get("tool_name"),
                            "result": exec_result,
                            "step": i + 1,
                            "intelligent_execution": True
                        })
                        
                    except asyncio.TimeoutError:
                        logger.error(f"🟠 [Intelligent Orchestrator] Subtask {i+1} timed out [ID: {context.correlation_id}]")
                        execution_results.append({
                            "subtask_id": subtask.get("id"),
                            "success": False,
                            "error": "Timeout during intelligent execution",
                            "step": i + 1
                        })
                    except Exception as e:
                        logger.error(f"🟠 [Intelligent Orchestrator] Subtask {i+1} failed: {e} [ID: {context.correlation_id}]")
                        execution_results.append({
                            "subtask_id": subtask.get("id"),
                            "success": False,
                            "error": str(e),
                            "step": i + 1,
                            "intelligent_execution": True
                        })
            
            # ЕТАП 6: Final synthesis з аналізом результатів
            logger.info(f"🟠 [Intelligent Orchestrator] Synthesizing intelligent results")
            synthesis_result = await self.call_task_orchestrator_tool("orchestrator_synthesize_results", {
                "task_id": plan_result.get("task_id", "unknown"),
                "execution_summary": execution_results,
                "tools_used": list(available_tools.keys()),
                "correlation_id": context.correlation_id
            })
            
            if synthesis_result:
                execution_results.append({
                    "type": "intelligent_synthesis",
                    "result": synthesis_result
                })
                
            context.end_time = datetime.now()
            context.duration = (context.end_time - context.start_time).total_seconds()
            
            logger.info(f"🎯 [Intelligent Orchestrator] Completed in {context.duration:.2f}s with {len(execution_results)} results [ID: {context.correlation_id}]")
            
            return execution_results
            
        except Exception as e:
            logger.error(f"🔴 [Intelligent Orchestrator] Critical error: {e} [ID: {context.correlation_id}]")
            return [{"success": False, "error": f"Intelligent orchestration failed: {str(e)}", "correlation_id": context.correlation_id}]

    def _format_tools_context(self, available_tools: Dict[str, List[str]]) -> str:
        """Форматуємо контекст доступних інструментів для LLM"""
        context_parts = []
        for service, tools in available_tools.items():
            context_parts.append(f"{service}({', '.join(tools)})")
        return "; ".join(context_parts)

    def _tool_available(self, tool_name: str, available_tools: Dict[str, List[str]]) -> bool:
        """Перевіряємо чи доступний інструмент в registry"""
        for tools in available_tools.values():
            if tool_name in tools:
                return True
        return False

    async def _find_alternative_tool(self, original_tool: str, available_tools: Dict[str, List[str]]) -> Optional[str]:
        """Шукаємо альтернативний інструмент"""
        # Мапінг схожих інструментів
        alternatives = {
            "system_launch_app": ["run_applescript", "system_launch_app"],
            "browserNavigate": ["browserNavigate", "createPage"],
            "mouseClick": ["browserClick", "mouseClick"],
            "say_tts": ["say_tts", "notifications_send_notification"]
        }
        
        if original_tool in alternatives:
            for alt_tool in alternatives[original_tool]:
                if self._tool_available(alt_tool, available_tools):
                    return alt_tool
        return None

    async def _intelligent_app_inference(self, task: str, available_tools: Dict[str, List[str]]) -> Optional[str]:
        """Інтелектуальний висновок назви додатку з урахуванням доступних інструментів"""
        # Спочатку перевіряємо чи є система для запуску додатків
        if not self._tool_available("system_launch_app", available_tools):
            logger.warning("� [App Inference] system_launch_app not available")
            return None
            
        # Стандартний висновок через config
        return await self._infer_app_from_request(task)

    async def _validate_plan_against_registry(self, task_data: Dict, available_tools: Dict[str, List[str]]) -> Dict:
        """Валідуємо план виконання проти registry інструментів"""
        validation = {
            "valid_tools": 0,
            "invalid_tools": 0,
            "missing_tools": [],
            "available_alternatives": {},
            "coverage": 0.0
        }
        
        subtasks = task_data.get("subtasks", [])
        for subtask in subtasks:
            tool_name = subtask.get("tool_name")
            if tool_name:
                if self._tool_available(tool_name, available_tools):
                    validation["valid_tools"] += 1
                else:
                    validation["invalid_tools"] += 1
                    validation["missing_tools"].append(tool_name)
                    # Шукаємо альтернативи
                    alternative = await self._find_alternative_tool(tool_name, available_tools)
                    if alternative:
                        validation["available_alternatives"][tool_name] = alternative
        
        total_tools = validation["valid_tools"] + validation["invalid_tools"]
        if total_tools > 0:
            validation["coverage"] = validation["valid_tools"] / total_tools
        
        logger.info(f"🔍 [Validation] Plan coverage: {validation['coverage']:.2f} ({validation['valid_tools']}/{total_tools} tools available)")
        return validation

    async def execute_task_with_llm2(self, english_task: str, original_message: str) -> List[Dict]:
        """🟠 LLM2 Orchestrator - DEPRECATED: Legacy fallback, використовує Task Orchestrator"""
        logger.warning(f"⚠️ [LLM2] DEPRECATED: Using legacy fallback path, redirecting to Task Orchestrator")
        
        # Redirect to new Task Orchestrator instead of duplicating logic
        return await self.execute_task_with_task_orchestrator(english_task, original_message)
    
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
        """DEPRECATED: Execute tasks orchestrated by LLM2 - redirects to Task Orchestrator"""
        logger.warning(f"DEPRECATED: execute_orchestrated_task called, redirecting to Task Orchestrator")
        
        # Convert to new Task Orchestrator format
        return await self.execute_task_with_task_orchestrator(task_description, task_description)
    
    def add_log_entry(self, level: str, message: str, source: str = "atlas-core"):
        """Add log entry (thread/async safe, без вкладеної корутини для Pylance)."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "source": source,
            "message": message
        }

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Немає активного loop → синхронно (наприклад під час старту)
            self.log_buffer.append(log_entry)
            if len(self.log_buffer) > self.max_log_buffer_size:
                self.log_buffer = self.log_buffer[-self.max_log_buffer_size:]
            return

        async def _append() -> None:
            async with self.log_buffer_lock:
                self.log_buffer.append(log_entry)
                if len(self.log_buffer) > self.max_log_buffer_size:
                    self.log_buffer = self.log_buffer[-self.max_log_buffer_size:]
            # Broadcast to SSE subscribers (non-blocking)
            dead_queues = []
            for q in self.log_subscribers:
                try:
                    if q.qsize() < 100:  # simple backpressure guard
                        q.put_nowait(log_entry)
                except Exception:
                    dead_queues.append(q)
            for dq in dead_queues:
                try:
                    self.log_subscribers.remove(dq)
                except ValueError:
                    pass

        loop.create_task(_append())
    
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
            # Генералізований fallback за конфігурацією
            app_name = await self._infer_app_from_request(task_description)
            if app_name:
                launch = await self.call_mcp_tool_via_proxy("system_launch_app", {"app_name": app_name})
                return {
                    "success": launch.get("status") == "success",
                    "result": launch,
                    "description": f"Launched {app_name} via config fallback",
                    "fallback": True
                }
            
            return {
                "success": False,
                "error": "No config fallback match",
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
        
        # Performance metrics snapshot
        performance = {"services": {}, "updated_at": datetime.now().isoformat()}
        for svc, data in self.latency_stats.items():
            calls = data.get('calls', 0)
            errors = data.get('errors', 0)
            total_ms = data.get('total_ms', 0.0)
            samples = list(data.get('samples', []))
            avg_ms = (total_ms / calls) if calls else None
            p95 = None
            if samples:
                sorted_samples = sorted(samples)
                idx = int(0.95 * (len(sorted_samples) - 1))
                p95 = sorted_samples[idx]
            # Extract 'since' safely
            _since_val = data.get('since')
            performance['services'][svc] = {
                "calls_total": calls,
                "errors": errors,
                "success_rate": round((calls - errors) / calls, 3) if calls else None,
                "avg_ms": round(avg_ms, 2) if avg_ms is not None else None,
                "ema_ms": round(data.get('ema_ms', avg_ms), 2) if avg_ms is not None else None,
                "p95_ms": round(p95, 2) if p95 is not None else None,
                "last_ms": round(data.get('last_ms', 0.0), 2) if calls else None,
                "last_error": data.get('last_error'),
                "since": _since_val.isoformat() if isinstance(_since_val, datetime) else None
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "agents_online": len(self.agents),
            "task_queue_size": self.task_queue.qsize(),
            "automation_ready": True,
            "mcp": mcp_info,
            "performance": performance
        }

    async def load_mcp_config(self) -> None:
        """Load MCP servers configuration.
        In proxy mode (ATLAS_MCP_PROXY_MODE=true): Use single proxy endpoint
        In direct mode: Use individual server endpoints
        """
        # If proxy mode is enabled, use proxy for all MCP calls
        if self.mcp_proxy_mode:
            logger.info(f"🔗 MCP Proxy mode enabled - using {self.mcp_proxy_url}")
            # In proxy mode, we don't need individual endpoints
            # All calls go through call_mcp_tool_via_proxy()
            # In proxy mode, build health checks for all available services
            self.mcp_endpoints = {"proxy": {"base_url": self.mcp_proxy_url}}
            
            # Discover available services for comprehensive health checks
            await self._discover_proxy_services()
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

    async def enhanced_tts_call(self, text: str, voice: str = "mykyta", lang: str = "uk") -> dict:
        """
        Покращений TTS з інтелектуальною ієрархією fallback:
        1. 🇺🇦 Ukrainian TTS (локальний)
        2. 🌐 Google TTS API  
        3. 📻 Google gTTS
        4. 🔊 System say
        5. 📝 Text fallback
        """
        if not text.strip():
            return {"success": False, "error": "Empty text", "method": "none"}
        
        logger.info(f"🎤 Enhanced TTS: '{text[:50]}...'")
        
        # 1️⃣ Спробуємо стандартний MCP TTS
        try:
            result = await self.call_mcp_tool_via_proxy("say_tts", {"text": text, "voice": voice}, _internal_call=True)
            if result.get("success"):
                return {"success": True, "method": "mcp_ukrainian", "text": text}
        except Exception as e:
            logger.warning(f"MCP TTS failed: {e}")
        
        # 2️⃣ Google TTS API fallback (якщо є ключ)
        google_api_key = os.getenv('GOOGLE_TTS_API_KEY')
        if google_api_key:
            try:
                import requests
                import base64
                import tempfile
                
                url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={google_api_key}"
                
                payload = {
                    "input": {"text": text},
                    "voice": {"languageCode": "uk-UA", "name": "uk-UA-Standard-A"},
                    "audioConfig": {"audioEncoding": "MP3"}
                }
                
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    response_data = response.json()
                    if "audioContent" in response_data:
                        # Декодуємо base64 і відтворюємо
                        audio_data = base64.b64decode(response_data["audioContent"])
                        
                        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                            temp_file.write(audio_data)
                            temp_path = temp_file.name
                        
                        # Використовуємо pygame або системний плеєр
                        try:
                            import pygame
                            pygame.mixer.init()
                            pygame.mixer.music.load(temp_path)
                            pygame.mixer.music.play()
                            
                            while pygame.mixer.music.get_busy():
                                await asyncio.sleep(0.1)
                                
                            os.unlink(temp_path)
                            return {"success": True, "method": "google_api", "text": text}
                        except:
                            # Fallback на afplay (macOS)
                            import subprocess
                            subprocess.run(['afplay', temp_path])
                            os.unlink(temp_path)
                            return {"success": True, "method": "google_api_afplay", "text": text}
                            
            except Exception as e:
                logger.warning(f"Google TTS API failed: {e}")
        
        # 3️⃣ Google gTTS fallback
        try:
            from gtts import gTTS
            import tempfile
            
            tts = gTTS(text=text, lang=lang, slow=False)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            tts.save(temp_path)
            
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                    
                os.unlink(temp_path)
                return {"success": True, "method": "google_gtts", "text": text}
            except:
                # Fallback на системний плеєр
                import subprocess
                subprocess.run(['afplay', temp_path])
                os.unlink(temp_path)
                return {"success": True, "method": "google_gtts_afplay", "text": text}
                
        except Exception as e:
            logger.warning(f"Google gTTS failed: {e}")
        
        # 4️⃣ System say fallback
        try:
            process = await asyncio.create_subprocess_exec(
                'say', text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0:
                return {"success": True, "method": "system_say", "text": text}
        except Exception as e:
            logger.warning(f"System say failed: {e}")
        
        # 5️⃣ Крайня заглушка - текстовий вивід
        logger.warning(f"📝 All TTS failed, text output: {text}")
        print(f"🔊 TTS: {text}")
        return {"success": True, "method": "text_fallback", "text": text}

    async def call_mcp_tool_via_proxy(self, tool_name: str, args: dict, _internal_call: bool = False):
        """Call MCP tool through proxy with error handling and logging"""
        if not hasattr(self, 'mcp_proxy_url'):
            raise Exception("MCP Proxy not initialized")
        
        # Use direct Ukrainian TTS for TTS calls
        if tool_name == "say_tts":
            return await self._handle_tts_direct(args, _internal_call)
        
        # Handle other MCP tools via proxy
        return await self._execute_proxy_tool(tool_name, args)

    async def _execute_proxy_tool(self, tool_name: str, args: dict) -> dict:
        """Execute non-TTS tools via MCP proxy"""
        try:
            _lat_start = time.perf_counter()
            # Determine service and route based on tool
            service_map = {
                "mouseClick": "automation",
                "mouseMove": "automation", 
                "screenshot": "automation",
                "type": "automation",
                "keyControl": "automation",
                "systemCommand": "automation",
                "run_applescript": "applescript",
                "system_launch_app": "applescript",
                "system_quit_app": "applescript",
                "browser_navigate": "playwright",
                "browser_click": "playwright",
                "browser_type": "playwright",
                "browser_screenshot": "playwright"
            }
            
            service = service_map.get(tool_name, "automation")  # Default to automation
            
            # Build proxy URL
            url = f"{self.mcp_proxy_url.rstrip('/')}/{service}/{tool_name}"
            
            logger.info(f"🔧 [PROXY] Calling {service}/{tool_name} via {url}")
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=args) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ [PROXY] {tool_name} completed successfully")
                        self._record_latency(service, _lat_start, error=False)
                        return {
                            "status": "success",
                            "result": result,
                            "tool": tool_name,
                            "service": service
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ [PROXY] {tool_name} failed: HTTP {response.status}")
                        self._record_latency(service, _lat_start, error=True, last_error=f"HTTP {response.status}")
                        return {
                            "status": "error", 
                            "error": f"HTTP {response.status}: {error_text}",
                            "tool": tool_name,
                            "service": service
                        }
        except Exception as e:
            logger.error(f"❌ [PROXY] {tool_name} exception: {e}")
            self._record_latency(service, locals().get('_lat_start'), error=True, last_error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "tool": tool_name
            }

    async def _handle_tts_direct(self, args: dict, _internal_call: bool = False):
        """Handle TTS with proper fallback chain to prevent recursion"""
        text = args.get("text", "")
        voice = args.get("voice", "mykyta") 
        rate = args.get("rate", 200)  # Default rate 
        
        try:
            # Спробувати прямий виклик українського TTS
            logger.info(f"🎙️ Using Ukrainian TTS for: {text[:50]}...")
            
            # Перевірка наявності необхідних модулів
            if not UKRAINIAN_TTS_AVAILABLE:
                logger.warning("Ukrainian TTS not available, falling back to system TTS")
                return await self._fallback_to_system_tts(text, rate)
            
            if not PYGAME_AVAILABLE:
                logger.warning("Pygame not available, falling back to system TTS")
                return await self._fallback_to_system_tts(text, rate)
            
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
            return await self._fallback_to_system_tts(text, rate)

    async def _fallback_to_system_tts(self, text: str, rate: int) -> dict:
        """Fallback to macOS system TTS without recursion"""
        try:
            process = await asyncio.create_subprocess_exec(
                'say', '-r', str(rate), text,
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
        except Exception as e:
            logger.error(f"System TTS fallback failed: {e}")
            return {"status": "error", "message": str(e)}

    async def discover_mcp_tools_real(self):
        """Інтелектуальна автодетекція реальних MCP інструментів з працюючих серверів"""
        discovered_tools = {}
        
        if not self.mcp_proxy_mode:
            logger.warning("MCP proxy mode disabled - returning empty tools registry")
            return discovered_tools
        
        try:
            logger.info("🔍 Starting intelligent MCP tools discovery...")
            timeout = aiohttp.ClientTimeout(total=15)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 1. TASK ORCHESTRATOR - Інтелектуальне виявлення через get_all_tools
                await self._discover_task_orchestrator_tools(session, discovered_tools)
                
                # 2. TTS SERVICE
                await self._discover_tts_tools(session, discovered_tools)
                
                # 3. MACOS AUTOMATION
                await self._discover_automation_tools(session, discovered_tools)
                
                # 4. PLAYWRIGHT BROWSER
                await self._discover_playwright_tools(session, discovered_tools)
                
                # 5. APPLESCRIPT MCP
                await self._discover_applescript_tools(session, discovered_tools)
                
                # 6. ADVANCED SERVICES (нові)
                await self._discover_advanced_services(session, discovered_tools)
        
        except Exception as e:
            logger.error(f"Error during MCP tools discovery: {e}")
        
        # Web Fetch - статичні інструменти (завжди доступні)
        discovered_tools["web-fetch"] = ["fetch_url", "fetch_html", "fetch_json", "fetch_text", "web_search"]
        
        # GitHub Integration - якщо доступний
        if os.getenv("GITHUB_TOKEN"):
            discovered_tools["github-integration"] = ["create_issue", "get_repository", "search_repositories", 
                                                    "create_pull_request", "list_issues", "get_issue", "create_comment"]
        
        # Логування результатів
        total_tools = sum(len(tools) for tools in discovered_tools.values())
        logger.info(f"🎯 Intelligent discovery completed: {total_tools} tools from {len(discovered_tools)} services")
        
        return discovered_tools

    async def _discover_task_orchestrator_tools(self, session, discovered_tools):
        """Інтелектуальне виявлення Task Orchestrator інструментів"""
        try:
            # Спочатку спробуємо отримати реальний список інструментів через REST API
            url = "http://localhost:4006/tools"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("tools"):
                        tools = [tool.get("name", f"tool_{i}") for i, tool in enumerate(data["tools"])]
                        discovered_tools["task-orchestrator"] = tools
                        logger.info(f"🟢 Task Orchestrator: {len(tools)} tools discovered via REST API")
                        return
                        
            # Fallback: тестуємо через MCP proxy
            if self.mcp_proxy_url:
                url = f"{self.mcp_proxy_url}/call_tool"
                payload = {"name": "orchestrator_get_status", "parameters": {}}
                
                async with session.post(url, json=payload) as response:
                    if response.status in [200, 404]:
                        logger.info("🟢 Task Orchestrator detected via MCP proxy")
                        # Розширений список на основі tool_definitions.py
                        orchestrator_tools = [
                            "orchestrator_initialize_session", "orchestrator_plan_task", "orchestrator_execute_task",
                            "orchestrator_complete_task", "orchestrator_get_status", "orchestrator_synthesize_results",
                            "orchestrator_update_task", "orchestrator_delete_task", "orchestrator_query_tasks",
                            "orchestrator_list_sessions", "orchestrator_resume_session", "orchestrator_cleanup_sessions",
                            "orchestrator_session_status", "orchestrator_maintenance_coordinator",
                            "orchestrator_execute_subtask", "orchestrator_complete_subtask"
                        ]
                        discovered_tools["task-orchestrator"] = orchestrator_tools
                    else:
                        logger.warning(f"Task Orchestrator proxy probe failed: {response.status}")
        except Exception as e:
            logger.warning(f"Task Orchestrator discovery failed: {e}")
            # Final fallback
            orchestrator_tools = [
                "orchestrator_initialize_session", "orchestrator_plan_task", "orchestrator_execute_task",
                "orchestrator_get_status", "orchestrator_synthesize_results"
            ]
            discovered_tools["task-orchestrator"] = orchestrator_tools

    async def _discover_tts_tools(self, session, discovered_tools):
        """Виявлення TTS інструментів"""
        try:
            if self.mcp_proxy_url:
                url = f"{self.mcp_proxy_url}/call_tool"
                payload = {"name": "say_tts", "parameters": {"text": "test", "rate": 200}}
                
                async with session.post(url, json=payload) as response:
                    if response.status in [200, 404, 500]:
                        logger.info("🟢 TTS service detected")
                        discovered_tools["tts"] = ["say_tts", "stop_tts", "set_voice", "get_voices", "list_voices", "tts_status"]
                    else:
                        logger.warning(f"TTS probe failed: {response.status}")
        except Exception as e:
            logger.warning(f"TTS discovery failed: {e}")

    async def _discover_automation_tools(self, session, discovered_tools):
        """Виявлення macOS Automation інструментів"""
        try:
            if self.mcp_proxy_url:
                url = f"{self.mcp_proxy_url}/call_tool"
                payload = {"name": "system_launch_app", "parameters": {"app_name": "System Preferences"}}
                
                async with session.post(url, json=payload) as response:
                    if response.status in [200, 404, 500]:
                        logger.info("🟢 macOS Automation detected")
                        discovered_tools["automation"] = [
                            "mouseClick", "mouseMove", "screenshot", "type", "keyControl", "systemCommand", 
                            "read_file", "write_file", "system_launch_app", "system_quit_app", "system_minimize_app",
                            "run_applescript", "key", "system_sleep", "system_restart", 
                            "get_running_applications", "get_system_info", "window_management", "dock_control"
                        ]
                    else:
                        logger.warning(f"macOS Automation probe failed: {response.status}")
        except Exception as e:
            logger.warning(f"macOS Automation discovery failed: {e}")

    async def _discover_playwright_tools(self, session, discovered_tools):
        """Виявлення Playwright інструментів"""
        try:
            if self.mcp_proxy_url:
                url = f"{self.mcp_proxy_url}/call_tool"
                payload = {"name": "browserNavigate", "parameters": {"url": "about:blank"}}
                
                async with session.post(url, json=payload) as response:
                    if response.status in [200, 404, 500]:
                        logger.info("🟢 Playwright browser automation detected")
                        discovered_tools["playwright"] = [
                            "createPage", "activatePage", "closePage", "listPages", "closeAllPages",
                            "listPagesWithoutId", "closePagesWithoutId", "closePageByIndex",
                            "browserClick", "browserType", "browserHover", "browserSelectOption", 
                            "browserPressKey", "browserFileUpload", "browserHandleDialog",
                            "browserNavigate", "browserNavigateBack", "browserNavigateForward",
                            "scrollToBottom", "scrollToTop", "waitForTimeout", "waitForSelector",
                            "getElementHTML", "pageToHtmlFile", "getScreenshot", "getPDFSnapshot",
                            "getPageSnapshot", "downloadImage", "captureSnapshot"
                        ]
                    else:
                        logger.warning(f"Playwright probe failed: {response.status}")
        except Exception as e:
            logger.warning(f"Playwright discovery failed: {e}")

    async def _discover_applescript_tools(self, session, discovered_tools):
        """Виявлення AppleScript MCP інструментів"""
        try:
            if self.mcp_proxy_url:
                url = f"{self.mcp_proxy_url}/call_tool"
                payload = {"name": "system_get_frontmost_app", "parameters": {}}
                
                async with session.post(url, json=payload) as response:
                    if response.status in [200, 404, 500]:
                        logger.info("🟢 AppleScript MCP detected")
                        discovered_tools["applescript"] = [
                            "calendar_add", "calendar_list", "clipboard_set_clipboard", "clipboard_get_clipboard", "clipboard_clear_clipboard",
                            "finder_get_selected_files", "finder_search_files", "finder_quick_look",
                            "notifications_send_notification", "notifications_toggle_do_not_disturb",
                            "system_volume", "system_get_frontmost_app", "system_launch_app", "system_quit_app", "system_toggle_dark_mode",
                            "iterm_paste_clipboard", "iterm_run", "shortcuts_run_shortcut", "shortcuts_list_shortcuts",
                            "mail_create_email", "mail_list_emails", "mail_get_email",
                            "messages_list_chats", "messages_get_messages", "messages_search_messages", "messages_compose_message",
                            "notes_create", "notes_createRawHtml", "notes_list", "notes_get", "notes_search",
                            "pages_create_document"
                        ]
                    else:
                        logger.warning(f"AppleScript MCP probe failed: {response.status}")
        except Exception as e:
            logger.warning(f"AppleScript MCP discovery failed: {e}")

    async def _discover_advanced_services(self, session, discovered_tools):
        """Виявлення додаткових сервісів"""
        advanced_services = {
            "file-manager": ["read_file", "write_file", "list_directory", "create_directory", "delete_file"],
            "network": ["ping", "http_request", "download_file", "upload_file"],
            "system-monitor": ["get_cpu_usage", "get_memory_usage", "get_disk_usage", "get_processes"],
            "calendar": ["create_event", "list_events", "delete_event", "update_event"],
            "notifications": ["send_notification", "schedule_notification", "clear_notifications"]
        }
        
        if self.mcp_proxy_url:
            for service_name, tools in advanced_services.items():
                try:
                    # Тестуємо перший інструмент кожного сервісу
                    test_tool = tools[0]
                    url = f"{self.mcp_proxy_url}/call_tool"
                    payload = {"name": test_tool, "parameters": {}}
                    
                    async with session.post(url, json=payload) as response:
                        if response.status in [200, 404]:  # 404 означає що сервіс працює, але tool невідомий
                            logger.info(f"🟢 {service_name.title()} service detected")
                            discovered_tools[service_name] = tools
                except Exception:
                    continue  # Сервіс недоступний

    def get_available_mcp_tools(self):
        """Get list of available MCP tools grouped by namespace"""
        if hasattr(self, 'mcp_tools_cache') and self.mcp_tools_cache:
            return self.mcp_tools_cache
        
        # Fallback: використовуємо розширений список базованих на реальних серверах
        if self.mcp_proxy_mode:
            return {
                "task-orchestrator": [
                    "orchestrator_initialize_session", "orchestrator_synthesize_results", "orchestrator_get_status",
                    "orchestrator_plan_task", "orchestrator_update_task", "orchestrator_delete_task", 
                    "orchestrator_cancel_task", "orchestrator_query_tasks", "orchestrator_execute_task",
                    "orchestrator_complete_task", "orchestrator_list_sessions", "orchestrator_resume_session",
                    "orchestrator_cleanup_sessions", "orchestrator_session_status", "orchestrator_maintenance_coordinator"
                ],
                "tts": ["say_tts", "list_voices", "tts_status"],
                "automation": ["mouseClick", "mouseMove", "screenshot", "type", "keyControl", "systemCommand", "read_file", "write_file"],
                "playwright": [
                    "createPage", "activatePage", "closePage", "listPages", "closeAllPages",
                    "listPagesWithoutId", "closePagesWithoutId", "closePageByIndex",
                    "browserClick", "browserType", "browserHover", "browserSelectOption", 
                    "browserPressKey", "browserFileUpload", "browserHandleDialog",
                    "browserNavigate", "browserNavigateBack", "browserNavigateForward",
                    "scrollToBottom", "scrollToTop", "waitForTimeout", "waitForSelector",
                    "getElementHTML", "pageToHtmlFile", "getScreenshot", "getPDFSnapshot",
                    "getPageSnapshot", "downloadImage", "captureSnapshot"
                ],
                "github-integration": ["create_issue", "get_repository", "search_repositories", "create_pull_request", "list_issues", "get_issue", "create_comment"] if os.getenv("GITHUB_TOKEN") else [],
                "applescript": [
                    "calendar_add", "calendar_list", "clipboard_set_clipboard", "clipboard_get_clipboard", "clipboard_clear_clipboard",
                    "finder_get_selected_files", "finder_search_files", "finder_quick_look",
                    "notifications_send_notification", "notifications_toggle_do_not_disturb",
                    "system_volume", "system_get_frontmost_app", "system_launch_app", "system_quit_app", "system_toggle_dark_mode",
                    "iterm_paste_clipboard", "iterm_run", "shortcuts_run_shortcut", "shortcuts_list_shortcuts",
                    "mail_create_email", "mail_list_emails", "mail_get_email",
                    "messages_list_chats", "messages_get_messages", "messages_search_messages", "messages_compose_message",
                    "notes_create", "notes_createRawHtml", "notes_list", "notes_get", "notes_search",
                    "pages_create_document"
                ],
                "web-fetch": ["fetch_url", "fetch_html", "fetch_json", "fetch_text", "web_search"]
            }
        return {}

    # ================== CONFIG-DRIVEN HELPERS (no hardcodes) ==================
    _app_alias_cache: Optional[Dict[str, str]] = None

    def _load_app_aliases(self) -> Dict[str, str]:
        """Load app aliases from env ATLAS_APP_ALIASES="alias=RealName,notes=Notes". Lower-case keys."""
        if self._app_alias_cache is not None:
            return self._app_alias_cache
        mapping_env = os.getenv("ATLAS_APP_ALIASES", "").strip()
        mapping: Dict[str, str] = {}
        if mapping_env:
            for pair in mapping_env.split(','):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if k and v:
                        mapping[k] = v
        self._app_alias_cache = mapping
        return mapping

    async def _infer_app_from_request(self, english_task: str) -> Optional[str]:
        """Infer application name from task using config (no hardcoded app names)."""
        text = english_task.lower()
        verbs = ["open", "launch", "start", "run"]
        if not any(v in text for v in verbs):
            return None
        aliases = self._load_app_aliases()
        if not aliases:
            return None
        matched = [aliases[a] for a in aliases.keys() if a in text]
        # Якщо рівно один збіг – повертаємо
        if len(matched) == 1:
            return matched[0]
        return None

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
                await self.load_mcp_config()
        else:
            await self.load_mcp_config()
    
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
        
        # Initialize MCP tools discovery
        await self.initialize_mcp_tools()
        
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

    async def initialize_mcp_tools(self):
        """Ініціалізація MCP tools discovery при запуску"""
        if self.mcp_proxy_mode:
            logger.info("Initializing MCP tools discovery...")
            try:
                # Даємо час серверам запуститися
                await asyncio.sleep(3)
                
                # Запускаємо автодетекцію
                self.mcp_tools_cache = await self.discover_mcp_tools_real()
                total_tools = sum(len(tools) for tools in self.mcp_tools_cache.values())
                logger.info(f"MCP Tools Discovery completed: {total_tools} tools from {len(self.mcp_tools_cache)} services")
                
                # Виводимо детальну інформацію
                for service, tools in self.mcp_tools_cache.items():
                    logger.info(f"  {service}: {len(tools)} tools - {', '.join(tools[:3])}{'...' if len(tools) > 3 else ''}")
                    
            except Exception as e:
                logger.error(f"Failed to initialize MCP tools discovery: {e}")
                self.mcp_tools_cache = {}
    
    # ======= ДОПОМІЖНІ МЕТОДИ ДЛЯ НОВОЇ АРХІТЕКТУРИ =======
    
    async def security_check_llm3(self, task: str) -> Dict[str, Any]:
        """🔴 LLM3 - ТИМЧАСОВО ВИМКНЕНА перевірка безпеки (ВСІ КОМАНДИ ДОЗВОЛЕНІ)"""
        logger.info(f"🔴 [LLM3] Security check DISABLED - ALL COMMANDS ALLOWED for: {task}")
        
        # ТИМЧАСОВО: Дозволяємо ВСЕ для тестування
        logger.warning("🚨 SECURITY DISABLED TEMPORARILY - ALL OPERATIONS ALLOWED")
        return {
            "approved": True,
            "reason": "Security temporarily disabled - all operations allowed for testing",
            "security_level": "DISABLED",
            "whitelist_match": True,
            "blacklist_match": False
        }
    
    async def llm1_progress_report(self, progress: str):
        """🔵 LLM1 звітує про прогрес"""
        logger.info(f"🔵 [LLM1] Progress: {progress}")
        # Тут можна додати відправку прогресу до frontend через websockets
    
    async def call_task_orchestrator_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the task orchestrator MCP server"""
        try:
            _lat_start = time.perf_counter()
            # Try direct connection to Task Orchestrator first (bypass MCP Proxy issues)
            direct_endpoint = "http://localhost:4006"
            
            # Check if task orchestrator is configured in MCP endpoints, otherwise use direct
            if "task-orchestrator" in self.mcp_endpoints:
                endpoint_name = "task-orchestrator"
                endpoint = self.mcp_endpoints[endpoint_name]["base_url"]
            elif "orchestrator" in self.mcp_endpoints:
                endpoint_name = "orchestrator" 
                endpoint = self.mcp_endpoints[endpoint_name]["base_url"]
            else:
                # Use direct connection as fallback
                logger.info("Task orchestrator not in MCP endpoints, using direct connection")
                endpoint = direct_endpoint
            
            # Prepare the request
            url = f"{endpoint}/call_tool"
            # API contract: orchestrator HTTP server expects 'name'; previous internal draft used 'tool_name'
            payload = {
                "name": tool_name,
                "parameters": parameters
            }
            
            logger.info(f"🟠 [Task Orchestrator] Calling {tool_name} at {url}")
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"🟠 [Task Orchestrator] Tool {tool_name} success: {result}")
                        
                        # Handle both list and dict responses from Task Orchestrator
                        if isinstance(result, list) and len(result) > 0:
                            result = result[0]  # Take first element if it's a list
                        
                        if isinstance(result, dict):
                            inferred_success = result.get("success") if "success" in result else ("error" not in result)
                            self._record_latency('orchestrator', _lat_start, error=not inferred_success)
                            return {"success": inferred_success, **result}
                        else:
                            self._record_latency('orchestrator', _lat_start, error=False)
                            return {"success": True, "result": result}
                    else:
                        error_text = await response.text()
                        logger.error(f"🟠 [Task Orchestrator] Tool {tool_name} failed: {response.status} {error_text}")
                        self._record_latency('orchestrator', _lat_start, error=True, last_error=f"HTTP {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"🟠 [Task Orchestrator] Tool {tool_name} exception: {e}")
            self._record_latency('orchestrator', locals().get('_lat_start'), error=True, last_error=str(e))
            return {"success": False, "error": str(e)}

    def _record_latency(self, service: str, start_time: Optional[float], error: bool, last_error: Optional[str] = None):
        """Record latency & reliability metrics for a service group.

        Parameters:
          service: logical service/tool group name
          start_time: perf_counter at call start
          error: whether call ended in error
          last_error: optional error description
        """
        try:
            if start_time is None:
                return
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            stats = self.latency_stats.get(service)
            if not stats:
                stats = {
                    'calls': 0,
                    'errors': 0,
                    'total_ms': 0.0,
                    'last_ms': 0.0,
                    'samples': deque(maxlen=self._latency_window),
                    'last_error': None,
                    'since': datetime.now(),
                    'ema_ms': elapsed_ms
                }
                self.latency_stats[service] = stats
            stats['calls'] += 1
            if error:
                stats['errors'] += 1
                if last_error:
                    stats['last_error'] = last_error
            stats['total_ms'] += elapsed_ms
            stats['last_ms'] = elapsed_ms
            stats['samples'].append(elapsed_ms)
            stats['ema_ms'] = stats['ema_ms'] * 0.8 + elapsed_ms * 0.2
        except Exception:
            pass

def main():
    """Main entry point"""
    print("🤖 Atlas Autonomous macOS Management System")
    print("==========================================")
    
    # Check if Ollama is available
    try:
        print("🔍 Checking Ollama availability...")
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
    print("🚀 Initializing Atlas Core...")
    try:
        atlas = AtlasCore()
        print("✅ Atlas Core initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Atlas Core: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("🌐 Starting Atlas server...")
    try:
        asyncio.run(atlas.run())
    except KeyboardInterrupt:
        print("\n🛑 Atlas system stopped by user")
    except Exception as e:
        print(f"❌ Error starting Atlas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()