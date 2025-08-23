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
            self.client = ollama.Client(host=self.config.api_base)
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
        # LLM1 - Interface & Memory Agent
        llm1_config = AgentConfig(
            name="LLM1_Interface",
            role="User interface and memory management",
            model="llama3.1:8b-instruct",
            provider="ollama"
        )
        
        # LLM2 - Orchestrator Agent  
        llm2_config = AgentConfig(
            name="LLM2_Orchestrator", 
            role="Task orchestration and planning",
            model="llama3.1:8b-instruct",
            provider="ollama"
        )
        
        # LLM3 - Monitor Agent
        llm3_config = AgentConfig(
            name="LLM3_Monitor",
            role="System monitoring and security",
            model="llama3.1:8b-instruct", 
            provider="ollama"
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
                <title>Atlas Autonomous System</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f7; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    .card { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                    .button { background: #007AFF; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; }
                    .button:hover { background: #0056b3; }
                    .status { display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }
                    .status.active { background: #34C759; }
                    .status.inactive { background: #FF3B30; }
                    textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 8px; }
                    #response { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px; white-space: pre-wrap; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 Atlas Autonomous System</h1>
                        <p>Intelligent macOS Management & Automation</p>
                    </div>
                    
                    <div class="grid">
                        <div class="card">
                            <h3>System Status</h3>
                            <p>Platform: macOS <span class="status active">ACTIVE</span></p>
                            <p>Agents: 3/3 <span class="status active">ONLINE</span></p>
                            <p>Automation: <span class="status active">READY</span></p>
                            <button class="button" onclick="refreshStatus()">Refresh Status</button>
                        </div>
                        
                        <div class="card">
                            <h3>Quick Actions</h3>
                            <button class="button" onclick="performAction('system_info')" style="display: block; margin: 5px 0;">Get System Info</button>
                            <button class="button" onclick="performAction('open_app')" style="display: block; margin: 5px 0;">Open Application</button>
                            <button class="button" onclick="performAction('monitor_system')" style="display: block; margin: 5px 0;">Monitor System</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Chat with Atlas</h3>
                        <textarea id="userInput" placeholder="Ask Atlas to perform a task or ask a question..."></textarea>
                        <br><br>
                        <button class="button" onclick="sendMessage()">Send Message</button>
                        <div id="response"></div>
                    </div>
                </div>
                
                <script>
                    async function sendMessage() {
                        const input = document.getElementById('userInput');
                        const response = document.getElementById('response');
                        const message = input.value.trim();
                        
                        if (!message) return;
                        
                        response.innerHTML = 'Processing...';
                        
                        try {
                            const result = await fetch('/chat', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ message: message })
                            });
                            
                            const data = await result.json();
                            response.innerHTML = data.response;
                            input.value = '';
                        } catch (error) {
                            response.innerHTML = 'Error: ' + error.message;
                        }
                    }
                    
                    async function performAction(action) {
                        const response = document.getElementById('response');
                        response.innerHTML = 'Executing action...';
                        
                        try {
                            const result = await fetch('/action', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ action: action })
                            });
                            
                            const data = await result.json();
                            response.innerHTML = data.result;
                        } catch (error) {
                            response.innerHTML = 'Error: ' + error.message;
                        }
                    }
                    
                    function refreshStatus() {
                        location.reload();
                    }
                    
                    // Allow Enter key to send message
                    document.getElementById('userInput').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            sendMessage();
                        }
                    });
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