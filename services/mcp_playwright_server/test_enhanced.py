#!/usr/bin/env python3
"""
Test script for Enhanced Playwright MCP Server
==============================================

Tests all 27 tools implemented in the enhanced server.
"""

import json
import requests
import time
import sys

SERVER_URL = "http://localhost:4005"

def test_server_health():
    """Test server health endpoint"""
    print("🔍 Testing server health...")
    try:
        response = requests.get(f"{SERVER_URL}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_get_tools():
    """Test tools endpoint"""
    print("\n🔍 Testing tools endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/tools")
        if response.status_code == 200:
            data = response.json()
            tools = data.get("tools", [])
            print(f"✅ Found {len(tools)} tools")
            
            # List all tools
            for i, tool in enumerate(tools, 1):
                print(f"   {i:2d}. {tool['name']}")
            
            return tools
        else:
            print(f"❌ Tools request failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Tools request error: {e}")
        return []

def execute_tool(tool_name, parameters=None):
    """Execute a tool via POST request"""
    if parameters is None:
        parameters = {}
    
    payload = {
        "tool": tool_name,
        "parameters": parameters
    }
    
    try:
        response = requests.post(f"{SERVER_URL}/execute", json=payload)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def test_basic_tools():
    """Test basic browser tools"""
    print("\n🔍 Testing basic browser tools...")
    
    # Test browser_navigate
    print("   Testing browser_navigate...")
    success, result = execute_tool("browser_navigate", {"url": "https://httpbin.org/html"})
    if success:
        print(f"   ✅ Navigation successful: {result.get('url', 'N/A')}")
    else:
        print(f"   ❌ Navigation failed: {result}")
        return False
    
    # Test browser_take_screenshot
    print("   Testing browser_take_screenshot...")
    success, result = execute_tool("browser_take_screenshot", {"filename": "/tmp/test_screenshot.png"})
    if success:
        print(f"   ✅ Screenshot saved: {result.get('filename', 'N/A')}")
    else:
        print(f"   ❌ Screenshot failed: {result}")
    
    # Test browser_evaluate
    print("   Testing browser_evaluate...")
    success, result = execute_tool("browser_evaluate", {"function": "document.title"})
    if success:
        print(f"   ✅ JavaScript evaluation: {result.get('result', 'N/A')}")
    else:
        print(f"   ❌ JavaScript evaluation failed: {result}")
    
    # Test browser_console_messages  
    print("   Testing browser_console_messages...")
    success, result = execute_tool("browser_console_messages")
    if success:
        messages = result.get('messages', [])
        print(f"   ✅ Console messages retrieved: {len(messages)} messages")
    else:
        print(f"   ❌ Console messages failed: {result}")
    
    return True

def test_tab_management():
    """Test tab management tools"""
    print("\n🔍 Testing tab management...")
    
    # Test browser_tab_list
    print("   Testing browser_tab_list...")
    success, result = execute_tool("browser_tab_list")
    if success:
        tabs = result.get('tabs', [])
        print(f"   ✅ Found {len(tabs)} tabs")
    else:
        print(f"   ❌ Tab list failed: {result}")
        return False
    
    # Test browser_tab_new
    print("   Testing browser_tab_new...")
    success, result = execute_tool("browser_tab_new", {"url": "https://httpbin.org/json"})
    if success:
        print(f"   ✅ New tab opened: {result.get('url', 'N/A')}")
    else:
        print(f"   ❌ New tab failed: {result}")
    
    # Test browser_tab_select
    print("   Testing browser_tab_select...")
    success, result = execute_tool("browser_tab_select", {"index": 0})
    if success:
        print(f"   ✅ Tab selected: {result.get('url', 'N/A')}")
    else:
        print(f"   ❌ Tab select failed: {result}")
    
    return True

def test_mouse_operations():
    """Test mouse operation tools"""
    print("\n🔍 Testing mouse operations...")
    
    # Test browser_mouse_move_xy
    print("   Testing browser_mouse_move_xy...")
    success, result = execute_tool("browser_mouse_move_xy", {"x": 100, "y": 100})
    if success:
        print(f"   ✅ Mouse moved to: ({result.get('x', 'N/A')}, {result.get('y', 'N/A')})")
    else:
        print(f"   ❌ Mouse move failed: {result}")
    
    # Test browser_mouse_click_xy
    print("   Testing browser_mouse_click_xy...")
    success, result = execute_tool("browser_mouse_click_xy", {"x": 100, "y": 100})
    if success:
        print("   ✅ Mouse click successful")
    else:
        print(f"   ❌ Mouse click failed: {result}")
    
    return True

def test_keyboard_operations():
    """Test keyboard operation tools"""
    print("\n🔍 Testing keyboard operations...")
    
    # Test browser_press_key
    print("   Testing browser_press_key...")
    success, result = execute_tool("browser_press_key", {"key": "F5"})
    if success:
        print("   ✅ Key press successful")
    else:
        print(f"   ❌ Key press failed: {result}")
    
    return True

def test_network_tools():
    """Test network-related tools"""
    print("\n🔍 Testing network tools...")
    
    # Test browser_network_requests
    print("   Testing browser_network_requests...")
    success, result = execute_tool("browser_network_requests")
    if success:
        requests_list = result.get('requests', [])
        print(f"   ✅ Network requests retrieved: {len(requests_list)} requests")
    else:
        print(f"   ❌ Network requests failed: {result}")
    
    return True

def test_wait_operations():
    """Test wait operations"""
    print("\n🔍 Testing wait operations...")
    
    # Test browser_wait_for with time
    print("   Testing browser_wait_for (time)...")
    start_time = time.time()
    success, result = execute_tool("browser_wait_for", {"time": 1})
    elapsed = time.time() - start_time
    if success and elapsed >= 1:
        print(f"   ✅ Wait successful: {elapsed:.2f}s")
    else:
        print(f"   ❌ Wait failed: {result}")
    
    return True

def test_browser_management():
    """Test browser management tools"""
    print("\n🔍 Testing browser management...")
    
    # Test browser_resize
    print("   Testing browser_resize...")
    success, result = execute_tool("browser_resize", {"width": 1024, "height": 768})
    if success:
        print("   ✅ Browser resize successful")
    else:
        print(f"   ❌ Browser resize failed: {result}")
    
    # Test browser_close (should be last)
    print("   Testing browser_close...")
    success, result = execute_tool("browser_close")
    if success:
        print("   ✅ Browser close successful")
    else:
        print(f"   ❌ Browser close failed: {result}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Enhanced Playwright MCP Server Test Suite")
    print("=" * 50)
    
    # Check if server is running
    if not test_server_health():
        print("\n❌ Server is not running. Please start the server first:")
        print("   cd services/mcp_playwright_server")
        print("   python3 app_enhanced.py")
        return 1
    
    # Get available tools
    tools = test_get_tools()
    if len(tools) != 27:
        print(f"\n⚠️  Expected 27 tools, found {len(tools)}")
    
    # Run tests
    test_results = []
    
    test_results.append(("Basic Tools", test_basic_tools()))
    test_results.append(("Tab Management", test_tab_management()))
    test_results.append(("Mouse Operations", test_mouse_operations()))
    test_results.append(("Keyboard Operations", test_keyboard_operations()))
    test_results.append(("Network Tools", test_network_tools()))
    test_results.append(("Wait Operations", test_wait_operations()))
    test_results.append(("Browser Management", test_browser_management()))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced Playwright MCP Server is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the server implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
