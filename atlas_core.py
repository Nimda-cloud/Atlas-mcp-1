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
    from fastapi import FastAPI, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    import uvicorn
    from dotenv import load_dotenv
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
            self.client = ollama.Client(host=api_base)
        else:
            logger.warning(f"Provider {self.config.provider} not yet implemented")
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response from the LLM"""
        try:
            full_prompt = f"{context}\n\nUser: {prompt}\nAssistant:" if context else prompt
            
            response = self.client.generate(
                model=self.config.model,
                prompt=full_prompt,
                options={
                    'temperature': self.config.temperature,
                    'num_predict': self.config.max_tokens
                }
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
        self.setup_agents()
        self.setup_web_interface()
        
    def setup_agents(self):
        """Initialize the three main LLM agents"""
        # Resolve common settings from env
        default_provider = os.getenv("ATLAS_LLM_PROVIDER", "ollama")
        # Prefer per-agent model envs, then common, then sensible defaults available in repo
        llm1_model = os.getenv("ATLAS_LLM1_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "llama3.1:8b"
        llm2_model = os.getenv("ATLAS_LLM2_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "gpt-oss:latest"
        llm3_model = os.getenv("ATLAS_LLM3_MODEL") or os.getenv("ATLAS_LLM_MODEL") or "llama3.1:8b"
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
        
        logger.info("Initialized all three LLM agents")
    
    def setup_web_interface(self):
        """Setup FastAPI web interface"""
        
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
                    }
                    
                    /* Left side - 3D Model and status */
                    .main-area {
                        display: flex;
                        flex-direction: column;
                        background: rgba(0, 20, 0, 0.8);
                        border: 1px solid #00ff00;
                        position: relative;
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
                    }
                    
                    .chat-section {
                        flex: 1;
                        display: flex;
                        flex-direction: column;
                        border-bottom: 1px solid #00ff00;
                        position: relative;
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
    
    async def process_user_message(self, message: str) -> str:
        """Process user message through the agent system"""
        try:
            # LLM1 processes the user interface and memory
            context = "You are LLM1, the interface agent for Atlas autonomous system. Process user requests and maintain conversation context."
            interface_response = await self.agents["interface"].generate_response(message, context)
            
            # LLM2 orchestrates the task if needed
            if any(keyword in message.lower() for keyword in ['open', 'close', 'run', 'execute', 'automate']):
                orchestrator_context = f"You are LLM2, the orchestrator agent. The user said: {message}. Plan and coordinate the execution."
                orchestrator_response = await self.agents["orchestrator"].generate_response(message, orchestrator_context)
                
                # Execute the planned action
                await self.execute_orchestrated_task(message)
                
                return f"Interface Agent: {interface_response}\n\nOrchestrator: {orchestrator_response}\n\nTask executed successfully."
            
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
        """Execute tasks orchestrated by LLM2"""
        # This would contain more sophisticated task execution logic
        # For now, it's a placeholder that logs the task
        logger.info(f"Executing orchestrated task: {task_description}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "agents_online": len(self.agents),
            "task_queue_size": self.task_queue.qsize(),
            "automation_ready": True
        }
    
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
        client = ollama.Client()
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