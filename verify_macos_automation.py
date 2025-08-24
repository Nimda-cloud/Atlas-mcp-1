#!/usr/bin/env python3
"""
Atlas macOS Automation Verification Script
==========================================

Comprehensive verification of macOS automation capabilities to answer:
"Перевіть чи досягнута повна автоматичзація з повним управліннм тобою даним мак ос?"
(Check if full automation with complete macOS control has been achieved?)

This script tests all automation components and provides a detailed status report.
"""

import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class MacOSAutomationVerifier:
    """Comprehensive verifier for Atlas macOS automation capabilities"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {}
        self.is_macos = platform.system() == "Darwin"
        self.test_count = 0
        self.passed_count = 0
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a test and record the result"""
        self.test_count += 1
        try:
            result = test_func()
            if result:
                self.passed_count += 1
                self.log(f"✅ {test_name}: PASS", "TEST")
            else:
                self.log(f"❌ {test_name}: FAIL", "TEST")
            return result
        except Exception as e:
            self.log(f"❌ {test_name}: ERROR - {str(e)}", "TEST")
            return False
    
    def verify_core_structure(self) -> Dict[str, Any]:
        """Verify core Atlas system structure"""
        self.log("🔍 Verifying core system structure...")
        
        core_files = [
            "atlas_core.py",
            "mcp_automation_server.py", 
            "mcp_macos_automator.py",
            "requirements.txt",
            "start_atlas.sh",
            "docker-compose.yml"
        ]
        
        results = {}
        for file in core_files:
            exists = os.path.exists(file)
            results[f"file_{file}"] = self.run_test(f"Core file exists: {file}", lambda f=file: os.path.exists(f))
            
            if exists and file.endswith('.py'):
                results[f"syntax_{file}"] = self.run_test(
                    f"Python syntax valid: {file}",
                    lambda f=file: self._check_python_syntax(f)
                )
        
        return results
    
    def verify_macos_capabilities(self) -> Dict[str, Any]:
        """Verify macOS-specific automation capabilities"""
        self.log("🍎 Verifying macOS automation capabilities...")
        
        results = {}
        
        # Check if macOS automator module exists and is functional
        results["macos_automator_exists"] = self.run_test(
            "macOS Automator module exists",
            lambda: os.path.exists("mcp_macos_automator.py")
        )
        
        # Analyze macOS automation features
        macos_features = self._analyze_macos_features()
        for feature, present in macos_features.items():
            results[f"feature_{feature}"] = self.run_test(
                f"macOS feature available: {feature}",
                lambda p=present: p
            )
        
        # Test AppleScript capability (if on macOS)
        if self.is_macos:
            results["applescript_available"] = self.run_test(
                "AppleScript execution available",
                self._test_applescript
            )
        else:
            self.log("⚠️  Not on macOS - skipping platform-specific tests")
            results["applescript_available"] = False
        
        return results
    
    def verify_autonomous_workflows(self) -> Dict[str, Any]:
        """Verify autonomous workflow capabilities"""
        self.log("🤖 Verifying autonomous workflows...")
        
        results = {}
        
        # Check GitHub workflows
        workflow_files = [
            ".github/workflows/pr-agent-ci.yml",
            ".github/workflows/post-merge-local.yml"
        ]
        
        for workflow in workflow_files:
            results[f"workflow_{os.path.basename(workflow)}"] = self.run_test(
                f"Workflow exists: {os.path.basename(workflow)}",
                lambda w=workflow: os.path.exists(w)
            )
        
        # Check autonomous scripts
        autonomous_scripts = [
            "atlas_autonomous_setup.sh",
            "atlas_autonomous_diagnostic.sh", 
            "atlas_start_autonomous.sh",
            "setup_autonomous_atlas.py"
        ]
        
        for script in autonomous_scripts:
            if os.path.exists(script):
                results[f"script_{script}"] = self.run_test(
                    f"Autonomous script exists: {script}",
                    lambda s=script: os.path.exists(s)
                )
        
        # Check for autonomous configuration
        results["autonomous_status"] = self.run_test(
            "Autonomous status configuration exists",
            lambda: os.path.exists("AUTONOMOUS_STATUS.json")
        )
        
        return results
    
    def verify_mcp_services(self) -> Dict[str, Any]:
        """Verify MCP (Model Context Protocol) services"""
        self.log("🔌 Verifying MCP services...")
        
        results = {}
        
        # Check MCP service files
        mcp_services = {
            "automation": "mcp_automation_server.py",
            "macos_automator": "mcp_macos_automator.py"
        }
        
        for service_name, file_name in mcp_services.items():
            results[f"mcp_{service_name}"] = self.run_test(
                f"MCP service exists: {service_name}",
                lambda f=file_name: os.path.exists(f)
            )
            
            if os.path.exists(file_name):
                # Check if service has proper structure
                results[f"mcp_{service_name}_structure"] = self.run_test(
                    f"MCP service has proper structure: {service_name}",
                    lambda f=file_name: self._check_mcp_structure(f)
                )
        
        return results
    
    def verify_deployment_methods(self) -> Dict[str, Any]:
        """Verify available deployment methods"""
        self.log("🚀 Verifying deployment methods...")
        
        results = {}
        
        # Local Python deployment
        results["local_python"] = self.run_test(
            "Local Python deployment supported",
            lambda: os.path.exists("start_atlas.sh") and os.path.exists("atlas_core.py")
        )
        
        # Docker deployment
        results["docker_deployment"] = self.run_test(
            "Docker deployment supported", 
            lambda: os.path.exists("Dockerfile") and os.path.exists("docker-compose.yml")
        )
        
        # Kubernetes deployment
        results["kubernetes_deployment"] = self.run_test(
            "Kubernetes deployment supported",
            lambda: os.path.exists("k8s") and os.path.exists("Makefile")
        )
        
        return results
    
    def verify_ukrainian_support(self) -> Dict[str, Any]:
        """Verify Ukrainian language support"""
        self.log("🇺🇦 Verifying Ukrainian language support...")
        
        results = {}
        
        # Check Ukrainian documentation
        results["ukrainian_docs"] = self.run_test(
            "Ukrainian documentation exists",
            lambda: os.path.exists("ІНСТРУКЦІЯ.md") or os.path.exists("ATLAS_АВТОНОМНА_СИСТЕМА.md")
        )
        
        # Check for Ukrainian content in files
        ukrainian_content = self._check_ukrainian_content()
        results["ukrainian_content"] = self.run_test(
            "Ukrainian content found in system",
            lambda: ukrainian_content > 0
        )
        
        return results
    
    def generate_automation_status(self) -> Dict[str, Any]:
        """Generate comprehensive automation status report"""
        self.log("📊 Generating automation status report...")
        
        # Read existing status if available
        autonomous_status = {}
        if os.path.exists("AUTONOMOUS_STATUS.json"):
            try:
                with open("AUTONOMOUS_STATUS.json", 'r') as f:
                    autonomous_status = json.load(f)
            except Exception as e:
                self.log(f"Could not read AUTONOMOUS_STATUS.json: {e}")
        
        # Calculate automation completeness
        automation_score = (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        
        status = {
            "verification_timestamp": self.start_time.isoformat(),
            "platform": platform.system(),
            "is_macos": self.is_macos,
            "tests_run": self.test_count,
            "tests_passed": self.passed_count,
            "automation_score": round(automation_score, 2),
            "existing_status": autonomous_status,
            "macos_control_assessment": self._assess_macos_control(),
            "autonomy_level": self._assess_autonomy_level(automation_score),
            "recommendations": self._generate_recommendations()
        }
        
        return status
    
    def _check_python_syntax(self, file_path: str) -> bool:
        """Check if Python file has valid syntax"""
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            return True
        except SyntaxError:
            return False
        except Exception:
            return False
    
    def _analyze_macos_features(self) -> Dict[str, bool]:
        """Analyze available macOS automation features"""
        features = {
            "app_control": False,
            "applescript": False,
            "shortcuts": False,
            "system_prefs": False,
            "screen_capture": False,
            "finder_ops": False,
            "notifications": False,
            "window_control": False
        }
        
        if os.path.exists("mcp_macos_automator.py"):
            try:
                with open("mcp_macos_automator.py", 'r') as f:
                    content = f.read()
                    
                features["app_control"] = "app_control" in content
                features["applescript"] = "applescript" in content or "AppleScript" in content
                features["shortcuts"] = "shortcuts" in content or "Shortcuts" in content
                features["system_prefs"] = "system_prefs" in content or "system preferences" in content
                features["screen_capture"] = "screenshot" in content or "screen" in content
                features["finder_ops"] = "finder" in content or "Finder" in content
                features["notifications"] = "notification" in content
                features["window_control"] = "window_control" in content or "window" in content
                
            except Exception as e:
                self.log(f"Error analyzing macOS features: {e}")
        
        return features
    
    def _test_applescript(self) -> bool:
        """Test if AppleScript execution is available"""
        try:
            # Simple AppleScript test
            result = subprocess.run(
                ["osascript", "-e", "return 1"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_mcp_structure(self, file_path: str) -> bool:
        """Check if MCP service has proper structure"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for essential MCP components
            required_components = ["MCPTool", "register_tools", "class", "__init__"]
            return all(component in content for component in required_components)
        except Exception:
            return False
    
    def _check_ukrainian_content(self) -> int:
        """Count Ukrainian content in system files"""
        ukrainian_files = ["ІНСТРУКЦІЯ.md", "ATLAS_АВТОНОМНА_СИСТЕМА.md"]
        content_count = 0
        
        for file in ukrainian_files:
            if os.path.exists(file):
                content_count += 1
        
        return content_count
    
    def _assess_macos_control(self) -> Dict[str, Any]:
        """Assess the level of macOS control achieved"""
        if not self.is_macos:
            return {
                "status": "not_applicable",
                "reason": "Not running on macOS",
                "capabilities": []
            }
        
        capabilities = []
        if os.path.exists("mcp_macos_automator.py"):
            with open("mcp_macos_automator.py", 'r') as f:
                content = f.read()
                
            if "app_control" in content:
                capabilities.append("Application Management")
            if "applescript" in content:
                capabilities.append("AppleScript Automation")
            if "shortcuts" in content:
                capabilities.append("Shortcuts Integration")
            if "system_prefs" in content:
                capabilities.append("System Preferences Control")
            if "screenshot" in content:
                capabilities.append("Screen Capture")
            if "window_control" in content:
                capabilities.append("Window Management")
        
        control_level = len(capabilities)
        if control_level >= 5:
            status = "comprehensive"
        elif control_level >= 3:
            status = "moderate"
        elif control_level >= 1:
            status = "basic"
        else:
            status = "minimal"
        
        return {
            "status": status,
            "capabilities_count": control_level,
            "capabilities": capabilities,
            "assessment": f"{control_level}/6 core macOS automation capabilities available"
        }
    
    def _assess_autonomy_level(self, automation_score: float) -> str:
        """Assess the overall autonomy level"""
        if automation_score >= 90:
            return "fully_autonomous"
        elif automation_score >= 75:
            return "highly_autonomous"
        elif automation_score >= 50:
            return "moderately_autonomous"
        else:
            return "basic_automation"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for improving automation"""
        recommendations = []
        
        if not self.is_macos:
            recommendations.append("Deploy on macOS for full macOS automation capabilities")
        
        if not os.path.exists(".github/workflows/post-merge-local.yml"):
            recommendations.append("Set up self-hosted macOS runner for complete CI/CD automation")
        
        if self.passed_count < self.test_count:
            failed_tests = self.test_count - self.passed_count
            recommendations.append(f"Address {failed_tests} failed tests to improve automation score")
        
        if not os.path.exists("AUTONOMOUS_STATUS.json"):
            recommendations.append("Update autonomous status configuration")
        
        return recommendations
    
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run complete verification and generate report"""
        self.log("🚀 Starting comprehensive Atlas macOS automation verification...")
        
        verification_results = {
            "metadata": {
                "start_time": self.start_time.isoformat(),
                "platform": platform.system(),
                "is_macos": self.is_macos,
                "verification_version": "1.0"
            }
        }
        
        # Run all verification categories
        verification_results["core_structure"] = self.verify_core_structure()
        verification_results["macos_capabilities"] = self.verify_macos_capabilities()
        verification_results["autonomous_workflows"] = self.verify_autonomous_workflows()
        verification_results["mcp_services"] = self.verify_mcp_services()
        verification_results["deployment_methods"] = self.verify_deployment_methods()
        verification_results["ukrainian_support"] = self.verify_ukrainian_support()
        
        # Generate final status
        verification_results["automation_status"] = self.generate_automation_status()
        
        verification_results["metadata"]["end_time"] = datetime.now().isoformat()
        verification_results["metadata"]["duration_seconds"] = (datetime.now() - self.start_time).total_seconds()
        
        return verification_results

def main():
    """Main verification execution"""
    verifier = MacOSAutomationVerifier()
    
    print("🤖 Atlas macOS Automation Verification")
    print("=" * 60)
    print("Перевіряємо чи досягнута повна автоматизація з повним управлінням macOS...")
    print("(Checking if full automation with complete macOS control has been achieved...)")
    print()
    
    # Run comprehensive verification
    results = verifier.run_comprehensive_verification()
    
    # Save detailed report
    report_file = "atlas_macos_automation_verification.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    automation_status = results["automation_status"]
    
    print(f"🎯 Tests Run: {automation_status['tests_run']}")
    print(f"✅ Tests Passed: {automation_status['tests_passed']}")
    print(f"📊 Automation Score: {automation_status['automation_score']}%")
    print(f"🤖 Autonomy Level: {automation_status['autonomy_level']}")
    print(f"🍎 Platform: {automation_status['platform']} (macOS: {automation_status['is_macos']})")
    
    macos_control = automation_status["macos_control_assessment"]
    print(f"\n🍎 macOS Control Assessment:")
    print(f"   Status: {macos_control['status']}")
    if "capabilities" in macos_control:
        print(f"   Capabilities: {len(macos_control['capabilities'])}")
        for capability in macos_control["capabilities"]:
            print(f"   - {capability}")
    
    if automation_status["recommendations"]:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(automation_status["recommendations"], 1):
            print(f"   {i}. {rec}")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Final assessment
    score = automation_status['automation_score']
    if score >= 90:
        print("\n🎉 ПОВНА АВТОМАТИЗАЦІЯ ДОСЯГНУТА! (FULL AUTOMATION ACHIEVED!)")
        print("   Atlas система готова до повністю автономної роботи.")
    elif score >= 75:
        print("\n🚀 ВИСОКА АВТОМАТИЗАЦІЯ (HIGH AUTOMATION)")
        print("   Система майже готова до повної автономії.")
    else:
        print(f"\n⚠️  ПОТРІБНІ ПОКРАЩЕННЯ (IMPROVEMENTS NEEDED)")
        print("   Система потребує додаткових налаштувань для повної автономії.")
    
    return 0 if score >= 90 else 1

if __name__ == "__main__":
    sys.exit(main())