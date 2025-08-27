#!/usr/bin/env python3
"""
Atlas Core (Simplified Direct-Orchestrator Mode)
================================================
Всі MCP інструменти (applescript, playwright, tts, orchestrator*) викликаються ТІЛЬКИ через HTTP сервер mcp-task-orchestrator (порт 4006).
Прибрано: proxy, автономні MCP endpoints, automation.
"""
import asyncio, os, time, re, platform, logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

try:
    import ollama  # type: ignore
except Exception:  # pragma: no cover
    ollama = None

ORCHESTRATOR_URL = os.getenv("ATLAS_ORCHESTRATOR_URL", "http://localhost:4006")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AtlasCore")


class LLMAgent:
    def __init__(self, model: str = "gpt-oss:latest", temperature: float = 0.7, max_tokens: int = 800):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None
        self._init_client()

    def _init_client(self):
        if ollama is None:
            logger.warning("Ollama not available")
            return
        base = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        if base and not str(base).startswith("http"):
            base = f"http://{base}"
        try:
            # Use synchronous client; we'll wrap calls in asyncio.to_thread
            self.client = ollama.Client(host=str(base))
        except Exception as e:
            logger.error(f"Init ollama failed: {e}")
            self.client = None

    async def generate(self, prompt: str, context: str = "") -> str:
        if self.client is None:
            return "(LLM недоступний)"
        full = f"{context}\n\nКористувач: {prompt}\nВідповідь:" if context else prompt
        try:
            client = self.client
            if client is None:
                return "(LLM клієнт не ініціалізований)"

            def _call(c=client):
                return c.generate(
                    model=self.model,
                    prompt=full,
                    options={"temperature": self.temperature, "num_predict": self.max_tokens}
                )
            resp = await asyncio.to_thread(_call, client)
            if isinstance(resp, dict):
                return resp.get("response", "") or resp.get("message", "")
            return str(resp)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "Помилка LLM"


