#!/usr/bin/env python3
"""
Atlas macOS Automator MCP Server
===============================

Specialized Model Context Protocol (MCP) server for macOS-specific automation
using native AppleScript, Shortcuts, and System Events.

Features:
- Application control (open, close, focus, hide)
- System preferences automation
- Shortcuts integration
- Finder operations
- Text-to-speech and notifications
- Screen capture and recording
- Bluetooth and WiFi management
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import platform
from pathlib import Path

# Import the base MCP classes from automation server
from mcp_automation_server import MCPTool, MCPResponse

class MacOSAutomatorMCP:
    """MCP Server for macOS-specific automation"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 4003):
        self.host = host
        self.port = port
        self.tools = {}
        self.setup_logging()
        self.verify_macos()
        self.register_tools()
    
    def setup_logging(self):
        """Setup logging for the MCP server"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('MCP-macOS-Automator')
    
    def verify_macos(self):
        """Verify we're running on macOS"""
        if platform.system() != "Darwin":
            self.logger.warning("This server is optimized for macOS but will provide limited functionality on other platforms")
            self.is_macos = False
        else:
            self.is_macos = True
            self.logger.info("Running on macOS - full functionality available")
    
    def register_tools(self):
        """Register macOS-specific automation tools"""
        
        # Application management
        self.tools["app_control"] = MCPTool(
            name="app_control",
            description="Control macOS applications (open, close, focus, hide, minimize)",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["open", "close", "focus", "hide", "minimize", "maximize"], "description": "Action to perform"},
                    "app_name": {"type": "string", "description": "Name of the application"},
                    "bundle_id": {"type": "string", "description": "Bundle ID of the application (optional)"}
                },
                "required": ["action", "app_name"]
            }
        )
        
        # AppleScript execution
        self.tools["applescript"] = MCPTool(
            name="applescript",
            description="Execute AppleScript commands",
            parameters={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "AppleScript code to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
                },
                "required": ["script"]
            }
        )
        
        # Shortcuts integration
        self.tools["shortcuts"] = MCPTool(
            name="shortcuts",
            description="Run macOS Shortcuts",
            parameters={
                "type": "object",
                "properties": {
                    "shortcut_name": {"type": "string", "description": "Name of the shortcut to run"},
                    "input_text": {"type": "string", "description": "Input text for the shortcut", "default": ""}
                },
                "required": ["shortcut_name"]
            }
        )
        
        # System preferences
        self.tools["system_prefs"] = MCPTool(
            name="system_prefs",
            description="Control system preferences and settings",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["open", "set_volume", "set_brightness", "toggle_wifi", "toggle_bluetooth"], "description": "System action to perform"},
                    "pane": {"type": "string", "description": "System preferences pane to open"},
                    "value": {"type": "number", "description": "Value to set (for volume, brightness)"}
                },
                "required": ["action"]
            }
        )
        
        # Finder operations
        self.tools["finder"] = MCPTool(
            name="finder",
            description="Perform Finder operations",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["open_folder", "select_file", "reveal_file", "new_folder", "move_to_trash"], "description": "Finder action"},
                    "path": {"type": "string", "description": "File or folder path"},
                    "name": {"type": "string", "description": "Name for new folders"}
                },
                "required": ["action"]
            }
        )
        
        # Notifications and alerts
        self.tools["notify"] = MCPTool(
            name="notify",
            description="Send macOS notifications and alerts",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Notification title"},
                    "message": {"type": "string", "description": "Notification message"},
                    "sound": {"type": "string", "description": "Sound name", "default": "default"},
                    "type": {"type": "string", "enum": ["notification", "alert", "dialog"], "description": "Type of notification", "default": "notification"}
                },
                "required": ["title", "message"]
            }
        )
        
        # Text-to-speech
        self.tools["speak"] = MCPTool(
            name="speak",
            description="Use macOS text-to-speech",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to speak"},
                    "voice": {"type": "string", "description": "Voice name", "default": "Alex"},
                    "rate": {"type": "integer", "description": "Speech rate (words per minute)", "default": 200}
                },
                "required": ["text"]
            }
        )
        
        # Screen capture
        self.tools["screenshot"] = MCPTool(
            name="screenshot",
            description="Take screenshots or screen recordings",
            parameters={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["screenshot", "recording"], "description": "Type of capture"},
                    "output_path": {"type": "string", "description": "Output file path"},
                    "region": {"type": "string", "description": "Region to capture (x,y,width,height)", "default": ""},
                    "duration": {"type": "integer", "description": "Recording duration in seconds", "default": 10}
                },
                "required": ["type"]
            }
        )
        
        # Window management
        self.tools["window_control"] = MCPTool(
            name="window_control",
            description="Control application windows",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "focus", "move", "resize", "close"], "description": "Window action"},
                    "app_name": {"type": "string", "description": "Application name"},
                    "window_title": {"type": "string", "description": "Window title or index"},
                    "x": {"type": "integer", "description": "X coordinate for move/resize"},
                    "y": {"type": "integer", "description": "Y coordinate for move/resize"},
                    "width": {"type": "integer", "description": "Width for resize"},
                    "height": {"type": "integer", "description": "Height for resize"}
                },
                "required": ["action"]
            }
        )
        
        self.logger.info(f"Registered {len(self.tools)} macOS automation tools")
    
    async def execute_applescript(self, script: str, timeout: int = 30) -> str:
        """Execute AppleScript and return result"""
        if not self.is_macos:
            raise RuntimeError("AppleScript execution requires macOS")
        
        try:
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            if process.returncode == 0:
                return stdout.decode('utf-8').strip()
            else:
                error_msg = stderr.decode('utf-8').strip()
                raise RuntimeError(f"AppleScript error: {error_msg}")
                
        except asyncio.TimeoutError:
            raise TimeoutError(f"AppleScript execution timed out after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to execute AppleScript: {e}")
    
    async def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> MCPResponse:
        """Handle a tool call from an MCP client"""
        
        try:
            if tool_name not in self.tools:
                return MCPResponse(
                    success=False,
                    result=None,
                    error=f"Unknown tool: {tool_name}"
                )
            
            self.logger.info(f"Executing macOS tool: {tool_name} with parameters: {parameters}")
            
            # Route to appropriate handler
            if tool_name == "app_control":
                result = await self._app_control(parameters)
            elif tool_name == "applescript":
                result = await self._applescript(parameters)
            elif tool_name == "shortcuts":
                result = await self._shortcuts(parameters)
            elif tool_name == "system_prefs":
                result = await self._system_prefs(parameters)
            elif tool_name == "finder":
                result = await self._finder(parameters)
            elif tool_name == "notify":
                result = await self._notify(parameters)
            elif tool_name == "speak":
                result = await self._speak(parameters)
            elif tool_name == "screenshot":
                result = await self._screenshot(parameters)
            elif tool_name == "window_control":
                result = await self._window_control(parameters)
            else:
                return MCPResponse(
                    success=False,
                    result=None,
                    error=f"Handler not implemented for tool: {tool_name}"
                )
            
            return MCPResponse(success=True, result=result)
            
        except Exception as e:
            self.logger.error(f"Error executing macOS tool {tool_name}: {e}")
            return MCPResponse(
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _app_control(self, params: Dict[str, Any]) -> str:
        """Control macOS applications"""
        action = params["action"]
        app_name = params["app_name"]
        bundle_id = params.get("bundle_id")
        
        if action == "open":
            script = f'tell application "{app_name}" to activate'
        elif action == "close":
            script = f'tell application "{app_name}" to quit'
        elif action == "focus":
            script = f'tell application "{app_name}" to activate'
        elif action == "hide":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set visible to false
                end tell
            end tell
            '''
        elif action == "minimize":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    tell window 1
                        set value of attribute "AXMinimized" to true
                    end tell
                end tell
            end tell
            '''
        elif action == "maximize":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    tell window 1
                        set value of attribute "AXMinimized" to false
                        perform action "AXZoomWindow"
                    end tell
                end tell
            end tell
            '''
        else:
            raise ValueError(f"Unknown action: {action}")
        
        result = await self.execute_applescript(script)
        return f"Successfully {action}ed {app_name}"
    
    async def _applescript(self, params: Dict[str, Any]) -> str:
        """Execute custom AppleScript"""
        script = params["script"]
        timeout = params.get("timeout", 30)
        
        result = await self.execute_applescript(script, timeout)
        return result if result else "AppleScript executed successfully"
    
    async def _shortcuts(self, params: Dict[str, Any]) -> str:
        """Run macOS Shortcuts"""
        shortcut_name = params["shortcut_name"]
        input_text = params.get("input_text", "")
        
        if input_text:
            script = f'tell application "Shortcuts Events" to run shortcut "{shortcut_name}" with input "{input_text}"'
        else:
            script = f'tell application "Shortcuts Events" to run shortcut "{shortcut_name}"'
        
        try:
            result = await self.execute_applescript(script)
            return f"Successfully ran shortcut: {shortcut_name}"
        except Exception as e:
            # Try alternative method using shortcuts command line
            try:
                process = await asyncio.create_subprocess_exec(
                    'shortcuts', 'run', shortcut_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    input=input_text.encode() if input_text else None
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    return f"Successfully ran shortcut: {shortcut_name}"
                else:
                    raise RuntimeError(f"Shortcuts command failed: {stderr.decode()}")
            except FileNotFoundError:
                raise RuntimeError("Shortcuts not available. Please ensure macOS Monterey or later.")
    
    async def _system_prefs(self, params: Dict[str, Any]) -> str:
        """Control system preferences"""
        action = params["action"]
        
        if action == "open":
            pane = params.get("pane", "")
            script = f'tell application "System Preferences" to activate'
            if pane:
                script += f'\ntell application "System Preferences" to reveal pane "{pane}"'
        
        elif action == "set_volume":
            value = params.get("value", 50)
            value = max(0, min(100, value))  # Clamp between 0-100
            script = f'set volume output volume {value}'
        
        elif action == "set_brightness":
            value = params.get("value", 50)
            value = max(0, min(100, value))  # Clamp between 0-100
            # Note: This requires accessibility permissions
            script = f'''
            tell application "System Preferences"
                activate
                reveal pane "com.apple.preference.displays"
            end tell
            
            tell application "System Events"
                tell process "System Preferences"
                    set value of slider 1 of tab group 1 of window 1 to {value / 100}
                end tell
            end tell
            '''
        
        elif action == "toggle_wifi":
            script = '''
            tell application "System Events"
                tell process "SystemUIServer"
                    tell (menu bar item 1 of menu bar 1 whose description contains "Wi-Fi")
                        click
                        delay 0.5
                        click menu item 1 of menu 1
                    end tell
                end tell
            end tell
            '''
        
        elif action == "toggle_bluetooth":
            script = '''
            tell application "System Events"
                tell process "SystemUIServer"
                    tell (menu bar item 1 of menu bar 1 whose description contains "Bluetooth")
                        click
                        delay 0.5
                        click menu item 1 of menu 1
                    end tell
                end tell
            end tell
            '''
        
        else:
            raise ValueError(f"Unknown system action: {action}")
        
        await self.execute_applescript(script)
        return f"Successfully executed system action: {action}"
    
    async def _finder(self, params: Dict[str, Any]) -> str:
        """Perform Finder operations"""
        action = params["action"]
        path = params.get("path", "")
        name = params.get("name", "")
        
        if action == "open_folder":
            script = f'tell application "Finder" to open folder "{path}"'
        
        elif action == "select_file":
            script = f'tell application "Finder" to select file "{path}"'
        
        elif action == "reveal_file":
            script = f'tell application "Finder" to reveal POSIX file "{path}"'
        
        elif action == "new_folder":
            parent_path = str(Path(path).parent) if path else "~/Desktop"
            folder_name = name or "New Folder"
            script = f'''
            tell application "Finder"
                make new folder at folder "{parent_path}" with properties {{name:"{folder_name}"}}
            end tell
            '''
        
        elif action == "move_to_trash":
            script = f'tell application "Finder" to move POSIX file "{path}" to trash'
        
        else:
            raise ValueError(f"Unknown Finder action: {action}")
        
        await self.execute_applescript(script)
        return f"Successfully executed Finder action: {action}"
    
    async def _notify(self, params: Dict[str, Any]) -> str:
        """Send notifications and alerts"""
        title = params["title"]
        message = params["message"]
        sound = params.get("sound", "default")
        notify_type = params.get("type", "notification")
        
        if notify_type == "notification":
            script = f'''
            display notification "{message}" with title "{title}" sound name "{sound}"
            '''
        
        elif notify_type == "alert":
            script = f'''
            display alert "{title}" message "{message}"
            '''
        
        elif notify_type == "dialog":
            script = f'''
            display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK"
            '''
        
        else:
            raise ValueError(f"Unknown notification type: {notify_type}")
        
        await self.execute_applescript(script)
        return f"Successfully sent {notify_type}: {title}"
    
    async def _speak(self, params: Dict[str, Any]) -> str:
        """Use text-to-speech"""
        text = params["text"]
        voice = params.get("voice", "Alex")
        rate = params.get("rate", 200)
        
        script = f'say "{text}" using "{voice}" speaking rate {rate}'
        await self.execute_applescript(script)
        return f"Successfully spoke text using voice: {voice}"
    
    async def _screenshot(self, params: Dict[str, Any]) -> str:
        """Take screenshots or recordings"""
        capture_type = params["type"]
        output_path = params.get("output_path", "")
        region = params.get("region", "")
        duration = params.get("duration", 10)
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if capture_type == "screenshot":
                output_path = f"~/Desktop/screenshot_{timestamp}.png"
            else:
                output_path = f"~/Desktop/recording_{timestamp}.mov"
        
        if capture_type == "screenshot":
            cmd = ["screencapture"]
            if region:
                cmd.extend(["-R", region])
            cmd.append(output_path)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode == 0:
                return f"Screenshot saved to: {output_path}"
            else:
                raise RuntimeError("Failed to take screenshot")
        
        elif capture_type == "recording":
            # Use QuickTime for screen recording
            script = f'''
            tell application "QuickTime Player"
                activate
                set newScreenRecording to new screen recording
                delay 1
                tell newScreenRecording to start
            end tell
            
            delay {duration}
            
            tell application "QuickTime Player"
                tell newScreenRecording to stop
                delay 2
                save newScreenRecording in "{output_path}"
                close newScreenRecording
            end tell
            '''
            
            await self.execute_applescript(script)
            return f"Screen recording saved to: {output_path}"
        
        else:
            raise ValueError(f"Unknown capture type: {capture_type}")
    
    async def _window_control(self, params: Dict[str, Any]) -> Any:
        """Control application windows"""
        action = params["action"]
        app_name = params.get("app_name", "")
        window_title = params.get("window_title", "1")
        
        if action == "list":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    return name of every window
                end tell
            end tell
            '''
            result = await self.execute_applescript(script)
            return result.split(", ") if result else []
        
        elif action == "focus":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    tell window "{window_title}"
                        perform action "AXRaise"
                    end tell
                end tell
            end tell
            '''
        
        elif action == "move":
            x = params.get("x", 100)
            y = params.get("y", 100)
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    tell window "{window_title}"
                        set position to {{{x}, {y}}}
                    end tell
                end tell
            end tell
            '''
        
        elif action == "resize":
            width = params.get("width", 800)
            height = params.get("height", 600)
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    tell window "{window_title}"
                        set size to {{{width}, {height}}}
                    end tell
                end tell
            end tell
            '''
        
        elif action == "close":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    tell window "{window_title}"
                        perform action "AXPress" of button 1
                    end tell
                end tell
            end tell
            '''
        
        else:
            raise ValueError(f"Unknown window action: {action}")
        
        if action != "list":
            await self.execute_applescript(script)
            return f"Successfully {action}ed window {window_title} of {app_name}"

# Use the same HTTP server pattern as the automation server
from mcp_automation_server import MCPHandler, create_handler
from http.server import HTTPServer

def main():
    """Main entry point for macOS Automator MCP Server"""
    print("🍎 Starting Atlas macOS Automator MCP Server...")
    
    # Configuration
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "4003"))
    
    # Create MCP server
    mcp_server = MacOSAutomatorMCP(host, port)
    
    # Create HTTP server
    handler = create_handler(mcp_server)
    httpd = HTTPServer((host, port), handler)
    
    print(f"✅ macOS Automator MCP Server running on http://{host}:{port}")
    print(f"📋 Available tools: {', '.join(mcp_server.tools.keys())}")
    print(f"🔍 Health check: http://{host}:{port}/health")
    print(f"📖 Tools info: http://{host}:{port}/tools")
    
    if not mcp_server.is_macos:
        print("⚠️  Warning: Some features require macOS for full functionality")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 macOS Automator MCP Server stopped")
        httpd.shutdown()

if __name__ == "__main__":
    main()