#!/usr/bin/env python3
"""
Простий HTTP сервер для мінімального фронтенду Atlas MCP
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_minimal_frontend():
    """Запуск мінімального фронтенду"""
    
    # Перевіряємо, чи існує файл
    frontend_file = Path(__file__).parent / "frontend-minimal.html"
    if not frontend_file.exists():
        print("❌ Файл frontend-minimal.html не знайдено!")
        return
    
    # Налаштування сервера
    PORT = 3052
    Handler = CustomHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🚀 Мінімальний фронтенд Atlas MCP запущено!")
            print(f"📱 URL: http://localhost:{PORT}/frontend-minimal.html")
            print(f"🛑 Натисніть Ctrl+C для зупинки")
            print("-" * 50)
            
            # Автоматично відкрити браузер
            webbrowser.open(f"http://localhost:{PORT}/frontend-minimal.html")
            
            # Запустити сервер
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n✅ Сервер зупинено")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Порт {PORT} вже використовується!")
            print("Спробуйте зупинити інші сервери або змініть порт")
        else:
            print(f"❌ Помилка запуску сервера: {e}")

if __name__ == "__main__":
    start_minimal_frontend()
