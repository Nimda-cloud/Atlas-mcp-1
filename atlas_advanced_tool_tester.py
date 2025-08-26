#!/usr/bin/env python3
"""
Atlas MCP Advanced Tool Tester
==============================

Advanced testing framework for all Atlas MCP tools and services.
Tests the actual system components and validates tool execution logic.

Features:
- Tests real Atlas system with dependencies
- Validates all 143+ tools from user status
- Tests execution logic and Ukrainian language support
- Provides detailed diagnostics and fixes
"""

import asyncio
import json
import subprocess
import sys
import time
import os
from pathlib import Path
import socket
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging


class AtlasAdvancedTester:
    """Advanced Atlas MCP system tester"""
    
    def __init__(self):
        self.results = []
        self.errors_found = []
        self.fixes_applied = []
        
        # Expected tools from user's status output  
        self.expected_tools = {
            "task-orchestrator": [
                "orchestrator_initialize_session",
                "orchestrator_synthesize_results", 
                "orchestrator_get_status",
                "orchestrator_plan_task",
                "orchestrator_update_task",
                "orchestrator_delete_task",
                "orchestrator_cancel_task",
                "orchestrator_query_tasks",
                "orchestrator_execute_task",
                "orchestrator_complete_task",
                "orchestrator_list_sessions",
                "orchestrator_resume_session",
                "orchestrator_cleanup_sessions",
                "orchestrator_session_status",
                "orchestrator_maintenance_coordinator",
                "template_create",
                "template_list",
                "template_load",
                "template_instantiate", 
                "template_validate",
                "template_delete",
                "template_info",
                "template_install_examples",
                "template_install_default_library",
                "template_get_installation_status",
                "template_validate_all",
                "template_uninstall",
                "orchestrator_restart_server",
                "orchestrator_health_check",
                "orchestrator_shutdown_prepare",
                "orchestrator_reconnect_test",
                "orchestrator_restart_status"
            ],
            "tts": [
                "say_tts",
                "stop_tts",
                "set_voice",
                "get_voices",
                "list_voices",
                "tts_status"
            ],
            "automation": [
                "mouseClick",
                "mouseMove", 
                "screenshot",
                "type",
                "keyControl",
                "systemCommand",
                "read_file",
                "write_file",
                "system_launch_app",
                "system_quit_app",
                "system_minimize_app",
                "run_applescript",
                "key",
                "system_sleep",
                "system_restart",
                "get_running_applications",
                "get_system_info",
                "window_management",
                "dock_control"
            ],
            "playwright": [
                "createPage",
                "activatePage",
                "closePage",
                "listPages",
                "closeAllPages",
                "listPagesWithoutId",
                "closePagesWithoutId",
                "closePageByIndex",
                "browserClick",
                "browserType",
                "browserHover",
                "browserSelectOption",
                "browserPressKey",
                "browserFileUpload",
                "browserHandleDialog",
                "browserNavigate",
                "browserNavigateBack",
                "browserNavigateForward",
                "scrollToBottom",
                "scrollToTop",
                "waitForTimeout",
                "waitForSelector",
                "getElementHTML",
                "pageToHtmlFile",
                "getScreenshot",
                "getPDFSnapshot",
                "getPageSnapshot",
                "downloadImage",
                "captureSnapshot"
            ],
            "applescript": [
                "calendar_add",
                "calendar_list",
                "clipboard_set_clipboard",
                "clipboard_get_clipboard",
                "clipboard_clear_clipboard",
                "finder_get_selected_files",
                "finder_search_files",
                "finder_quick_look",
                "notifications_send_notification",
                "notifications_toggle_do_not_disturb",
                "system_volume",
                "system_get_frontmost_app",
                "system_launch_app",
                "system_quit_app",
                "system_toggle_dark_mode",
                "iterm_paste_clipboard",
                "iterm_run",
                "shortcuts_run_shortcut",
                "shortcuts_list_shortcuts",
                "mail_create_email",
                "mail_list_emails",
                "mail_get_email",
                "messages_list_chats",
                "messages_get_messages",
                "messages_search_messages",
                "messages_compose_message",
                "notes_create",
                "notes_createRawHtml",
                "notes_list",
                "notes_get",
                "notes_search",
                "pages_create_document"
            ],
            "file-manager": [
                "read_file",
                "write_file",
                "list_directory",
                "create_directory",
                "delete_file"
            ],
            "network": [
                "ping",
                "http_request",
                "download_file",
                "upload_file"
            ],
            "system-monitor": [
                "get_cpu_usage",
                "get_memory_usage",
                "get_disk_usage",
                "get_processes"
            ],
            "calendar": [
                "create_event",
                "list_events",
                "delete_event",
                "update_event"
            ],
            "notifications": [
                "send_notification",
                "schedule_notification",
                "clear_notifications"
            ],
            "web-fetch": [
                "fetch_url",
                "fetch_html",
                "fetch_json",
                "fetch_text",
                "web_search"
            ]
        }
        
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def log_result(self, name: str, status: bool, message: str, details: Optional[Dict] = None):
        """Log test result"""
        icon = "✅" if status else "❌"
        self.logger.info(f"{icon} {name}: {message}")
        
        self.results.append({
            'name': name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        self.logger.info("\n🔍 Checking Dependencies...")
        
        # Check Python modules
        required_modules = [
            'json', 'subprocess', 'asyncio', 'pathlib', 'socket',
            'urllib.request', 'http.server', 'threading'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                self.log_result(f"Module: {module}", True, "Available")
            except ImportError:
                self.log_result(f"Module: {module}", False, "Missing")
        
        # Check for Go
        try:
            result = subprocess.run(['go', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log_result("Go Language", True, f"Available: {version}")
            else:
                self.log_result("Go Language", False, "Not working")
        except FileNotFoundError:
            self.log_result("Go Language", False, "Not installed")
        
        # Check for system tools
        system_tools = ['curl', 'lsof', 'netstat', 'pkill']
        for tool in system_tools:
            try:
                result = subprocess.run(['which', tool], capture_output=True)
                if result.returncode == 0:
                    self.log_result(f"Tool: {tool}", True, "Available")
                else:
                    self.log_result(f"Tool: {tool}", False, "Not found")
            except:
                self.log_result(f"Tool: {tool}", False, "Check failed")
    
    def start_atlas_services(self):
        """Start Atlas services in the correct order"""
        self.logger.info("\n🚀 Starting Atlas Services...")
        
        # Stop any existing services first
        self.stop_all_services()
        time.sleep(2)
        
        services_to_start = [
            {
                'name': 'Task Orchestrator',
                'script': 'task_orchestrator_http_server.py',
                'port': 4006,
                'timeout': 10
            },
            {
                'name': 'MCP Proxy',
                'script': 'mcp-proxy/start-atlas-proxy.sh',
                'port': 9090,
                'timeout': 15,
                'background': True
            }
        ]
        
        for service in services_to_start:
            self.start_service(service)
            time.sleep(3)  # Give time to start
        
        # Start Atlas Core last (it depends on others)
        atlas_core = {
            'name': 'Atlas Core',
            'script': 'atlas_core.py',
            'port': 8000,
            'timeout': 20,
            'background': True
        }
        
        self.start_service(atlas_core)
        time.sleep(5)  # Give Atlas Core time to initialize
    
    def start_service(self, service_config):
        """Start a single service"""
        name = service_config['name']
        script = service_config['script']
        port = service_config['port']
        timeout = service_config.get('timeout', 10)
        background = service_config.get('background', False)
        
        self.logger.info(f"🔄 Starting {name} ({script})...")
        
        # Check if port is already in use
        if self.check_port(port):
            self.log_result(f"Port {port}", False, f"Already in use for {name}")
            return False
        
        try:
            if script.endswith('.sh'):
                cmd = [f'./{script}']
            else:
                cmd = ['python3', script]
            
            if background:
                # Start in background
                with open(f'{name.lower().replace(" ", "_")}.log', 'w') as log_file:
                    process = subprocess.Popen(
                        cmd,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        cwd='.' if not '/' in script else str(Path(script).parent)
                    )
                
                # Wait a bit and check if it started
                time.sleep(3)
                if self.check_port(port):
                    self.log_result(f"Service: {name}", True, f"Started on port {port}")
                    return True
                else:
                    self.log_result(f"Service: {name}", False, f"Failed to bind to port {port}")
                    return False
            else:
                # Start and wait
                result = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_result(f"Service: {name}", True, "Started successfully")
                    return True
                else:
                    self.log_result(f"Service: {name}", False, f"Failed: {result.stderr}")
                    return False
                    
        except Exception as e:
            self.log_result(f"Service: {name}", False, f"Exception: {e}")
            return False
    
    def stop_all_services(self):
        """Stop all Atlas services"""
        self.logger.info("🛑 Stopping all Atlas services...")
        
        services_to_stop = [
            'atlas_core.py',
            'task_orchestrator_http_server.py',
            'atlas-mcp-proxy',
            'mock_atlas_core.py',
            'simple_task_orchestrator.py',
            'simple_mcp_proxy.py'
        ]
        
        for service in services_to_stop:
            try:
                subprocess.run(['pkill', '-f', service], capture_output=True)
            except:
                pass
    
    def check_port(self, port: int) -> bool:
        """Check if port is in use"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def test_atlas_status_comprehensive(self):
        """Test Atlas status and compare with expected tools"""
        self.logger.info("\n📊 Testing Atlas Status (Comprehensive)...")
        
        try:
            response = urllib.request.urlopen('http://localhost:8000/status', timeout=10)
            data = json.loads(response.read().decode())
            
            self.log_result("Atlas Status", True, "Retrieved successfully", data)
            
            # Check basic fields
            agents_online = data.get('agents_online', 0)
            automation_ready = data.get('automation_ready', False)
            
            self.log_result("Agents Online", agents_online >= 3, f"{agents_online} agents")
            self.log_result("Automation Ready", automation_ready, str(automation_ready))
            
            # Test MCP tools comprehensively
            mcp_data = data.get('mcp', {})
            tools = mcp_data.get('tools', {})
            
            if tools:
                total_tools = sum(len(tool_list) for tool_list in tools.values())
                self.log_result("MCP Tools Total", total_tools > 100, f"{total_tools} tools")
                
                # Check each category against expected
                for category, expected_tools in self.expected_tools.items():
                    actual_tools = tools.get(category, [])
                    
                    if actual_tools:
                        coverage = len(set(actual_tools) & set(expected_tools))
                        coverage_pct = (coverage / len(expected_tools)) * 100
                        
                        status = coverage_pct > 50  # At least 50% coverage
                        message = f"{len(actual_tools)} actual, {coverage}/{len(expected_tools)} expected ({coverage_pct:.1f}%)"
                        
                        self.log_result(f"Tools: {category}", status, message, {
                            'actual_tools': actual_tools,
                            'expected_tools': expected_tools,
                            'missing_tools': list(set(expected_tools) - set(actual_tools))
                        })
                    else:
                        self.log_result(f"Tools: {category}", False, "No tools found")
            else:
                self.log_result("MCP Tools", False, "No tools data")
                
        except Exception as e:
            self.log_result("Atlas Status", False, f"Failed: {e}")
    
    def test_tool_execution(self):
        """Test actual tool execution"""
        self.logger.info("\n⚙️ Testing Tool Execution...")
        
        # Test chat with Ukrainian
        ukrainian_tests = [
            "Привіт! Тест системи",
            "Який зараз час?",
            "Покажи статус системи",
            "відкрий мені програму мюзік"
        ]
        
        for i, text in enumerate(ukrainian_tests, 1):
            try:
                data = json.dumps({'text': text}).encode()
                req = urllib.request.Request(
                    'http://localhost:8000/chat',
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                
                response = urllib.request.urlopen(req, timeout=30)
                result = json.loads(response.read().decode())
                
                if result.get('success'):
                    self.log_result(f"Ukrainian Chat {i}", True, f"Response: {result.get('response', '')[:50]}...")
                else:
                    self.log_result(f"Ukrainian Chat {i}", False, "No success flag")
                    
            except Exception as e:
                self.log_result(f"Ukrainian Chat {i}", False, f"Error: {e}")
        
        # Test TTS
        try:
            data = json.dumps({'text': 'Тест українського TTS'}).encode()
            req = urllib.request.Request(
                'http://localhost:8000/tts',
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read().decode())
            
            self.log_result("Ukrainian TTS", result.get('success', False), result.get('message', 'No message'))
            
        except Exception as e:
            self.log_result("Ukrainian TTS", False, f"Error: {e}")
    
    def test_mcp_proxy_comprehensive(self):
        """Test MCP proxy comprehensively"""
        self.logger.info("\n🔗 Testing MCP Proxy (Comprehensive)...")
        
        proxy_endpoints = [
            '/health',
            '/status', 
            '/tools',
            '/api/status',
            '/api/tools',
            '/'
        ]
        
        for endpoint in proxy_endpoints:
            try:
                response = urllib.request.urlopen(f'http://localhost:9090{endpoint}', timeout=10)
                
                if response.status == 200:
                    data = response.read().decode()
                    try:
                        json_data = json.loads(data)
                        self.log_result(f"Proxy: {endpoint}", True, "Working (JSON)", json_data)
                    except:
                        self.log_result(f"Proxy: {endpoint}", True, "Working (Text)", {'content': data[:100]})
                else:
                    self.log_result(f"Proxy: {endpoint}", False, f"HTTP {response.status}")
                    
            except urllib.error.HTTPError as e:
                self.log_result(f"Proxy: {endpoint}", False, f"HTTP {e.code}")
            except Exception as e:
                self.log_result(f"Proxy: {endpoint}", False, f"Error: {e}")
    
    def diagnose_missing_tools(self):
        """Diagnose why tools might be missing"""
        self.logger.info("\n🔍 Diagnosing Missing Tools...")
        
        # Check if individual MCP servers are running
        mcp_servers = {
            'Playwright MCP': 3001,
            'Atlas Coordinator': 3002, 
            'MCP Orchestrator': 3003,
            'Atlas 2 Visual': 3004,
            'Context MCP': 3005,
            'macOS Automator': 3006,
            'Streaming TTS': 3007,
            'Linux Automator': 3008,
            'Atlas Controller': 3009
        }
        
        for server_name, port in mcp_servers.items():
            if self.check_port(port):
                self.log_result(f"MCP Server: {server_name}", True, f"Running on port {port}")
                
                # Try to get health info
                try:
                    response = urllib.request.urlopen(f'http://localhost:{port}/health', timeout=5)
                    if response.status == 200:
                        self.log_result(f"Health: {server_name}", True, "Healthy")
                    else:
                        self.log_result(f"Health: {server_name}", False, f"HTTP {response.status}")
                except:
                    self.log_result(f"Health: {server_name}", False, "No health endpoint")
            else:
                self.log_result(f"MCP Server: {server_name}", False, f"Not running on port {port}")
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        self.logger.info("\n📋 Generating Final Report...")
        
        passed = sum(1 for r in self.results if r['status'])
        total = len(self.results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║               ATLAS MCP ADVANCED TEST REPORT                 ║
╠═══════════════════════════════════════════════════════════════╣
║ Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                    ║
║ Total Tests: {total:3d} | Passed: {passed:3d} | Failed: {total-passed:3d}                    ║
║ Success Rate: {success_rate:5.1f}%                                    ║
╚═══════════════════════════════════════════════════════════════╝

🎯 KEY FINDINGS:
"""
        
        # Analyze tool coverage
        tool_results = [r for r in self.results if 'Tools:' in r['name']]
        if tool_results:
            report += "\n📊 TOOL COVERAGE ANALYSIS:\n"
            for result in tool_results:
                status = "✅" if result['status'] else "❌"
                report += f"   {status} {result['name']}: {result['message']}\n"
        
        # Service status
        service_results = [r for r in self.results if 'Service:' in r['name']]
        if service_results:
            report += "\n🔧 SERVICE STATUS:\n"
            for result in service_results:
                status = "✅" if result['status'] else "❌"
                report += f"   {status} {result['name']}: {result['message']}\n"
        
        # Ukrainian support
        ukrainian_results = [r for r in self.results if 'Ukrainian' in r['name']]
        if ukrainian_results:
            report += "\n🇺🇦 UKRAINIAN SUPPORT:\n"
            for result in ukrainian_results:
                status = "✅" if result['status'] else "❌"
                report += f"   {status} {result['name']}: {result['message']}\n"
        
        # Recommendations
        failed_results = [r for r in self.results if not r['status']]
        if failed_results:
            report += f"\n🚨 ISSUES TO FIX:\n"
            for result in failed_results:
                report += f"   ❌ {result['name']}: {result['message']}\n"
        
        report += f"""
🎯 RECOMMENDATIONS:
   1. Start missing MCP servers on ports 3001-3009
   2. Check MCP proxy configuration for tool routing
   3. Verify all dependencies are installed
   4. Monitor service logs for errors
   
📈 SYSTEM STATUS: {'EXCELLENT' if success_rate >= 90 else 'GOOD' if success_rate >= 70 else 'NEEDS WORK'}
"""
        
        print(report)
        
        # Save to file
        with open('atlas_advanced_test_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        return success_rate >= 70
    
    def run_comprehensive_tests(self) -> bool:
        """Run all comprehensive tests"""
        self.logger.info("🚀 Atlas MCP Advanced Testing Suite")
        self.logger.info("=" * 50)
        
        try:
            # Phase 1: Check dependencies
            self.check_dependencies()
            
            # Phase 2: Start services (try real system first)
            self.start_atlas_services()
            
            # Wait for services to stabilize
            time.sleep(10)
            
            # Phase 3: Comprehensive testing
            self.test_atlas_status_comprehensive()
            self.test_tool_execution()
            self.test_mcp_proxy_comprehensive()
            self.diagnose_missing_tools()
            
            # Phase 4: Generate report
            success = self.generate_final_report()
            
            return success
            
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Testing interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"\n💥 Testing failed: {e}")
            return False
        finally:
            # Don't stop services automatically - let user decide
            pass


def main():
    """Main execution"""
    print("🎯 Atlas MCP Advanced Tool Tester")
    print("=" * 40)
    
    tester = AtlasAdvancedTester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n✅ Advanced testing SUCCESSFUL")
        return 0
    else:
        print("\n⚠️ Advanced testing completed with issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())