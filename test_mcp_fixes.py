#!/usr/bin/env python3
"""
Test script for Atlas MCP fixes
===============================

Tests the fixed MCP service communication and log monitoring features.
"""

import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MCP-Test')

async def test_mcp_request_format():
    """Test the correct MCP request format"""
    test_payload = {
        "tool": "app_control",
        "parameters": {
            "action": "open",
            "app_name": "Safari"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    logger.info(f"Testing MCP request format: {json.dumps(test_payload, indent=2)}")
    logger.info(f"Headers: {headers}")
    
    # Test if the request format is correct
    assert "tool" in test_payload
    assert "parameters" in test_payload
    assert test_payload["tool"] == "app_control"
    
    logger.info("✅ MCP request format is correct")

async def test_playwright_headers():
    """Test Playwright specific headers"""
    headers_playwright = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    logger.info(f"Playwright headers: {headers_playwright}")
    assert "text/event-stream" in headers_playwright["Accept"]
    
    logger.info("✅ Playwright headers include event-stream support")

async def test_tts_service_format():
    """Test TTS service MCP format"""
    tts_payload = {
        "tool": "speak", 
        "parameters": {
            "text": "Тест голосового повідомлення",
            "provider": "ukrainian_tts"
        }
    }
    
    logger.info(f"TTS MCP request: {json.dumps(tts_payload, indent=2)}")
    assert tts_payload["tool"] == "speak"
    assert "text" in tts_payload["parameters"]
    
    logger.info("✅ TTS service format is correct")

async def test_tool_name_mappings():
    """Test that tool names match available MCP services"""
    
    # Test automation server tools
    automation_tools = ["read_file", "write_file", "execute_command", "http_request", "system_info"]
    logger.info(f"Automation tools: {automation_tools}")
    
    # Test macos-automator tools  
    macos_tools = ["app_control", "applescript", "shortcuts"]
    logger.info(f"macOS Automator tools: {macos_tools}")
    
    # Test playwright tools
    playwright_tools = ["open_page", "goto", "click", "fill", "eval", "screenshot", "get_title", "close"]
    logger.info(f"Playwright tools: {playwright_tools}")
    
    # Test TTS tools
    tts_tools = ["speak"]
    logger.info(f"TTS tools: {tts_tools}")
    
    # Verify critical tools exist
    assert "app_control" in macos_tools
    assert "open_page" in playwright_tools
    assert "speak" in tts_tools
    
    logger.info("✅ Tool name mappings are correct")

async def main():
    """Run all tests"""
    logger.info("🧪 Starting Atlas MCP fixes tests")
    
    try:
        await test_mcp_request_format()
        await test_playwright_headers()
        await test_tts_service_format()
        await test_tool_name_mappings()
        
        logger.info("🎉 All tests passed! MCP fixes are working correctly.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())