#!/usr/bin/env python3
"""
Script to open 3D GLB models with different applications
"""
import os
import subprocess
import sys
from pathlib import Path

def find_glb_files():
    """Find all GLB files in current directory"""
    current_dir = Path('/Users/dev/Documents/GitHub/Atlas-mcp')
    glb_files = list(current_dir.glob('*.glb'))
    return sorted(glb_files)

def open_with_blender(file_path):
    """Try to open GLB file with Blender"""
    blender_paths = [
        '/Applications/Blender.app/Contents/MacOS/Blender',
        '/usr/local/bin/blender',
        'blender'
    ]
    
    for blender_path in blender_paths:
        if os.path.exists(blender_path) or blender_path == 'blender':
            try:
                subprocess.run([blender_path, str(file_path)], check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
    return False

def open_with_finder(file_path):
    """Open GLB file with default macOS application"""
    try:
        subprocess.run(['open', str(file_path)], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def show_online_viewers():
    """Show links to online 3D viewers"""
    viewers = [
        {
            'name': 'glTF Viewer by Don McCurdy',
            'url': 'https://gltf-viewer.donmccurdy.com/',
            'description': 'Найкращий онлайн переглядач GLB/GLTF файлів'
        },
        {
            'name': 'Babylon.js Sandbox',
            'url': 'https://sandbox.babylonjs.com/',
            'description': 'Потужний 3D переглядач з багатьма налаштуваннями'
        },
        {
            'name': 'Three.js Editor',
            'url': 'https://threejs.org/editor/',
            'description': '3D редактор в браузері'
        },
        {
            'name': 'Model Viewer',
            'url': 'https://modelviewer.dev/',
            'description': 'Google Model Viewer для веб-сторінок'
        }
    ]
    
    print("\n🌐 Онлайн переглядачі 3D моделей:")
    print("=" * 50)
    for viewer in viewers:
        print(f"📍 {viewer['name']}")
        print(f"   URL: {viewer['url']}")
        print(f"   {viewer['description']}")
        print()

def main():
    print("🤖 Atlas MCP - 3D Models Viewer")
    print("=" * 40)
    
    # Find GLB files
    glb_files = find_glb_files()
    
    if not glb_files:
        print("❌ GLB файли не знайдено!")
        return
    
    print(f"📦 Знайдено {len(glb_files)} GLB моделей:")
    for i, file in enumerate(glb_files, 1):
        file_size = file.stat().st_size / 1024  # KB
        print(f"  {i}. {file.name} ({file_size:.1f} KB)")
    
    print("\n🎯 Способи перегляду моделей:")
    print("1. 💻 Локальний веб-переглядач (рекомендується)")
    print("2. 🎨 Відкрити з Blender")
    print("3. 🍎 Відкрити з системним додатком (macOS)")
    print("4. 🌐 Показати онлайн переглядачі")
    print("5. 📋 Показати інструкції")
    print("0. ❌ Вихід")
    
    while True:
        try:
            choice = input("\n👉 Оберіть опцію (0-5): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                print("\n🚀 Запускаю локальний веб-сервер...")
                os.system('python3 start_3d_viewer.py')
            elif choice == '2':
                print("\n📋 Доступні GLB файли:")
                for i, file in enumerate(glb_files, 1):
                    print(f"  {i}. {file.name}")
                
                try:
                    file_choice = int(input("Оберіть номер файлу: ")) - 1
                    if 0 <= file_choice < len(glb_files):
                        selected_file = glb_files[file_choice]
                        print(f"🎨 Відкриваю {selected_file.name} в Blender...")
                        if open_with_blender(selected_file):
                            print("✅ Blender запущено успішно!")
                        else:
                            print("❌ Blender не знайдено. Встановіть Blender з https://www.blender.org/")
                    else:
                        print("❌ Невірний номер файлу!")
                except ValueError:
                    print("❌ Введіть правильний номер!")
            elif choice == '3':
                print("\n📋 Доступні GLB файли:")
                for i, file in enumerate(glb_files, 1):
                    print(f"  {i}. {file.name}")
                
                try:
                    file_choice = int(input("Оберіть номер файлу: ")) - 1
                    if 0 <= file_choice < len(glb_files):
                        selected_file = glb_files[file_choice]
                        print(f"🍎 Відкриваю {selected_file.name} системним додатком...")
                        if open_with_finder(selected_file):
                            print("✅ Файл відкрито!")
                        else:
                            print("❌ Не вдалося відкрити файл!")
                    else:
                        print("❌ Невірний номер файлу!")
                except ValueError:
                    print("❌ Введіть правильний номер!")
            elif choice == '4':
                show_online_viewers()
            elif choice == '5':
                print("\n📋 Інструкції для перегляду 3D моделей:")
                print("=" * 50)
                print("1. 💻 Локальний веб-переглядач:")
                print("   - Запустіть опцію 1")
                print("   - Відкриється браузер з інтерактивним переглядачем")
                print("   - Перетягуйте мишею для обертання")
                print("   - Колесо миші для масштабування")
                print()
                print("2. 🎨 Blender (професійний 3D редактор):")
                print("   - Скачайте з https://www.blender.org/")
                print("   - File → Import → glTF 2.0 (.glb/.gltf)")
                print()
                print("3. 🌐 Онлайн переглядачі:")
                print("   - Завантажте GLB файл на один з сайтів")
                print("   - Дивіться список в опції 4")
                print()
                print("4. 📱 VS Code:")
                print("   - Встановіть розширення 'glTF Tools'")
                print("   - Клікніть на GLB файл в Explorer")
                print()
            else:
                print("❌ Невірна опція! Оберіть 0-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 До побачення!")
            break

if __name__ == "__main__":
    main()
