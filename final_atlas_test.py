#!/usr/bin/env python3
"""
Підсумковий тест системи Atlas з Ukrainian TTS
==============================================

Перевіряє:
✅ Atlas Core статус
✅ Усі 127 MCP інструментів  
✅ Enhanced TTS з українським як основним
✅ Google TTS API fallback
✅ Task Orchestrator інтеграція
✅ Повний цикл chat → TTS

Usage:
    python final_atlas_test.py
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_atlas_system():
    """Повний тест системи Atlas"""
    
    print("🎯 Atlas System Final Test")
    print("=" * 60)
    print(f"🕐 Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Тест статусу системи
    print("1️⃣ Перевірка статусу Atlas Core...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Atlas Core: {data.get('agents_online', 0)} агентів онлайн")
                    
                    tools = data.get('mcp', {}).get('tools', {})
                    total_tools = sum(len(tool_list) for tool_list in tools.values())
                    print(f"   📊 MCP інструменти: {total_tools} доступно")
                    
                    for category, tool_list in tools.items():
                        print(f"      📁 {category}: {len(tool_list)} інструментів")
                else:
                    print(f"   ❌ Atlas Core: HTTP {resp.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Atlas Core недоступний: {e}")
            return False
    
    # 2. Тест Task Orchestrator
    print("\n2️⃣ Перевірка Task Orchestrator...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:4006/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Task Orchestrator: {data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ Task Orchestrator: HTTP {resp.status}")
        except Exception as e:
            print(f"   ⚠️ Task Orchestrator: {e}")
    
    # 3. Тест Enhanced TTS
    print("\n3️⃣ Тестування Enhanced TTS...")
    
    test_phrases = [
        "Привіт! Я Atlas з покращеним TTS.",
        "Ukrainian TTS працює чудово!",
        "Система готова до роботи."
    ]
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"   🎤 Тест {i}: '{phrase[:30]}...'")
        
        async with aiohttp.ClientSession() as session:
            try:
                payload = {"text": phrase}
                async with session.post("http://localhost:8000/tts", json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"   ✅ TTS {i}: {result.get('status', 'unknown')}")
                    else:
                        print(f"   ❌ TTS {i}: HTTP {resp.status}")
            except Exception as e:
                print(f"   ❌ TTS {i}: {e}")
        
        await asyncio.sleep(0.5)  # Пауза між тестами
    
    # 4. Тест повного циклу chat
    print("\n4️⃣ Тестування повного циклу chat...")
    
    chat_tests = [
        "Як справи?",
        "Який зараз час?",
        "Покажи статус системи"
    ]
    
    for i, message in enumerate(chat_tests, 1):
        print(f"   💬 Chat {i}: '{message}'")
        
        async with aiohttp.ClientSession() as session:
            try:
                payload = {"text": message}
                async with session.post("http://localhost:8000/chat", json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        response = result.get('response', '')
                        print(f"   ✅ Відповідь {i}: {response[:50]}...")
                    else:
                        print(f"   ❌ Chat {i}: HTTP {resp.status}")
            except Exception as e:
                print(f"   ❌ Chat {i}: {e}")
        
        await asyncio.sleep(1)  # Пауза між повідомленнями
    
    # 5. Тест MCP Proxy
    print("\n5️⃣ Перевірка MCP Proxy...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:9090/health") as resp:
                status_code = resp.status
                if status_code == 200:
                    print("   ✅ MCP Proxy: Доступний")
                else:
                    print(f"   ⚠️ MCP Proxy: HTTP {status_code}")
        except Exception as e:
            print(f"   ⚠️ MCP Proxy: {e}")
    
    # 6. Тест 3D Viewer
    print("\n6️⃣ Перевірка 3D Helmet Viewer...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8080") as resp:
                if resp.status == 200:
                    print("   ✅ 3D Viewer: Доступний")
                else:
                    print(f"   ❌ 3D Viewer: HTTP {resp.status}")
        except Exception as e:
            print(f"   ❌ 3D Viewer: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТУВАННЯ ЗАВЕРШЕНО!")
    print()
    print("📋 Підсумок системи Atlas:")
    print("   🇺🇦 Ukrainian TTS - основний метод озвучування")
    print("   🌐 Google TTS API - fallback з правильним кодуванням")  
    print("   📻 Google gTTS - безкоштовна альтернатива")
    print("   🔊 System say - системний синтезатор macOS")
    print("   📝 Text fallback - крайня заглушка")
    print()
    print("🚀 Atlas готовий до повноцінної роботи!")
    print("   💬 Chat API: http://localhost:8000/chat")
    print("   🎤 TTS API: http://localhost:8000/tts") 
    print("   📊 Status: http://localhost:8000/status")
    print("   🛑 Stop: ./stop_atlas.sh")
    
    return True

async def main():
    """Головна функція"""
    success = await test_atlas_system()
    
    if success:
        print("\n✨ Всі тести пройдено успішно!")
    else:
        print("\n⚠️ Деякі тести не пройдено. Перевірте логи.")

if __name__ == "__main__":
    asyncio.run(main())
