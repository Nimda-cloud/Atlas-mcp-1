#!/usr/bin/env python3
"""
Atlas MCP Automation Server
==========================

Model Context Protocol (MCP) server for general automation tasks.
This server provides a standardized interface for various automation
capabilities that can be used by the Atlas LLM agents.

Features:
- System automation (file operations, process management)
- Network operations (HTTP requests, API calls)
- Text processing and data manipulation
- Integration with external services
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
import shutil
import requests
from pathlib import Path

# MCP Protocol implementation
from dataclasses import dataclass

@dataclass
class MCPTool:
    """Represents an MCP tool/function"""
    name: str
    description: str
    parameters: Dict[str, Any]

@dataclass
class MCPResponse:
    """Represents an MCP response"""
    success: bool
    result: Any
    error: Optional[str] = None

class MCPAutomationServer:
    """MCP Server for automation tasks"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 4002):
        self.host = host
        self.port = port
        self.tools = {}
        self.setup_logging()
        self.register_tools()
    
    def setup_logging(self):
        """Setup logging for the MCP server"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('MCP-Automation')
    
    def register_tools(self):
        """Register available automation tools"""
        
        # File system operations
        self.tools["read_file"] = MCPTool(
            name="read_file",
            description="Read contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to read"}
                },
                "required": ["file_path"]
            }
        )
        
        self.tools["write_file"] = MCPTool(
            name="write_file", 
            description="Write content to a file",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"},
                    "append": {"type": "boolean", "description": "Whether to append or overwrite", "default": False}
                },
                "required": ["file_path", "content"]
            }
        )
        
        self.tools["list_directory"] = MCPTool(
            name="list_directory",
            description="List contents of a directory",
            parameters={
                "type": "object", 
                "properties": {
                    "directory_path": {"type": "string", "description": "Path to the directory to list"},
                    "recursive": {"type": "boolean", "description": "Whether to list recursively", "default": False}
                },
                "required": ["directory_path"]
            }
        )
        
        # Process management
        self.tools["execute_command"] = MCPTool(
            name="execute_command",
            description="Execute a system command",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                    "capture_output": {"type": "boolean", "description": "Whether to capture output", "default": True}
                },
                "required": ["command"]
            }
        )
        
        # Network operations
        self.tools["http_request"] = MCPTool(
            name="http_request",
            description="Make HTTP request",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to request"},
                    "method": {"type": "string", "description": "HTTP method", "default": "GET"},
                    "headers": {"type": "object", "description": "HTTP headers", "default": {}},
                    "data": {"type": "object", "description": "Request data", "default": {}}
                },
                "required": ["url"]
            }
        )
        
        # System information
        self.tools["system_info"] = MCPTool(
            name="system_info",
            description="Get system information",
            parameters={
                "type": "object",
                "properties": {
                    "info_type": {"type": "string", "description": "Type of info to get", "default": "all"}
                }
            }
        )
        
        self.logger.info(f"Registered {len(self.tools)} automation tools")
    
    async def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> MCPResponse:
        """Handle a tool call from an MCP client"""
        
        try:
            if tool_name not in self.tools:
                return MCPResponse(
                    success=False,
                    result=None,
                    error=f"Unknown tool: {tool_name}"
                )
            
            self.logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
            
            # Route to appropriate handler
            if tool_name == "read_file":
                result = await self._read_file(parameters)
            elif tool_name == "write_file":
                result = await self._write_file(parameters)
            elif tool_name == "list_directory":
                result = await self._list_directory(parameters)
            elif tool_name == "execute_command":
                result = await self._execute_command(parameters)
            elif tool_name == "http_request":
                result = await self._http_request(parameters)
            elif tool_name == "system_info":
                result = await self._system_info(parameters)
            else:
                return MCPResponse(
                    success=False,
                    result=None,
                    error=f"Handler not implemented for tool: {tool_name}"
                )
            
            return MCPResponse(success=True, result=result)
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {e}")
            return MCPResponse(
                success=False,
                result=None,
                error=str(e)
            )
    
    async def _read_file(self, params: Dict[str, Any]) -> str:
        """Read file contents"""
        file_path = params["file_path"]
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def _write_file(self, params: Dict[str, Any]) -> str:
        """Write file contents"""
        file_path = params["file_path"]
        content = params["content"]
        append = params.get("append", False)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully {'appended to' if append else 'wrote'} {file_path}"
    
    async def _list_directory(self, params: Dict[str, Any]) -> List[str]:
        """List directory contents"""
        directory_path = params["directory_path"]
        recursive = params.get("recursive", False)
        
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if recursive:
            files = []
            for root, dirs, filenames in os.walk(directory_path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
                for dirname in dirs:
                    files.append(os.path.join(root, dirname) + "/")
            return files
        else:
            return os.listdir(directory_path)
    
    async def _execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system command"""
        command = params["command"]
        timeout = params.get("timeout", 30)
        capture_output = params.get("capture_output", True)
        
        try:
            if capture_output:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                
                return {
                    "return_code": process.returncode,
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8')
                }
            else:
                process = await asyncio.create_subprocess_shell(command)
                return_code = await asyncio.wait_for(process.wait(), timeout=timeout)
                return {"return_code": return_code}
                
        except asyncio.TimeoutError:
            raise TimeoutError(f"Command timed out after {timeout} seconds")
    
    async def _http_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request"""
        url = params["url"]
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        data = params.get("data", {})
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                timeout=30
            )
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
    
    async def _system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information"""
        info_type = params.get("info_type", "all")
        
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "timestamp": datetime.now().isoformat()
        }
        
        if info_type == "all" or info_type == "disk":
            if shutil.which("df"):
                try:
                    process = await asyncio.create_subprocess_shell(
                        "df -h",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await process.communicate()
                    info["disk_usage"] = stdout.decode('utf-8')
                except:
                    pass
        
        if info_type == "all" or info_type == "memory":
            try:
                import psutil
                memory = psutil.virtual_memory()
                info["memory"] = {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percentage": memory.percent
                }
            except ImportError:
                pass
        
        return info

# Simple HTTP server for MCP protocol
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MCPHandler(BaseHTTPRequestHandler):
    """HTTP handler for MCP requests"""
    
    def __init__(self, mcp_server, *args, **kwargs):
        self.mcp_server = mcp_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self._send_response(200, {"status": "healthy", "tools": list(self.mcp_server.tools.keys())})
        elif self.path == "/tools":
            tools_info = {}
            for name, tool in self.mcp_server.tools.items():
                tools_info[name] = {
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            self._send_response(200, tools_info)
        else:
            self._send_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/execute":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                
                tool_name = request_data.get("tool")
                parameters = request_data.get("parameters", {})
                
                # Execute tool asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    response = loop.run_until_complete(
                        self.mcp_server.handle_tool_call(tool_name, parameters)
                    )
                    
                    self._send_response(200, {
                        "success": response.success,
                        "result": response.result,
                        "error": response.error
                    })
                    
                finally:
                    loop.close()
                    
            except Exception as e:
                self._send_response(500, {"error": str(e)})
        else:
            self._send_response(404, {"error": "Not found"})
    
    def _send_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        pass

def create_handler(mcp_server):
    """Create handler with MCP server instance"""
    def handler(*args, **kwargs):
        MCPHandler(mcp_server, *args, **kwargs)
    return handler

def main():
    """Main entry point for MCP Automation Server"""
    print("🔧 Starting Atlas MCP Automation Server...")
    
    # Configuration
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "4002"))
    
    # Create MCP server
    mcp_server = MCPAutomationServer(host, port)
    
    # Create HTTP server
    handler = create_handler(mcp_server)
    httpd = HTTPServer((host, port), handler)
    
    print(f"✅ MCP Automation Server running on http://{host}:{port}")
    print(f"📋 Available tools: {', '.join(mcp_server.tools.keys())}")
    print(f"🔍 Health check: http://{host}:{port}/health")
    print(f"📖 Tools info: http://{host}:{port}/tools")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 MCP Automation Server stopped")
        httpd.shutdown()

if __name__ == "__main__":
    main()