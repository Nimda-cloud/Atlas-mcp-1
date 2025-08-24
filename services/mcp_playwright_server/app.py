#!/usr/bin/env python3
"""
Playwright MCP Server
=====================

Minimal MCP-style HTTP server that exposes basic Playwright browser automation tools.
Endpoints:
- GET /health
- GET /tools
- POST /execute { tool: str, parameters: dict }

Tools:
- open_page { url }
- click { selector }
- fill { selector, text }
- eval { script }
- screenshot { path?, full_page? } -> returns { saved_to } or { image_base64 }
- get_title {}
- goto { url }    (alias of open_page)
- close {}
"""

import asyncio
import base64
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass
from typing import Any, Dict, Optional

from playwright.async_api import async_playwright, Browser, Page


@dataclass
class MCPTool:
    name: str
    description: str
    parameters: Dict[str, Any]


class PlaywrightMCP:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self.tools = {
            "open_page": MCPTool(
                name="open_page",
                description="Open a page by URL",
                parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
            ),
            "goto": MCPTool(
                name="goto",
                description="Navigate to URL (alias of open_page)",
                parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
            ),
            "click": MCPTool(
                name="click",
                description="Click an element by CSS selector",
                parameters={"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]},
            ),
            "fill": MCPTool(
                name="fill",
                description="Fill input/textarea",
                parameters={"type": "object", "properties": {"selector": {"type": "string"}, "text": {"type": "string"}}, "required": ["selector", "text"]},
            ),
            "eval": MCPTool(
                name="eval",
                description="Evaluate JavaScript in the page context",
                parameters={"type": "object", "properties": {"script": {"type": "string"}}, "required": ["script"]},
            ),
            "screenshot": MCPTool(
                name="screenshot",
                description="Take a screenshot",
                parameters={"type": "object", "properties": {"path": {"type": "string"}, "full_page": {"type": "boolean", "default": False}},},
            ),
            "get_title": MCPTool(
                name="get_title",
                description="Get current page title",
                parameters={"type": "object", "properties": {}},
            ),
            "close": MCPTool(
                name="close",
                description="Close the browser",
                parameters={"type": "object", "properties": {}},
            ),
        }

    async def _ensure_page(self):
        if self._browser is None:
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=self.headless)
        if self._page is None:
            context = await self._browser.new_context()
            self._page = await context.new_page()

    async def handle(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool not in self.tools:
            raise ValueError(f"Unknown tool: {tool}")

        # Tools that don't need a page
        if tool == "close":
            if self._page:
                await self._page.context.close()
                self._page = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            return {"closed": True}

        if tool in ("open_page", "goto", "click", "fill", "eval", "screenshot", "get_title"):
            await self._ensure_page()

        if tool in ("open_page", "goto"):
            assert self._page is not None
            url = params["url"]
            resp = await self._page.goto(url)
            return {"status": resp.status if resp else 0, "url": self._page.url}

        if tool == "click":
            assert self._page is not None
            await self._page.click(params["selector"])
            return {"clicked": params["selector"]}

        if tool == "fill":
            assert self._page is not None
            await self._page.fill(params["selector"], params["text"])
            return {"filled": params["selector"]}

        if tool == "eval":
            assert self._page is not None
            script = params["script"]
            result = await self._page.evaluate(script)
            return {"result": result}

        if tool == "screenshot":
            assert self._page is not None
            path = params.get("path")
            full_page = bool(params.get("full_page", False))
            if path:
                await self._page.screenshot(path=path, full_page=full_page)
                return {"saved_to": path}
            else:
                buf = await self._page.screenshot(full_page=full_page)
                return {"image_base64": base64.b64encode(buf).decode("ascii")}

        if tool == "get_title":
            assert self._page is not None
            return {"title": await self._page.title()}

        raise ValueError(f"Unhandled tool: {tool}")


class Handler(BaseHTTPRequestHandler):
    def __init__(self, server: PlaywrightMCP, *args, **kwargs):
        self.server_impl = server
        super().__init__(*args, **kwargs)

    def _send(self, code: int, data: Dict[str, Any]):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "healthy", "tools": list(self.server_impl.tools.keys())})
        elif self.path == "/tools":
            tools = {name: {"description": t.description, "parameters": t.parameters} for name, t in self.server_impl.tools.items()}
            self._send(200, tools)
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/execute":
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
            tool = payload.get("tool")
            params = payload.get("parameters", {})

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.server_impl.handle(tool, params))
            finally:
                loop.close()

            self._send(200, {"success": True, "result": result})
        except Exception as e:
            self._send(500, {"success": False, "error": str(e)})


from typing import Any, cast

def create_handler(server: PlaywrightMCP):
    def _handler(*args: Any, **kwargs: Any) -> None:
        Handler(server, *args, **kwargs)
    return cast(Any, _handler)


def main():
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "4005"))
    headless = os.getenv("PW_HEADLESS", "true").lower() != "false"
    impl = PlaywrightMCP(headless=headless)
    httpd = HTTPServer((host, port), create_handler(impl))
    print(f"🎭 Playwright MCP listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
