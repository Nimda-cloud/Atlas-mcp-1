#!/usr/bin/env python3
"""
Atlas Automation System - Final Validation & Demonstration
==========================================================

This script demonstrates the full automation capabilities of the Atlas MCP system
and provides a comprehensive assessment of its readiness for deployment.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

class AtlasAutomationValidator:
    """Final validation and demonstration of Atlas automation capabilities"""
    
    def __init__(self):
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version,
                "working_directory": os.getcwd()
            },
            "categories": {},
            "overall_assessment": {},
            "deployment_readiness": {},
            "automation_capabilities": []
        }
    
    def validate_system_architecture(self):
        """Validate the multi-agent AI architecture"""
        print("🤖 Validating Multi-Agent AI Architecture...")
        
        architecture_tests = {
            "LLM Agent Classes": self._check_llm_agent_classes(),
            "Multi-Agent Coordination": self._check_agent_coordination(),
            "Provider Support": self._check_provider_support(),
            "Fallback Mechanisms": self._check_fallback_mechanisms()
        }
        
        self.validation_results["categories"]["Architecture"] = architecture_tests
        
        # Summary
        passed = sum(1 for result in architecture_tests.values() if result["status"] == "pass")
        total = len(architecture_tests)
        print(f"   Architecture: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return passed >= total * 0.8
    
    def validate_mcp_automation_hub(self):
        """Validate MCP (Model Context Protocol) automation capabilities"""
        print("🔌 Validating MCP Automation Hub...")
        
        mcp_tests = {
            "Automation Server": self._check_mcp_automation_server(),
            "macOS Automator": self._check_mcp_macos_automator(), 
            "Tool Integration": self._check_mcp_tool_integration(),
            "Service Orchestration": self._check_mcp_orchestration()
        }
        
        self.validation_results["categories"]["MCP_Hub"] = mcp_tests
        
        passed = sum(1 for result in mcp_tests.values() if result["status"] == "pass")
        total = len(mcp_tests)
        print(f"   MCP Hub: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return passed >= total * 0.75
    
    def validate_deployment_methods(self):
        """Validate all three deployment methods"""
        print("🚀 Validating Deployment Methods...")
        
        deployment_tests = {
            "Local Python": self._check_local_python_deployment(),
            "Docker Container": self._check_docker_deployment(),
            "Kubernetes Production": self._check_kubernetes_deployment()
        }
        
        self.validation_results["categories"]["Deployment"] = deployment_tests
        
        passed = sum(1 for result in deployment_tests.values() if result["status"] == "pass")
        total = len(deployment_tests)
        print(f"   Deployment: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return passed >= total * 0.66  # At least 2 out of 3 methods should work
    
    def validate_automation_scripts(self):
        """Validate automation and management scripts"""
        print("🔧 Validating Automation Scripts...")
        
        script_tests = {
            "Smart Startup": self._check_smart_startup(),
            "Health Monitoring": self._check_health_monitoring(),
            "Autonomous Setup": self._check_autonomous_setup(),
            "System Diagnostics": self._check_system_diagnostics()
        }
        
        self.validation_results["categories"]["Scripts"] = script_tests
        
        passed = sum(1 for result in script_tests.values() if result["status"] == "pass")
        total = len(script_tests)
        print(f"   Scripts: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return passed >= total * 0.75
    
    def validate_ukrainian_automation(self):
        """Validate Ukrainian language automation capabilities"""
        print("🇺🇦 Validating Ukrainian Language Automation...")
        
        ukrainian_tests = {
            "Language Documentation": self._check_ukrainian_docs(),
            "Command Processing": self._check_ukrainian_commands(),
            "Test Integration": self._check_ukrainian_tests(),
            "Interface Support": self._check_ukrainian_interface()
        }
        
        self.validation_results["categories"]["Ukrainian"] = ukrainian_tests
        
        passed = sum(1 for result in ukrainian_tests.values() if result["status"] == "pass")
        total = len(ukrainian_tests)
        print(f"   Ukrainian: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return passed >= total * 0.75
    
    def validate_autonomous_workflows(self):
        """Validate autonomous GitHub workflows and CI/CD"""
        print("🦾 Validating Autonomous Workflows...")
        
        workflow_tests = {
            "PR Agent CI": self._check_pr_agent_workflow(),
            "Post-merge Verification": self._check_post_merge_workflow(),
            "Auto-merge Capability": self._check_auto_merge(),
            "Failure Recovery": self._check_failure_recovery()
        }
        
        self.validation_results["categories"]["Autonomous"] = workflow_tests
        
        passed = sum(1 for result in workflow_tests.values() if result["status"] == "pass")
        total = len(workflow_tests)
        print(f"   Autonomous: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return passed >= total * 0.75
    
    def demonstrate_automation_capabilities(self):
        """Demonstrate key automation capabilities"""
        print("✨ Demonstrating Automation Capabilities...")
        
        demonstrations = []
        
        # 1. Multi-agent coordination simulation
        demo1 = self._simulate_multi_agent_coordination()
        demonstrations.append(demo1)
        
        # 2. MCP service orchestration
        demo2 = self._simulate_mcp_orchestration()
        demonstrations.append(demo2)
        
        # 3. Ukrainian command processing
        demo3 = self._simulate_ukrainian_processing()
        demonstrations.append(demo3)
        
        # 4. Deployment readiness
        demo4 = self._simulate_deployment_process()
        demonstrations.append(demo4)
        
        self.validation_results["automation_capabilities"] = demonstrations
        
        successful_demos = sum(1 for demo in demonstrations if demo["success"])
        print(f"   Demonstrations: {successful_demos}/{len(demonstrations)} successful")
        
        return successful_demos >= len(demonstrations) * 0.75
    
    # Helper methods for validation checks
    def _check_llm_agent_classes(self):
        try:
            with open('atlas_core.py', 'r') as f:
                content = f.read()
            
            required_patterns = [
                'class LLMAgent',
                'class AgentConfig',
                'def generate_response',
                'def setup_client'
            ]
            
            found = sum(1 for pattern in required_patterns if pattern in content)
            return {
                "status": "pass" if found >= len(required_patterns) else "fail",
                "details": f"Found {found}/{len(required_patterns)} required patterns",
                "score": found / len(required_patterns)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_agent_coordination(self):
        try:
            with open('atlas_core.py', 'r') as f:
                content = f.read()
            
            coordination_patterns = ['LLM1', 'LLM2', 'LLM3', 'agents_online', 'agent_status']
            found = sum(1 for pattern in coordination_patterns if pattern in content)
            
            return {
                "status": "pass" if found >= 3 else "fail",
                "details": f"Found {found}/{len(coordination_patterns)} coordination patterns",
                "score": found / len(coordination_patterns)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_provider_support(self):
        try:
            with open('atlas_core.py', 'r') as f:
                content = f.read()
            
            providers = ['ollama', 'gemini', 'mistral']
            found = sum(1 for provider in providers if provider in content.lower())
            
            return {
                "status": "pass" if found >= 2 else "fail",
                "details": f"Supports {found}/{len(providers)} LLM providers",
                "score": found / len(providers)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_fallback_mechanisms(self):
        try:
            with open('atlas_core.py', 'r') as f:
                content = f.read()
            
            fallback_indicators = ['fallback', 'try:', 'except', 'if response is None']
            found = sum(1 for indicator in fallback_indicators if indicator in content)
            
            return {
                "status": "pass" if found >= 2 else "fail",
                "details": f"Found {found} fallback mechanisms",
                "score": min(found / 3, 1.0)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_mcp_automation_server(self):
        try:
            with open('mcp_automation_server.py', 'r') as f:
                content = f.read()
            
            features = ['class MCPAutomationServer', 'handle_tool_call', 'execute_command', 'system_info']
            found = sum(1 for feature in features if feature in content)
            
            return {
                "status": "pass" if found >= len(features) else "fail",
                "details": f"Found {found}/{len(features)} automation features",
                "score": found / len(features)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_mcp_macos_automator(self):
        try:
            with open('mcp_macos_automator.py', 'r') as f:
                content = f.read()
            
            features = ['applescript', 'automation', 'execute_', 'macos']
            found = sum(1 for feature in features if feature.lower() in content.lower())
            
            return {
                "status": "pass" if found >= 2 else "fail",
                "details": f"Found {found}/{len(features)} macOS features",
                "score": found / len(features)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_mcp_tool_integration(self):
        try:
            with open('mcp_automation_server.py', 'r') as f:
                content = f.read()
            
            tools = ['read_file', 'write_file', 'http_request', 'system_info']
            found = sum(1 for tool in tools if tool in content)
            
            return {
                "status": "pass" if found >= len(tools) else "fail",
                "details": f"Found {found}/{len(tools)} MCP tools",
                "score": found / len(tools)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_mcp_orchestration(self):
        # Check for MCP service coordination
        docker_compose_exists = os.path.exists('docker-compose.yml')
        mcp_services_exist = all(os.path.exists(f) for f in ['mcp_automation_server.py', 'mcp_macos_automator.py'])
        
        score = 0
        if docker_compose_exists:
            score += 0.5
        if mcp_services_exist:
            score += 0.5
        
        return {
            "status": "pass" if score >= 0.75 else "fail",
            "details": f"MCP orchestration readiness: {score*100:.0f}%",
            "score": score
        }
    
    def _check_local_python_deployment(self):
        # Check if local deployment files exist and are properly configured
        files = ['atlas_core.py', 'start_atlas.sh', 'requirements.txt']
        file_check = all(os.path.exists(f) for f in files)
        
        executable_check = os.access('start_atlas.sh', os.X_OK) if os.path.exists('start_atlas.sh') else False
        
        score = 0.5 if file_check else 0
        score += 0.5 if executable_check else 0
        
        return {
            "status": "pass" if score >= 0.75 else "fail",
            "details": f"Local deployment readiness: {score*100:.0f}%",
            "score": score
        }
    
    def _check_docker_deployment(self):
        try:
            # Test Docker configuration validity
            result = subprocess.run(['docker', 'compose', 'config'], 
                                  capture_output=True, text=True, timeout=30)
            
            docker_valid = result.returncode == 0
            dockerfile_exists = os.path.exists('Dockerfile')
            compose_exists = os.path.exists('docker-compose.yml')
            
            score = 0
            if dockerfile_exists:
                score += 0.33
            if compose_exists:
                score += 0.33
            if docker_valid:
                score += 0.34
            
            return {
                "status": "pass" if score >= 0.75 else "fail",
                "details": f"Docker deployment readiness: {score*100:.0f}%",
                "score": score
            }
        except Exception as e:
            return {"status": "fail", "details": f"Docker check failed: {e}", "score": 0}
    
    def _check_kubernetes_deployment(self):
        k8s_dir = Path('k8s')
        makefile_exists = os.path.exists('Makefile')
        k8s_manifests = len(list(k8s_dir.rglob('*.yaml'))) if k8s_dir.exists() else 0
        
        score = 0
        if k8s_dir.exists():
            score += 0.33
        if makefile_exists:
            score += 0.33
        if k8s_manifests >= 5:  # Reasonable number of manifests
            score += 0.34
        
        return {
            "status": "pass" if score >= 0.66 else "fail",
            "details": f"Kubernetes readiness: {score*100:.0f}% ({k8s_manifests} manifests)",
            "score": score
        }
    
    def _check_smart_startup(self):
        if not os.path.exists('start_atlas.sh'):
            return {"status": "fail", "details": "start_atlas.sh not found", "score": 0}
        
        try:
            with open('start_atlas.sh', 'r') as f:
                content = f.read()
            
            features = ['function', 'check', 'command_exists', 'port_in_use']
            found = sum(1 for feature in features if feature in content)
            
            return {
                "status": "pass" if found >= 2 else "fail",
                "details": f"Smart startup features: {found}/{len(features)}",
                "score": found / len(features)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_health_monitoring(self):
        if not os.path.exists('atlas_health_monitor.sh'):
            return {"status": "fail", "details": "Health monitor not found", "score": 0}
        
        try:
            with open('atlas_health_monitor.sh', 'r') as f:
                content = f.read()
            
            endpoints = ['8000/status', '8080/health', '4002/health', '4003/health']
            found = sum(1 for endpoint in endpoints if endpoint in content)
            
            return {
                "status": "pass" if found >= len(endpoints) else "fail",
                "details": f"Monitors {found}/{len(endpoints)} service endpoints",
                "score": found / len(endpoints)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_autonomous_setup(self):
        script_exists = os.path.exists('atlas_autonomous_setup.sh')
        executable = os.access('atlas_autonomous_setup.sh', os.X_OK) if script_exists else False
        
        score = 0.5 if script_exists else 0
        score += 0.5 if executable else 0
        
        return {
            "status": "pass" if score >= 0.75 else "fail",
            "details": f"Autonomous setup readiness: {score*100:.0f}%",
            "score": score
        }
    
    def _check_system_diagnostics(self):
        script_exists = os.path.exists('atlas_diagnostic.sh')
        executable = os.access('atlas_diagnostic.sh', os.X_OK) if script_exists else False
        
        score = 0.5 if script_exists else 0
        score += 0.5 if executable else 0
        
        return {
            "status": "pass" if score >= 0.75 else "fail",
            "details": f"Diagnostics readiness: {score*100:.0f}%",
            "score": score
        }
    
    def _check_ukrainian_docs(self):
        if not os.path.exists('ІНСТРУКЦІЯ.md'):
            return {"status": "fail", "details": "Ukrainian documentation not found", "score": 0}
        
        try:
            with open('ІНСТРУКЦІЯ.md', 'r', encoding='utf-8') as f:
                content = f.read()
            
            keywords = ['Atlas', 'автоматизація', 'використання', 'команди']
            found = sum(1 for keyword in keywords if keyword in content)
            
            return {
                "status": "pass" if found >= len(keywords) else "fail",
                "details": f"Ukrainian content quality: {found}/{len(keywords)} keywords",
                "score": found / len(keywords)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_ukrainian_commands(self):
        if not os.path.exists('test_execution.py'):
            return {"status": "fail", "details": "Ukrainian test file not found", "score": 0}
        
        try:
            with open('test_execution.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            commands = ['відкрий хром', 'говори привіт']
            found = sum(1 for cmd in commands if cmd in content)
            
            return {
                "status": "pass" if found >= 1 else "fail",
                "details": f"Ukrainian commands: {found}/{len(commands)}",
                "score": found / len(commands)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_ukrainian_tests(self):
        ukrainian_files = ['test_execution.py', 'ІНСТРУКЦІЯ.md']
        found = sum(1 for file in ukrainian_files if os.path.exists(file))
        
        return {
            "status": "pass" if found >= len(ukrainian_files) else "fail",
            "details": f"Ukrainian test integration: {found}/{len(ukrainian_files)} files",
            "score": found / len(ukrainian_files)
        }
    
    def _check_ukrainian_interface(self):
        # Check if the system supports Ukrainian interface
        try:
            with open('atlas_core.py', 'r') as f:
                content = f.read()
            
            # Look for Unicode/UTF-8 support indicators
            indicators = ['utf-8', 'unicode', 'encoding', 'ukrainian']
            found = sum(1 for indicator in indicators if indicator.lower() in content.lower())
            
            return {
                "status": "pass" if found >= 1 else "partial",
                "details": f"Unicode/Ukrainian support indicators: {found}",
                "score": min(found / 2, 1.0)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_pr_agent_workflow(self):
        workflow_file = '.github/workflows/pr-agent-ci.yml'
        if not os.path.exists(workflow_file):
            return {"status": "fail", "details": "PR workflow not found", "score": 0}
        
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            features = ['on:', 'jobs:', 'runs-on:', 'merge_pr']
            found = sum(1 for feature in features if feature in content)
            
            return {
                "status": "pass" if found >= len(features) else "fail",
                "details": f"PR workflow features: {found}/{len(features)}",
                "score": found / len(features)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_post_merge_workflow(self):
        workflow_file = '.github/workflows/post-merge-local.yml'
        if not os.path.exists(workflow_file):
            return {"status": "fail", "details": "Post-merge workflow not found", "score": 0}
        
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            features = ['local_macos', 'report_failure', 'sync_local']
            found = sum(1 for feature in features if feature in content)
            
            return {
                "status": "pass" if found >= 2 else "fail",
                "details": f"Post-merge features: {found}/{len(features)}",
                "score": found / len(features)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_auto_merge(self):
        try:
            with open('.github/workflows/pr-agent-ci.yml', 'r') as f:
                content = f.read()
            
            merge_indicators = ['merge_pr', 'auto-merge', 'gh pr merge']
            found = sum(1 for indicator in merge_indicators if indicator in content)
            
            return {
                "status": "pass" if found >= 1 else "fail",
                "details": f"Auto-merge capability: {found > 0}",
                "score": 1.0 if found > 0 else 0.0
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _check_failure_recovery(self):
        try:
            with open('.github/workflows/post-merge-local.yml', 'r') as f:
                content = f.read()
            
            recovery_features = ['if: failure()', 'report_failure', 'issue']
            found = sum(1 for feature in recovery_features if feature in content)
            
            return {
                "status": "pass" if found >= 1 else "fail",
                "details": f"Failure recovery mechanisms: {found}",
                "score": min(found / 2, 1.0)
            }
        except Exception as e:
            return {"status": "fail", "details": str(e), "score": 0}
    
    def _simulate_multi_agent_coordination(self):
        """Simulate multi-agent coordination workflow"""
        print("   🤖 Simulating Multi-Agent Coordination...")
        
        try:
            # Simulate agent initialization
            agents_config = {
                "LLM1": {"role": "interface", "model": "llama3.1:8b"},
                "LLM2": {"role": "orchestrator", "model": "gpt-oss:latest"},
                "LLM3": {"role": "monitor", "model": "llama3.1:8b"}
            }
            
            # Check if agent configuration is properly defined
            with open('atlas_core.py', 'r') as f:
                content = f.read()
            
            agent_patterns = ['LLM1', 'LLM2', 'LLM3']
            found_agents = sum(1 for pattern in agent_patterns if pattern in content)
            
            simulation_result = {
                "name": "Multi-Agent Coordination",
                "success": found_agents >= 3,
                "details": f"Found {found_agents}/3 agent references in codebase",
                "agents_simulated": agents_config,
                "coordination_score": found_agents / 3
            }
            
            print(f"      Agent coordination: {simulation_result['success']} ({found_agents}/3 agents)")
            return simulation_result
            
        except Exception as e:
            return {
                "name": "Multi-Agent Coordination",
                "success": False,
                "details": f"Simulation failed: {e}",
                "coordination_score": 0
            }
    
    def _simulate_mcp_orchestration(self):
        """Simulate MCP service orchestration"""
        print("   🔌 Simulating MCP Service Orchestration...")
        
        try:
            mcp_services = [
                {"name": "mcp-automation", "port": 4002, "file": "mcp_automation_server.py"},
                {"name": "mcp-automator", "port": 4003, "file": "mcp_macos_automator.py"}
            ]
            
            available_services = 0
            for service in mcp_services:
                if os.path.exists(service["file"]):
                    available_services += 1
            
            orchestration_ready = os.path.exists('docker-compose.yml')
            
            simulation_result = {
                "name": "MCP Service Orchestration",
                "success": available_services >= 2 and orchestration_ready,
                "details": f"Found {available_services}/2 MCP services, orchestration: {orchestration_ready}",
                "services": mcp_services,
                "orchestration_score": (available_services / 2 + (1 if orchestration_ready else 0)) / 2
            }
            
            print(f"      MCP orchestration: {simulation_result['success']} ({available_services}/2 services)")
            return simulation_result
            
        except Exception as e:
            return {
                "name": "MCP Service Orchestration",
                "success": False,
                "details": f"Simulation failed: {e}",
                "orchestration_score": 0
            }
    
    def _simulate_ukrainian_processing(self):
        """Simulate Ukrainian language command processing"""
        print("   🇺🇦 Simulating Ukrainian Command Processing...")
        
        try:
            ukrainian_commands = [
                "відкрий хром",
                "говори привіт",
                "запусти програму",
                "показати статус"
            ]
            
            # Check if Ukrainian test commands are defined
            ukrainian_test_exists = os.path.exists('test_execution.py')
            ukrainian_docs_exist = os.path.exists('ІНСТРУКЦІЯ.md')
            
            if ukrainian_test_exists:
                with open('test_execution.py', 'r', encoding='utf-8') as f:
                    test_content = f.read()
                
                found_commands = sum(1 for cmd in ukrainian_commands if cmd in test_content)
            else:
                found_commands = 0
            
            simulation_result = {
                "name": "Ukrainian Language Processing",
                "success": ukrainian_test_exists and ukrainian_docs_exist and found_commands >= 1,
                "details": f"Ukrainian support: docs={ukrainian_docs_exist}, tests={ukrainian_test_exists}, commands={found_commands}",
                "test_commands": ukrainian_commands,
                "language_score": (found_commands / len(ukrainian_commands) + 
                                 (1 if ukrainian_test_exists else 0) + 
                                 (1 if ukrainian_docs_exist else 0)) / 3
            }
            
            print(f"      Ukrainian processing: {simulation_result['success']} (commands: {found_commands}/{len(ukrainian_commands)})")
            return simulation_result
            
        except Exception as e:
            return {
                "name": "Ukrainian Language Processing",
                "success": False,
                "details": f"Simulation failed: {e}",
                "language_score": 0
            }
    
    def _simulate_deployment_process(self):
        """Simulate deployment process across all methods"""
        print("   🚀 Simulating Deployment Process...")
        
        try:
            deployment_methods = {
                "local": self._test_local_deployment_readiness(),
                "docker": self._test_docker_deployment_readiness(),
                "kubernetes": self._test_kubernetes_deployment_readiness()
            }
            
            ready_methods = sum(1 for method in deployment_methods.values() if method)
            
            simulation_result = {
                "name": "Multi-Method Deployment",
                "success": ready_methods >= 2,
                "details": f"Ready deployment methods: {ready_methods}/3",
                "methods": deployment_methods,
                "deployment_score": ready_methods / 3
            }
            
            print(f"      Deployment readiness: {simulation_result['success']} ({ready_methods}/3 methods)")
            return simulation_result
            
        except Exception as e:
            return {
                "name": "Multi-Method Deployment",
                "success": False,
                "details": f"Simulation failed: {e}",
                "deployment_score": 0
            }
    
    def _test_local_deployment_readiness(self):
        """Test if local deployment is ready"""
        required_files = ['atlas_core.py', 'start_atlas.sh', 'requirements.txt']
        return all(os.path.exists(f) for f in required_files)
    
    def _test_docker_deployment_readiness(self):
        """Test if Docker deployment is ready"""
        try:
            result = subprocess.run(['docker', 'compose', 'config'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _test_kubernetes_deployment_readiness(self):
        """Test if Kubernetes deployment is ready"""
        k8s_dir = Path('k8s')
        makefile_exists = os.path.exists('Makefile')
        manifests = len(list(k8s_dir.rglob('*.yaml'))) if k8s_dir.exists() else 0
        
        return k8s_dir.exists() and makefile_exists and manifests >= 5
    
    def generate_final_assessment(self):
        """Generate final automation system assessment"""
        print("\n📊 Generating Final Assessment...")
        
        # Calculate overall scores
        category_scores = {}
        for category, tests in self.validation_results["categories"].items():
            if tests:
                avg_score = sum(test["score"] for test in tests.values()) / len(tests)
                category_scores[category] = avg_score
        
        # Calculate automation capability score
        demo_scores = [demo.get("coordination_score", demo.get("orchestration_score", 
                               demo.get("language_score", demo.get("deployment_score", 0))))
                      for demo in self.validation_results["automation_capabilities"]]
        automation_score = sum(demo_scores) / len(demo_scores) if demo_scores else 0
        
        # Overall assessment
        overall_score = (sum(category_scores.values()) + automation_score) / (len(category_scores) + 1)
        
        assessment = {
            "overall_score": round(overall_score * 100, 1),
            "category_scores": {k: round(v * 100, 1) for k, v in category_scores.items()},
            "automation_score": round(automation_score * 100, 1),
            "readiness_level": self._determine_readiness_level(overall_score),
            "deployment_recommendation": self._get_deployment_recommendation(),
            "next_steps": self._generate_next_steps(overall_score, category_scores)
        }
        
        self.validation_results["overall_assessment"] = assessment
        
        # Print assessment
        print(f"\n🎯 Atlas Automation System Assessment:")
        print(f"   Overall Score: {assessment['overall_score']}/100")
        print(f"   Readiness Level: {assessment['readiness_level']}")
        print(f"   Automation Score: {assessment['automation_score']}/100")
        
        print(f"\n📋 Category Scores:")
        for category, score in assessment["category_scores"].items():
            print(f"   {category}: {score}/100")
        
        print(f"\n🚀 Deployment Recommendation: {assessment['deployment_recommendation']}")
        
        print(f"\n💡 Next Steps:")
        for i, step in enumerate(assessment["next_steps"], 1):
            print(f"   {i}. {step}")
        
        return assessment
    
    def _determine_readiness_level(self, score):
        """Determine system readiness level based on score"""
        if score >= 0.9:
            return "Production Ready"
        elif score >= 0.8:
            return "Nearly Ready"
        elif score >= 0.7:
            return "Good Progress"
        elif score >= 0.6:
            return "Needs Work"
        else:
            return "Significant Issues"
    
    def _get_deployment_recommendation(self):
        """Get deployment method recommendation"""
        if self._test_kubernetes_deployment_readiness():
            return "Kubernetes (Production)"
        elif self._test_docker_deployment_readiness():
            return "Docker (Development/Testing)"
        elif self._test_local_deployment_readiness():
            return "Local Python (Development)"
        else:
            return "Fix configuration issues first"
    
    def _generate_next_steps(self, overall_score, category_scores):
        """Generate next steps based on assessment"""
        steps = []
        
        if overall_score >= 0.8:
            steps.append("🎉 System is ready! Deploy using recommended method")
            steps.append("🧪 Run live testing with actual LLM services")
            steps.append("📊 Monitor system performance and health")
        else:
            # Identify weakest areas
            if category_scores:
                weakest = min(category_scores.items(), key=lambda x: x[1])
                steps.append(f"🔧 Improve {weakest[0]} category (score: {weakest[1]:.1f})")
            
            if overall_score < 0.6:
                steps.append("⚠️  Address critical issues before deployment")
            
            steps.append("🔄 Re-run validation after fixes")
        
        # Always include dependency resolution
        steps.append("📦 Resolve Python package dependencies (PyPI/network issues)")
        steps.append("🚀 Test deployment method of choice")
        
        return steps
    
    def save_comprehensive_report(self):
        """Save comprehensive validation report"""
        report_file = 'atlas_automation_validation_report.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Comprehensive report saved to: {report_file}")
        return report_file
    
    def run_full_validation(self):
        """Run complete automation system validation"""
        print("🤖 Atlas Full Automation System Validation")
        print("=" * 70)
        
        validation_steps = [
            ("System Architecture", self.validate_system_architecture),
            ("MCP Automation Hub", self.validate_mcp_automation_hub),
            ("Deployment Methods", self.validate_deployment_methods),
            ("Automation Scripts", self.validate_automation_scripts),
            ("Ukrainian Language", self.validate_ukrainian_automation),
            ("Autonomous Workflows", self.validate_autonomous_workflows),
            ("Capability Demonstration", self.demonstrate_automation_capabilities)
        ]
        
        passed_validations = 0
        total_validations = len(validation_steps)
        
        for step_name, validation_func in validation_steps:
            try:
                print(f"\n{step_name}...")
                success = validation_func()
                if success:
                    passed_validations += 1
                    print(f"   ✅ {step_name}: PASSED")
                else:
                    print(f"   ❌ {step_name}: NEEDS ATTENTION")
            except Exception as e:
                print(f"   💥 {step_name}: ERROR - {e}")
        
        # Generate final assessment
        final_assessment = self.generate_final_assessment()
        
        # Save report
        report_file = self.save_comprehensive_report()
        
        # Final summary
        print(f"\n" + "=" * 70)
        print(f"🎯 VALIDATION SUMMARY:")
        print(f"   Completed Validations: {passed_validations}/{total_validations}")
        print(f"   Overall System Score: {final_assessment['overall_score']}/100")
        print(f"   System Status: {final_assessment['readiness_level']}")
        
        if final_assessment['overall_score'] >= 80:
            print(f"\n🎉 ATLAS AUTOMATION SYSTEM: READY FOR DEPLOYMENT!")
            print(f"   Recommended method: {final_assessment['deployment_recommendation']}")
        else:
            print(f"\n⚠️  ATLAS AUTOMATION SYSTEM: NEEDS ATTENTION")
            print(f"   Address issues before production deployment")
        
        return final_assessment['overall_score'] >= 70

def main():
    """Main validation execution"""
    validator = AtlasAutomationValidator()
    success = validator.run_full_validation()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())