#!/usr/bin/env python3
"""
Адаптивне управління нічним освітленням 3D шолома через Playwright
"""
import asyncio
import random
import time

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright не встановлено. Запустіть: pip install playwright")
    exit(1)

class NightLightingController:
    def __init__(self):
        self.browser = None
        self.page = None
        self.is_running = False
        
    async def start(self, url="http://localhost:8080/3d_viewer.html"):
        """Запуск контролера освітлення"""
        try:
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(headless=False)
                self.page = await self.browser.new_page()
                
                # Відкриваємо 3D viewer
                await self.page.goto(url)
                await self.page.wait_for_timeout(2000)  # Дочекатися завантаження моделі
                
                print("🌙 Нічне освітлення активовано")
                print("🔦 Ліхтарики працюють")
                print("👁️ Око шолома світиться")
                print("⏹️ Натисніть Ctrl+C для зупинки")
                
                self.is_running = True
                
                # Запускаємо цикл адаптивного освітлення
                await self.adaptive_lighting_loop()
        except Exception as e:
            print(f"❌ Помилка запуску: {e}")
    
    async def adaptive_lighting_loop(self):
        """Основний цикл адаптивного освітлення"""
        while self.is_running:
            try:
                # Випадково змінюємо інтенсивність ліхтариків
                await self.adjust_flashlights()
                
                # Змінюємо пульсацію ока
                await self.adjust_eye_glow()
                
                # Додаємо атмосферні ефекти
                await self.add_atmospheric_effects()
                
                # Пауза між змінами
                await self.page.wait_for_timeout(random.randint(2000, 5000))
                
            except Exception as e:
                print(f"❌ Помилка в циклі: {e}")
                break
    
    async def adjust_flashlights(self):
        """Адаптивне налаштування ліхтариків"""
        if not self.page:
            return
            
        # Випадкова інтенсивність для лівого ліхтарика
        left_intensity = random.uniform(0.2, 0.8)
        left_size = random.uniform(150, 250)
        
        # Випадкова інтенсивність для правого ліхтарика  
        right_intensity = random.uniform(0.1, 0.6)
        right_size = random.uniform(100, 200)
        
        js_code = f"""
            const leftFlashlight = document.querySelector('.flashlight-left');
            const rightFlashlight = document.querySelector('.flashlight-right');
            
            if (leftFlashlight) {{
                leftFlashlight.style.opacity = '{left_intensity}';
                leftFlashlight.style.width = '{left_size}px';
                leftFlashlight.style.height = '{left_size}px';
            }}
            
            if (rightFlashlight) {{
                rightFlashlight.style.opacity = '{right_intensity}';
                rightFlashlight.style.width = '{right_size}px';
                rightFlashlight.style.height = '{right_size}px';
            }}
        """
        await self.page.evaluate(js_code)
    
    async def adjust_eye_glow(self):
        """Адаптивне налаштування світіння ока"""
        if not self.page:
            return
            
        # Випадкова інтенсивність та розмір ока
        eye_intensity = random.uniform(0.4, 1.0)
        eye_size = random.uniform(20, 40)
        eye_blur = random.uniform(1, 4)
        
        # Випадковий колір (зелений спектр)
        green_value = random.randint(200, 255)
        
        js_code = f"""
            const eyeGlow = document.querySelector('.eye-glow');
            if (eyeGlow) {{
                eyeGlow.style.opacity = '{eye_intensity}';
                eyeGlow.style.width = '{eye_size}px';
                eyeGlow.style.height = '{eye_size}px';
                eyeGlow.style.filter = 'blur({eye_blur}px)';
                eyeGlow.style.background = 'radial-gradient(circle, rgba(0,{green_value},100,0.8) 0%, rgba(0,{green_value},100,0.3) 50%, transparent 80%)';
            }}
        """
        await self.page.evaluate(js_code)
    
    async def add_atmospheric_effects(self):
        """Додавання атмосферних ефектів"""
        if not self.page:
            return
            
        # Випадкове регулювання загальної атмосфери
        fog_intensity = random.uniform(0.01, 0.05)
        
        js_code = f"""
            const body = document.body;
            body.style.setProperty('--fog-intensity', '{fog_intensity}');
        """
        await self.page.evaluate(js_code)
        
        # Іноді додаємо ефект "блимання" ліхтариків
        if random.random() < 0.3:  # 30% ймовірність
            await self.flashlight_flicker()
    
    async def flashlight_flicker(self):
        """Ефект блимання ліхтариків"""
        if not self.page:
            return
            
        # Швидке блимання лівого ліхтарика
        for _ in range(3):
            await self.page.evaluate("""
                const leftFlashlight = document.querySelector('.flashlight-left');
                if (leftFlashlight) leftFlashlight.style.opacity = '0.1';
            """)
            await self.page.wait_for_timeout(100)
            
            await self.page.evaluate("""
                const leftFlashlight = document.querySelector('.flashlight-left');
                if (leftFlashlight) leftFlashlight.style.opacity = '0.7';
            """)
            await self.page.wait_for_timeout(150)
    
    async def stop(self):
        """Зупинка контролера"""
        self.is_running = False
        if self.browser:
            await self.browser.close()
        print("🌙 Нічне освітлення вимкнено")

async def main():
    controller = NightLightingController()
    
    try:
        await controller.start()
    except KeyboardInterrupt:
        print("\n🛑 Зупинка контролера...")
        await controller.stop()
    except Exception as e:
        print(f"❌ Помилка: {e}")
        await controller.stop()

if __name__ == "__main__":
    asyncio.run(main())
