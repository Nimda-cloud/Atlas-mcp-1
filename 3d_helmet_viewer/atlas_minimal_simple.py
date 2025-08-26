#!/usr/bin/env python3
"""
Atlas Minimal Frontend Server - Simplified
Мінімалістичний хакерський інтерфейс для Atlas з 3D viewer у фоні
"""

import json
import logging
import time
import subprocess
import threading
import queue
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import requests

# Налаштування    except KeyboardInterrupt:
        print("\n🛑 Server stopping...")
        if live_streamer:
            live_streamer.stop_streaming()
        print("🛑 Server stopped")
        httpd.shutdown()ання
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveLogStreamer:
    """Клас для стрімінгу живих логів системи"""
    
    def __init__(self):
        self.log_queue = queue.Queue()
        self.is_running = False
        self.mcp_proxy_url = "http://localhost:4010"
        self.atlas_core_url = "http://localhost:8000"
        
    def start_streaming(self):
        """Запуск стрімінгу логів"""
        self.is_running = True
        threading.Thread(target=self._system_monitor, daemon=True).start()
        threading.Thread(target=self._mcp_monitor, daemon=True).start()
        threading.Thread(target=self._atlas_monitor, daemon=True).start()
        
    def stop_streaming(self):
        """Зупинка стрімінгу"""
        self.is_running = False
        
    def get_logs(self):
        """Отримання нових логів"""
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return logs
        
    def _add_log(self, message, level="info"):
        """Додавання логу до черги"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        if self.log_queue.qsize() < 100:  # Обмеження розміру черги
            self.log_queue.put({
                "message": log_entry,
                "level": level,
                "timestamp": timestamp
            })
            
    def _system_monitor(self):
        """Моніторинг системи"""
        while self.is_running:
            try:
                # Інформація про процеси
                result = subprocess.run(
                    ["ps", "aux"], 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    atlas_processes = [line for line in lines if 'atlas' in line.lower() and 'grep' not in line]
                    mcp_processes = [line for line in lines if 'mcp' in line and 'grep' not in line]
                    
                    if atlas_processes:
                        self._add_log(f"[ATLAS] {len(atlas_processes)} процесів активно")
                    
                    if mcp_processes:
                        self._add_log(f"[MCP] {len(mcp_processes)} сервісів працює")
                
                # Мережева активність
                try:
                    result = subprocess.run(
                        ["netstat", "-an"], 
                        capture_output=True, 
                        text=True
                    )
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        listening_ports = [line for line in lines if '*.8000' in line or '*.4010' in line or '*.8080' in line]
                        if listening_ports:
                            self._add_log(f"[NET] {len(listening_ports)} портів слухає")
                except:
                    pass
                    
                time.sleep(5)
                
            except Exception as e:
                self._add_log(f"[ERROR] System monitor: {str(e)}", "error")
                time.sleep(10)
                
    def _mcp_monitor(self):
        """Моніторинг MCP сервісів"""
        while self.is_running:
            try:
                # Перевірка MCP proxy
                response = requests.get(f"{self.mcp_proxy_url}/health", timeout=2)
                if response.status_code == 200:
                    self._add_log("[MCP] Proxy online")
                else:
                    self._add_log(f"[MCP] Proxy status: {response.status_code}", "warning")
                    
            except requests.exceptions.ConnectionError:
                self._add_log("[MCP] Proxy offline", "warning")
            except Exception as e:
                self._add_log(f"[MCP] Error: {str(e)[:50]}...", "error")
                
            time.sleep(8)
            
    def _atlas_monitor(self):
        """Моніторинг Atlas Core"""
        while self.is_running:
            try:
                # Перевірка Atlas Core
                response = requests.get(f"{self.atlas_core_url}/health", timeout=2)
                if response.status_code == 200:
                    self._add_log("[ATLAS] Core operational")
                else:
                    self._add_log(f"[ATLAS] Core status: {response.status_code}", "warning")
                    
            except requests.exceptions.ConnectionError:
                self._add_log("[ATLAS] Core offline", "warning")
            except Exception as e:
                self._add_log(f"[ATLAS] Error: {str(e)[:50]}...", "error")
                
            time.sleep(7)

class AtlasMinimalHandler(SimpleHTTPRequestHandler):
    live_streamer = None  # Глобальний стрімер логів
    
    def __init__(self, *args, **kwargs):
        self.mcp_proxy_url = "http://localhost:4010"
        self.atlas_core_url = "http://localhost:8000"
        super().__init__(*args, **kwargs)

    @classmethod
    def set_live_streamer(cls, streamer):
        """Встановлення live streamer"""
        cls.live_streamer = streamer

    def do_GET(self):
        """Обробка GET запитів"""
        if self.path == "/" or self.path == "/index.html":
            self.serve_frontend()
        elif self.path == "/DamagedHelmet.glb":
            self.serve_3d_model()
        elif self.path == "/api/health":
            self.serve_health()
        elif self.path == "/api/logs":
            self.serve_live_logs()
        else:
            super().do_GET()

    def do_POST(self):
        """Обробка POST запитів"""
        if self.path == "/api/chat":
            self.handle_chat()
        elif self.path == "/api/tts/speak":
            self.handle_tts()
        else:
            self.send_error(404, "Not Found")

    def serve_frontend(self):
        """Головна сторінка з мінімалістичним інтерфейсом"""
        try:
            html_path = Path(__file__).parent / "atlas_minimal_frontend.html"
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error serving frontend: {e}")
            self.send_error(500, str(e))

    def serve_3d_model(self):
        """3D модель шолома"""
        try:
            model_path = Path(__file__).parent / "DamagedHelmet.glb"
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "3D model not found")
        except Exception as e:
            logger.error(f"Error serving 3D model: {e}")
            self.send_error(500, str(e))

    def serve_health(self):
        """Перевірка стану сервісів"""
        try:
            services = {
                "atlas_minimal": True,
                "mcp_proxy": self.check_service(self.mcp_proxy_url),
                "atlas_core": self.check_service(self.atlas_core_url),
                "timestamp": datetime.now().isoformat()
            }
            
            response = json.dumps(services).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self.send_error(500, str(e))

    def serve_live_logs(self):
        """Отримання живих логів"""
        try:
            if self.live_streamer is None:
                logs = [{"message": "[SYSTEM] Log streamer not initialized", "level": "warning", "timestamp": datetime.now().strftime("%H:%M:%S")}]
            else:
                logs = self.live_streamer.get_logs()
                if not logs:
                    logs = [{"message": "[SYSTEM] No new logs", "level": "info", "timestamp": datetime.now().strftime("%H:%M:%S")}]
            
            response = json.dumps({"logs": logs}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            logger.error(f"Live logs error: {e}")
            self.send_error(500, str(e))

    def handle_chat(self):
        """Обробка чат запитів"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get("message", "")
            if not message:
                self.send_json_response({"error": "Message is required"}, 400)
                return
            
            # Спробувати MCP proxy спочатку
            response = self.send_to_mcp_proxy(message)
            if response:
                self.send_json_response({"response": response})
                return
            
            # Fallback на Atlas Core
            response = self.send_to_atlas_core(message)
            if response:
                self.send_json_response({"response": response})
                return
            
            self.send_json_response({"response": "Всі сервіси недоступні"})
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            self.send_json_response({"error": str(e)}, 500)

    def handle_tts(self):
        """Обробка TTS запитів"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            text = data.get("text", "")
            if not text:
                self.send_json_response({"error": "Text is required"}, 400)
                return
            
            success = self.send_tts_request(text)
            if success:
                self.send_json_response({"status": "success"})
            else:
                self.send_json_response({"error": "TTS service unavailable"}, 503)
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            self.send_json_response({"error": str(e)}, 500)

    def send_json_response(self, data, status_code=200):
        """Відправка JSON відповіді"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def send_to_mcp_proxy(self, message):
        """Відправлення повідомлення через MCP proxy"""
        try:
            response = requests.post(
                f"{self.mcp_proxy_url}/api/chat",
                json={"message": message},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", data.get("message"))
        except Exception as e:
            logger.debug(f"MCP proxy request failed: {e}")
        return None

    def send_to_atlas_core(self, message):
        """Відправлення повідомлення до Atlas Core"""
        try:
            response = requests.post(
                f"{self.atlas_core_url}/api/chat",
                json={"message": message},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", data.get("message"))
        except Exception as e:
            logger.debug(f"Atlas Core request failed: {e}")
        return None

    def send_tts_request(self, text):
        """TTS запит через MCP proxy"""
        try:
            response = requests.post(
                f"{self.mcp_proxy_url}/api/tts",
                json={"text": text},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"TTS request failed: {e}")
        return False

    def check_service(self, url):
        """Перевірка доступності сервісу"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            return response.status_code < 500
        except:
            return False

def main():
    """Запуск сервера"""
    port = 8080
    server_address = ('', port)
    
    # Зміна робочої директорії
    os.chdir(Path(__file__).parent)
    
    # Ініціалізація live streamer
    live_streamer = LiveLogStreamer()
    AtlasMinimalHandler.set_live_streamer(live_streamer)
    live_streamer.start_streaming()
    
    httpd = HTTPServer(server_address, AtlasMinimalHandler)
    
    print("🚀 Starting Atlas Minimal Frontend Server...")
    print(f"📱 Interface: http://localhost:{port}")
    print("💾 3D Viewer: Background layer")
    print("📋 MCP Logs: Left panel (LIVE)")
    print("💬 Chat: Right panel")
    print("🎤 Voice: Single/Double click modes")
    print(f"🎯 Server running on port {port}")
    print("🟢 Live logs streaming enabled")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopping...")
        if AtlasMinimalHandler.live_streamer:
            AtlasMinimalHandler.live_streamer.stop_streaming()
        print("🛑 Server stopped")
        httpd.shutdown()

if __name__ == "__main__":
    import os
    main()
