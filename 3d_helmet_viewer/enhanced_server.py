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
try:
    import docker  # type: ignore
except Exception:  # pragma: no cover
    docker = None
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
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

        # Docker client for real-time logs (optional)
        self.docker_client = None
        self.enabled_services = (
            os.getenv(
                "LOG_SERVICES",
                "atlas,atlas-,mcp-,redis,qdrant,prometheus,grafana"
            ).split(",")
        )
        if docker is not None and os.path.exists("/var/run/docker.sock"):
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized for log streaming")
            except Exception as e:
                logger.warning(f"Docker client not available: {e}")
        
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

        @self.app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            # Small transparent favicon to avoid 404 noise
            return Response(content=b"", media_type="image/x-icon", status_code=204)
        
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
                # Graceful fallback so UI can continue with browser TTS
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "fallback",
                        "provider": "browser",
                        "message": "TTS service unavailable, using browser TTS"
                    }
                )
        
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
        """Get logs from Docker containers using Docker SDK if available, else fallback."""
        import datetime
        entries: list[Dict[str, Any]] = []

        if self.docker_client is None:
            # Fallback sample logs
            now = datetime.datetime.now().isoformat()
            return [
                {"timestamp": now, "level": "INFO", "service": "atlas-core", "message": "Processing user request"},
                {"timestamp": now, "level": "SUCCESS", "service": "mcp-tts", "message": "TTS synthesis completed"},
                {"timestamp": now, "level": "DEBUG", "service": "redis", "message": "Cache hit ratio: 94.2%"},
            ]

        # Collect recent logs from matching containers
        try:
            containers = self.docker_client.containers.list(all=False)
            patterns = tuple(s.strip() for s in self.enabled_services if s.strip())

            def include_container(name: str) -> bool:
                if not patterns:
                    return True
                for p in patterns:
                    if not p:
                        continue
                    # exact or prefix match
                    if name == p or name.startswith(p):
                        return True
                return False

            for c in containers:
                # name may include leading '/' in attrs; prefer Names list
                cname = None
                try:
                    if c.name:
                        cname = c.name
                except Exception:
                    pass
                if not cname:
                    try:
                        names = c.attrs.get("Name") or c.attrs.get("Names")
                        if isinstance(names, list) and names:
                            cname = names[0].lstrip("/")
                        elif isinstance(names, str):
                            cname = names.lstrip("/")
                    except Exception:
                        pass
                if not cname:
                    continue

                if not include_container(cname):
                    continue

                try:
                    raw = c.logs(tail=20, stdout=True, stderr=True, timestamps=True)
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="replace")
                    for line in raw.splitlines():
                        ts = None
                        msg = line
                        # If timestamps=True, Docker prepends RFC3339 timestamp
                        if len(line) > 20 and line[4] == '-':
                            # naive split on first space
                            parts = line.split(" ", 1)
                            if len(parts) == 2:
                                ts, msg = parts[0], parts[1]
                        # Try to guess level
                        lvl = "INFO"
                        up = msg.upper()
                        for cand in (" ERROR ", "[ERROR]", " ERROR:", " ERR "):
                            if cand in up:
                                lvl = "ERROR"
                                break
                        else:
                            for cand in (" WARN ", "[WARN]", " WARNING", " WARN:"):
                                if cand in up:
                                    lvl = "WARNING"
                                    break
                            else:
                                for cand in (" DEBUG ", "[DEBUG]", " DBG "):
                                    if cand in up:
                                        lvl = "DEBUG"
                                        break
                                else:
                                    for cand in (" SUCCESS ", "[SUCCESS]", " OK "):
                                        if cand in up:
                                            lvl = "SUCCESS"
                                            break

                        entries.append({
                            "timestamp": ts or datetime.datetime.now().isoformat(),
                            "level": lvl,
                            "service": cname,
                            "message": msg.rstrip()
                        })
                except Exception as e:
                    logger.debug(f"Failed to get logs for {cname}: {e}")

            # Keep only the latest ~100 entries
            entries = entries[-100:]
            return entries
        except Exception as e:
            logger.warning(f"Docker log collection failed, using fallback: {e}")
            now = datetime.datetime.now().isoformat()
            return [
                {"timestamp": now, "level": "INFO", "service": "atlas-core", "message": "(fallback) No Docker logs available"}
            ]
    
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
    # Run the server; if uvicorn reload fails (e.g., no watchdog), run without reload
    try:
        uvicorn.run(
            "enhanced_server:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info"
        )
    except Exception:
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")