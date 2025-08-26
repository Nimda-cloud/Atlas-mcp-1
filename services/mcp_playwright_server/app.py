#!/usr/bin/env python3
"""
Enhanced Playwright MCP Server
==============================

Повноцінний MCP-сумісний сервер з розширеним набором інструментів Playwright.
Підтримує офіційний MCP протокол та має більше можливостей браузерної автоматизації.

Endpoints:
- GET /health - перевірка здоров'я
- POST /execute - виконання інструментів
- GET /tools - список доступних інструментів

Інструменти (15 total):
Навігація:
- open_page, goto - відкрити/перейти на URL
- wait_for - чекати елемент

Взаємодія:
- click - клік по елементу
- hover - ховер над елементом  
- fill - заповнити поле
- select - вибрати опцію
- keyboard - натиснути клавіші
- scroll - прокрутити

Отримання даних:
- get_title - заголовок сторінки
- get_text - текст елементу
- get_attribute - атрибут елементу
- screenshot - скріншот
- eval - виконати JavaScript

Управління:
- close - закрити браузер
"""

import asyncio
import base64
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

try:
    from playwright.async_api import async_playwright, Browser, Page  # type: ignore
except ImportError:
    # For local development when playwright might not be installed
    async_playwright = None  # type: ignore
    Browser = None  # type: ignore
    Page = None  # type: ignore


@dataclass
class MCPTool:
    name: str
    description: str
    parameters: Dict[str, Any]


class EnhancedPlaywrightMCP:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser: Optional[Any] = None  # type: ignore
        self._page: Optional[Any] = None  # type: ignore
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
            "hover": MCPTool(
                name="hover",
                description="Hover over an element by CSS selector",
                parameters={"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]},
            ),
            "select": MCPTool(
                name="select",
                description="Select option from SELECT element",
                parameters={"type": "object", "properties": {"selector": {"type": "string"}, "value": {"type": "string"}}, "required": ["selector", "value"]},
            ),
            "wait_for": MCPTool(
                name="wait_for",
                description="Wait for element to appear or disappear",
                parameters={"type": "object", "properties": {"selector": {"type": "string"}, "state": {"type": "string", "enum": ["visible", "hidden"], "default": "visible"}, "timeout": {"type": "number", "default": 30000}}, "required": ["selector"]},
            ),
            "keyboard": MCPTool(
                name="keyboard",
                description="Press keyboard keys",
                parameters={"type": "object", "properties": {"key": {"type": "string"}, "modifiers": {"type": "array", "items": {"type": "string"}}}, "required": ["key"]},
            ),
            "get_text": MCPTool(
                name="get_text",
                description="Get text content of element",
                parameters={"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]},
            ),
            "get_attribute": MCPTool(
                name="get_attribute",
                description="Get attribute value of element",
                parameters={"type": "object", "properties": {"selector": {"type": "string"}, "attribute": {"type": "string"}}, "required": ["selector", "attribute"]},
            ),
            "scroll": MCPTool(
                name="scroll",
                description="Scroll page or element",
                parameters={"type": "object", "properties": {"selector": {"type": "string"}, "x": {"type": "number", "default": 0}, "y": {"type": "number", "default": 0}}, "required": []},
            ),
            "close": MCPTool(
                name="close",
                description="Close the browser",
                parameters={"type": "object", "properties": {}},
            ),
        }

    async def _ensure_page(self):
        if self._browser is None:
            pw = await async_playwright().start()  # type: ignore
            self._browser = await pw.chromium.launch(headless=self.headless)
        if self._page is None:
            context = await self._browser.new_context()  # type: ignore
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

        if tool in ("open_page", "goto", "click", "fill", "eval", "screenshot", "get_title", 
                   "hover", "select", "wait_for", "keyboard", "get_text", "get_attribute", "scroll"):
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

        if tool == "hover":
            assert self._page is not None
            await self._page.hover(params["selector"])
            return {"hovered": params["selector"]}

        if tool == "select":
            assert self._page is not None
            await self._page.select_option(params["selector"], params["value"])
            return {"selected": params["value"], "selector": params["selector"]}

        if tool == "wait_for":
            assert self._page is not None
            selector = params["selector"]
            state = params.get("state", "visible")
            timeout = params.get("timeout", 30000)
            
            if state == "visible":
                await self._page.wait_for_selector(selector, timeout=timeout)
            else:  # hidden
                await self._page.wait_for_selector(selector, state="hidden", timeout=timeout)
            return {"waited_for": selector, "state": state}

        if tool == "keyboard":
            assert self._page is not None
            key = params["key"]
            modifiers = params.get("modifiers", [])
            
            # Press modifiers first
            for modifier in modifiers:
                await self._page.keyboard.down(modifier)
            
            # Press main key
            await self._page.keyboard.press(key)
            
            # Release modifiers
            for modifier in reversed(modifiers):
                await self._page.keyboard.up(modifier)
                
            return {"pressed": key, "modifiers": modifiers}

        if tool == "get_text":
            assert self._page is not None
            text = await self._page.text_content(params["selector"])
            return {"text": text or ""}

        if tool == "get_attribute":
            assert self._page is not None
            value = await self._page.get_attribute(params["selector"], params["attribute"])
            return {"attribute": params["attribute"], "value": value}

        if tool == "scroll":
            assert self._page is not None
            selector = params.get("selector")
            x = params.get("x", 0)
            y = params.get("y", 0)
            
            if selector:
                # Scroll element
                await self._page.locator(params["selector"]).scroll_into_view_if_needed()
                return {"scrolled": "element", "selector": selector}
            else:
                # Scroll page
                await self._page.evaluate(f"window.scrollBy({x}, {y})")
                return {"scrolled": "page", "x": x, "y": y}

        raise ValueError(f"Unhandled tool: {tool}")


class Handler(BaseHTTPRequestHandler):
    def __init__(self, server: EnhancedPlaywrightMCP, *args, **kwargs):
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

def create_handler(server: EnhancedPlaywrightMCP):
    def _handler(*args: Any, **kwargs: Any) -> None:
        Handler(server, *args, **kwargs)
    return cast(Any, _handler)


def main():
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "4005"))
    headless = os.getenv("PW_HEADLESS", "true").lower() != "false"
    impl = EnhancedPlaywrightMCP(headless=headless)
    httpd = HTTPServer((host, port), create_handler(impl))
    print(f"🎭 Enhanced Playwright MCP listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
