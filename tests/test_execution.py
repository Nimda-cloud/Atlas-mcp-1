#!/usr/bin/env python3
"""
Тестування нової системи виконання завдань Atlas MCP
"""

import asyncio
import json
import aiohttp
import os

async def test_atlas_execution():
    """Тестуємо нову систему виконання завдань"""
    
    print("🧪 Тестування Atlas MCP виконання завдань...")
    
    # Тестові команди
    test_commands = [
        "відкрий хром",
        "open chrome browser", 
        "launch safari",
        "говори привіт"
    ]
    
    # URL Atlas API в Kubernetes
    atlas_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print(f"\n📡 Підключення до Atlas API: {atlas_url}")
        
        # Перевіряємо статус
        try:
            async with session.get(f"{atlas_url}/status") as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"✅ Atlas онлайн: {status['agents_online']} агентів, {status['mcp']['count_online']} MCP сервісів")
                else:
                    print(f"❌ Atlas недоступний: HTTP {response.status}")
                    return
        except Exception as e:
            print(f"❌ Помилка підключення: {e}")
            return
        
        # Тестуємо кожну команду
        for i, command in enumerate(test_commands, 1):
            print(f"\n🔄 Тест {i}: '{command}'")
            
            try:
                async with session.post(
                    f"{atlas_url}/chat",
                    json={"message": command},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        print(f"📝 Відповідь Atlas:")
                        
                        # Показуємо відповідь по частинах
                        lines = response_text.split('\n')
                        for line in lines:
                            if line.strip():
                                if "Interface Agent:" in line:
                                    print(f"   🤖 LLM1 (Interface): {line.split('Interface Agent:')[1].strip()}")
                                elif "Orchestrator (gpt-oss):" in line:
                                    print(f"   🧠 LLM2 (gpt-oss): {line.split('Orchestrator (gpt-oss):')[1].strip()}")
                                elif "✅" in line:
                                    print(f"   {line}")
                                elif "❌" in line:
                                    print(f"   {line}")
                                else:
                                    print(f"   {line}")
                        
                        # Перевіряємо, чи були виконані дії
                        if "✅ Успішно виконано" in response_text:
                            print(f"   🎉 Завдання виконано успішно!")
                        elif "❌ Помилки у" in response_text:
                            print(f"   ⚠️  Є помилки у виконанні")
                        else:
                            print(f"   ℹ️  Відповідь без виконання дій")
                    else:
                        error_text = await response.text()
                        print(f"❌ Помилка API: HTTP {response.status} - {error_text}")
                        
            except asyncio.TimeoutError:
                print(f"⏰ Таймаут при виконанні команди")
            except Exception as e:
                print(f"❌ Помилка при тестуванні: {e}")
    
    print(f"\n✨ Тестування завершено!")

if __name__ == "__main__":
    asyncio.run(test_atlas_execution())
