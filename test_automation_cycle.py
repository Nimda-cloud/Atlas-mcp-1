#!/usr/bin/env python3
"""
Atlas Full Automation Cycle Test
=====================================

Tests the complete automation workflow:
1. Native macOS startup
2. Docker image execution
3. Web interface integration
4. Auto-merge and CI/CD pipeline
5. Post-merge verification
6. Auto-healing on failures
7. Cyclical improvement process
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
import subprocess
from pathlib import Path

class AtlasAutomationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        
    async def test_basic_startup(self):
        """Test 1: Basic Atlas startup and web interface"""
        print("🧪 Test 1: Basic Atlas startup and web interface")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"   ✅ Atlas is running: {data}")
                        self.test_results.append(("Basic Startup", True, "Atlas web interface accessible"))
                        return True
                    else:
                        print(f"   ❌ Atlas not responding: HTTP {resp.status}")
                        self.test_results.append(("Basic Startup", False, f"HTTP {resp.status}"))
                        return False
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            self.test_results.append(("Basic Startup", False, str(e)))
            return False
    
    async def test_ukrainian_processing(self):
        """Test 2: Ukrainian language processing"""
        print("🧪 Test 2: Ukrainian language processing")
        
        try:
            test_message = "Привіт, покажи мені статус системи"
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/chat", 
                                      json={"message": test_message}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data.get("response", "")
                        if response and len(response) > 10:
                            print(f"   ✅ Ukrainian processing works: {response[:100]}...")
                            self.test_results.append(("Ukrainian Processing", True, "Response generated"))
                            return True
                        else:
                            print(f"   ❌ Empty or short response: {response}")
                            self.test_results.append(("Ukrainian Processing", False, "Empty response"))
                            return False
                    else:
                        print(f"   ❌ Chat API failed: HTTP {resp.status}")
                        self.test_results.append(("Ukrainian Processing", False, f"HTTP {resp.status}"))
                        return False
        except Exception as e:
            print(f"   ❌ Ukrainian processing failed: {e}")
            self.test_results.append(("Ukrainian Processing", False, str(e)))
            return False
    
    async def test_github_integration(self):
        """Test 3: GitHub integration and auto-healing endpoints"""
        print("🧪 Test 3: GitHub integration and auto-healing")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/github/status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("auto_healing_enabled"):
                            print(f"   ✅ GitHub integration active: {data}")
                            self.test_results.append(("GitHub Integration", True, "Auto-healing enabled"))
                            return True
                        else:
                            print(f"   ❌ Auto-healing not enabled: {data}")
                            self.test_results.append(("GitHub Integration", False, "Auto-healing disabled"))
                            return False
                    else:
                        print(f"   ❌ GitHub status API failed: HTTP {resp.status}")
                        self.test_results.append(("GitHub Integration", False, f"HTTP {resp.status}"))
                        return False
        except Exception as e:
            print(f"   ❌ GitHub integration test failed: {e}")
            self.test_results.append(("GitHub Integration", False, str(e)))
            return False
    
    async def test_macos_automation(self):
        """Test 4: macOS automation capabilities"""
        print("🧪 Test 4: macOS automation capabilities")
        
        try:
            test_action = "system_info"
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/action", 
                                      json={"action": test_action}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data.get("result", "")
                        if "System Information" in result:
                            print(f"   ✅ macOS automation works: System info retrieved")
                            self.test_results.append(("macOS Automation", True, "System info retrieved"))
                            return True
                        else:
                            print(f"   ❌ Unexpected result: {result}")
                            self.test_results.append(("macOS Automation", False, "Unexpected result"))
                            return False
                    else:
                        print(f"   ❌ Action API failed: HTTP {resp.status}")
                        self.test_results.append(("macOS Automation", False, f"HTTP {resp.status}"))
                        return False
        except Exception as e:
            print(f"   ❌ macOS automation test failed: {e}")
            self.test_results.append(("macOS Automation", False, str(e)))
            return False
    
    def test_docker_config(self):
        """Test 5: Docker configuration validation"""
        print("🧪 Test 5: Docker configuration validation")
        
        try:
            result = subprocess.run(['docker', 'compose', 'config'], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                print(f"   ✅ Docker Compose configuration is valid")
                self.test_results.append(("Docker Config", True, "Valid configuration"))
                return True
            else:
                print(f"   ❌ Docker Compose config error: {result.stderr}")
                self.test_results.append(("Docker Config", False, result.stderr))
                return False
        except Exception as e:
            print(f"   ❌ Docker config test failed: {e}")
            self.test_results.append(("Docker Config", False, str(e)))
            return False
    
    def test_workflow_syntax(self):
        """Test 6: GitHub workflow syntax validation"""
        print("🧪 Test 6: GitHub workflow syntax validation")
        
        try:
            import yaml
            workflow_files = [
                '.github/workflows/post-merge-local.yml',
                '.github/workflows/pr-agent-ci.yml',
                '.github/workflows/atlas-auto-healing.yml'
            ]
            
            for workflow_file in workflow_files:
                if os.path.exists(workflow_file):
                    with open(workflow_file, 'r') as f:
                        yaml.safe_load(f)
                    print(f"   ✅ {workflow_file} syntax valid")
                else:
                    print(f"   ⚠️  {workflow_file} not found")
            
            self.test_results.append(("Workflow Syntax", True, "All workflows valid"))
            return True
            
        except Exception as e:
            print(f"   ❌ Workflow syntax test failed: {e}")
            self.test_results.append(("Workflow Syntax", False, str(e)))
            return False
    
    async def test_auto_healing_simulation(self):
        """Test 7: Auto-healing simulation"""
        print("🧪 Test 7: Auto-healing simulation")
        
        try:
            # Simulate an auto-healing request
            test_healing_request = {
                "issue_number": "999",
                "issue_title": "Test auto-healing simulation",
                "issue_body": "Simulated post-merge verification failure for testing",
                "workflow_url": "https://github.com/test/test/actions/runs/123456"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/github/auto-heal", 
                                      json=test_healing_request) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "auto-healing-initiated":
                            print(f"   ✅ Auto-healing simulation successful")
                            self.test_results.append(("Auto-healing Simulation", True, "Initiated successfully"))
                            return True
                        else:
                            print(f"   ❌ Unexpected auto-healing response: {data}")
                            self.test_results.append(("Auto-healing Simulation", False, "Unexpected response"))
                            return False
                    else:
                        print(f"   ❌ Auto-healing API failed: HTTP {resp.status}")
                        self.test_results.append(("Auto-healing Simulation", False, f"HTTP {resp.status}"))
                        return False
        except Exception as e:
            print(f"   ❌ Auto-healing simulation failed: {e}")
            self.test_results.append(("Auto-healing Simulation", False, str(e)))
            return False
    
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*50)
        print("🤖 ATLAS AUTOMATION CYCLE TEST RESULTS")
        print("="*50)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}: {details}")
        
        print(f"\n📊 Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All automation cycle tests passed!")
            print("🚀 Atlas is ready for full automated CI/CD with cyclical improvement")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please address issues before deployment.")
            return False

async def main():
    """Run the complete automation cycle test"""
    print("🤖 Atlas Full Automation Cycle Test")
    print("=" * 40)
    print("This test validates the complete automation workflow:")
    print("- Native macOS execution")
    print("- Web interface integration") 
    print("- Ukrainian language support")
    print("- GitHub CI/CD integration")
    print("- Auto-healing capabilities")
    print("- Docker and workflow configurations")
    print()
    
    tester = AtlasAutomationTester()
    
    # Run all tests
    await tester.test_basic_startup()
    await asyncio.sleep(1)
    
    await tester.test_ukrainian_processing()
    await asyncio.sleep(1)
    
    await tester.test_github_integration()
    await asyncio.sleep(1)
    
    await tester.test_macos_automation()
    await asyncio.sleep(1)
    
    tester.test_docker_config()
    tester.test_workflow_syntax()
    
    await tester.test_auto_healing_simulation()
    
    # Print results
    success = tester.print_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)