#!/usr/bin/env python3
"""
Enhanced Ukrainian TTS with Intelligent Fallbacks
==================================================

Ієрархія TTS:
1. 🇺🇦 Ukrainian TTS (robinhad/ukrainian-tts) - локальний
2. 🌐 Google TTS API - fallback з правильним кодуванням
3. 🔊 System say command - крайня заглушка
4. 📝 Text output - якщо все не працює

Автор: Atlas AI Team
"""

import asyncio
import base64
import io
import json
import logging
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pygame
import requests

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTTSEngine:
    """Покращений TTS движок з інтелектуальними fallback механізмами"""
    
    def __init__(self):
        self.ukrainian_tts = None
        self.pygame_initialized = False
        self.google_api_key = os.getenv('GOOGLE_TTS_API_KEY')
        self.google_available = bool(self.google_api_key)
        
        self._init_ukrainian_tts()
        self._init_pygame()
        self._test_system_say()
    
    def _init_ukrainian_tts(self):
        """Ініціалізація українського TTS"""
        try:
            from ukrainian_tts.tts import TTS
            self.ukrainian_tts = TTS(device='cpu')
            logger.info("✅ Ukrainian TTS initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Ukrainian TTS initialization failed: {e}")
            self.ukrainian_tts = None
    
    def _init_pygame(self):
        """Ініціалізація pygame для відтворення звуку"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.pygame_initialized = True
            logger.info("✅ Pygame audio initialized")
        except Exception as e:
            logger.warning(f"⚠️ Pygame initialization failed: {e}")
            self.pygame_initialized = False
    
    def _test_system_say(self):
        """Перевірка доступності system say command"""
        try:
            result = subprocess.run(['say', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.system_say_available = True
                logger.info("✅ System 'say' command available")
            else:
                self.system_say_available = False
        except Exception:
            self.system_say_available = False
            logger.warning("⚠️ System 'say' command not available")
    
    async def speak_ukrainian_local(self, text: str, voice: str = "mykyta") -> Tuple[bool, str]:
        """
        1️⃣ Спроба озвучування через локальний Ukrainian TTS
        
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if not self.ukrainian_tts:
            return False, "Ukrainian TTS not initialized"
        
        try:
            logger.info(f"🇺🇦 Trying Ukrainian TTS: {text[:50]}...")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Генерація аудіо
            with open(temp_path, 'wb') as output_file:
                self.ukrainian_tts.tts(text, voice, "dictionary", output_file)
            
            # Відтворення
            if self.pygame_initialized:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            
            # Очищення
            Path(temp_path).unlink(missing_ok=True)
            
            logger.info("✅ Ukrainian TTS succeeded")
            return True, "Success"
            
        except Exception as e:
            error_msg = f"Ukrainian TTS error: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    async def speak_google_api(self, text: str, lang: str = "uk-UA") -> Tuple[bool, str]:
        """
        2️⃣ Fallback через Google TTS API з правильним кодуванням
        
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if not self.google_available:
            return False, "Google API key not provided"
        
        try:
            logger.info(f"🌐 Trying Google TTS API: {text[:50]}...")
            
            # Правильний формат запиту до Google TTS API
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.google_api_key}"
            
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": lang,
                    "name": f"{lang}-Standard-A"  # Жіночий голос
                },
                "audioConfig": {
                    "audioEncoding": "MP3"
                }
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code != 200:
                try:
                    error_info = response.json()
                    return False, f"Google API error {response.status_code}: {error_info}"
                except:
                    return False, f"Google API error {response.status_code}: {response.text}"
            
            # Правильне декодування відповіді
            response_data = response.json()
            
            if "audioContent" not in response_data:
                return False, "No audioContent in Google API response"
            
            # Декодування base64
            audio_data = base64.b64decode(response_data["audioContent"])
            
            # Збереження і відтворення
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_data)
            
            if self.pygame_initialized:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            
            # Очищення
            Path(temp_path).unlink(missing_ok=True)
            
            logger.info("✅ Google TTS API succeeded")
            return True, "Success"
            
        except Exception as e:
            error_msg = f"Google TTS API error: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    async def speak_google_gtts(self, text: str, lang: str = "uk") -> Tuple[bool, str]:
        """
        3️⃣ Fallback через Google TTS (gTTS library)
        
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            from gtts import gTTS
            logger.info(f"📻 Trying Google gTTS: {text[:50]}...")
            
            tts = gTTS(text=text, lang=lang, slow=False)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            tts.save(temp_path)
            
            if self.pygame_initialized:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            
            Path(temp_path).unlink(missing_ok=True)
            
            logger.info("✅ Google gTTS succeeded")
            return True, "Success"
            
        except Exception as e:
            error_msg = f"Google gTTS error: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    async def speak_system_say(self, text: str) -> Tuple[bool, str]:
        """
        4️⃣ Fallback через system say command
        
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if not self.system_say_available:
            return False, "System say command not available"
        
        try:
            logger.info(f"🔊 Trying system say: {text[:50]}...")
            
            # Запускаємо say асинхронно
            process = await asyncio.create_subprocess_exec(
                'say', text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("✅ System say succeeded")
                return True, "Success"
            else:
                error_msg = f"System say failed: {stderr.decode()}"
                return False, error_msg
                
        except Exception as e:
            error_msg = f"System say error: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def speak_text_fallback(self, text: str) -> Tuple[bool, str]:
        """
        5️⃣ Крайня заглушка - просто виводимо текст
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        logger.warning(f"📝 All TTS failed, text output: {text}")
        print(f"🔊 TTS: {text}")
        return True, "Text output fallback"
    
    async def speak(self, text: str, voice: str = "mykyta", lang: str = "uk") -> Dict[str, Any]:
        """
        Головний метод з інтелектуальною ієрархією fallback
        
        Args:
            text: Текст для озвучування
            voice: Голос для українського TTS
            lang: Мова для Google TTS
        
        Returns:
            Dict з результатом та метаданими
        """
        if not text.strip():
            return {
                "success": False,
                "error": "Empty text provided",
                "method": "none"
            }
        
        # Логуємо спробу
        logger.info(f"🎤 TTS Request: '{text[:100]}...' (voice: {voice}, lang: {lang})")
        
        # 1️⃣ Спробуємо Ukrainian TTS
        success, error = await self.speak_ukrainian_local(text, voice)
        if success:
            return {
                "success": True,
                "method": "ukrainian_local",
                "voice": voice,
                "text": text
            }
        
        # 2️⃣ Спробуємо Google TTS API
        if lang == "uk":
            success, error = await self.speak_google_api(text, "uk-UA")
            if success:
                return {
                    "success": True,
                    "method": "google_api",
                    "lang": "uk-UA",
                    "text": text
                }
        
        # 3️⃣ Спробуємо Google gTTS
        success, error = await self.speak_google_gtts(text, lang)
        if success:
            return {
                "success": True,
                "method": "google_gtts",
                "lang": lang,
                "text": text
            }
        
        # 4️⃣ Спробуємо system say
        success, error = await self.speak_system_say(text)
        if success:
            return {
                "success": True,
                "method": "system_say",
                "text": text
            }
        
        # 5️⃣ Крайня заглушка
        success, message = self.speak_text_fallback(text)
        return {
            "success": True,
            "method": "text_fallback",
            "message": message,
            "text": text
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Статус всіх TTS движків"""
        return {
            "ukrainian_tts": bool(self.ukrainian_tts),
            "pygame": self.pygame_initialized,
            "google_api": self.google_available,
            "google_gtts": True,  # gTTS завжди доступна якщо є інтернет
            "system_say": self.system_say_available,
            "fallback_order": [
                "ukrainian_local",
                "google_api",
                "google_gtts", 
                "system_say",
                "text_fallback"
            ]
        }

# MCP Server Implementation
class TTSMCPServer:
    """MCP Server для TTS функціональності"""
    
    def __init__(self):
        self.tts_engine = EnhancedTTSEngine()
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Обробка MCP запитів"""
        
        if method == "say_tts":
            text = params.get("text", "")
            voice = params.get("voice", "mykyta")
            lang = params.get("lang", "uk")
            rate = params.get("rate", 200)  # Backward compatibility
            
            result = await self.tts_engine.speak(text, voice, lang)
            return result
            
        elif method == "stop_tts":
            if self.tts_engine.pygame_initialized:
                pygame.mixer.music.stop()
            return {"success": True, "message": "TTS stopped"}
            
        elif method == "tts_status":
            return self.tts_engine.get_status()
            
        elif method == "list_voices":
            return {
                "ukrainian_voices": ["mykyta", "oleksa", "tetiana", "lada"],
                "google_voices": ["uk-UA", "en-US", "ru-RU"],
                "current_engine": "enhanced_multi_fallback"
            }
            
        else:
            return {"success": False, "error": f"Unknown method: {method}"}

# Main entry point
async def main():
    """Основна функція для запуску MCP сервера"""
    server = TTSMCPServer()
    
    logger.info("🚀 Enhanced Ukrainian TTS MCP Server started")
    logger.info(f"📊 TTS Status: {server.tts_engine.get_status()}")
    
    # Тестовий запуск
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_text = "Привіт! Це тест нового TTS движка з інтелектуальними fallback механізмами."
        result = await server.handle_request("say_tts", {"text": test_text})
        logger.info(f"🎯 Test result: {result}")
    
    # TODO: Тут має бути основний MCP цикл
    logger.info("✅ TTS MCP Server ready")

if __name__ == "__main__":
    asyncio.run(main())
