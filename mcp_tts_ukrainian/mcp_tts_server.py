#!/usr/bin/env python3
"""
Ukrainian TTS MCP Server
=========================

Надає TTS (Text-to-Speech) можливості з підтримкою української мови:
- Основний движок: robinhad/ukrainian-tts
- Fallback: Google TTS (gTTS)
- Підтримка MCP протоколу

Автор: Atlas AI Team
"""

import asyncio
import io
import json
import logging
import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

import pygame
import requests
from gtts import gTTS

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UkrainianTTSEngine:
    """Движок для української TTS з підтримкою fallback на Google TTS"""
    
    def __init__(self):
        self.ukrainian_tts = None
        self.pygame_initialized = False
        self._init_ukrainian_tts()
        self._init_pygame()
    
    def _init_ukrainian_tts(self):
        """Ініціалізація українського TTS"""
        try:
            from ukrainian_tts.tts import TTS
            self.ukrainian_tts = TTS(device='cpu')  # Використовуємо CPU для сумісності
            logger.info("✅ Ukrainian TTS initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Ukrainian TTS initialization failed: {e}")
            self.ukrainian_tts = None
    
    def _init_pygame(self):
        """Ініціалізація pygame для відтворення звуку"""
        try:
            pygame.mixer.init()
            self.pygame_initialized = True
            logger.info("✅ Pygame audio initialized")
        except Exception as e:
            logger.warning(f"⚠️ Pygame initialization failed: {e}")
            self.pygame_initialized = False
    
    async def speak_ukrainian(self, text: str, voice: str = "mykyta") -> bool:
        """
        Озвучування тексту українською TTS
        
        Args:
            text: Текст для озвучування
            voice: Голос (mykyta, oleksa, tetiana, lada)
        
        Returns:
            bool: True якщо успішно, False якщо помилка
        """
        if not self.ukrainian_tts:
            logger.warning("Ukrainian TTS not available, falling back to Google TTS")
            return await self.speak_google(text, lang='uk')
        
        try:
            # Створення тимчасового файлу
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Генерація через ukrainian-tts з правильними параметрами
            with open(temp_path, 'wb') as output_file:
                self.ukrainian_tts.tts(text, voice, "dictionary", output_file)
            
            # Відтворення
            if self.pygame_initialized:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                # Чекаємо закінчення відтворення
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            
            # Очищення тимчасового файлу
            Path(temp_path).unlink(missing_ok=True)
            
            logger.info("✅ Ukrainian TTS playback completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ukrainian TTS failed: {e}")
            return await self.speak_google(text, lang='uk')
    
    async def speak_google(self, text: str, lang: str = 'uk') -> bool:
        """
        Fallback озвучування через Google TTS
        
        Args:
            text: Текст для озвучування
            lang: Мова (uk, en, ru)
        
        Returns:
            bool: True якщо успішно, False якщо помилка
        """
        try:
            logger.info(f"🌐 Using Google TTS fallback for: {text[:50]}...")
            
            # Генерація через gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            tts.save(temp_path)
            
            # Відтворення
            if self.pygame_initialized:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                # Чекаємо закінчення відтворення
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            
            # Очищення
            Path(temp_path).unlink(missing_ok=True)
            
            logger.info("✅ Google TTS playback completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Google TTS failed: {e}")
            return False
    
    async def speak(self, text: str, voice: str = "mykyta", lang: str = "uk") -> Dict[str, Any]:
        """
        Головний метод для озвучування
        
        Args:
            text: Текст для озвучування
            voice: Голос для українського TTS
            lang: Мова (uk, en, ru)
        
        Returns:
            Dict з результатом операції
        """
        if not text.strip():
            return {"status": "error", "message": "Empty text provided"}
        
        try:
            # Спробувати українську TTS для української мови
            if lang == 'uk':
                success = await self.speak_ukrainian(text, voice)
            else:
                # Для інших мов використовувати Google TTS
                success = await self.speak_google(text, lang)
            
            if success:
                return {
                    "status": "success", 
                    "message": f"Successfully spoke: {text[:50]}{'...' if len(text) > 50 else ''}",
                    "engine": "ukrainian-tts" if lang == 'uk' and self.ukrainian_tts else "google-tts",
                    "voice": voice if lang == 'uk' else "default",
                    "language": lang
                }
            else:
                return {
                    "status": "error", 
                    "message": "All TTS engines failed",
                    "text": text[:100]
                }
                
        except Exception as e:
            logger.error(f"TTS speak error: {e}")
            return {
                "status": "error", 
                "message": str(e),
                "text": text[:100]
            }


class MCPTTSServer:
    """MCP сервер для українського TTS"""
    
    def __init__(self):
        self.tts_engine = UkrainianTTSEngine()
        logger.info("🎙️ Ukrainian TTS MCP Server initialized")
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Отримання списку доступних інструментів"""
        return {
            "tools": {
                "say_tts": {
                    "description": "Text-to-speech using Ukrainian TTS with Google TTS fallback",
                    "parameters": {
                        "text": {"type": "string", "description": "Text to speak"},
                        "voice": {
                            "type": "string", 
                            "description": "Voice for Ukrainian TTS", 
                            "enum": ["mykyta", "oleksa", "tetiana", "lada"],
                            "default": "mykyta"
                        },
                        "lang": {
                            "type": "string",
                            "description": "Language code",
                            "enum": ["uk", "en", "ru"],
                            "default": "uk"
                        },
                        "rate": {"type": "number", "description": "Speech rate (ignored, for compatibility)", "default": 200}
                    },
                    "required": ["text"]
                },
                "list_voices": {
                    "description": "List available voices",
                    "parameters": {},
                    "required": []
                },
                "tts_status": {
                    "description": "Get TTS engine status",
                    "parameters": {},
                    "required": []
                }
            }
        }
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Виклик інструменту"""
        try:
            if tool_name == "say_tts":
                text = args.get("text", "")
                voice = args.get("voice", "mykyta")
                lang = args.get("lang", "uk")
                
                return await self.tts_engine.speak(text, voice, lang)
            
            elif tool_name == "list_voices":
                return {
                    "status": "success",
                    "voices": {
                        "ukrainian": ["mykyta", "oleksa", "tetiana", "lada"],
                        "google": ["default (per language)"]
                    },
                    "languages": ["uk", "en", "ru"]
                }
            
            elif tool_name == "tts_status":
                return {
                    "status": "success",
                    "engines": {
                        "ukrainian_tts": self.tts_engine.ukrainian_tts is not None,
                        "google_tts": True,
                        "pygame_audio": self.tts_engine.pygame_initialized
                    },
                    "primary_engine": "ukrainian-tts" if self.tts_engine.ukrainian_tts else "google-tts"
                }
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }


async def main():
    """Головна функція MCP сервера"""
    server = MCPTTSServer()
    
    logger.info("🚀 Starting Ukrainian TTS MCP Server...")
    
    # MCP протокол через stdin/stdout
    while True:
        try:
            # Читання запиту з stdin
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            
            # Обробка запиту
            if request.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": server.get_available_tools()
                }
            
            elif request.get("method") == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                result = await server.call_tool(tool_name, args)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False)
                            }
                        ]
                    }
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {request.get('method')}"
                    }
                }
            
            # Відправка відповіді
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
            
        except EOFError:
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
