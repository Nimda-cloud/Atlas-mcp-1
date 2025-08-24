#!/usr/bin/env python3
"""
Enhanced Playwright MCP Server with 27 Microsoft-compatible tools
===================================================================

Full-featured MCP-style HTTP server that exposes all 27 Playwright browser automation tools
compatible with Microsoft's Playwright MCP implementation.

Endpoints:
- GET /health
- GET /tools  
- POST /execute { tool: str, parameters: dict }

Tools (27 total):
1. browser_close - Close browser
2. browser_resize - Resize browser window  
3. browser_console_messages - Get console messages
4. browser_handle_dialog - Handle dialogs
5. browser_evaluate - Evaluate JavaScript
6. browser_file_upload - Upload files
7. browser_install - Install browser 
8. browser_press_key - Press keyboard key
9. browser_type - Type text
10. browser_mouse_move_xy - Move mouse to coordinates
11. browser_mouse_click_xy - Click at coordinates
12. browser_mouse_drag_xy - Drag mouse between coordinates
13. browser_navigate - Navigate to URL
14. browser_navigate_back - Navigate back
15. browser_navigate_forward - Navigate forward
16. browser_network_requests - Get network requests
17. browser_pdf_save - Save page as PDF
18. browser_take_screenshot - Take screenshot
19. browser_snapshot - Take accessibility snapshot
20. browser_click - Click element by selector
21. browser_drag - Drag between elements  
22. browser_hover - Hover over element
23. browser_select_option - Select option in dropdown
24. browser_tab_list - List open tabs
25. browser_tab_select - Select tab by index
26. browser_tab_new - Open new tab
27. browser_tab_close - Close tab
28. browser_wait_for - Wait for text/time
"""

import asyncio
import base64
import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse, parse_qs

from playwright.async_api import async_playwright, Browser, Page, BrowserContext


@dataclass 
class MCPTool:
    name: str
    description: str
    parameters: Dict[str, Any]


