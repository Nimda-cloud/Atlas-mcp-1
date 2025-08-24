#!/usr/bin/env python3
"""
Simple HTTP server for viewing 3D GLB models
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class GLBHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for GLB files
        if self.path.endswith('.glb'):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def start_server(port=8080):
    """Start local HTTP server for 3D models"""
    
    # Change to the directory containing GLB files
    os.chdir('/Users/dev/Documents/GitHub/Atlas-mcp')
    
    with socketserver.TCPServer(("", port), GLBHandler) as httpd:
        print(f"🚀 Сервер запущено на http://localhost:{port}")
        print(f"📁 Обслуговується директорія: {os.getcwd()}")
        print(f"🌐 Відкрийте http://localhost:{port}/3d_viewer.html для перегляду моделей")
        print("⏹️  Натисніть Ctrl+C для зупинки сервера")
        
        # Try to open browser automatically
        try:
            webbrowser.open(f'http://localhost:{port}/3d_viewer.html')
        except:
            pass
            
        httpd.serve_forever()

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n🛑 Сервер зупинено")
    except Exception as e:
        print(f"❌ Помилка: {e}")
