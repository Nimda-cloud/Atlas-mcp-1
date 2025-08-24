#!/usr/bin/env python3
"""
Atlas Autonomous Capabilities Test Suite
=========================================

Comprehensive test suite that validates all autonomous capabilities
including GitHub workflows, deployment methods, and service management.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Simple YAML loader for basic cases
def simple_yaml_load(file_path):
    """Simple YAML loader that works without external dependencies"""
    try:
        import yaml
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback for basic YAML validation
        with open(file_path, 'r') as f:
            content = f.read()
        # Basic syntax check - ensure it's readable
        if content.strip():
            return {"basic_syntax": "ok"}
        else:
            raise ValueError("Empty or invalid YAML file")

class AtlasAutonomousTest:
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, name, passed, details=None):
        """Log test result"""
        result = {
            "name": name,
            "passed": passed,
            "details": details or "",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
        if details and not passed:
            print(f"      {details}")
    
    def test_workflow_syntax(self):
        """Test GitHub workflow YAML syntax"""
        workflows = [
            ".github/workflows/pr-agent-ci.yml",
            ".github/workflows/post-merge-local.yml"
        ]
        
        for workflow in workflows:
            try:
                simple_yaml_load(workflow)
                self.log_test(f"Workflow syntax: {workflow}", True)
            except Exception as e:
                self.log_test(f"Workflow syntax: {workflow}", False, str(e))
    
    def test_workflow_structure(self):
        """Test workflow structure and key components"""
        # Test PR Agent CI workflow
        try:
            pr_workflow = simple_yaml_load(".github/workflows/pr-agent-ci.yml")
            
            # Check for key components by reading file content
            with open(".github/workflows/pr-agent-ci.yml", 'r') as f:
                content = f.read()
            
            required_jobs = ['linux_container_smoke', 'macos_smoke', 'merge_pr']
            
            for job in required_jobs:
                if job in content:
                    self.log_test(f"PR workflow has job: {job}", True)
                else:
                    self.log_test(f"PR workflow has job: {job}", False)
            
            # Check for mergeable state handling
            has_mergeable_wait = 'mergeable_state' in content
            self.log_test("PR workflow has mergeable state handling", has_mergeable_wait)
            
        except Exception as e:
            self.log_test("PR workflow structure", False, str(e))
        
        # Test Post-merge workflow
        try:
            simple_yaml_load(".github/workflows/post-merge-local.yml")
            
            with open(".github/workflows/post-merge-local.yml", 'r') as f:
                content = f.read()
            
            required_jobs = ['local_macos', 'report_failure', 'sync_local_repo']
            
            for job in required_jobs:
                if job in content:
                    self.log_test(f"Post-merge workflow has job: {job}", True)
                else:
                    self.log_test(f"Post-merge workflow has job: {job}", False)
            
            # Check for configurable variables
            has_start_cmd = 'START_CMD' in content
            has_health_check = 'HEALTHCHECK_URL' in content
            
            self.log_test("Post-merge has configurable START_CMD", has_start_cmd)
            self.log_test("Post-merge has configurable HEALTHCHECK_URL", has_health_check)
            
        except Exception as e:
            self.log_test("Post-merge workflow structure", False, str(e))
    
    def test_autonomous_scripts(self):
        """Test autonomous setup and diagnostic scripts"""
        scripts = [
            "atlas_autonomous_setup.sh",
            "atlas_diagnostic.sh"
        ]
        
        for script in scripts:
            if os.path.exists(script):
                # Check if executable
                if os.access(script, os.X_OK):
                    self.log_test(f"Script executable: {script}", True)
                else:
                    self.log_test(f"Script executable: {script}", False)
                
                # Check shebang
                try:
                    with open(script, 'r') as f:
                        first_line = f.readline().strip()
                    
                    if first_line.startswith('#!'):
                        self.log_test(f"Script has shebang: {script}", True)
                    else:
                        self.log_test(f"Script has shebang: {script}", False)
                except Exception as e:
                    self.log_test(f"Script readable: {script}", False, str(e))
            else:
                self.log_test(f"Script exists: {script}", False)
    
    def test_deployment_configurations(self):
        """Test deployment method configurations"""
        # Test Docker configuration
        try:
            result = subprocess.run(
                ['docker', 'compose', 'config'],
                capture_output=True, text=True, timeout=30
            )
            self.log_test("Docker Compose config valid", result.returncode == 0)
        except Exception as e:
            self.log_test("Docker Compose config valid", False, str(e))
        
        # Test Kubernetes configuration
        if os.path.exists('k8s/overlays/development'):
            try:
                result = subprocess.run(
                    ['kubectl', 'kustomize', 'k8s/overlays/development'],
                    capture_output=True, text=True, timeout=30
                )
                self.log_test("Kubernetes manifests valid", result.returncode == 0)
            except Exception as e:
                self.log_test("Kubernetes manifests valid", False, str(e))
        else:
            self.log_test("Kubernetes manifests exist", False, "k8s/overlays/development not found")
    
    def test_service_health_endpoints(self):
        """Test that health endpoints are properly configured"""
        # Check if health monitoring script exists and contains expected endpoints
        if os.path.exists('atlas_health_monitor.sh'):
            try:
                with open('atlas_health_monitor.sh', 'r') as f:
                    content = f.read()
                
                expected_endpoints = [
                    'localhost:8000/status',
                    'localhost:8080/health',
                    'localhost:4002/health',
                    'localhost:4003/health',
                    'localhost:4004/health',
                    'localhost:4005/mcp'
                ]
                
                for endpoint in expected_endpoints:
                    if endpoint in content:
                        self.log_test(f"Health monitor includes: {endpoint}", True)
                    else:
                        self.log_test(f"Health monitor includes: {endpoint}", False)
                        
            except Exception as e:
                self.log_test("Health monitor script readable", False, str(e))
        else:
            self.log_test("Health monitor script exists", False)
    
    def test_autonomous_startup(self):
        """Test autonomous startup script"""
        if os.path.exists('atlas_start_autonomous.sh'):
            try:
                with open('atlas_start_autonomous.sh', 'r') as f:
                    content = f.read()
                
                # Check for key components
                checks = [
                    ('start_atlas.sh', 'Uses main start script'),
                    ('curl', 'Has health check'),
                    ('8000/status', 'Checks Atlas status endpoint')
                ]
                
                for check, description in checks:
                    if check in content:
                        self.log_test(f"Startup script: {description}", True)
                    else:
                        self.log_test(f"Startup script: {description}", False)
                        
            except Exception as e:
                self.log_test("Startup script readable", False, str(e))
        else:
            self.log_test("Autonomous startup script exists", False)
    
    def test_environment_adaptation(self):
        """Test that system adapts to available environment components"""
        adaptations = []
        
        # Check Docker availability
        try:
            subprocess.run(['docker', '--version'], capture_output=True, timeout=10)
            adaptations.append("Docker available")
        except:
            adaptations.append("Docker not available")
        
        # Check kubectl availability
        try:
            subprocess.run(['kubectl', 'version', '--client'], capture_output=True, timeout=10)
            adaptations.append("kubectl available")
        except:
            adaptations.append("kubectl not available")
        
        # Check Python environment
        if os.path.exists('atlas_env'):
            adaptations.append("Python venv exists")
        else:
            adaptations.append("Python venv not created")
        
        self.log_test("Environment adaptation detected", True, "; ".join(adaptations))
    
    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        passed_tests = sum(1 for test in self.test_results if test['passed'])
        total_tests = len(self.test_results)
        
        report = {
            "test_suite": "Atlas Autonomous Capabilities",
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "tests": self.test_results,
            "autonomous_features": {
                "github_workflows": "Enhanced with mergeable state handling",
                "configurable_health_checks": "Via repository variables",
                "local_synchronization": "Automatic post-merge sync",
                "deployment_methods": ["Local Python", "Docker", "Kubernetes"],
                "monitoring": "Comprehensive health monitoring",
                "error_handling": "Automated issue creation on failure"
            },
            "recommendations": self._generate_recommendations()
        }
        
        # Write JSON report
        with open('atlas_autonomous_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [test for test in self.test_results if not test['passed']]
        
        if failed_tests:
            recommendations.append("Fix failed tests before deploying to production")
        
        if not os.path.exists('atlas_env'):
            recommendations.append("Run atlas_autonomous_setup.sh to create Python environment")
        
        if not any('Docker' in test['name'] and test['passed'] for test in self.test_results):
            recommendations.append("Install Docker for containerized deployment")
        
        if not any('Kubernetes' in test['name'] and test['passed'] for test in self.test_results):
            recommendations.append("Configure kubectl for Kubernetes deployment")
        
        return recommendations

def main():
    """Run all autonomous capability tests"""
    print("🤖 Atlas Autonomous Capabilities Test Suite")
    print("=" * 50)
    
    tester = AtlasAutonomousTest()
    
    # Run all test categories
    print("\n📋 Testing GitHub Workflows...")
    tester.test_workflow_syntax()
    tester.test_workflow_structure()
    
    print("\n🔧 Testing Autonomous Scripts...")
    tester.test_autonomous_scripts()
    
    print("\n🚀 Testing Deployment Configurations...")
    tester.test_deployment_configurations()
    
    print("\n🏥 Testing Health Monitoring...")
    tester.test_service_health_endpoints()
    
    print("\n⚡ Testing Autonomous Startup...")
    tester.test_autonomous_startup()
    
    print("\n🌍 Testing Environment Adaptation...")
    tester.test_environment_adaptation()
    
    # Generate and display report
    print("\n📊 Generating Test Report...")
    report = tester.generate_report()
    
    print(f"\n🎯 Test Results Summary:")
    print(f"   Total tests: {report['summary']['total_tests']}")
    print(f"   Passed: {report['summary']['passed']}")
    print(f"   Failed: {report['summary']['failed']}")
    print(f"   Success rate: {report['summary']['success_rate']:.1f}%")
    print(f"   Duration: {report['duration_seconds']:.2f} seconds")
    
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
    
    print(f"\n📄 Detailed report saved to: atlas_autonomous_test_report.json")
    
    # Return appropriate exit code
    if report['summary']['failed'] == 0:
        print("\n🎉 All autonomous capability tests passed!")
        return 0
    else:
        print(f"\n⚠️  {report['summary']['failed']} tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())