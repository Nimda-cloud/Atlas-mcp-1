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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import platform

# Third-party imports (will be installed via requirements.txt)
try:
    import aiohttp
    import ollama
    from fastapi import FastAPI, HTTPException, Response
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    import uvicorn
    from dotenv import load_dotenv
    # Prometheus metrics
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except ImportError as e:
    print(f"Missing required packages. Please run: pip install -r requirements.txt")
    print(f"Error: {e}")
    sys.exit(1)

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

            response = self.client.generate(
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
        # MCP config store
        self.mcp_endpoints: Dict[str, Dict[str, str]] = {}
        
        # MCP Proxy support
        self.mcp_proxy_mode = os.getenv('ATLAS_MCP_PROXY_MODE', 'false').lower() == 'true'
        self.mcp_proxy_url = os.getenv('ATLAS_MCP_PROXY_URL', 'http://127.0.0.1:4010')
        self.mcp_tools_cache = {}
        
        # LLM1 log monitoring and feedback system
        self.log_monitor_task = None
        self.last_feedback_time = datetime.now()
        self.monitoring_enabled = True
        self.log_buffer = []
        self.max_log_buffer_size = 100
        
        self.setup_agents()
        self.setup_web_interface()
        if self.mcp_proxy_mode:
            logger.info("Atlas MCP Proxy mode enabled")
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
            <head>
                <title>ATLAS // HACKER TERMINAL</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Source+Code+Pro:wght@300;400;600&display=swap" rel="stylesheet">
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    
                    body { 
                        font-family: 'Source Code Pro', monospace; 
                        background: #000; 
                        color: #00ff00; 
                        overflow: hidden; 
                        height: 100vh;
                        position: relative;
                    }
                    
                    /* Matrix rain background effect */
                    #matrix-bg {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        z-index: -1;
                        opacity: 0.1;
                    }
                    
                    .container {
                        display: grid;
                        grid-template-columns: 1fr 400px;
                        height: 100vh;
                        gap: 2px;
                        background: #001100;
                        /* Prevent grid children from pushing layout vertically */
                        overflow: hidden;
                    }
                    
                    /* Left side - 3D Model and status */
                    .main-area {
                        display: flex;
                        flex-direction: column;
                        background: rgba(0, 20, 0, 0.8);
                        border: 1px solid #00ff00;
                        position: relative;
                        /* Ensure status bar stays visible within viewport */
                        min-height: 0;
                        overflow: hidden;
                    }
                    
                    .header {
                        padding: 10px 20px;
                        background: linear-gradient(45deg, #001100, #003300);
                        border-bottom: 1px solid #00ff00;
                        text-align: center;
                    }
                    
                    .header h1 {
                        font-family: 'Orbitron', monospace;
                        font-weight: 900;
                        font-size: 24px;
                        color: #00ff00;
                        text-shadow: 0 0 10px #00ff00;
                        letter-spacing: 3px;
                    }
                    
                    .header .subtitle {
                        font-size: 12px;
                        color: #00aa00;
                        opacity: 0.8;
                        margin-top: 5px;
                    }
                    
                    /* 3D Model Area */
                    .model-area {
                        flex: 1;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        position: relative;
                        background: radial-gradient(circle, rgba(0,40,0,0.3) 0%, rgba(0,0,0,0.8) 100%);
                    }
                    
                    .ai-avatar {
                        width: 200px;
                        height: 200px;
                        border: 2px solid #00ff00;
                        border-radius: 50%;
                        background: radial-gradient(circle, rgba(0,255,0,0.1) 0%, rgba(0,100,0,0.05) 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-family: 'Orbitron', monospace;
                        font-size: 48px;
                        color: #00ff00;
                        text-shadow: 0 0 20px #00ff00;
                        animation: pulse 2s infinite;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    
                    .ai-avatar:hover {
                        box-shadow: 0 0 30px #00ff00;
                        transform: scale(1.05);
                    }
                    
                    .ai-avatar.speaking {
                        animation: speak 0.5s infinite alternate;
                        box-shadow: 0 0 40px #00ff00;
                    }
                    
                    @keyframes pulse {
                        0%, 100% { opacity: 0.7; }
                        50% { opacity: 1; }
                    }
                    
                    @keyframes speak {
                        0% { transform: scale(1); }
                        100% { transform: scale(1.1); }
                    }
                    
                    .status-bar {
                        padding: 10px 20px;
                        background: rgba(0, 40, 0, 0.9);
                        border-top: 1px solid #00ff00;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        font-size: 12px;
                    }
                    
                    .status-item {
                        display: flex;
                        align-items: center;
                        gap: 5px;
                    }
                    
                    .status-led {
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #00ff00;
                        box-shadow: 0 0 5px #00ff00;
                        animation: blink 1s infinite;
                    }
                    
                    @keyframes blink {
                        0%, 50% { opacity: 1; }
                        51%, 100% { opacity: 0.3; }
                    }
                    
                    /* Right side - Chat and Logs */
                    .right-panel {
                        display: flex;
                        flex-direction: column;
                        background: rgba(0, 20, 0, 0.9);
                        border: 1px solid #00ff00;
                        /* Allow flex children to shrink to fit height */
                        min-height: 0;
                        overflow: hidden;
                    }
                    
                    .chat-section {
                        flex: 1;
                        display: flex;
                        flex-direction: column;
                        border-bottom: 1px solid #00ff00;
                        position: relative;
                        /* Critical for preventing content from pushing layout */
                        min-height: 0;
                    }
                    
                    .chat-header {
                        padding: 10px;
                        background: linear-gradient(45deg, #001100, #003300);
                        border-bottom: 1px solid #00ff00;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    
                    .chat-title {
                        font-family: 'Orbitron', monospace;
                        font-weight: 700;
                        color: #00ff00;
                        font-size: 14px;
                    }
                    
                    .admin-btn {
                        background: rgba(0, 255, 0, 0.1);
                        border: 1px solid #00ff00;
                        color: #00ff00;
                        padding: 4px 8px;
                        font-size: 10px;
                        cursor: pointer;
                        font-family: 'Source Code Pro', monospace;
                        transition: all 0.3s ease;
                    }
                    
                    .admin-btn:hover {
                        background: rgba(0, 255, 0, 0.2);
                        box-shadow: 0 0 10px #00ff00;
                    }
                    
                    .chat-messages {
                        flex: 1;
                        padding: 10px;
                        overflow-y: auto;
                        background: rgba(0, 0, 0, 0.5);
                        /* Avoid min-content height overflow */
                        min-height: 0;
                    }
                    
                    .message {
                        margin-bottom: 10px;
                        padding: 8px;
                        background: rgba(0, 40, 0, 0.3);
                        border-left: 2px solid #00ff00;
                        font-size: 12px;
                        line-height: 1.4;
                    }
                    
                    .message.user {
                        background: rgba(0, 60, 0, 0.3);
                        border-left-color: #00aa00;
                    }
                    
                    .message.system {
                        background: rgba(0, 80, 0, 0.3);
                        border-left-color: #00ffaa;
                    }
                    
                    .chat-input-area {
                        padding: 10px;
                        background: rgba(0, 40, 0, 0.8);
                        border-top: 1px solid #00ff00;
                    }
                    
                    .chat-input {
                        width: 100%;
                        background: rgba(0, 0, 0, 0.7);
                        border: 1px solid #00ff00;
                        color: #00ff00;
                        padding: 8px;
                        font-family: 'Source Code Pro', monospace;
                        font-size: 12px;
                        resize: none;
                        height: 60px;
                    }
                    
                    .chat-input:focus {
                        outline: none;
                        box-shadow: 0 0 10px #00ff00;
                    }
                    
                    .send-btn {
                        margin-top: 5px;
                        background: rgba(0, 255, 0, 0.1);
                        border: 1px solid #00ff00;
                        color: #00ff00;
                        padding: 8px 16px;
                        cursor: pointer;
                        font-family: 'Source Code Pro', monospace;
                        font-size: 12px;
                        width: 100%;
                        transition: all 0.3s ease;
                    }
                    
                    .send-btn:hover {
                        background: rgba(0, 255, 0, 0.2);
                        box-shadow: 0 0 15px #00ff00;
                    }
                    
                    /* Logs section */
                    .logs-section {
                        height: 200px;
                        display: flex;
                        flex-direction: column;
                        background: rgba(0, 0, 0, 0.8);
                    }
                    
                    .logs-header {
                        padding: 8px 10px;
                        background: linear-gradient(45deg, #001100, #003300);
                        border-bottom: 1px solid #00ff00;
                        font-family: 'Orbitron', monospace;
                        font-weight: 700;
                        color: #00ff00;
                        font-size: 12px;
                    }
                    
                    .logs-content {
                        flex: 1;
                        overflow-y: auto;
                        padding: 5px;
                        font-size: 10px;
                        line-height: 1.2;
                    }
                    
                    .log-entry {
                        margin-bottom: 2px;
                        opacity: 0.8;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    
                    .log-entry.info { color: #00aa00; }
                    .log-entry.warning { color: #ffaa00; }
                    .log-entry.error { color: #ff4444; }
                    .log-entry.success { color: #00ff88; }
                    
                    /* Scrollbar styling */
                    ::-webkit-scrollbar {
                        width: 6px;
                    }
                    
                    ::-webkit-scrollbar-track {
                        background: rgba(0, 0, 0, 0.3);
                    }
                    
                    ::-webkit-scrollbar-thumb {
                        background: #00ff00;
                        border-radius: 3px;
                    }
                    
                    ::-webkit-scrollbar-thumb:hover {
                        background: #00aa00;
                    }
                    
                    /* Admin Panel (hidden by default) */
                    .admin-panel {
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        width: 400px;
                        height: 300px;
                        background: rgba(0, 0, 0, 0.95);
                        border: 2px solid #00ff00;
                        padding: 20px;
                        display: none;
                        z-index: 1000;
                        box-shadow: 0 0 50px #00ff00;
                    }
                    
                    .admin-panel.active {
                        display: block;
                    }
                    
                    .admin-panel h3 {
                        font-family: 'Orbitron', monospace;
                        color: #00ff00;
                        margin-bottom: 15px;
                        text-align: center;
                    }
                    
                    .admin-grid {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 10px;
                    }
                    
                    .admin-button {
                        background: rgba(0, 255, 0, 0.1);
                        border: 1px solid #00ff00;
                        color: #00ff00;
                        padding: 10px;
                        cursor: pointer;
                        font-family: 'Source Code Pro', monospace;
                        font-size: 11px;
                        text-align: center;
                        transition: all 0.3s ease;
                    }
                    
                    .admin-button:hover {
                        background: rgba(0, 255, 0, 0.2);
                        box-shadow: 0 0 10px #00ff00;
                    }
                    
                    .close-admin {
                        position: absolute;
                        top: 10px;
                        right: 15px;
                        background: none;
                        border: none;
                        color: #00ff00;
                        font-size: 18px;
                        cursor: pointer;
                    }
                </style>
            </head>
            <body>
                <canvas id="matrix-bg"></canvas>
                
                <div class="container">
                    <!-- Left side - Main Area with 3D Model -->
                    <div class="main-area">
                        <div class="header">
                            <h1>ATLAS</h1>
                            <div class="subtitle">AUTONOMOUS NEURAL INTERFACE</div>
                        </div>
                        
                        <div class="model-area">
                            <div class="ai-avatar" id="aiAvatar" onclick="speakStatus()">
                                ⬢
                            </div>
                        </div>
                        
                        <div class="status-bar">
                            <div class="status-item">
                                <div class="status-led"></div>
                                <span>AGENTS: 3/3 ONLINE</span>
                            </div>
                            <div class="status-item">
                                <div class="status-led"></div>
                                <span>SYSTEM: READY</span>
                            </div>
                            <div class="status-item">
                                <div class="status-led"></div>
                                <span>AUTOMATION: ACTIVE</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Right side - Chat and Logs -->
                    <div class="right-panel">
                        <div class="chat-section">
                            <div class="chat-header">
                                <div class="chat-title">NEURAL LINK</div>
                                <button class="admin-btn" onclick="toggleAdmin()">ADMIN</button>
                            </div>
                            
                            <div class="chat-messages" id="chatMessages">
                                <div class="message system">
                                    <strong>[SYSTEM]</strong> Atlas Neural Interface initialized.<br>
                                    All agents online. Awaiting commands.
                                </div>
                            </div>
                            
                            <div class="chat-input-area">
                                <textarea id="userInput" class="chat-input" placeholder="Enter command..."></textarea>
                                <button class="send-btn" onclick="sendMessage()">TRANSMIT</button>
                            </div>
                        </div>
                        
                        <div class="logs-section">
                            <div class="logs-header">SYSTEM LOGS</div>
                            <div class="logs-content" id="systemLogs">
                                <div class="log-entry info">[INFO] System initialization complete</div>
                                <div class="log-entry success">[OK] LLM1 Interface Agent: ONLINE</div>
                                <div class="log-entry success">[OK] LLM2 Orchestrator Agent: ONLINE</div>
                                <div class="log-entry success">[OK] LLM3 Monitor Agent: ONLINE</div>
                                <div class="log-entry info">[INFO] Web interface loaded</div>
                                <div class="log-entry info">[INFO] Awaiting user input...</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Admin Panel -->
                <div class="admin-panel" id="adminPanel">
                    <button class="close-admin" onclick="toggleAdmin()">×</button>
                    <h3>ADMIN CONTROL MATRIX</h3>
                    <div class="admin-grid">
                        <button class="admin-button" onclick="performAction('system_info')">SYSTEM INFO</button>
                        <button class="admin-button" onclick="performAction('monitor_system')">DEEP SCAN</button>
                        <button class="admin-button" onclick="performAction('open_app')">LAUNCH APP</button>
                        <button class="admin-button" onclick="refreshStatus()">REFRESH</button>
                        <button class="admin-button" onclick="clearLogs()">CLEAR LOGS</button>
                        <button class="admin-button" onclick="toggleVoice()">VOICE TOGGLE</button>
                    </div>
                </div>
                
                <script>
                    // Matrix rain effect
                    function initMatrix() {
                        const canvas = document.getElementById('matrix-bg');
                        const ctx = canvas.getContext('2d');
                        
                        canvas.width = window.innerWidth;
                        canvas.height = window.innerHeight;
                        
                        const chars = "ATLAS0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
                        const charArray = chars.split("");
                        const columns = canvas.width / 20;
                        const drops = [];
                        
                        for(let x = 0; x < columns; x++) {
                            drops[x] = 1;
                        }
                        
                        function draw() {
                            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
                            ctx.fillRect(0, 0, canvas.width, canvas.height);
                            
                            ctx.fillStyle = '#00ff00';
                            ctx.font = '15px Source Code Pro';
                            
                            for(let i = 0; i < drops.length; i++) {
                                const text = charArray[Math.floor(Math.random() * charArray.length)];
                                ctx.fillText(text, i * 20, drops[i] * 20);
                                
                                if(drops[i] * 20 > canvas.height && Math.random() > 0.975) {
                                    drops[i] = 0;
                                }
                                drops[i]++;
                            }
                        }
                        
                        setInterval(draw, 35);
                    }
                    
                    // Initialize matrix effect
                    initMatrix();
                    
                    // Chat functionality
                    async function sendMessage() {
                        const input = document.getElementById('userInput');
                        const messages = document.getElementById('chatMessages');
                        const message = input.value.trim();
                        
                        if (!message) return;
                        
                        // Add user message
                        addMessage(message, 'user');
                        input.value = '';
                        
                        // Show processing
                        addMessage('Processing command...', 'system');
                        animateAvatar(true);
                        
                        try {
                            const result = await fetch('/chat', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ message: message })
                            });
                            
                            const data = await result.json();
                            
                            // Remove processing message
                            const lastMsg = messages.lastElementChild;
                            if (lastMsg && lastMsg.textContent.includes('Processing')) {
                                messages.removeChild(lastMsg);
                            }
                            
                            addMessage(data.response, 'system');
                            addLog('Command executed: ' + message, 'success');
                            
                        } catch (error) {
                            addMessage('ERROR: ' + error.message, 'system');
                            addLog('Error: ' + error.message, 'error');
                        }
                        
                        animateAvatar(false);
                    }
                    
                    function addMessage(text, type) {
                        const messages = document.getElementById('chatMessages');
                        const msgDiv = document.createElement('div');
                        msgDiv.className = 'message ' + type;
                        
                        const prefix = type === 'user' ? '[USER]' : '[ATLAS]';
                        msgDiv.innerHTML = '<strong>' + prefix + '</strong> ' + text;
                        
                        messages.appendChild(msgDiv);
                        messages.scrollTop = messages.scrollHeight;
                    }
                    
                    function addLog(text, level = 'info') {
                        const logs = document.getElementById('systemLogs');
                        const logDiv = document.createElement('div');
                        logDiv.className = 'log-entry ' + level;
                        
                        const timestamp = new Date().toTimeString().split(' ')[0];
                        logDiv.textContent = '[' + timestamp + '] ' + text;
                        
                        logs.appendChild(logDiv);
                        logs.scrollTop = logs.scrollHeight;
                        
                        // Keep max 50 log entries
                        while (logs.children.length > 50) {
                            logs.removeChild(logs.firstChild);
                        }
                    }
                    
                    function animateAvatar(speaking) {
                        const avatar = document.getElementById('aiAvatar');
                        if (speaking) {
                            avatar.classList.add('speaking');
                        } else {
                            avatar.classList.remove('speaking');
                        }
                    }
                    
                    async function performAction(action) {
                        addLog('Executing action: ' + action, 'info');
                        animateAvatar(true);
                        
                        try {
                            const result = await fetch('/action', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ action: action })
                            });
                            
                            const data = await result.json();
                            addMessage(data.result, 'system');
                            addLog('Action completed: ' + action, 'success');
                            
                        } catch (error) {
                            addMessage('ERROR: ' + error.message, 'system');
                            addLog('Action failed: ' + error.message, 'error');
                        }
                        
                        animateAvatar(false);
                    }
                    
                    function toggleAdmin() {
                        const panel = document.getElementById('adminPanel');
                        panel.classList.toggle('active');
                    }
                    
                    function speakStatus() {
                        addMessage('All systems operational. 3 agents online. Automation ready.', 'system');
                        animateAvatar(true);
                        setTimeout(() => animateAvatar(false), 2000);
                    }
                    
                    function refreshStatus() {
                        location.reload();
                    }
                    
                    function clearLogs() {
                        document.getElementById('systemLogs').innerHTML = '';
                        addLog('Logs cleared', 'info');
                    }
                    
                    function toggleVoice() {
                        addLog('Voice system toggle requested', 'info');
                        addMessage('Voice synthesis system status: READY', 'system');
                    }
                    
                    // Enter key to send message
                    document.getElementById('userInput').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            sendMessage();
                        }
                    });
                    
                    // Window resize handler
                    window.addEventListener('resize', () => {
                        const canvas = document.getElementById('matrix-bg');
                        canvas.width = window.innerWidth;
                        canvas.height = window.innerHeight;
                    });
                    
                    // Initial log entries
                    setTimeout(() => {
                        addLog('Neural link established', 'success');
                        addLog('Monitoring system events...', 'info');
                    }, 1000);
                </script>
            </body>
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
        
        @self.app.get("/status")
        async def status():
            return await self.get_system_status()

        @self.app.get("/metrics")
        async def metrics():
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    async def process_user_message(self, message: str) -> str:
        """Process user message through the agent system"""
        logger.info(f"ENTERING process_user_message with message: {repr(message)}")
        try:
            # LLM1 processes the user interface and provides a brief response
            context = """Ти називаєшся Атлас. Ти розмовляєш ТІЛЬКИ українською мовою. 
НІКОЛИ не використовуй російську мову. НІКОЛИ не додавай англійські переклади в дужках.
НІКОЛИ не починай відповідь з "Atlas Interface:" або будь-якого іншого префіксу.
Відповідай КОРОТКО і природно українською мовою. Максимум 1-2 речення для підтвердження."""
            
            interface_response = await self.agents["interface"].generate_response(message, context)
            
            # Debug: log the raw response
            logger.info(f"Raw interface_response: {repr(interface_response)}")
            
            # Remove English translations in parentheses and clean up response
            cleaned_response = self._clean_response(interface_response)
            
            # LLM2 orchestrates the task if needed
            if any(keyword in message.lower() for keyword in ['open', 'close', 'run', 'execute', 'automate', 'відкрий', 'закрий', 'запусти', 'виконай', 'розгорни', 'фільм']):
                # Execute the planned action via LLM2
                execution_results = await self.execute_orchestrated_task(message)
                
                # Generate concise status report
                results_summary = ""
                if execution_results:
                    successful_steps = [r for r in execution_results if r.get("success", True)]
                    failed_steps = [r for r in execution_results if not r.get("success", True)]
                    
                    if successful_steps:
                        results_summary += f"\n✅ Успішно виконано {len(successful_steps)} кроків:"
                        for result in successful_steps[:3]:  # Show first 3 successful results
                            if "description" in result:
                                results_summary += f"\n  • {result.get('description', 'Завдання виконано')}"
                    
                    if failed_steps:
                        results_summary += f"\n❌ Помилки у {len(failed_steps)} кроках:"
                        for result in failed_steps[:2]:  # Show first 2 errors
                            results_summary += f"\n  • {result.get('error', 'Невідома помилка')}"
                
                return f"{cleaned_response}{results_summary}"
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Помилка при обробці вашого запиту: {str(e)}"
    
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
        """Load MCP servers from environment variables into self.mcp_endpoints.
        Supported variable formats:
          - ATLAS_MCP_SERVERS: comma-separated list of names (e.g., "automation,macos-automator,tts,playwright")
          - ATLAS_MCP_<NAME_UPPER>_URL for generic mapping
          - Specific shorthands: ATLAS_MCP_TTS_URL, ATLAS_MCP_PLAYWRIGHT_URL
        Defaults (docker-compose service names):
          automation -> http://mcp-automation:4002
          macos-automator -> http://mcp-automator:4003
          tts -> http://mcp-tts:4004
          playwright -> http://mcp-playwright:4005/mcp
        Health path rules:
          - If base_url ends with '/mcp' -> use it as-is and accept HTTP 200 or 400 as "online"
          - Else append '/health' and expect HTTP 200
        """
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
        """Load MCP configuration in proxy mode - single endpoint aggregation"""
        proxy_url = self.mcp_proxy_url
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test TTS endpoint specifically (since we know it works)
                test_url = f"{proxy_url}/tts/sse"
                async with session.get(test_url) as resp:
                    if resp.status == 200:
                        # Extract session from SSE endpoint response
                        content = await resp.text()
                        logger.info(f"MCP Proxy SSE response: {content[:200]}...")
                        
                        # For now, we'll mark proxy as connected
                        self.mcp_tools_cache = {
                            "tts": ["say_tts", "elevenlabs_tts", "google_tts", "openai_tts"],
                            "automation": ["mouseClick", "mouseMove", "screenshot", "type", "keyControl"],
                            "applescript": ["run_applescript"],
                            "automator": ["run_workflow"],
                            "playwright": ["browser_navigate", "browser_click", "browser_type"],
                            "vnc": ["vnc_screenshot", "vnc_control"]
                        }
                        
                        logger.info(f"MCP Proxy: Connected to {proxy_url}")
                        logger.info(f"Available namespaces: {list(self.mcp_tools_cache.keys())}")
                        return True
                    else:
                        logger.error(f"MCP Proxy returned HTTP {resp.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to connect to MCP proxy at {proxy_url}: {e}")
            return False

    async def call_mcp_tool_via_proxy(self, tool_name: str, args: dict):
        """Call MCP tool through proxy with error handling and logging"""
        if not hasattr(self, 'mcp_proxy_url'):
            raise Exception("MCP Proxy not initialized")
        
        # For TBXark proxy, we need to use SSE endpoints
        # This is a simplified implementation - in real use, you'd implement proper SSE client
        
        # For now, let's implement basic say_tts directly
        if tool_name == "say_tts":
            text = args.get("text", "")
            rate = args.get("rate", 200)
            
            try:
                # Use macOS say command directly
                process = await asyncio.create_subprocess_exec(
                    'say', '-r', str(rate), text,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"TTS: Successfully spoke text: {text[:50]}...")
                    return {"status": "success", "message": f"Speaking: {text}"}
                else:
                    logger.error(f"TTS error: {stderr.decode()}")
                    return {"status": "error", "message": stderr.decode()}
                    
            except Exception as e:
                logger.error(f"TTS exception: {e}")
                return {"status": "error", "message": str(e)}
        
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
        models = client.list()
        print(f"✅ Ollama available with {len(models.get('models', []))} models")
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