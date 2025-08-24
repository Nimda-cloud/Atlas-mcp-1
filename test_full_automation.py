#!/usr/bin/env python3
"""
Atlas Full Automation System Test
=================================

Comprehensive test suite to validate the full automation capabilities
of the Atlas MCP system without requiring external dependencies.
"""

import os
import sys
import json
import subprocess
import time
import ast
from pathlib import Path
from datetime import datetime

class AtlasFullAutomationTest:
    """Comprehensive test suite for Atlas automation system"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.system_info = {
            "platform": sys.platform,
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "test_start": self.start_time.isoformat()
        }
        
    def log_test(self, category, name, passed, details=None):
        """Log test result with category"""
        result = {
            "category": category,
            "name": name,
            "passed": passed,
            "details": details or "",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} [{category}] {name}")
        if details and not passed:
            print(f"      {details}")
    
    def test_core_system_structure(self):
        """Test core system file structure and configuration"""
        print("\n🏗️  Testing Core System Structure...")
        
        # Core Python files
        core_files = [
            'atlas_core.py',
            'mcp_automation_server.py', 
            'mcp_macos_automator.py'
        ]
        
        for file in core_files:
            if os.path.exists(file):
                self.log_test("Structure", f"Core file exists: {file}", True)
                
                # Test syntax
                try:
                    with open(file, 'r') as f:
                        source = f.read()
                    ast.parse(source)
                    self.log_test("Structure", f"Syntax valid: {file}", True)
                except Exception as e:
                    self.log_test("Structure", f"Syntax valid: {file}", False, str(e))
            else:
                self.log_test("Structure", f"Core file exists: {file}", False)
        
        # Configuration files
        config_files = [
            'requirements.txt',
            'docker-compose.yml',
            'Dockerfile',
            '.env.k8s.example'
        ]
        
        for file in config_files:
            exists = os.path.exists(file)
            self.log_test("Structure", f"Config file: {file}", exists)
    
    def test_multi_agent_architecture(self):
        """Test multi-agent architecture definitions"""
        print("\n🤖 Testing Multi-Agent Architecture...")
        
        try:
            with open('atlas_core.py', 'r') as f:
                source = f.read()
            
            # Check for agent-related classes and functions
            agent_indicators = [
                'class LLMAgent',
                'class AgentConfig', 
                'class AtlasCore',
                'generate_response',
                'call_ollama_api',
                'call_gemini_api',
                'interface_agent',
                'orchestrator_agent',
                'monitor_agent'
            ]
            
            for indicator in agent_indicators:
                if indicator in source:
                    self.log_test("Architecture", f"Found: {indicator}", True)
                else:
                    self.log_test("Architecture", f"Found: {indicator}", False)
            
            # Check for multi-agent coordination
            coordination_patterns = [
                'agents_online',
                'agent_status',
                'LLM1',
                'LLM2', 
                'LLM3'
            ]
            
            for pattern in coordination_patterns:
                if pattern in source:
                    self.log_test("Architecture", f"Multi-agent pattern: {pattern}", True)
                else:
                    self.log_test("Architecture", f"Multi-agent pattern: {pattern}", False)
                    
        except Exception as e:
            self.log_test("Architecture", "Source code analysis", False, str(e))
    
    def test_mcp_services_structure(self):
        """Test MCP (Model Context Protocol) services structure"""
        print("\n🔌 Testing MCP Services Structure...")
        
        # Check MCP automation server
        try:
            with open('mcp_automation_server.py', 'r') as f:
                automation_source = f.read()
            
            mcp_automation_features = [
                'class MCPAutomationServer',
                'handle_tool_call',
                'read_file',
                'write_file',
                'execute_command',
                'system_info',
                'http_request'
            ]
            
            for feature in mcp_automation_features:
                if feature in automation_source:
                    self.log_test("MCP", f"Automation feature: {feature}", True)
                else:
                    self.log_test("MCP", f"Automation feature: {feature}", False)
                    
        except Exception as e:
            self.log_test("MCP", "Automation server analysis", False, str(e))
        
        # Check MCP macOS automator
        try:
            with open('mcp_macos_automator.py', 'r') as f:
                macos_source = f.read()
            
            macos_features = [
                'class MCPMacOSAutomator',
                'applescript',
                'automation',
                'execute_',
                'get_system_info'
            ]
            
            for feature in macos_features:
                if feature in macos_source:
                    self.log_test("MCP", f"macOS feature: {feature}", True)
                else:
                    self.log_test("MCP", f"macOS feature: {feature}", False)
                    
        except Exception as e:
            self.log_test("MCP", "macOS automator analysis", False, str(e))
    
    def test_automation_scripts(self):
        """Test automation and management scripts"""
        print("\n🔧 Testing Automation Scripts...")
        
        scripts = [
            'start_atlas.sh',
            'atlas_health_monitor.sh',
            'atlas_diagnostic.sh',
            'atlas_autonomous_setup.sh',
            'install_macos.sh',
            'restart_atlas.sh'
        ]
        
        for script in scripts:
            if os.path.exists(script):
                self.log_test("Scripts", f"Script exists: {script}", True)
                
                # Check if executable
                if os.access(script, os.X_OK):
                    self.log_test("Scripts", f"Executable: {script}", True)
                else:
                    self.log_test("Scripts", f"Executable: {script}", False)
                
                # Check shebang
                try:
                    with open(script, 'r') as f:
                        first_line = f.readline().strip()
                    
                    if first_line.startswith('#!/'):
                        self.log_test("Scripts", f"Has shebang: {script}", True)
                    else:
                        self.log_test("Scripts", f"Has shebang: {script}", False)
                except Exception as e:
                    self.log_test("Scripts", f"Read script: {script}", False, str(e))
            else:
                self.log_test("Scripts", f"Script exists: {script}", False)
    
    def test_deployment_configurations(self):
        """Test deployment method configurations"""
        print("\n🚀 Testing Deployment Configurations...")
        
        # Test Docker configuration
        try:
            with open('docker-compose.yml', 'r') as f:
                compose_content = f.read()
            
            docker_features = [
                'atlas-core',
                'mcp-automation',
                'mcp-automator',
                'atlas-3d',
                'version:',
                'services:',
                'ports:',
                '8000:8000'
            ]
            
            for feature in docker_features:
                if feature in compose_content:
                    self.log_test("Deployment", f"Docker feature: {feature}", True)
                else:
                    self.log_test("Deployment", f"Docker feature: {feature}", False)
                    
        except Exception as e:
            self.log_test("Deployment", "Docker compose analysis", False, str(e))
        
        # Test Kubernetes configuration
        k8s_path = Path('k8s')
        if k8s_path.exists():
            self.log_test("Deployment", "Kubernetes directory exists", True)
            
            k8s_files = list(k8s_path.rglob('*.yaml')) + list(k8s_path.rglob('*.yml'))
            self.log_test("Deployment", f"Kubernetes manifests found: {len(k8s_files)}", len(k8s_files) > 0)
        else:
            self.log_test("Deployment", "Kubernetes directory exists", False)
        
        # Test Makefile for Kubernetes operations
        if os.path.exists('Makefile'):
            self.log_test("Deployment", "Makefile exists", True)
            
            try:
                with open('Makefile', 'r') as f:
                    makefile_content = f.read()
                
                make_targets = [
                    'build-images',
                    'install-dev',
                    'status-dev',
                    'clean-dev'
                ]
                
                for target in make_targets:
                    if target in makefile_content:
                        self.log_test("Deployment", f"Make target: {target}", True)
                    else:
                        self.log_test("Deployment", f"Make target: {target}", False)
                        
            except Exception as e:
                self.log_test("Deployment", "Makefile analysis", False, str(e))
        else:
            self.log_test("Deployment", "Makefile exists", False)
    
    def test_health_monitoring_system(self):
        """Test health monitoring and diagnostic capabilities"""
        print("\n🏥 Testing Health Monitoring System...")
        
        # Test health monitor script
        if os.path.exists('atlas_health_monitor.sh'):
            try:
                with open('atlas_health_monitor.sh', 'r') as f:
                    monitor_content = f.read()
                
                # Check for service endpoints
                health_endpoints = [
                    'localhost:8000/status',
                    'localhost:8080/health', 
                    'localhost:4002/health',
                    'localhost:4003/health',
                    'localhost:4004/health',
                    'localhost:4005/mcp'
                ]
                
                for endpoint in health_endpoints:
                    if endpoint in monitor_content:
                        self.log_test("Monitoring", f"Health endpoint: {endpoint}", True)
                    else:
                        self.log_test("Monitoring", f"Health endpoint: {endpoint}", False)
                
                # Check for monitoring functions
                monitor_functions = [
                    'check_service',
                    'timeout',
                    'curl'
                ]
                
                for func in monitor_functions:
                    if func in monitor_content:
                        self.log_test("Monitoring", f"Monitor function: {func}", True)
                    else:
                        self.log_test("Monitoring", f"Monitor function: {func}", False)
                        
            except Exception as e:
                self.log_test("Monitoring", "Health monitor analysis", False, str(e))
        else:
            self.log_test("Monitoring", "Health monitor script exists", False)
        
        # Test diagnostic script
        if os.path.exists('atlas_diagnostic.sh'):
            self.log_test("Monitoring", "Diagnostic script exists", True)
        else:
            self.log_test("Monitoring", "Diagnostic script exists", False)
    
    def test_ukrainian_language_support(self):
        """Test Ukrainian language processing capabilities"""
        print("\n🇺🇦 Testing Ukrainian Language Support...")
        
        # Check Ukrainian instruction file
        if os.path.exists('ІНСТРУКЦІЯ.md'):
            self.log_test("Language", "Ukrainian instructions exist", True)
            
            try:
                with open('ІНСТРУКЦІЯ.md', 'r', encoding='utf-8') as f:
                    instruction_content = f.read()
                
                ukrainian_features = [
                    'Atlas Autonomous System',
                    'використання',
                    'команди',
                    'автоматизація',
                    'інсталяція'
                ]
                
                for feature in ukrainian_features:
                    if feature in instruction_content:
                        self.log_test("Language", f"Ukrainian content: {feature}", True)
                    else:
                        self.log_test("Language", f"Ukrainian content: {feature}", False)
                        
            except Exception as e:
                self.log_test("Language", "Ukrainian instructions analysis", False, str(e))
        else:
            self.log_test("Language", "Ukrainian instructions exist", False)
        
        # Check for Ukrainian language processing in test files
        test_files = ['test_execution.py']
        for test_file in test_files:
            if os.path.exists(test_file):
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        test_content = f.read()
                    
                    ukrainian_test_commands = [
                        'відкрий хром',
                        'говори привіт',
                        'тестування'
                    ]
                    
                    for cmd in ukrainian_test_commands:
                        if cmd in test_content:
                            self.log_test("Language", f"Ukrainian test command: {cmd}", True)
                        else:
                            self.log_test("Language", f"Ukrainian test command: {cmd}", False)
                            
                except Exception as e:
                    self.log_test("Language", f"Test file analysis: {test_file}", False, str(e))
    
    def test_autonomous_capabilities(self):
        """Test autonomous system capabilities"""
        print("\n🦾 Testing Autonomous Capabilities...")
        
        # Test GitHub workflows for autonomous operation
        workflows = [
            '.github/workflows/pr-agent-ci.yml',
            '.github/workflows/post-merge-local.yml'
        ]
        
        for workflow in workflows:
            if os.path.exists(workflow):
                self.log_test("Autonomous", f"Workflow exists: {workflow}", True)
                
                try:
                    with open(workflow, 'r') as f:
                        workflow_content = f.read()
                    
                    # Check for autonomous features
                    autonomous_features = [
                        'on:',
                        'jobs:',
                        'runs-on:',
                        'steps:'
                    ]
                    
                    for feature in autonomous_features:
                        if feature in workflow_content:
                            self.log_test("Autonomous", f"Workflow feature: {feature}", True)
                        else:
                            self.log_test("Autonomous", f"Workflow feature: {feature}", False)
                            
                except Exception as e:
                    self.log_test("Autonomous", f"Workflow analysis: {workflow}", False, str(e))
            else:
                self.log_test("Autonomous", f"Workflow exists: {workflow}", False)
        
        # Test autonomous setup script
        if os.path.exists('atlas_autonomous_setup.sh'):
            self.log_test("Autonomous", "Autonomous setup script exists", True)
        else:
            self.log_test("Autonomous", "Autonomous setup script exists", False)
    
    def test_integration_capabilities(self):
        """Test system integration and API capabilities"""
        print("\n🔗 Testing Integration Capabilities...")
        
        # Check for API endpoint definitions
        try:
            with open('atlas_core.py', 'r') as f:
                core_source = f.read()
            
            api_endpoints = [
                '/status',
                '/chat',
                '/health',
                'FastAPI',
                '@app.post',
                '@app.get'
            ]
            
            for endpoint in api_endpoints:
                if endpoint in core_source:
                    self.log_test("Integration", f"API endpoint: {endpoint}", True)
                else:
                    self.log_test("Integration", f"API endpoint: {endpoint}", False)
                    
        except Exception as e:
            self.log_test("Integration", "API analysis", False, str(e))
        
        # Check integration examples
        integration_dir = Path('archived_3d_assets/frontend-express-standalone/examples')
        if integration_dir.exists():
            examples = list(integration_dir.glob('*.js'))
            self.log_test("Integration", f"Integration examples found: {len(examples)}", len(examples) > 0)
        else:
            self.log_test("Integration", "Integration examples directory", False)
    
    def simulate_basic_workflow(self):
        """Simulate basic automation workflow (without external dependencies)"""
        print("\n⚡ Simulating Basic Automation Workflow...")
        
        # Test basic system commands that don't require external packages
        basic_commands = [
            ['python', '--version'],
            ['ls', '-la'],
            ['echo', 'Atlas automation test']
        ]
        
        for cmd in basic_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                success = result.returncode == 0
                self.log_test("Workflow", f"Basic command: {' '.join(cmd)}", success)
                if not success:
                    self.log_test("Workflow", f"Command error: {' '.join(cmd)}", False, result.stderr)
            except Exception as e:
                self.log_test("Workflow", f"Command execution: {' '.join(cmd)}", False, str(e))
        
        # Test file operations simulation
        test_file = 'test_automation_output.txt'
        try:
            # Write test
            with open(test_file, 'w') as f:
                f.write(f"Atlas automation test at {datetime.now().isoformat()}")
            self.log_test("Workflow", "File write operation", True)
            
            # Read test
            with open(test_file, 'r') as f:
                content = f.read()
            self.log_test("Workflow", "File read operation", "Atlas automation test" in content)
            
            # Cleanup
            os.remove(test_file)
            self.log_test("Workflow", "File cleanup operation", True)
            
        except Exception as e:
            self.log_test("Workflow", "File operations", False, str(e))
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating Comprehensive Report...")
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group by category
        categories = {}
        for result in self.test_results:
            category = result['category']
            if category not in categories:
                categories[category] = {'passed': 0, 'failed': 0, 'tests': []}
            
            if result['passed']:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
            categories[category]['tests'].append(result)
        
        # Generate report
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            "test_metadata": {
                "system_info": self.system_info,
                "test_start": self.start_time.isoformat(),
                "test_end": end_time.isoformat(),
                "duration_seconds": duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2)
            },
            "categories": categories,
            "detailed_results": self.test_results,
            "automation_assessment": self._generate_automation_assessment(categories),
            "recommendations": self._generate_recommendations(categories)
        }
        
        # Save report
        report_file = 'atlas_full_automation_test_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n🎯 Full Automation Test Results Summary:")
        print(f"   Total tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Duration: {duration:.2f} seconds")
        
        print(f"\n📋 Category Breakdown:")
        for category, stats in categories.items():
            total = stats['passed'] + stats['failed']
            rate = (stats['passed'] / total * 100) if total > 0 else 0
            print(f"   {category}: {stats['passed']}/{total} ({rate:.1f}%)")
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return report
    
    def _generate_automation_assessment(self, categories):
        """Generate automation system assessment"""
        assessment = {
            "overall_readiness": "unknown",
            "critical_areas": [],
            "strengths": [],
            "automation_score": 0
        }
        
        # Calculate automation score based on category performance
        weights = {
            "Structure": 0.15,
            "Architecture": 0.20,
            "MCP": 0.20,
            "Scripts": 0.15,
            "Deployment": 0.10,
            "Monitoring": 0.10,
            "Language": 0.05,
            "Autonomous": 0.05
        }
        
        total_score = 0
        for category, weight in weights.items():
            if category in categories:
                stats = categories[category]
                total = stats['passed'] + stats['failed']
                if total > 0:
                    category_score = (stats['passed'] / total) * weight * 100
                    total_score += category_score
        
        assessment["automation_score"] = round(total_score, 1)
        
        # Determine readiness level
        if total_score >= 90:
            assessment["overall_readiness"] = "excellent"
        elif total_score >= 75:
            assessment["overall_readiness"] = "good"
        elif total_score >= 60:
            assessment["overall_readiness"] = "fair"
        else:
            assessment["overall_readiness"] = "needs_improvement"
        
        # Identify strengths and critical areas
        for category, stats in categories.items():
            total = stats['passed'] + stats['failed']
            if total > 0:
                success_rate = (stats['passed'] / total) * 100
                if success_rate >= 80:
                    assessment["strengths"].append(category)
                elif success_rate < 50:
                    assessment["critical_areas"].append(category)
        
        return assessment
    
    def _generate_recommendations(self, categories):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Network dependency issue
        recommendations.append({
            "priority": "high",
            "area": "Dependencies", 
            "issue": "Network issues prevent pip package installation",
            "recommendation": "Use Docker deployment or pre-installed environments to avoid PyPI SSL issues",
            "action": "Consider using 'make install-dev' for Kubernetes deployment"
        })
        
        # Check for failed categories
        for category, stats in categories.items():
            total = stats['passed'] + stats['failed']
            if total > 0:
                success_rate = (stats['passed'] / total) * 100
                if success_rate < 80:
                    recommendations.append({
                        "priority": "medium",
                        "area": category,
                        "issue": f"Category has {success_rate:.1f}% success rate",
                        "recommendation": f"Review and fix failing tests in {category} category",
                        "action": "Check detailed test results for specific failures"
                    })
        
        # Positive recommendations
        if len([c for c, s in categories.items() if (s['passed'] / (s['passed'] + s['failed']) if s['passed'] + s['failed'] > 0 else 0) >= 0.9]) >= 3:
            recommendations.append({
                "priority": "info",
                "area": "Overall",
                "issue": "System shows strong automation foundation",
                "recommendation": "Focus on deployment testing and live service validation",
                "action": "Run 'docker compose up' or './start_atlas.sh --local' to test live system"
            })
        
        return recommendations
    
    def run_all_tests(self):
        """Run all automation tests"""
        print("🤖 Atlas Full Automation System Test")
        print("=" * 60)
        
        test_methods = [
            self.test_core_system_structure,
            self.test_multi_agent_architecture,
            self.test_mcp_services_structure,
            self.test_automation_scripts,
            self.test_deployment_configurations,
            self.test_health_monitoring_system,
            self.test_ukrainian_language_support,
            self.test_autonomous_capabilities,
            self.test_integration_capabilities,
            self.simulate_basic_workflow
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test method {test_method.__name__} failed: {e}")
                self.log_test("System", test_method.__name__, False, str(e))
        
        # Generate final report
        report = self.generate_comprehensive_report()
        
        print(f"\n🎯 Automation Assessment:")
        assessment = report['automation_assessment']
        print(f"   Overall Readiness: {assessment['overall_readiness']}")
        print(f"   Automation Score: {assessment['automation_score']}/100")
        
        if assessment['strengths']:
            print(f"   Strengths: {', '.join(assessment['strengths'])}")
        if assessment['critical_areas']:
            print(f"   Critical Areas: {', '.join(assessment['critical_areas'])}")
        
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"   {i}. [{rec['priority'].upper()}] {rec['area']}: {rec['recommendation']}")
        
        # Return overall success
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        return passed_tests >= (total_tests * 0.75)  # 75% success threshold

def main():
    """Main test execution"""
    tester = AtlasFullAutomationTest()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 Atlas Full Automation System: READY")
        print(f"💡 Next steps: Deploy and test live system functionality")
        return 0
    else:
        print(f"\n⚠️  Atlas Full Automation System: NEEDS ATTENTION")
        print(f"💡 Review test report and address critical issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())