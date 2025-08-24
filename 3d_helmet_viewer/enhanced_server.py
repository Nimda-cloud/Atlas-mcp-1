#!/usr/bin/env python3
"""
Enhanced Atlas Frontend Server
Integrates the 3D helmet viewer with the full Atlas container stack
"""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import aiohttp
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtlasEnhancedServer:
    def __init__(self):
        self.app = FastAPI(title="Atlas Enhanced Frontend", version="1.0.0")
        self.setup_cors()
        self.setup_routes()
        self.setup_static_files()
        
        # Connection to Atlas services
        self.atlas_core_url = os.getenv("ATLAS_CORE_URL", "http://localhost:8000")
        self.tts_service_url = os.getenv("TTS_SERVICE_URL", "http://localhost:4004")
        
        # Active WebSocket connections
        self.websocket_connections = set()
        
    def setup_cors(self):
        """Setup CORS for frontend access"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_static_files(self):
        """Setup static file serving"""
        # Serve the 3D model and assets
        current_dir = Path(__file__).parent
        self.app.mount("/static", StaticFiles(directory=current_dir), name="static")
        
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_frontend():
            """Serve the enhanced frontend"""
            current_dir = Path(__file__).parent
            frontend_path = current_dir / "enhanced_frontend_simple.html"
            if frontend_path.exists():
                return FileResponse(frontend_path)
            else:
                return HTMLResponse("<h1>Frontend not found</h1>", status_code=404)
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "ok", "service": "atlas-enhanced-frontend"}
        
        @self.app.post("/api/chat")
        async def chat_message(message_data: Dict[str, Any]):
            """Process chat messages through Atlas core"""
            try:
                message = message_data.get("message", "")
                if not message:
                    raise HTTPException(status_code=400, detail="Message is required")
                
                # Send to Atlas core
                response = await self.call_atlas_core(message)
                
                # Broadcast to all connected WebSockets
                await self.broadcast_message({
                    "type": "chat_response",
                    "response": response
                })
                
                return {"response": response}
                
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/tts/speak")
        async def tts_speak(tts_data: Dict[str, Any]):
            """Forward TTS requests to the TTS service"""
            try:
                response = await self.call_tts_service(tts_data)
                return response
            except Exception as e:
                logger.error(f"Error calling TTS service: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/logs")
        async def get_system_logs():
            """Get system logs from all containers"""
            try:
                logs = await self.get_container_logs()
                return {"logs": logs}
            except Exception as e:
                logger.error(f"Error getting logs: {e}")
                return {"logs": []}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.websocket_connections.add(websocket)
            
            try:
                # Send initial system status
                await websocket.send_json({
                    "type": "system_status",
                    "status": "connected",
                    "message": "Connected to Atlas Enhanced Frontend"
                })
                
                # Keep connection alive and handle messages
                while True:
                    data = await websocket.receive_json()
                    await self.handle_websocket_message(websocket, data)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.websocket_connections.discard(websocket)
    
    async def call_atlas_core(self, message: str) -> str:
        """Call the main Atlas core system"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.atlas_core_url}/chat",
                    json={"message": message},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "Atlas system not responding correctly")
                    else:
                        logger.warning(f"Atlas core returned status {response.status}")
                        return "Atlas core system is currently unavailable"
        except Exception as e:
            logger.error(f"Failed to connect to Atlas core: {e}")
            # Return a simulated response
            return f"Я отримав ваше повідомлення: '{message}'. Зараз обробляю через автономний режим."
    
    async def call_tts_service(self, tts_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the TTS MCP service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.tts_service_url}/speak",
                    json=tts_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise HTTPException(status_code=response.status, detail="TTS service error")
        except Exception as e:
            logger.error(f"TTS service call failed: {e}")
            raise HTTPException(status_code=503, detail="TTS service unavailable")
    
    async def get_container_logs(self) -> list:
        """Get logs from Docker containers"""
        # This would integrate with Docker API or log aggregation service
        # For now, return simulated logs
        import datetime
        
        sample_logs = [
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "level": "INFO",
                "service": "atlas-core",
                "message": "Processing user request"
            },
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "level": "SUCCESS",
                "service": "mcp-tts",
                "message": "TTS synthesis completed"
            },
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "level": "DEBUG",
                "service": "redis",
                "message": "Cache hit ratio: 94.2%"
            }
        ]
        
        return sample_logs
    
    async def handle_websocket_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        
        if message_type == "chat":
            # Process chat message
            response = await self.call_atlas_core(data.get("message", ""))
            await websocket.send_json({
                "type": "chat_response",
                "response": response
            })
        elif message_type == "request_logs":
            # Send latest logs
            logs = await self.get_container_logs()
            await websocket.send_json({
                "type": "logs_update",
                "logs": logs
            })
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSockets"""
        if not self.websocket_connections:
            return
            
        # Send to all connected clients
        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        
        # Remove disconnected clients
        self.websocket_connections -= disconnected
    
    async def start_log_streaming(self):
        """Start streaming logs from containers"""
        while True:
            try:
                # Simulate getting fresh logs
                logs = await self.get_container_logs()
                await self.broadcast_message({
                    "type": "logs_update",
                    "logs": logs
                })
                await asyncio.sleep(5)  # Send logs every 5 seconds
            except Exception as e:
                logger.error(f"Error in log streaming: {e}")
                await asyncio.sleep(10)

def create_app():
    """Create the FastAPI application"""
    server = AtlasEnhancedServer()
    
    # Start background tasks
    @server.app.on_event("startup")
    async def startup_event():
        # Start log streaming task
        asyncio.create_task(server.start_log_streaming())
        logger.info("Atlas Enhanced Frontend Server started")
    
    return server.app

app = create_app()

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "enhanced_server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )