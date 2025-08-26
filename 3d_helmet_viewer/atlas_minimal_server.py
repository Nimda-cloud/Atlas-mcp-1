#!/usr/bin/env python3
"""
Atlas Minimal Frontend Server
Мінімалістичний хакерський інтерфейс для Atlas з 3D viewer у фоні
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import aiohttp
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AtlasMinimalServer:
    def __init__(self):
        self.app = FastAPI(title="Atlas Minimal Frontend")
        self.setup_routes()
        
        # MCP Proxy endpoints
        self.mcp_proxy_url = "http://localhost:4010"
        self.atlas_core_url = "http://localhost:8000"
        
        # WebSocket connections for real-time logs
        self.websocket_connections = set()
        
        # Start background tasks
        asyncio.create_task(self.log_monitor())

    def setup_routes(self):
        """Налаштування маршрутів"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_frontend():
            """Головна сторінка з мінімалістичним інтерфейсом"""
            html_path = Path(__file__).parent / "atlas_minimal_frontend.html"
            return FileResponse(html_path)
        
        @self.app.get("/DamagedHelmet.glb")
        async def serve_3d_model():
            """3D модель шолома"""
            model_path = Path(__file__).parent / "DamagedHelmet.glb"
            if model_path.exists():
                return FileResponse(model_path)
            else:
                return JSONResponse({"error": "3D model not found"}, status_code=404)
        
        @self.app.post("/api/chat")
        async def chat_endpoint(request: Request):
            """Чат з Atlas через MCP proxy або Atlas Core"""
            try:
                data = await request.json()
                message = data.get("message", "")
                
                if not message:
                    return JSONResponse({"error": "Message is required"}, status_code=400)
                
                # Спробувати MCP proxy спочатку
                response = await self.send_to_mcp_proxy(message)
                if response:
                    await self.broadcast_log(f"[MCP] User: {message[:50]}...")
                    await self.broadcast_log(f"[MCP] Response: {response[:50]}...")
                    return JSONResponse({"response": response})
                
                # Fallback на Atlas Core
                response = await self.send_to_atlas_core(message)
                if response:
                    await self.broadcast_log(f"[ATLAS] User: {message[:50]}...")
                    await self.broadcast_log(f"[ATLAS] Response: {response[:50]}...")
                    return JSONResponse({"response": response})
                
                await self.broadcast_log("[ERROR] All services unavailable", "error")
                return JSONResponse({"response": "Всі сервіси недоступні"})
                
            except Exception as e:
                logger.error(f"Chat error: {e}")
                await self.broadcast_log(f"[ERROR] Chat: {str(e)}", "error")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.post("/api/tts/speak")
        async def tts_endpoint(request: Request):
            """TTS через MCP proxy"""
            try:
                data = await request.json()
                text = data.get("text", "")
                
                if not text:
                    return JSONResponse({"error": "Text is required"}, status_code=400)
                
                # Спробувати через MCP proxy
                success = await self.send_tts_request(text)
                
                if success:
                    await self.broadcast_log(f"[TTS] Generated audio for: {text[:30]}...")
                    return JSONResponse({"status": "success"})
                else:
                    await self.broadcast_log("[TTS] Service unavailable", "warning")
                    return JSONResponse({"error": "TTS service unavailable"}, status_code=503)
                
            except Exception as e:
                logger.error(f"TTS error: {e}")
                await self.broadcast_log(f"[ERROR] TTS: {str(e)}", "error")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.websocket("/ws/logs")
        async def websocket_logs(websocket: WebSocket):
            """WebSocket для real-time логів"""
            await websocket.accept()
            self.websocket_connections.add(websocket)
            
            try:
                await websocket.send_text(json.dumps({
                    "type": "log",
                    "message": "[SYSTEM] WebSocket connected",
                    "level": "info",
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Тримати з'єднання відкритим
                while True:
                    await websocket.receive_text()
                    
            except WebSocketDisconnect:
                self.websocket_connections.discard(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.websocket_connections.discard(websocket)
        
        @self.app.get("/api/health")
        async def health_check():
            """Перевірка стану сервісів"""
            services = {
                "atlas_minimal": True,
                "mcp_proxy": await self.check_mcp_proxy(),
                "atlas_core": await self.check_atlas_core(),
                "timestamp": datetime.now().isoformat()
            }
            return JSONResponse(services)

    async def send_to_mcp_proxy(self, message: str) -> Optional[str]:
        """Відправлення повідомлення через MCP proxy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_proxy_url}/api/chat",
                    json={"message": message},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", data.get("message"))
        except Exception as e:
            logger.debug(f"MCP proxy request failed: {e}")
        return None

    async def send_to_atlas_core(self, message: str) -> Optional[str]:
        """Відправлення повідомлення до Atlas Core"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.atlas_core_url}/api/chat",
                    json={"message": message},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", data.get("message"))
        except Exception as e:
            logger.debug(f"Atlas Core request failed: {e}")
        return None

    async def send_tts_request(self, text: str) -> bool:
        """TTS запит через MCP proxy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_proxy_url}/api/tts",
                    json={"text": text},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.debug(f"TTS request failed: {e}")
        return False

    async def check_mcp_proxy(self) -> bool:
        """Перевірка MCP proxy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_proxy_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status < 500
        except:
            return False

    async def check_atlas_core(self) -> bool:
        """Перевірка Atlas Core"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.atlas_core_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status < 500
        except:
            return False

    async def broadcast_log(self, message: str, level: str = "info"):
        """Розсилання логів через WebSocket"""
        if not self.websocket_connections:
            return
        
        log_data = {
            "type": "log",
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(log_data))
            except:
                disconnected.add(websocket)
        
        # Видалити відключені з'єднання
        self.websocket_connections -= disconnected

    async def log_monitor(self):
        """Моніторинг системи та генерація логів"""
        await asyncio.sleep(2)  # Дати час для ініціалізації
        
        while True:
            try:
                # Перевірка сервісів
                mcp_online = await self.check_mcp_proxy()
                atlas_online = await self.check_atlas_core()
                
                if mcp_online:
                    await self.broadcast_log("[MCP] Proxy operational")
                else:
                    await self.broadcast_log("[MCP] Proxy offline", "warning")
                
                if atlas_online:
                    await self.broadcast_log("[ATLAS] Core operational")
                else:
                    await self.broadcast_log("[ATLAS] Core offline", "warning")
                
                # Системна інформація
                await self.broadcast_log(f"[SYSTEM] Connections: {len(self.websocket_connections)}")
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Log monitor error: {e}")
                await asyncio.sleep(5)

def main():
    """Запуск сервера"""
    server = AtlasMinimalServer()
    
    print("🚀 Starting Atlas Minimal Frontend Server...")
    print("📱 Interface: http://localhost:8080")
    print("💾 3D Viewer: Background layer")
    print("📋 MCP Logs: Left panel")
    print("💬 Chat: Right panel")
    print("🎤 Voice: Single/Double click modes")
    
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )

if __name__ == "__main__":
    main()
