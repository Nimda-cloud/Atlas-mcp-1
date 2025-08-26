#!/usr/bin/env python3
"""
Simple MCP Proxy Server
=======================
Basic HTTP server for MCP proxy functionality
"""

import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime

class MCPProxyHandler(http.server.BaseHTTPRequestHandler):
    """Simple MCP proxy request handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_health_response()
        elif self.path == '/status':
            self.send_status_response()
        elif self.path == '/tools':
            self.send_tools_response()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/execute':
            self.send_execute_response()
        else:
            self.send_error(404, "Endpoint not found")
    
    def send_health_response(self):
        """Send health check response"""
        response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "mode": "proxy",
            "version": "1.0.0"
        }
        self.send_json_response(200, response)
    
    def send_status_response(self):
        """Send status response"""
        response = {
            "status": "ok",
            "mode": "proxy",
            "proxy_url": "http://127.0.0.1:9090",
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(200, response)
    
    def send_tools_response(self):
        """Send tools list response"""
        tools = {
            "available_tools": [
                "test_tool_1",
                "test_tool_2", 
                "health_check"
            ],
            "total_count": 3,
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(200, tools)
    
    def send_execute_response(self):
        """Send execute response"""
        response = {
            "success": True,
            "message": "Tool execution simulated",
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(200, response)
    
    def send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def main():
    """Start the MCP proxy server"""
    PORT = 9090
    
    with socketserver.TCPServer(("", PORT), MCPProxyHandler) as httpd:
        print(f"🚀 MCP Proxy Server starting on port {PORT}")
        print(f"📍 Health: http://localhost:{PORT}/health")
        print(f"📊 Status: http://localhost:{PORT}/status")
        print(f"🛠️ Tools: http://localhost:{PORT}/tools")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()
