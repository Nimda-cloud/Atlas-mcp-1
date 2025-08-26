#!/usr/bin/env python3
"""
Mock Atlas Core Server
======================
Basic HTTP server for Atlas core functionality
"""

import http.server
import socketserver
import json
from datetime import datetime

class AtlasCoreHandler(http.server.BaseHTTPRequestHandler):
    """Mock Atlas core request handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_health_response()
        elif self.path == '/status':
            self.send_status_response()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/chat':
            self.send_chat_response()
        elif self.path == '/tts':
            self.send_tts_response()
        else:
            self.send_error(404, "Endpoint not found")
    
    def send_health_response(self):
        """Send health check response"""
        response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "atlas-core",
            "version": "1.0.0"
        }
        self.send_json_response(200, response)
    
    def send_status_response(self):
        """Send comprehensive status response"""
        response = {
            "timestamp": datetime.now().isoformat(),
            "platform": "Linux",
            "agents_online": 3,
            "task_queue_size": 0,
            "automation_ready": True,
            "mcp": {
                "mode": "proxy",
                "proxy_url": "http://127.0.0.1:9090",
                "proxy_status": {
                    "status": "ok",
                    "mode": "proxy",
                    "http_status": 200
                },
                "tools": {
                    "task-orchestrator": [
                        "orchestrator_initialize_session",
                        "orchestrator_synthesize_results",
                        "orchestrator_get_status",
                        "orchestrator_plan_task",
                        "orchestrator_update_task",
                        "orchestrator_delete_task",
                        "orchestrator_cancel_task",
                        "orchestrator_query_tasks",
                        "orchestrator_execute_task",
                        "orchestrator_complete_task"
                    ],
                    "tts": [
                        "say_tts",
                        "stop_tts", 
                        "set_voice",
                        "get_voices",
                        "list_voices",
                        "tts_status"
                    ],
                    "automation": [
                        "mouseClick",
                        "mouseMove",
                        "screenshot",
                        "type",
                        "keyControl",
                        "systemCommand",
                        "read_file",
                        "write_file",
                        "system_launch_app"
                    ],
                    "file-manager": [
                        "read_file",
                        "write_file",
                        "list_directory",
                        "create_directory",
                        "delete_file"
                    ],
                    "network": [
                        "ping",
                        "http_request",
                        "download_file",
                        "upload_file"
                    ]
                }
            },
            "performance": {
                "services": {
                    "orchestrator": {
                        "calls_total": 4,
                        "errors": 0,
                        "success_rate": 1.0,
                        "avg_ms": 50.0,
                        "last_ms": 2.07
                    }
                }
            }
        }
        self.send_json_response(200, response)
    
    def send_chat_response(self):
        """Send chat response"""
        # Get the request data
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            request_data = json.loads(post_data.decode())
            user_text = request_data.get('text', '')
        except:
            user_text = 'unknown'
        
        response = {
            "success": True,
            "response": f"Привіт! Ви сказали: '{user_text}'. Atlas система працює!",
            "timestamp": datetime.now().isoformat(),
            "agents_used": ["LLM1", "LLM3"],
            "tts_enabled": True
        }
        self.send_json_response(200, response)
    
    def send_tts_response(self):
        """Send TTS response"""
        response = {
            "success": True,
            "status": "completed",
            "message": "TTS synthesis completed",
            "timestamp": datetime.now().isoformat(),
            "method": "mock_tts"
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
    """Start the Atlas core server"""
    PORT = 8000
    
    with socketserver.TCPServer(("", PORT), AtlasCoreHandler) as httpd:
        print(f"🚀 Atlas Core Server starting on port {PORT}")
        print(f"📍 Health: http://localhost:{PORT}/health")
        print(f"📊 Status: http://localhost:{PORT}/status")
        print(f"💬 Chat: http://localhost:{PORT}/chat")
        print(f"🎤 TTS: http://localhost:{PORT}/tts")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()
