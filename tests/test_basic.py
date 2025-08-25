#!/usr/bin/env python3
"""
Atlas System Basic Test
======================

Basic test script to verify Atlas code structure and syntax without external dependencies.
"""

import sys
import os
import ast
import json
from pathlib import Path

def test_python_syntax():
    """Test Python syntax of all Python files"""
    print("🧪 Testing Python syntax...")
    
    python_files = [
        'atlas_core.py',
        'mcp_automation_server.py', 
        'mcp_macos_automator.py'
    ]
    
    for file in python_files:
        if not os.path.exists(file):
            print(f"❌ Missing file: {file}")
            return False
        
        try:
            with open(file, 'r') as f:
                source = f.read()
            
            # Parse AST to check syntax
            ast.parse(source)
            print(f"✅ {file} syntax valid")
            
        except SyntaxError as e:
            print(f"❌ Syntax error in {file}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error checking {file}: {e}")
            return False
    
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("🧪 Testing file structure...")
    
    required_files = [
        'atlas_core.py',
        'mcp_automation_server.py',
        'mcp_macos_automator.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'docker-entrypoint.sh',
        'install_macos.sh',
        'start_atlas.sh',
        'README.md',
        'ІНСТРУКЦІЯ.md',
        '.gitignore'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ {file} exists")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def test_shell_scripts():
    """Test that shell scripts have proper shebang and are executable"""
    print("🧪 Testing shell scripts...")
    
    shell_scripts = [
        'install_macos.sh',
        'start_atlas.sh', 
        'docker-entrypoint.sh'
    ]
    
    for script in shell_scripts:
        if not os.path.exists(script):
            print(f"❌ Missing script: {script}")
            return False
        
        # Check if executable
        if not os.access(script, os.X_OK):
            print(f"❌ Script not executable: {script}")
            return False
        
        # Check shebang
        with open(script, 'r') as f:
            first_line = f.readline().strip()
        
        if not first_line.startswith('#!'):
            print(f"❌ Missing shebang in {script}")
            return False
        
        print(f"✅ {script} is properly configured")
    
    return True

def test_requirements_format():
    """Test requirements.txt format"""
    print("🧪 Testing requirements.txt format...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    try:
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()
        
        # Basic checks
        key_packages = ['ollama', 'fastapi', 'uvicorn', 'aiohttp']
        found_packages = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                package_name = line.split('>=')[0].split('==')[0].split('[')[0]
                found_packages.append(package_name)
        
        missing_packages = []
        for package in key_packages:
            if package not in found_packages:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing key packages: {', '.join(missing_packages)}")
            return False
        
        print(f"✅ requirements.txt contains {len(found_packages)} packages")
        return True
        
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def test_docker_files():
    """Test Docker configuration files"""
    print("🧪 Testing Docker files...")
    
    # Test Dockerfile
    if not os.path.exists('Dockerfile'):
        print("❌ Dockerfile not found")
        return False
    
    with open('Dockerfile', 'r') as f:
        dockerfile_content = f.read()
    
    if 'FROM python:' not in dockerfile_content:
        print("❌ Dockerfile missing Python base image")
        return False
    
    if 'COPY requirements.txt' not in dockerfile_content:
        print("❌ Dockerfile not copying requirements.txt")
        return False
    
    print("✅ Dockerfile looks valid")
    
    # Test docker-compose.yml
    if not os.path.exists('docker-compose.yml'):
        print("❌ docker-compose.yml not found")
        return False
    
    with open('docker-compose.yml', 'r') as f:
        compose_content = f.read()
    
    if 'atlas-core:' not in compose_content:
        print("❌ docker-compose.yml missing atlas-core service")
        return False
    
    if '8000:8000' not in compose_content:
        print("❌ docker-compose.yml missing port mapping")
        return False
    
    print("✅ docker-compose.yml looks valid")
    return True

def test_documentation():
    """Test documentation files"""
    print("🧪 Testing documentation...")
    
    # Test README.md
    if not os.path.exists('README.md'):
        print("❌ README.md not found")
        return False
    
    with open('README.md', 'r') as f:
        readme_content = f.read()
    
    if '# 🤖 Atlas Autonomous System' not in readme_content:
        print("❌ README.md missing proper title")
        return False
    
    if 'Installation' not in readme_content:
        print("❌ README.md missing installation instructions")
        return False
    
    print("✅ README.md looks valid")
    
    # Test Ukrainian instructions
    if not os.path.exists('ІНСТРУКЦІЯ.md'):
        print("❌ ІНСТРУКЦІЯ.md not found")
        return False
    
    with open('ІНСТРУКЦІЯ.md', 'r', encoding='utf-8') as f:
        instruction_content = f.read()
    
    if 'Atlas Autonomous System' not in instruction_content:
        print("❌ ІНСТРУКЦІЯ.md missing proper content")
        return False
    
    print("✅ ІНСТРУКЦІЯ.md looks valid")
    return True

def test_class_structure():
    """Test that main classes are properly defined"""
    print("🧪 Testing class structure...")
    
    try:
        # Parse atlas_core.py
        with open('atlas_core.py', 'r') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Find classes
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        expected_classes = ['AtlasCore', 'LLMAgent', 'MacOSAutomation', 'AgentConfig']
        
        for expected_class in expected_classes:
            if expected_class in classes:
                print(f"✅ Found class: {expected_class}")
            else:
                print(f"❌ Missing class: {expected_class}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing class structure: {e}")
        return False

def main():
    """Run all basic tests"""
    print("🤖 Atlas Basic Test Suite")
    print("=" * 40)
    
    tests = [
        test_python_syntax,
        test_file_structure,
        test_shell_scripts,
        test_requirements_format,
        test_docker_files,
        test_documentation,
        test_class_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All basic tests passed! Atlas code structure is ready.")
        print("💡 To run full tests, install dependencies with: pip install -r requirements.txt")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())