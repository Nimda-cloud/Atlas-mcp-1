#!/usr/bin/env python3
"""
Enhanced Atlas Frontend Server - Native MCP Version
Integrates with native MCP protocol via TBXark proxy
"""
import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import aiohttp
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPEnhancedServer:
    def __init__(self):
        self.app = FastAPI(title="Atlas Enhanced Frontend - MCP Native", version="2.0.0")
        self.setup_cors()
        self.setup_routes()
        self.setup_static_files()
        
        # MCP Proxy configuration
        self.mcp_proxy_url = os.getenv("MCP_PROXY_URL", "http://localhost:4010")
        self.atlas_core_url = os.getenv("ATLAS_CORE_URL", "http://localhost:8000")
        
        # Available MCP tools cache
        self.mcp_tools_cache = {}
        self.websocket_connections = set()
        
        # MCP tool mappings
        self.tool_mappings = {
            "tts": {
                "elevenlabs_tts": "elevenlabs",
                "google_tts": "google",
                "openai_tts": "openai", 
                "say_tts": "system"
            },
            "automation": {
                "mouseClick": "mouse_click",
                "screenshot": "take_screenshot",
                "keyControl": "key_press",
                "getActiveWindow": "get_active_window"
            }
        }
        
    def setup_cors(self):
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_static_files(self):
        """Setup static file serving"""
        # Serve the 3D viewer and other static files
        static_dir = Path(__file__).parent
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            """Serve the enhanced frontend HTML"""
            frontend_file = Path(__file__).parent / "enhanced_frontend.html"
            if frontend_file.exists():
                return FileResponse(frontend_file)
            else:
                return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Atlas Enhanced Frontend - MCP Native</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #00ff00; }
                        .container { max-width: 800px; margin: 0 auto; }
                        .status { padding: 20px; border: 1px solid #00ff00; margin: 20px 0; }
                        .tools-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
                        .tool-card { padding: 15px; border: 1px solid #333; background: #2a2a2a; }
                        button { background: #00ff00; color: #000; border: none; padding: 10px 20px; cursor: pointer; }
                        input, textarea { background: #333; color: #00ff00; border: 1px solid #555; padding: 8px; width: 100%; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Atlas Enhanced Frontend - MCP Native</h1>
                        <div class="status" id="status">Loading MCP status...</div>
                        
                        <h2>Available MCP Tools</h2>
                        <div class="tools-grid" id="toolsGrid">Loading tools...</div>
                        
                        <h2>Chat з Atlas</h2>
                        <div>
                            <textarea id="chatInput" placeholder="Введіть ваше повідомлення... (Ctrl+Enter для відправки)" rows="3" style="width: 100%; margin-bottom: 10px;" onkeydown="handleChatKeyPress(event)"></textarea>
                            <button onclick="sendChatMessage()">Відправити повідомлення</button>
                            <div id="chatResponse" style="margin-top: 10px; padding: 10px; background: #2a2a2a; border: 1px solid #555;"></div>
                        </div>
                        
                        <h2>Test TTS</h2>
                        <div>
                            <input type="text" id="ttsText" placeholder="Enter text to speak..." value="Hello from MCP TTS">
                            <select id="ttsProvider">
                                <option value="say_tts">System TTS</option>
                                <option value="google_tts">Google TTS</option>
                                <option value="openai_tts">OpenAI TTS</option>
                                <option value="elevenlabs_tts">ElevenLabs TTS</option>
                            </select>
                            <button onclick="testTTS()">Speak</button>
                        </div>
                        
                        <h2>Test Automation</h2>
                        <div>
                            <button onclick="takeScreenshot()">Take Screenshot</button>
                            <button onclick="getActiveWindow()">Get Active Window</button>
                        </div>
                        
                        <h2>Live Logs</h2>
                        <div>
                            <button onclick="loadLogs()">Оновити логи</button>
                            <button onclick="clearLogs()">Очистити</button>
                        </div>
                        <div id="logs" style="height: 300px; overflow-y: scroll; background: #000; padding: 10px; font-family: monospace;"></div>
                    </div>
                    
                    <script>
                        const ws = new WebSocket('ws://localhost:8080/ws');
                        
                        ws.onmessage = function(event) {
                            const data = JSON.parse(event.data);
                            console.log('WebSocket message:', data);
                            
                            if (data.type === 'log') {
                                addLog(data.message);
                            } else if (data.type === 'mcp_tools') {
                                updateToolsGrid(data.tools);
                            } else if (data.type === 'status') {
                                updateStatus(data.status);
                            }
                        };
                        
                        function addLog(message) {
                            const logs = document.getElementById('logs');
                            const timestamp = new Date().toLocaleTimeString();
                            logs.innerHTML += `[${timestamp}] ${message}\n`;
                            logs.scrollTop = logs.scrollHeight;
                        }
                        
                        function updateStatus(status) {
                            document.getElementById('status').innerHTML = 
                                `<strong>MCP Proxy:</strong> ${status.proxy_status}<br>
                                 <strong>Tools Available:</strong> ${status.tools_count}<br>
                                 <strong>Last Update:</strong> ${new Date().toLocaleString()}`;
                        }
                        
                        function updateToolsGrid(tools) {
                            const grid = document.getElementById('toolsGrid');
                            grid.innerHTML = '';
                            
                            Object.entries(tools).forEach(([namespace, toolList]) => {
                                const card = document.createElement('div');
                                card.className = 'tool-card';
                                card.innerHTML = `
                                    <h3>${namespace.toUpperCase()}</h3>
                                    <ul>
                                        ${toolList.map(tool => `<li>${tool}</li>`).join('')}
                                    </ul>
                                `;
                                grid.appendChild(card);
                            });
                        }
                        
                        function handleChatKeyPress(event) {
                            // Ctrl+Enter або Cmd+Enter для відправки
                            if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                                event.preventDefault();
                                sendChatMessage();
                            }
                        }
                        
                        async function sendChatMessage() {
                            const input = document.getElementById('chatInput');
                            const responseDiv = document.getElementById('chatResponse');
                            const message = input.value.trim();
                            
                            if (!message) {
                                alert('Будь ласка, введіть повідомлення');
                                return;
                            }
                            
                            responseDiv.innerHTML = 'Відправляю повідомлення...';
                            addLog(`Користувач: ${message}`);
                            
                            try {
                                const response = await fetch('/api/chat', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({message: message})
                                });
                                const result = await response.json();
                                responseDiv.innerHTML = `<strong>Atlas:</strong> ${result.response}`;
                                addLog(`Atlas: ${result.response}`);
                                input.value = '';
                            } catch (error) {
                                responseDiv.innerHTML = `<strong>Помилка:</strong> ${error.message}`;
                                addLog(`Помилка чату: ${error.message}`);
                            }
                        }
                        
                        async function testTTS() {
                            const text = document.getElementById('ttsText').value;
                            const provider = document.getElementById('ttsProvider').value;
                            
                            if (!text.trim()) {
                                alert('Будь ласка, введіть текст для озвучення');
                                return;
                            }
                            
                            addLog(`Початок TTS: ${provider} - "${text}"`);
                            
                            try {
                                // Використовуємо новий MCP API
                                const response = await fetch('/api/mcp/tts', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({tool: provider, text: text})
                                });
                                const result = await response.json();
                                
                                if (result.status === 'success') {
                                    addLog(`TTS успішно: ${JSON.stringify(result.result)}`);
                                } else if (result.status === 'error' && result.error.includes('HTTP 202')) {
                                    addLog(`TTS прийнято до обробки (асинхронно)`);
                                } else {
                                    addLog(`TTS помилка: ${result.error || JSON.stringify(result)}`);
                                }
                            } catch (error) {
                                addLog(`TTS виняток: ${error.message}`);
                            }
                        }
                        
                        async function takeScreenshot() {
                            try {
                                const response = await fetch('/api/mcp/automation', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({tool: 'screenshot'})
                                });
                                const result = await response.json();
                                addLog(`Screenshot: ${JSON.stringify(result)}`);
                            } catch (error) {
                                addLog(`Screenshot Error: ${error.message}`);
                            }
                        }
                        
                        async function getActiveWindow() {
                            try {
                                const response = await fetch('/api/mcp/automation', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({tool: 'getActiveWindow'})
                                });
                                const result = await response.json();
                                addLog(`Active Window: ${JSON.stringify(result)}`);
                            } catch (error) {
                                addLog(`Window Error: ${error.message}`);
                            }
                        }
                        
                        function clearLogs() {
                            document.getElementById('logs').innerHTML = '';
                        }
                        
                        async function loadLogs() {
                            try {
                                const response = await fetch('/api/logs');
                                const data = await response.json();
                                const logs = document.getElementById('logs');
                                logs.innerHTML = '';
                                data.logs.forEach(log => {
                                    logs.innerHTML += log + '\n';
                                });
                                logs.scrollTop = logs.scrollHeight;
                                addLog('Логи оновлено');
                            } catch (error) {
                                addLog(`Помилка завантаження логів: ${error.message}`);
                            }
                        }
                        
                        // Load initial data
                        fetch('/api/mcp/status').then(r => r.json()).then(data => updateStatus(data));
                        fetch('/api/mcp/tools').then(r => r.json()).then(data => updateToolsGrid(data));
                        
                        addLog('Enhanced Frontend MCP Native initialized');
                    </script>
                </body>
                </html>
                """)

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.websocket_connections.add(websocket)
            logger.info("WebSocket connection opened")
            
            try:
                # Send initial status
                await websocket.send_json({
                    "type": "status",
                    "status": await self.get_mcp_status()
                })
                
                # Send available tools
                await websocket.send_json({
                    "type": "mcp_tools", 
                    "tools": await self.get_mcp_tools()
                })
                
                while True:
                    # Keep connection alive and handle messages
                    data = await websocket.receive_json()
                    logger.info(f"WebSocket received: {data}")
                    
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                        
            except WebSocketDisconnect:
                self.websocket_connections.discard(websocket)
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.websocket_connections.discard(websocket)

        @self.app.get("/api/mcp/status")
        async def mcp_status():
            """Get MCP proxy status"""
            return await self.get_mcp_status()

        @self.app.get("/api/mcp/tools")  
        async def mcp_tools():
            """Get available MCP tools"""
            return await self.get_mcp_tools()

        @self.app.post("/api/mcp/tts")
        async def mcp_tts(request_data: Dict[str, Any]):
            """Call MCP TTS tools via SSE"""
            tool = request_data.get("tool", "say_tts")
            text = request_data.get("text", "Hello from MCP")
            
            return await self.call_mcp_tool_sse("tts", tool, {"text": text})

        @self.app.post("/api/mcp/automation")
        async def mcp_automation(request_data: Dict[str, Any]):
            """Call MCP automation tools via SSE"""
            tool = request_data.get("tool", "screenshot")
            args = request_data.get("args", {})
            
            return await self.call_mcp_tool_sse("automation", tool, args)

        @self.app.post("/api/tts/speak")
        async def tts_speak_legacy(request_data: Dict[str, Any]):
            """Legacy TTS endpoint for compatibility"""
            text = request_data.get("text", "Hello from MCP")
            provider = request_data.get("provider", "say_tts")
            
            # Redirect to MCP TTS
            return await self.call_mcp_tool_sse("tts", provider, {"text": text})

        @self.app.get("/api/logs")
        async def get_recent_logs():
            """Get recent system logs"""
            try:
                # Read last 50 lines from our log file
                log_file = Path(__file__).parent / "enhanced_frontend_mcp.log"
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-50:] if len(lines) > 50 else lines
                        return {"logs": [line.strip() for line in recent_lines]}
                else:
                    return {"logs": ["Лог файл не знайдено"]}
            except Exception as e:
                logger.error(f"Error reading logs: {e}")
                return {"logs": [f"Помилка читання логів: {str(e)}"]}

        @self.app.post("/api/chat")
        async def chat_message(message_data: Dict[str, Any]):
            """Process chat messages through Atlas Core with MCP tools"""
            try:
                message = message_data.get("message", "")
                if not message:
                    raise HTTPException(status_code=400, detail="Message is required")
                
                logger.info(f"Processing chat message: {message}")
                
                # Send to Atlas Core
                response = await self.call_atlas_core(message)
                
                logger.info(f"Atlas response: {response}")
                
                # Broadcast to WebSocket connections
                await self.broadcast_message({
                    "type": "chat_response",
                    "message": message,
                    "response": response
                })
                
                return {"response": response}
                
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def get_mcp_status(self) -> Dict[str, Any]:
        """Get MCP proxy status"""
        try:
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test MCP proxy health
                async with session.get(f"{self.mcp_proxy_url}/tts/sse") as resp:
                    if resp.status == 200:
                        tools = await self.get_mcp_tools()
                        total_tools = sum(len(tools_list) for tools_list in tools.values())
                        return {
                            "proxy_status": "connected",
                            "proxy_url": self.mcp_proxy_url,
                            "tools_count": total_tools,
                            "timestamp": time.time()
                        }
                    else:
                        return {
                            "proxy_status": "error",
                            "proxy_url": self.mcp_proxy_url,
                            "tools_count": 0,
                            "error": f"HTTP {resp.status}"
                        }
        except Exception as e:
            return {
                "proxy_status": "disconnected",
                "proxy_url": self.mcp_proxy_url,
                "tools_count": 0,
                "error": str(e)
            }

    async def get_mcp_tools(self) -> Dict[str, List[str]]:
        """Get available MCP tools from proxy"""
        if self.mcp_tools_cache:
            return self.mcp_tools_cache
            
        # For now, return known tools from our mappings
        tools = {
            "tts": list(self.tool_mappings["tts"].keys()),
            "automation": list(self.tool_mappings["automation"].keys())
        }
        
        self.mcp_tools_cache = tools
        return tools

    async def call_mcp_tool_sse(self, namespace: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via TBXark proxy SSE endpoint"""
        try:
            # Step 1: Get SSE session endpoint
            sse_url = f"{self.mcp_proxy_url}/{namespace}/sse"
            
            logger.info(f"Getting SSE endpoint for {namespace}/{tool}")
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Get the session endpoint
                async with session.get(
                    sse_url,
                    headers={"Accept": "text/event-stream"}
                ) as resp:
                    if resp.status != 200:
                        return {
                            "status": "error",
                            "tool": f"{namespace}/{tool}",
                            "error": f"Failed to get SSE endpoint: HTTP {resp.status}"
                        }
                    
                    # Read the first event to get the endpoint
                    session_endpoint = None
                    async for line in resp.content:
                        line_str = line.decode().strip()
                        if line_str.startswith('data: http'):
                            session_endpoint = line_str[6:]  # Remove 'data: ' prefix
                            break
                    
                    if not session_endpoint:
                        return {
                            "status": "error", 
                            "tool": f"{namespace}/{tool}",
                            "error": "No session endpoint received"
                        }
                    
                    logger.info(f"Got session endpoint: {session_endpoint}")
                    
                    # Step 2: Send the tool call request to session endpoint
                    request_payload = {
                        "method": "tools/call",
                        "params": {
                            "name": tool,
                            "arguments": args
                        }
                    }
                    
                    async with session.post(
                        session_endpoint,
                        json=request_payload,
                        headers={"Content-Type": "application/json"}
                    ) as tool_resp:
                        if tool_resp.status == 200:
                            result = await tool_resp.json()
                            logger.info(f"MCP tool result: {result}")
                            
                            # Broadcast to WebSocket connections
                            await self.broadcast_message({
                                "type": "log",
                                "message": f"MCP {namespace}/{tool}: {str(result)[:100]}..."
                            })
                            
                            return {
                                "status": "success",
                                "tool": f"{namespace}/{tool}",
                                "result": result
                            }
                        else:
                            error_text = await tool_resp.text()
                            logger.error(f"Tool call failed: HTTP {tool_resp.status}: {error_text}")
                            return {
                                "status": "error",
                                "tool": f"{namespace}/{tool}",
                                "error": f"HTTP {tool_resp.status}: {error_text}"
                            }
                        
        except Exception as e:
            logger.error(f"Exception calling MCP tool {namespace}/{tool}: {e}")
            return {
                "status": "exception",
                "tool": f"{namespace}/{tool}",
                "error": str(e)
            }

    async def call_atlas_core(self, message: str) -> str:
        """Call Atlas Core for chat processing"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.atlas_core_url}/chat",
                    json={"message": message},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "No response from Atlas Core")
                    else:
                        logger.warning(f"Atlas core returned status {response.status}")
                        return f"Atlas Core unavailable (HTTP {response.status})"
        except Exception as e:
            logger.error(f"Failed to connect to Atlas core: {e}")
            return f"Atlas Core connection failed: {str(e)}"

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all WebSocket connections"""
        if not self.websocket_connections:
            return
            
        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected connections
        self.websocket_connections -= disconnected

def main():
    """Main entry point"""
    logger.info("Starting Atlas Enhanced Frontend Server - MCP Native")
    
    server = MCPEnhancedServer()
    
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        server.app,
        host=host,
        port=port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
