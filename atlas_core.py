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
    import json
    import re
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

# Load environment variables from .env if present
try:
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
    fallback_model: Optional[str] = None

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
    """Enhanced LLM agent with support for multiple providers"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = None
        self.fallback_config = None
        self.setup_client()
        self.setup_fallback()

    def setup_client(self):
        """Setup the LLM client based on provider"""
        if self.config.provider == "ollama":
            # Allow both OLLAMA_URL (with scheme) and OLLAMA_HOST (host:port)
            api_base = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST") or self.config.api_base
            if api_base and not api_base.startswith("http"):
                api_base = f"http://{api_base}"
            self.client = ollama.Client(host=api_base)
        elif self.config.provider == "gemini":
            self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                logger.warning("GEMINI_API_KEY not found, will use fallback")
        elif self.config.provider == "mistral":
            self.api_key = os.getenv("MISTRAL_API_KEY")
            if not self.api_key:
                logger.warning("MISTRAL_API_KEY not found, will use fallback")
        else:
            logger.warning(f"Provider {self.config.provider} not yet implemented")

    def setup_fallback(self):
        """Setup fallback configuration"""
        fallback_model = getattr(self.config, 'fallback_model', None)
        if fallback_model:
            self.fallback_config = AgentConfig(
                name=f"{self.config.name}_fallback",
                role=self.config.role,
                model=fallback_model,
                provider="ollama",
                api_base=os.getenv("OLLAMA_URL") or "http://ollama-host:11434",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

    async def call_gemini_api(self, prompt: str) -> Optional[str]:
        """Call Gemini API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:generateContent"
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.api_key
            }
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['candidates'][0]['content']['parts'][0]['text']
                    else:
                        logger.error(f"Gemini API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return None

    async def call_mistral_api(self, prompt: str) -> Optional[str]:
        """Call Mistral API"""
        try:
            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            data = {
                "model": "mistral-large-latest",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        logger.error(f"Mistral API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Mistral API call failed: {e}")
            return None

    async def call_ollama_api(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Call Ollama API"""
        try:
            if self.client is None:
                logger.error("Ollama client is not initialized")
                return None
                
            response = self.client.generate(
                model=model or self.config.model,
                prompt=prompt,
                options={
                    'temperature': self.config.temperature,
                    'num_predict': self.config.max_tokens,
                },
            )
            return response['response']
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return None

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response from the LLM with fallback support"""
        try:
            full_prompt = f"{context}\n\nUser: {prompt}\nAssistant:" if context else prompt
            
            # Try primary provider first
            response = None
            if self.config.provider == "gemini" and hasattr(self, 'api_key') and self.api_key:
                response = await self.call_gemini_api(full_prompt)
            elif self.config.provider == "mistral" and hasattr(self, 'api_key') and self.api_key:
                response = await self.call_mistral_api(full_prompt)
            elif self.config.provider == "ollama":
                response = await self.call_ollama_api(full_prompt)
                
            # If primary fails, try fallback
            if response is None and self.fallback_config:
                logger.info(f"Primary provider failed for {self.config.name}, using fallback")
                response = await self.call_ollama_api(full_prompt, self.fallback_config.model)
                
            return response or f"Error: Unable to generate response from {self.config.name}"
            
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
        self.setup_agents()
        self.setup_web_interface()
        self.load_mcp_config()
        
    def setup_agents(self):
        """Initialize the three main LLM agents with new provider support"""
        # Resolve common settings from env
        default_provider = os.getenv("ATLAS_LLM_PROVIDER", "ollama")
        
        # Get models from environment with new defaults
        llm1_model = os.getenv("ATLAS_LLM1_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "gemini-2.0-flash"
        llm1_fallback = os.getenv("ATLAS_LLM1_FALLBACK") or "llama3.1:8b"
        
        llm2_model = os.getenv("ATLAS_LLM2_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "gpt-oss:latest"
        
        llm3_model = os.getenv("ATLAS_LLM3_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "mistral"
        llm3_fallback = os.getenv("ATLAS_LLM3_FALLBACK") or "llama3.1:8b"
        
        api_base = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        if api_base and not str(api_base).startswith("http"):
            api_base = f"http://{api_base}"

        # LLM1 - Interface & Memory Agent (Gemini with Ollama fallback)
        llm1_provider = "gemini" if llm1_model.startswith("gemini") else default_provider
        llm1_config = AgentConfig(
            name="LLM1_Interface",
            role="User interface and memory management",
            model=llm1_model,
            provider=llm1_provider,
            api_base=str(api_base)
        )
        llm1_config.fallback_model = llm1_fallback
        
        # LLM2 - Orchestrator Agent (Ollama with gpt-oss)
        llm2_config = AgentConfig(
            name="LLM2_Orchestrator", 
            role="Task orchestration and planning",
            model=llm2_model,
            provider="ollama",  # Always use Ollama for LLM2
            api_base=str(api_base)
        )
        
        # LLM3 - Monitor Agent (Mistral with Ollama fallback)
        llm3_provider = "mistral" if llm3_model == "mistral" else default_provider
        llm3_config = AgentConfig(
            name="LLM3_Monitor",
            role="System monitoring and security",
            model=llm3_model,
            provider=llm3_provider,
            api_base=str(api_base)
        )
        llm3_config.fallback_model = llm3_fallback
        
        self.agents = {
            "interface": LLMAgent(llm1_config),
            "orchestrator": LLMAgent(llm2_config),
            "monitor": LLMAgent(llm3_config)
        }
        
        logger.info("Initialized all three LLM agents with new provider support")
        logger.info(f"LLM1: {llm1_provider}:{llm1_model} (fallback: {llm1_fallback})")
        logger.info(f"LLM2: ollama:{llm2_model}")
        logger.info(f"LLM3: {llm3_provider}:{llm3_model} (fallback: {llm3_fallback})")
    
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
        try:
            # LLM1 processes the user interface and memory
            context = "You are LLM1, the interface agent for Atlas autonomous system. Process user requests and maintain conversation context."
            interface_response = await self.agents["interface"].generate_response(message, context)
            
            # LLM2 orchestrates the task if needed
            if any(keyword in message.lower() for keyword in ['open', 'close', 'run', 'execute', 'automate', 'start', 'launch', 'відкрий', 'запусти']):
                orchestrator_context = f"You are LLM2, the orchestrator agent using gpt-oss:latest. The user said: {message}. Plan and coordinate the execution."
                orchestrator_response = await self.agents["orchestrator"].generate_response(message, orchestrator_context)
                
                # Execute the planned action through intelligent MCP routing
                execution_results = await self.execute_orchestrated_task(message)
                
                # Format results for user
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
                
                return f"Atlas Interface: {interface_response}\n\nOrchestrator (gpt-oss): {orchestrator_response}\n{results_summary}"
            
            return f"Atlas Interface: {interface_response}"
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error processing your request: {str(e)}"
    
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
        try:
            logger.info(f"LLM2 analyzing task: {task_description}")
            
            # LLM2 with gpt-oss:latest analyzes the task and creates execution plan
            orchestrator_prompt = f"""You are LLM2, the intelligent orchestrator agent using gpt-oss:latest model. 

Your task: {task_description}

Available MCP services and their capabilities:
1. mcp-automation (port 4002): File operations, system commands, HTTP requests
2. mcp-automator (port 4003): macOS app control (open/close apps), AppleScript, Shortcuts
3. mcp-playwright (port 4005): Web browser automation, page navigation, form filling
4. mcp-tts (port 4004): Text-to-speech synthesis

Analyze the user's request and create a step-by-step execution plan. For each step, specify:
- Which MCP service to use
- What specific action/tool to call
- Required parameters

Respond with a JSON execution plan in this format:
{{
    "analysis": "Brief analysis of the task",
    "steps": [
        {{
            "service": "mcp-automator|mcp-automation|mcp-playwright|mcp-tts",
            "tool": "tool_name",
            "parameters": {{"param1": "value1", "param2": "value2"}},
            "description": "What this step does"
        }}
    ],
    "expected_outcome": "What should happen after execution"
}}

Important: Only use actions that the MCP services actually support. For macOS apps, use mcp-automator with app_control tool."""

            # Generate execution plan with LLM2
            plan_response = await self.agents["orchestrator"].generate_response(
                orchestrator_prompt, 
                "You are the intelligent orchestrator. Create precise execution plans."
            )
            
            logger.info(f"LLM2 execution plan: {plan_response}")
            
            # Try to parse the JSON plan
            execution_results = []
            try:
                # Extract JSON from response (handle potential markdown formatting)
                json_start = plan_response.find('{')
                json_end = plan_response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    plan_json = plan_response[json_start:json_end]
                    execution_plan = json.loads(plan_json)
                    
                    logger.info(f"Parsed execution plan: {execution_plan}")
                    
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
            logger.error(f"Error in orchestrated task execution: {e}")
            return [{"error": f"Task execution failed: {str(e)}"}]

    async def execute_mcp_step(self, step: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Execute a single step from the LLM2 execution plan"""
        try:
            service = step.get("service", "")
            tool = step.get("tool", "")
            parameters = step.get("parameters", {})
            description = step.get("description", "")
            
            logger.info(f"Step {step_number}: {description} via {service}.{tool}")
            
            # Map service names to endpoints
            service_map = {
                "mcp-automation": "automation",
                "mcp-automator": "macos-automator", 
                "mcp-playwright": "playwright",
                "mcp-tts": "tts"
            }
            
            endpoint_key = service_map.get(service)
            if not endpoint_key or endpoint_key not in self.mcp_endpoints:
                return {"step": step_number, "error": f"Unknown service: {service}"}
            
            endpoint_config = self.mcp_endpoints[endpoint_key]
            base_url = endpoint_config["base_url"]
            
            # Prepare MCP request
            mcp_request = {
                "tool": tool,
                "parameters": parameters
            }
            
            # Execute MCP call
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{base_url}/execute",
                        json=mcp_request,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Step {step_number} completed successfully")
                            return {
                                "step": step_number,
                                "service": service,
                                "tool": tool,
                                "success": True,
                                "result": result
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"Step {step_number} failed: HTTP {response.status} - {error_text}")
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
        """Fallback execution when LLM2 plan parsing fails"""
        logger.info(f"Executing fallback for: {task_description}")
        
        task_lower = task_description.lower()
        
        # Simple keyword-based task routing
        if any(keyword in task_lower for keyword in ['open', 'launch', 'start']) and any(app in task_lower for app in ['chrome', 'safari', 'firefox', 'browser']):
            # Browser opening task
            try:
                # Try Chrome first
                if 'chrome' in task_lower:
                    app_name = "Google Chrome"
                elif 'safari' in task_lower:
                    app_name = "Safari"
                elif 'firefox' in task_lower:
                    app_name = "Firefox"
                else:
                    app_name = "Safari"  # Default browser
                
                return await self.execute_mcp_step({
                    "service": "mcp-automator",
                    "tool": "app_control",
                    "parameters": {"action": "open", "app_name": app_name},
                    "description": f"Open {app_name}"
                }, 1)
                
            except Exception as e:
                return {"error": f"Failed to open browser: {str(e)}"}
        
        elif any(keyword in task_lower for keyword in ['say', 'speak', 'voice']):
            # TTS task
            text_to_speak = task_description
            return await self.execute_mcp_step({
                "service": "mcp-tts",
                "tool": "speak",
                "parameters": {"text": text_to_speak},
                "description": "Text-to-speech"
            }, 1)
        
        else:
            # Generic automation attempt
            return {"error": f"Could not determine how to execute: {task_description}"}

    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        # Probe MCP endpoints with short timeouts
        mcp_status = await self.check_mcp_status()
        return {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "agents_online": len(self.agents),
            "task_queue_size": self.task_queue.qsize(),
            "automation_ready": True,
            "mcp": {
                "configured": list(self.mcp_endpoints.keys()),
                "endpoints": {k: v.get("base_url") for k, v in self.mcp_endpoints.items()},
                "online": mcp_status,
                "count_online": sum(1 for v in mcp_status.values() if v),
            }
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
            # All exceptions are handled inside _probe, so we don't expect exceptions here
            probe_results = await asyncio.gather(*tasks)
            for name, ok in probe_results:
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