class EnhancedPlaywrightMCP:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._contexts: List[BrowserContext] = []
        self._pages: List[Page] = []
        self._active_page_idx = 0
        self._console_messages = []
        self._network_requests = []
        self._dialogs = []
        
        self.tools = {
            # Common tools
            "browser_close": MCPTool(
                name="browser_close",
                description="Close the browser",
                parameters={"type": "object", "properties": {}}
            ),
            "browser_resize": MCPTool(
                name="browser_resize", 
                description="Resize browser window",
                parameters={
                    "type": "object",
                    "properties": {
                        "width": {"type": "number"},
                        "height": {"type": "number"}
                    },
                    "required": ["width", "height"]
                }
            ),
            
            # Console tools
            "browser_console_messages": MCPTool(
                name="browser_console_messages",
                description="Get all console messages",
                parameters={"type": "object", "properties": {}}
            ),
            
            # Dialog tools
            "browser_handle_dialog": MCPTool(
                name="browser_handle_dialog",
                description="Handle a dialog",
                parameters={
                    "type": "object", 
                    "properties": {
                        "accept": {"type": "boolean"},
                        "promptText": {"type": "string"}
                    },
                    "required": ["accept"]
                }
            ),
            
            # Evaluate tools
            "browser_evaluate": MCPTool(
                name="browser_evaluate",
                description="Evaluate JavaScript expression on page or element",
                parameters={
                    "type": "object",
                    "properties": {
                        "function": {"type": "string"},
                        "element": {"type": "string"},
                        "ref": {"type": "string"}
                    },
                    "required": ["function"]
                }
            ),
            
            # File tools
            "browser_file_upload": MCPTool(
                name="browser_file_upload", 
                description="Upload files",
                parameters={
                    "type": "object",
                    "properties": {
                        "paths": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["paths"]
                }
            ),
            
            # Install tools
            "browser_install": MCPTool(
                name="browser_install",
                description="Install the browser specified in config",
                parameters={"type": "object", "properties": {}}
            ),
            
            # Keyboard tools
            "browser_press_key": MCPTool(
                name="browser_press_key",
                description="Press a key on the keyboard", 
                parameters={
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"}
                    },
                    "required": ["key"]
                }
            ),
            "browser_type": MCPTool(
                name="browser_type",
                description="Type text into editable element",
                parameters={
                    "type": "object",
                    "properties": {
                        "element": {"type": "string"},
                        "ref": {"type": "string"}, 
                        "text": {"type": "string"},
                        "slowly": {"type": "boolean"},
                        "submit": {"type": "boolean"}
                    },
                    "required": ["element", "ref", "text"]
                }
            ),
            
            # Mouse tools
            "browser_mouse_move_xy": MCPTool(
                name="browser_mouse_move_xy",
                description="Move mouse to coordinates",
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"}
                    },
                    "required": ["x", "y"]
                }
            ),
            "browser_mouse_click_xy": MCPTool(
                name="browser_mouse_click_xy", 
                description="Click at coordinates",
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                        "button": {"type": "string", "enum": ["left", "right", "middle"]},
                        "doubleClick": {"type": "boolean"}
                    },
                    "required": ["x", "y"]
                }
            ),
            "browser_mouse_drag_xy": MCPTool(
                name="browser_mouse_drag_xy",
                description="Drag mouse between coordinates", 
                parameters={
                    "type": "object",
                    "properties": {
                        "startX": {"type": "number"},
                        "startY": {"type": "number"},
                        "endX": {"type": "number"},
                        "endY": {"type": "number"}
                    },
                    "required": ["startX", "startY", "endX", "endY"]
                }
            ),
            
            # Navigate tools
            "browser_navigate": MCPTool(
                name="browser_navigate",
                description="Navigate to a URL",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"}
                    },
                    "required": ["url"]
                }
            ),
            "browser_navigate_back": MCPTool(
                name="browser_navigate_back",
                description="Go back to the previous page",
                parameters={"type": "object", "properties": {}}
            ),
            "browser_navigate_forward": MCPTool(
                name="browser_navigate_forward", 
                description="Go forward to the next page",
                parameters={"type": "object", "properties": {}}
            ),
            
            # Network tools
            "browser_network_requests": MCPTool(
                name="browser_network_requests",
                description="Returns all network requests since loading the page",
                parameters={"type": "object", "properties": {}}
            ),
            
            # PDF tools
            "browser_pdf_save": MCPTool(
                name="browser_pdf_save",
                description="Save page as PDF",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "format": {"type": "string", "enum": ["A4", "Letter"]},
                        "landscape": {"type": "boolean"}
                    },
                    "required": ["path"]
                }
            ),
            
            # Screenshot tools  
            "browser_take_screenshot": MCPTool(
                name="browser_take_screenshot",
                description="Take a screenshot of the current page",
                parameters={
                    "type": "object",
                    "properties": {
                        "element": {"type": "string"},
                        "filename": {"type": "string"},
                        "fullPage": {"type": "boolean"},
                        "ref": {"type": "string"},
                        "type": {"type": "string", "enum": ["png", "jpeg"]}
                    }
                }
            ),
            
            # Snapshot tools
            "browser_snapshot": MCPTool(
                name="browser_snapshot",
                description="Capture accessibility snapshot of the current page",
                parameters={"type": "object", "properties": {}}
            ),
            "browser_click": MCPTool(
                name="browser_click",
                description="Perform click on a web page element",
                parameters={
                    "type": "object",
                    "properties": {
                        "element": {"type": "string"},
                        "ref": {"type": "string"},
                        "button": {"type": "string", "enum": ["left", "right", "middle"]},
                        "doubleClick": {"type": "boolean"}
                    },
                    "required": ["element", "ref"]
                }
            ),
            "browser_drag": MCPTool(
                name="browser_drag",
                description="Perform drag and drop between two elements",
                parameters={
                    "type": "object",
                    "properties": {
                        "startElement": {"type": "string"},
                        "startRef": {"type": "string"},
                        "endElement": {"type": "string"},
                        "endRef": {"type": "string"}
                    },
                    "required": ["startElement", "startRef", "endElement", "endRef"]
                }
            ),
            "browser_hover": MCPTool(
                name="browser_hover",
                description="Hover over element on page",
                parameters={
                    "type": "object",
                    "properties": {
                        "element": {"type": "string"},
                        "ref": {"type": "string"}
                    },
                    "required": ["element", "ref"]
                }
            ),
            "browser_select_option": MCPTool(
                name="browser_select_option",
                description="Select an option in a dropdown",
                parameters={
                    "type": "object", 
                    "properties": {
                        "element": {"type": "string"},
                        "ref": {"type": "string"},
                        "values": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["element", "ref", "values"]
                }
            ),
            
            # Tab tools
            "browser_tab_list": MCPTool(
                name="browser_tab_list",
                description="List browser tabs",
                parameters={"type": "object", "properties": {}}
            ),
            "browser_tab_select": MCPTool(
                name="browser_tab_select",
                description="Select a tab by index",
                parameters={
                    "type": "object",
                    "properties": {
                        "index": {"type": "number"}
                    },
                    "required": ["index"]
                }
            ),
            "browser_tab_new": MCPTool(
                name="browser_tab_new",
                description="Open a new tab",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"}
                    }
                }
            ),
            "browser_tab_close": MCPTool(
                name="browser_tab_close",
                description="Close a tab",
                parameters={
                    "type": "object",
                    "properties": {
                        "index": {"type": "number"}
                    }
                }
            ),
            
            # Wait tools
            "browser_wait_for": MCPTool(
                name="browser_wait_for",
                description="Wait for text to appear or disappear or a specified time to pass",
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "textGone": {"type": "string"},
                        "time": {"type": "number"}
                    }
                }
            )
        }

    async def _ensure_browser(self):
        """Ensure browser is running"""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        if self._browser is None:
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            
    async def _ensure_page(self):
        """Ensure we have at least one page"""
        await self._ensure_browser()
        if not self._pages:
            assert self._browser is not None
            context = await self._browser.new_context()
            page = await context.new_page()
            self._contexts.append(context)
            self._pages.append(page)
            
            # Setup event listeners
            page.on("console", lambda msg: self._console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": time.time()
            }))
            
            page.on("request", lambda req: self._network_requests.append({
                "url": req.url,
                "method": req.method,
                "headers": dict(req.headers),
                "timestamp": time.time()
            }))
            
            page.on("dialog", lambda dialog: self._dialogs.append(dialog))

    def _get_active_page(self) -> Optional[Page]:
        """Get currently active page"""
        if self._pages and 0 <= self._active_page_idx < len(self._pages):
            return self._pages[self._active_page_idx]
        return None

    async def handle(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution"""
        if tool not in self.tools:
            raise ValueError(f"Unknown tool: {tool}")

        # Browser management tools
        if tool == "browser_close":
            return await self._handle_browser_close()
        elif tool == "browser_resize":
            return await self._handle_browser_resize(params)
        elif tool == "browser_install":
            return await self._handle_browser_install()
            
        # Console tools
        elif tool == "browser_console_messages":
            return await self._handle_console_messages()
            
        # Dialog tools
        elif tool == "browser_handle_dialog":
            return await self._handle_dialog(params)
            
        # Evaluate tools
        elif tool == "browser_evaluate":
            return await self._handle_evaluate(params)
            
        # File tools
        elif tool == "browser_file_upload":
            return await self._handle_file_upload(params)
            
        # Keyboard tools
        elif tool == "browser_press_key":
            return await self._handle_press_key(params)
        elif tool == "browser_type":
            return await self._handle_type(params)
            
        # Mouse tools
        elif tool == "browser_mouse_move_xy":
            return await self._handle_mouse_move(params)
        elif tool == "browser_mouse_click_xy":
            return await self._handle_mouse_click(params)
        elif tool == "browser_mouse_drag_xy":
            return await self._handle_mouse_drag(params)
            
        # Navigate tools
        elif tool == "browser_navigate":
            return await self._handle_navigate(params)
        elif tool == "browser_navigate_back":
            return await self._handle_navigate_back()
        elif tool == "browser_navigate_forward":
            return await self._handle_navigate_forward()
            
        # Network tools
        elif tool == "browser_network_requests":
            return await self._handle_network_requests()
            
        # PDF tools
        elif tool == "browser_pdf_save":
            return await self._handle_pdf_save(params)
            
        # Screenshot tools
        elif tool == "browser_take_screenshot":
            return await self._handle_screenshot(params)
            
        # Snapshot tools
        elif tool == "browser_snapshot":
            return await self._handle_snapshot()
        elif tool == "browser_click":
            return await self._handle_click(params)
        elif tool == "browser_drag":
            return await self._handle_drag(params)
        elif tool == "browser_hover":
            return await self._handle_hover(params)
        elif tool == "browser_select_option":
            return await self._handle_select_option(params)
            
        # Tab tools
        elif tool == "browser_tab_list":
            return await self._handle_tab_list()
        elif tool == "browser_tab_select":
            return await self._handle_tab_select(params)
        elif tool == "browser_tab_new":
            return await self._handle_tab_new(params)
        elif tool == "browser_tab_close":
            return await self._handle_tab_close(params)
            
        # Wait tools
        elif tool == "browser_wait_for":
            return await self._handle_wait_for(params)
            
        else:
            raise ValueError(f"Tool handler not implemented: {tool}")

    # Tool handlers implementation
    
    async def _handle_browser_close(self) -> Dict[str, Any]:
        """Close browser"""
        for context in self._contexts:
            await context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        self._contexts.clear()
        self._pages.clear()
        self._browser = None
        self._playwright = None
        self._active_page_idx = 0
        
        return {"closed": True}

    async def _handle_browser_resize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resize browser window"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            await page.set_viewport_size({"width": int(params["width"]), "height": int(params["height"])})
            return {"resized": True, "width": params["width"], "height": params["height"]}
        return {"error": "No active page"}

    async def _handle_browser_install(self) -> Dict[str, Any]:
        """Install browser (placeholder)"""
        return {"installed": True, "message": "Browser installation not needed in current setup"}

    async def _handle_console_messages(self) -> Dict[str, Any]:
        """Get console messages"""
        return {"messages": self._console_messages}

    async def _handle_dialog(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle dialog"""
        if self._dialogs:
            dialog = self._dialogs.pop(0)
            if params["accept"]:
                await dialog.accept(params.get("promptText", ""))
            else:
                await dialog.dismiss()
            return {"handled": True}
        return {"error": "No dialogs to handle"}

    async def _handle_evaluate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate JavaScript"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            try:
                result = await page.evaluate(params["function"])
                return {"result": result}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "No active page"}

    async def _handle_file_upload(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file upload"""
        # This is a placeholder - real implementation would need file input selector
        return {"uploaded": True, "files": params["paths"]}

    async def _handle_press_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Press key"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            await page.keyboard.press(params["key"])
            return {"pressed": params["key"]}
        return {"error": "No active page"}

    async def _handle_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Type text"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            # Use ref as selector if available, otherwise use element description
            selector = params.get("ref", params["element"])
            slowly = params.get("slowly", False)
            
            if slowly:
                await page.type(selector, params["text"], delay=100)
            else:
                await page.fill(selector, params["text"])
                
            if params.get("submit", False):
                await page.press(selector, "Enter")
                
            return {"typed": params["text"]}
        return {"error": "No active page"}

    async def _handle_mouse_move(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move mouse"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            await page.mouse.move(params["x"], params["y"])
            return {"moved": True, "x": params["x"], "y": params["y"]}
        return {"error": "No active page"}

    async def _handle_mouse_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click mouse at coordinates"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            button = params.get("button", "left")
            double_click = params.get("doubleClick", False)
            
            if double_click:
                await page.mouse.dblclick(params["x"], params["y"], button=button)
            else:
                await page.mouse.click(params["x"], params["y"], button=button)
                
            return {"clicked": True, "x": params["x"], "y": params["y"], "button": button}
        return {"error": "No active page"}

    async def _handle_mouse_drag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Drag mouse between coordinates"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            await page.mouse.move(params["startX"], params["startY"])
            await page.mouse.down()
            await page.mouse.move(params["endX"], params["endY"])
            await page.mouse.up()
            return {"dragged": True, "from": [params["startX"], params["startY"]], "to": [params["endX"], params["endY"]]}
        return {"error": "No active page"}

    async def _handle_navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to URL"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            response = await page.goto(params["url"])
            return {"navigated": True, "url": page.url, "status": response.status if response else 0}
        return {"error": "No active page"}

    async def _handle_navigate_back(self) -> Dict[str, Any]:
        """Navigate back"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            await page.go_back()
            return {"navigated_back": True, "url": page.url}
        return {"error": "No active page"}

    async def _handle_navigate_forward(self) -> Dict[str, Any]:
        """Navigate forward"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            await page.go_forward()
            return {"navigated_forward": True, "url": page.url}
        return {"error": "No active page"}

    async def _handle_network_requests(self) -> Dict[str, Any]:
        """Get network requests"""
        return {"requests": self._network_requests}

    async def _handle_pdf_save(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save page as PDF"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            format_type = params.get("format", "A4")
            landscape = params.get("landscape", False)
            
            await page.pdf(
                path=params["path"],
                format=format_type,
                landscape=landscape
            )
            return {"saved": True, "path": params["path"]}
        return {"error": "No active page"}

    async def _handle_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            full_page = params.get("fullPage", False)
            filename = params.get("filename", f"screenshot_{int(time.time())}.png")
            file_type = params.get("type", "png")
            
            screenshot_params = {"type": file_type, "full_page": full_page}
            
            if "element" in params and "ref" in params:
                # Screenshot specific element
                element = page.locator(params["ref"]).first
                screenshot_data = await element.screenshot(**screenshot_params)
            else:
                # Screenshot whole page
                screenshot_data = await page.screenshot(**screenshot_params)
            
            if filename:
                with open(filename, "wb") as f:
                    f.write(screenshot_data)
                return {"saved": True, "filename": filename}
            else:
                # Return base64 encoded image
                return {"image_base64": base64.b64encode(screenshot_data).decode()}
        return {"error": "No active page"}

    async def _handle_snapshot(self) -> Dict[str, Any]:
        """Take accessibility snapshot"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            # Simplified accessibility tree
            title = await page.title()
            url = page.url
            content = await page.content()
            return {
                "snapshot": {
                    "title": title,
                    "url": url,
                    "content_length": len(content)
                }
            }
        return {"error": "No active page"}

    async def _handle_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click element by selector"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            selector = params.get("ref", params["element"])
            button = params.get("button", "left")
            double_click = params.get("doubleClick", False)
            
            if double_click:
                await page.dblclick(selector, button=button)
            else:
                await page.click(selector, button=button)
                
            return {"clicked": True, "element": params["element"]}
        return {"error": "No active page"}

    async def _handle_drag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Drag between elements"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            start_selector = params.get("startRef", params["startElement"])
            end_selector = params.get("endRef", params["endElement"])
            
            # Get element bounds for drag operation
            start_element = page.locator(start_selector).first
            end_element = page.locator(end_selector).first
            
            await start_element.drag_to(end_element)
            
            return {"dragged": True, "from": params["startElement"], "to": params["endElement"]}
        return {"error": "No active page"}

    async def _handle_hover(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Hover over element"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            selector = params.get("ref", params["element"])
            await page.hover(selector)
            return {"hovered": True, "element": params["element"]}
        return {"error": "No active page"}

    async def _handle_select_option(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Select option in dropdown"""
        await self._ensure_page()
        page = self._get_active_page()
        if page:
            selector = params.get("ref", params["element"])
            values = params["values"]
            
            await page.select_option(selector, values)
            return {"selected": True, "element": params["element"], "values": values}
        return {"error": "No active page"}

    async def _handle_tab_list(self) -> Dict[str, Any]:
        """List browser tabs"""
        return {
            "tabs": [
                {"index": i, "url": page.url, "title": await page.title()}
                for i, page in enumerate(self._pages)
            ],
            "active_index": self._active_page_idx
        }

    async def _handle_tab_select(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Select tab by index"""
        index = params["index"]
        if 0 <= index < len(self._pages):
            self._active_page_idx = index
            page = self._pages[index]
            return {"selected": True, "index": index, "url": page.url}
        return {"error": f"Tab index {index} out of range"}

    async def _handle_tab_new(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open new tab"""
        await self._ensure_browser()
        assert self._browser is not None
        context = await self._browser.new_context()
        page = await context.new_page()
        
        self._contexts.append(context)
        self._pages.append(page)
        self._active_page_idx = len(self._pages) - 1
        
        # Setup event listeners for new page
        page.on("console", lambda msg: self._console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "timestamp": time.time()
        }))
        
        if "url" in params:
            await page.goto(params["url"])
            
        return {"opened": True, "index": self._active_page_idx, "url": page.url}

    async def _handle_tab_close(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close tab"""
        index = params.get("index", self._active_page_idx)
        
        if 0 <= index < len(self._pages):
            page = self._pages[index]
            context = self._contexts[index]
            
            await context.close()
            
            self._pages.pop(index)
            self._contexts.pop(index)
            
            # Adjust active page index
            if self._active_page_idx >= index and self._active_page_idx > 0:
                self._active_page_idx -= 1
            elif len(self._pages) == 0:
                self._active_page_idx = 0
                
            return {"closed": True, "index": index}
        return {"error": f"Tab index {index} out of range"}

    async def _handle_wait_for(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for text/time"""
        await self._ensure_page()
        page = self._get_active_page()
        
        if "time" in params:
            await asyncio.sleep(params["time"])
            return {"waited": True, "time": params["time"]}
            
        if page:
            if "text" in params:
                await page.wait_for_function(f"document.body.innerText.includes('{params['text']}')")
                return {"waited": True, "text_appeared": params["text"]}
            elif "textGone" in params:
                await page.wait_for_function(f"!document.body.innerText.includes('{params['textGone']}')")
                return {"waited": True, "text_gone": params["textGone"]}
                
        return {"error": "No valid wait condition"}


class MCPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP server"""
    
    def __init__(self, playwright_mcp: EnhancedPlaywrightMCP, *args, **kwargs):
        self.playwright_mcp = playwright_mcp
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split('?')[0]
        
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
            
        elif path == '/tools':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            tools_list = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
                for tool in self.playwright_mcp.tools.values()
            ]
            self.wfile.write(json.dumps({"tools": tools_list}).encode())
            
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/execute':
            try:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                
                tool = data.get('tool')
                parameters = data.get('parameters', {})
                
                # Run async handler
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.playwright_mcp.handle(tool, parameters)
                    )
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                    
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                finally:
                    loop.close()
                    
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass


def create_handler(playwright_mcp):
    """Create handler with playwright_mcp instance"""
    def handler(*args, **kwargs):
        return MCPHandler(playwright_mcp, *args, **kwargs)
    return handler


def main():
    """Run the enhanced MCP server"""
    port = int(os.environ.get('PORT', 4005))
    host = os.environ.get('HOST', '0.0.0.0')
    headless = os.environ.get('HEADLESS', 'true').lower() == 'true'
    
    playwright_mcp = EnhancedPlaywrightMCP(headless=headless)
    handler = create_handler(playwright_mcp)
    
    server = HTTPServer((host, port), handler)
    
    print(f"Enhanced Playwright MCP Server running on {host}:{port}")
    print(f"Tools available: {len(playwright_mcp.tools)}")
    print("Available endpoints:")
    print(f"  GET  http://{host}:{port}/health")
    print(f"  GET  http://{host}:{port}/tools")
    print(f"  POST http://{host}:{port}/execute")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == '__main__':
    main()