class AtlasCore:
    def __init__(self):
        self.app = FastAPI(title="Atlas Core Simplified", version="0.3")
        self.interface_agent = LLMAgent()
        self.current_voice = "male"
        self.latency_stats: Dict[str, Dict[str, Any]] = {}
        self._latency_window = 200
        self._setup_http()

    # ---------------- HTTP Setup ----------------
    def _setup_http(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"], allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )
        self.REQUEST_COUNT = Counter("atlas_requests_total", "Total HTTP requests", ["method", "path", "status"])
        self.REQUEST_LATENCY = Histogram("atlas_request_latency_seconds", "Request latency", ["method", "path"])

        @self.app.middleware("http")
        async def metrics_mw(request, call_next):  # type: ignore
            start = time.perf_counter()
            status_code = 500
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            finally:
                self.REQUEST_COUNT.labels(request.method, request.url.path, status_code).inc()
                self.REQUEST_LATENCY.labels(request.method, request.url.path).observe(time.perf_counter() - start)

        @self.app.get("/")
        async def root():
            return {"message": "Atlas Core Simplified", "orchestrator": ORCHESTRATOR_URL}

        @self.app.get("/tools")
        async def tools():
            raw = await self._fetch_orchestrator_tools()
            return {"via": ORCHESTRATOR_URL, "tools": self._group_tools(raw)}

        @self.app.post("/call_tool")
        async def call_tool(req: Dict[str, Any]):
            name = req.get("name") or req.get("tool_name")
            if not name:
                raise HTTPException(400, "Missing tool name")
            return await self._orchestrator_call(name, req.get("parameters", {}))

        @self.app.post("/chat")
        async def chat(req: Dict[str, Any]):
            msg = req.get("message", "").strip()
            if not msg:
                return {"response": "Повідомлення порожнє"}
            ctx = "Ти - інтерфейс Atlas. Відповідай дуже коротко (1-2 речення) УКРАЇНСЬКОЮ. Якщо треба дія — скажи що передаєш завдання."  # noqa: E501
            raw = await self.interface_agent.generate(msg, ctx)
            return {"response": self._clean_response(raw)}

        @self.app.post("/tts")
        async def tts(req: Dict[str, Any]):
            text = req.get("text", "").strip()
            if not text:
                return {"success": False, "error": "empty text"}
            return await self._orchestrator_call("say_tts", {"text": text, "voice": self.current_voice})

        @self.app.get("/status")
        async def status():
            raw = await self._fetch_orchestrator_tools()
            grouped = self._group_tools(raw)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "platform": platform.system(),
                "orchestrator": ORCHESTRATOR_URL,
                "groups": list(grouped.keys()),
                "tool_count": sum(len(v) for v in grouped.values())
            }

        @self.app.get("/metrics")
        async def metrics():  # prometheus scrape
            from fastapi import Response
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # ---------------- Internal helpers ----------------
    async def _fetch_orchestrator_tools(self) -> List[Dict[str, Any]]:
        url = f"{ORCHESTRATOR_URL}/tools"
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("tools", []) if isinstance(data, dict) else []
        except Exception as e:  # pragma: no cover
            logger.warning(f"Cannot fetch tools: {e}")
        return [
            {"name": "orchestrator_plan_task"},
            {"name": "orchestrator_execute_task"},
            {"name": "say_tts"},
            {"name": "run_applescript"},
            {"name": "browserNavigate"},
        ]

    def _group_tools(self, tools: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        groups: Dict[str, List[str]] = {"task-orchestrator": [], "applescript": [], "playwright": [], "tts": []}
        for t in tools:
            name = t.get("name", "")
            if not name:
                continue
            if name.startswith("orchestrator_"):
                groups["task-orchestrator"].append(name)
            elif name.startswith("browser") or name.startswith("page"):
                groups["playwright"].append(name)
            elif name in ("say_tts", "stop_tts"):
                groups["tts"].append(name)
            elif name.startswith("run_applescript") or name.startswith("system_") or "applescript" in name:
                groups["applescript"].append(name)
        return {k: v for k, v in groups.items() if v}

    async def _orchestrator_call(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{ORCHESTRATOR_URL}/call_tool"
        start = time.perf_counter()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.post(url, json={"name": tool, "parameters": params}) as resp:
                    result = await resp.json()
                    self._record_latency(tool.split('_')[0], start, error=not result or result.get("success") is False)
                    return result
        except Exception as e:
            logger.error(f"Tool call failed {tool}: {e}")
            self._record_latency(tool.split('_')[0], start, error=True, last_error=str(e))
            return {"success": False, "error": str(e), "tool": tool}

    def _record_latency(self, service: str, start: float, error: bool, last_error: Optional[str] = None):
        elapsed_ms = (time.perf_counter() - start) * 1000
        stats = self.latency_stats.get(service)
        if not stats:
            from collections import deque
            stats = {
                "calls": 0, "errors": 0, "total_ms": 0.0, "last_ms": 0.0,
                "samples": deque(maxlen=self._latency_window), "ema_ms": elapsed_ms,
                "since": datetime.utcnow().isoformat(), "last_error": None
            }
            self.latency_stats[service] = stats
        stats["calls"] += 1
        if error:
            stats["errors"] += 1
            stats["last_error"] = last_error
        stats["total_ms"] += elapsed_ms
        stats["last_ms"] = elapsed_ms
        stats["samples"].append(elapsed_ms)
        stats["ema_ms"] = stats["ema_ms"] * 0.8 + elapsed_ms * 0.2

    def _clean_response(self, txt: str) -> str:
        cleaned = re.sub(r'^(Atlas Interface:|Interface Agent:|Atlas:|LLM1:|Assistant:)\s*', '', txt.strip())
        return re.sub(r'\s+', ' ', cleaned).strip() or "(порожньо)"

    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


def main():
    logger.info("Starting simplified Atlas Core (orchestrator-only mode)")
    core = AtlasCore()
    asyncio.run(core.run())


if __name__ == "__main__":
    main()