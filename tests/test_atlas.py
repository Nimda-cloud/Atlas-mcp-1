#!/usr/bin/env python3
"""
Atlas System Test
================

Basic test script to verify Atlas components are working correctly.
This test can be run without full system setup to check core functionality.
"""

import sys
import os
import json
import asyncio
import subprocess
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test core imports
        import atlas_core
        import mcp_automation_server
        import mcp_macos_automator
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration():
    """Test configuration loading and validation"""
    print("🧪 Testing configuration...")
    
    try:
        # Test creating AtlasCore instance (without starting)
        from atlas_core import AtlasCore, AgentConfig
        
        # Create config
        config = AgentConfig(
            name="test_agent",
            role="test",
            model="test_model",
            provider="test_provider"
        )
        
        print("✅ Configuration system working")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_macos_automation():
    """Test macOS automation capabilities"""
    print("🧪 Testing macOS automation...")
    
    try:
        from atlas_core import MacOSAutomation
        
        # Create automation instance
        macos = MacOSAutomation()
        
        # Test system info gathering (async)
        async def test_system_info():
            info = await macos.get_system_info()
            return info is not None and 'platform' in info
        
        # Run async test
        result = asyncio.run(test_system_info())
        
        if result:
            print("✅ macOS automation system working")
            return True
        else:
            print("❌ macOS automation test failed")
            return False
            
    except Exception as e:
        print(f"❌ macOS automation error: {e}")
        return False

def test_mcp_servers():
    """Test MCP server initialization"""
    print("🧪 Testing MCP servers...")
    
    try:
        # Test automation server
        from mcp_automation_server import MCPAutomationServer, MCPTool, MCPResponse
        
        automation_server = MCPAutomationServer()
        if len(automation_server.tools) > 0:
            print(f"✅ Automation MCP server initialized with {len(automation_server.tools)} tools")
        else:
            print("❌ Automation MCP server has no tools")
            return False
        
        # Test macOS automator server
        from mcp_macos_automator import MacOSAutomatorMCP
        
        macos_server = MacOSAutomatorMCP()
        if len(macos_server.tools) > 0:
            print(f"✅ macOS Automator MCP server initialized with {len(macos_server.tools)} tools")
        else:
            print("❌ macOS Automator MCP server has no tools")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ MCP server error: {e}")
        return False

def test_web_interface():
    """Test web interface initialization"""
    print("🧪 Testing web interface...")
    
    try:
        from atlas_core import AtlasCore
        
        # Create Atlas instance (without starting)
        atlas = AtlasCore()
        
        # Check if FastAPI app is created
        if hasattr(atlas, 'app') and atlas.app is not None:
            print("✅ Web interface (FastAPI) initialized")
            return True
        else:
            print("❌ Web interface not initialized")
            return False
            
    except Exception as e:
        print(f"❌ Web interface error: {e}")
        return False

def test_docker_config():
    """Test Docker configuration validity"""
    print("🧪 Testing Docker configuration...")
    
    try:
        # Check if Docker files exist
        docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-entrypoint.sh']
        
        for file in docker_files:
            if not os.path.exists(file):
                print(f"❌ Missing Docker file: {file}")
                return False
        
        # Test docker-compose syntax
        result = subprocess.run(
            ['docker-compose', 'config'], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Docker configuration is valid")
            return True
        else:
            print(f"❌ Docker configuration error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("⚠️  Docker not available - skipping Docker tests")
        return True
    except Exception as e:
        print(f"❌ Docker test error: {e}")
        return False

def test_requirements():
    """Test that requirements.txt is valid"""
    print("🧪 Testing requirements.txt...")
    
    try:
        if not os.path.exists('requirements.txt'):
            print("❌ requirements.txt not found")
            return False
        
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        # Basic validation
        if 'ollama' in requirements and 'fastapi' in requirements:
            print("✅ requirements.txt looks valid")
            return True
        else:
            print("❌ requirements.txt missing key dependencies")
            return False
            
    except Exception as e:
        print(f"❌ Requirements test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 Atlas System Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_configuration, 
        test_macos_automation,
        test_mcp_servers,
        test_web_interface,
        test_docker_config,
        test_requirements
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
        print("🎉 All tests passed! Atlas system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())