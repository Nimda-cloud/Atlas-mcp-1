#!/usr/bin/env python3
"""
Simple HTTP server for the enhanced Atlas frontend
Works without external dependencies
"""
import http.server
import socketserver
import os
import json
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, parse_qs

class EnhancedHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_POST(self):
        """Handle POST requests for API endpoints"""
        if self.path == '/api/chat':
            self.handle_chat()
        elif self.path == '/api/tts/speak':
            self.handle_tts()
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.end_headers()

    def handle_chat(self):
        """Handle chat API requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get('message', '')
            
            # Simple response generation
            responses = [
                f"Я отримав ваше повідомлення: '{message}'. Обробляю запит...",
                f"Зрозуміло! Щодо '{message}' - це цікаве питання. Аналізую...",
                f"Команда '{message}' прийнята. Виконую операцію...",
                f"Дякую за повідомлення: '{message}'. Система готова до роботи.",
            ]
            
            import random
            response = random.choice(responses)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {'response': response}
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")

    def handle_tts(self):
        """Handle TTS API requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Return mock TTS response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {
                'status': 'success',
                'message': 'TTS service not available, using browser fallback',
                'provider': 'browser'
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")

def start_enhanced_server(port=8080):
    """Start enhanced HTTP server"""
    
    # Change to this file's directory
    base_dir = Path(__file__).parent.resolve()
    os.chdir(base_dir)
    
    with socketserver.TCPServer(("", port), EnhancedHandler) as httpd:
        print(f"🚀 Atlas Enhanced Frontend запущено на http://localhost:{port}")
        print(f"📁 Обслуговується директорія: {os.getcwd()}")
        print(f"🌐 Відкрийте http://localhost:{port}/enhanced_frontend_simple.html")
        print("⏹️  Натисніть Ctrl+C для зупинки сервера")
        
        # Try to open browser automatically
        try:
            webbrowser.open(f'http://localhost:{port}/enhanced_frontend_simple.html')
        except:
            pass
            
        httpd.serve_forever()

if __name__ == "__main__":
    try:
        start_enhanced_server()
    except KeyboardInterrupt:
        print("\n🛑 Сервер зупинено")
    except Exception as e:
        print(f"❌ Помилка: {e}")