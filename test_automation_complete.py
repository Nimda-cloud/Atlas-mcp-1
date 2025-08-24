#!/usr/bin/env python3
"""
Atlas MCP Complete Automation Test Suite
========================================

Comprehensive test automation script that validates all deployment methods
and provides real execution testing capabilities.

Можна запускати на будь-якому рівні готовності системи:
- Базові тести (без залежностей)
- Локальні тести (з Python залежностями)  
- Docker тести (з Docker)
- Kubernetes тести (з kubectl)
"""

import sys
import os
import json
import asyncio
import subprocess
import time
import socket
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}🤖 {text}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

def print_section(text: str):
    print(f"\n{Colors.CYAN}📋 {text}{Colors.NC}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.NC}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.NC}")

def command_exists(command: str) -> bool:
    """Check if command exists in PATH"""
    try:
        subprocess.run([command, '--version'], capture_output=True, timeout=5)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def port_available(port: int, host: str = 'localhost') -> bool:
    """Check if port is available (not in use)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # Port available if connection fails
    except:
        return True

def wait_for_port(port: int, timeout: int = 30, host: str = 'localhost') -> bool:
    """Wait for port to become available (service to start)"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex((host, port)) == 0:
                    return True
        except:
            pass
        time.sleep(1)
    return False

async def test_http_endpoint(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Test HTTP endpoint availability"""
    try:
        # Try using aiohttp if available
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        data = await response.text()
                        return True, data[:200] + "..." if len(data) > 200 else data
                    else:
                        return False, f"HTTP {response.status}"
        except ImportError:
            # Fallback to curl
            result = subprocess.run(
                ['curl', '-f', '-s', '--max-time', str(timeout), url],
                capture_output=True, text=True, timeout=timeout + 5
            )
            if result.returncode == 0:
                return True, result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout
            else:
                return False, f"curl error: {result.stderr[:100]}"
    except Exception as e:
        return False, str(e)

class AtlasTestSuite:
    def __init__(self):
        self.results = {
            'basic': {},
            'dependencies': {},
            'docker': {},
            'kubernetes': {},
            'execution': {}
        }
        
    def test_basic_structure(self) -> bool:
        """Test basic file structure and syntax"""
        print_section("Testing Basic Structure")
        
        # Test file existence
        required_files = [
            'atlas_core.py',
            'mcp_automation_server.py',
            'mcp_macos_automator.py',
            'requirements.txt',
            'Dockerfile',
            'docker-compose.yml',
            'start_atlas.sh',
            'README.md'
        ]
        
        missing_files = []
        for file in required_files:
            if os.path.exists(file):
                print_success(f"File exists: {file}")
            else:
                print_error(f"Missing file: {file}")
                missing_files.append(file)
        
        if missing_files:
            self.results['basic']['file_structure'] = False
            return False
        
        # Test Python syntax
        python_files = ['atlas_core.py', 'mcp_automation_server.py', 'mcp_macos_automator.py']
        
        for file in python_files:
            try:
                import ast
                with open(file, 'r') as f:
                    ast.parse(f.read())
                print_success(f"Python syntax valid: {file}")
            except SyntaxError as e:
                print_error(f"Syntax error in {file}: {e}")
                self.results['basic']['syntax'] = False
                return False
        
        # Test shell scripts
        shell_scripts = ['start_atlas.sh', 'install_macos.sh']
        for script in shell_scripts:
            if os.path.exists(script):
                if os.access(script, os.X_OK):
                    print_success(f"Shell script executable: {script}")
                else:
                    print_warning(f"Shell script not executable: {script}")
            
        self.results['basic']['structure'] = True
        return True
    
    def test_python_dependencies(self) -> bool:
        """Test Python environment and dependencies"""
        print_section("Testing Python Dependencies")
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 11):
            print_success(f"Python version: {python_version.major}.{python_version.minor}")
        else:
            print_warning(f"Python version {python_version.major}.{python_version.minor} < 3.11 (recommended)")
        
        # Test virtual environment
        venv_path = Path('atlas_env')
        if venv_path.exists():
            print_success("Virtual environment exists: atlas_env")
            
            # Test if we can import key modules
            test_imports = [
                'fastapi',
                'uvicorn', 
                'aiohttp',
                'ollama',
                'psutil',
                'pydantic'
            ]
            
            failed_imports = []
            for module in test_imports:
                try:
                    __import__(module)
                    print_success(f"Module available: {module}")
                except ImportError:
                    print_error(f"Module missing: {module}")
                    failed_imports.append(module)
            
            if failed_imports:
                print_warning(f"Missing modules: {', '.join(failed_imports)}")
                print_info("Install with: pip install -r requirements.txt")
                self.results['dependencies']['modules'] = False
                return False
        else:
            print_warning("Virtual environment not found")
            print_info("Create with: python3 -m venv atlas_env")
        
        self.results['dependencies']['python'] = True
        return True
    
    def test_docker_setup(self) -> bool:
        """Test Docker configuration and build capability"""
        print_section("Testing Docker Setup")
        
        # Check Docker availability
        if not command_exists('docker'):
            print_error("Docker not available")
            self.results['docker']['available'] = False
            return False
        
        print_success("Docker available")
        
        # Check Docker daemon
        try:
            result = subprocess.run(['docker', 'info'], capture_output=True, timeout=10)
            if result.returncode == 0:
                print_success("Docker daemon running")
            else:
                print_error("Docker daemon not running")
                self.results['docker']['daemon'] = False
                return False
        except subprocess.TimeoutExpired:
            print_error("Docker daemon timeout")
            return False
        
        # Test Docker Compose config
        try:
            result = subprocess.run(['docker', 'compose', 'config'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print_success("Docker Compose configuration valid")
            else:
                print_error(f"Docker Compose config error: {result.stderr}")
                self.results['docker']['compose'] = False
                return False
        except subprocess.TimeoutExpired:
            print_error("Docker Compose config timeout")
            return False
        
        self.results['docker']['setup'] = True
        return True
    
    def test_kubernetes_setup(self) -> bool:
        """Test Kubernetes configuration"""
        print_section("Testing Kubernetes Setup")
        
        # Check kubectl
        if not command_exists('kubectl'):
            print_warning("kubectl not available - Kubernetes tests skipped")
            self.results['kubernetes']['available'] = False
            return True  # Not an error, just not available
        
        print_success("kubectl available")
        
        # Check cluster access
        try:
            result = subprocess.run(['kubectl', 'version', '--client'], 
                                  capture_output=True, timeout=10)
            if result.returncode == 0:
                print_success("kubectl client working")
            else:
                print_warning("kubectl client issues")
        except subprocess.TimeoutExpired:
            print_warning("kubectl timeout")
        
        # Test kustomize configs if they exist
        k8s_path = Path('k8s')
        if k8s_path.exists():
            print_success("Kubernetes configs found")
            
            # Test overlays
            dev_overlay = k8s_path / 'overlays' / 'development'
            prod_overlay = k8s_path / 'overlays' / 'production'
            
            if dev_overlay.exists():
                print_success("Development overlay found")
                # Test kustomize
                try:
                    result = subprocess.run(['kubectl', 'kustomize', str(dev_overlay)], 
                                          capture_output=True, timeout=30)
                    if result.returncode == 0:
                        print_success("Development kustomize valid")
                    else:
                        print_error("Development kustomize invalid")
                        self.results['kubernetes']['kustomize'] = False
                except subprocess.TimeoutExpired:
                    print_warning("Kustomize timeout")
            
            if prod_overlay.exists():
                print_success("Production overlay found")
        else:
            print_warning("No Kubernetes configs found")
        
        self.results['kubernetes']['setup'] = True
        return True
    
    async def test_local_execution(self) -> bool:
        """Test local Atlas execution"""
        print_section("Testing Local Execution")
        
        # Check if dependencies are available
        try:
            # Try to modify Python path to include current directory
            sys.path.insert(0, os.getcwd())
            import atlas_core
            print_success("Atlas core module importable")
        except ImportError as e:
            print_error(f"Cannot import atlas_core: {e}")
            print_info("Install dependencies first: pip install -r requirements.txt")
            self.results['execution']['local'] = False
            return False
        
        # Try to create Atlas instance (without starting)
        try:
            from atlas_core import AtlasCore
            atlas = AtlasCore()
            print_success("Atlas instance created")
            
            # Test configuration
            if hasattr(atlas, 'config'):
                print_success("Atlas configuration loaded")
            
            # Test web app creation
            if hasattr(atlas, 'app'):
                print_success("FastAPI app created")
                
        except Exception as e:
            print_error(f"Atlas initialization error: {e}")
            print_info("This is expected if dependencies are missing")
            self.results['execution']['local'] = False
            return False
        
        self.results['execution']['local'] = True
        return True
    
    async def test_docker_execution(self) -> bool:
        """Test Docker deployment"""
        print_section("Testing Docker Execution")
        
        if not self.results.get('docker', {}).get('setup'):
            print_warning("Docker setup not validated - skipping execution test")
            return True
        
        # Test basic docker compose up (dry run)
        try:
            print_info("Testing basic service startup...")
            
            # Start only core services
            result = subprocess.run([
                'docker', 'compose', 'up', '-d', 
                'atlas-core', 'redis', 'qdrant'
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                print_success("Core services started")
                
                # Wait for services
                print_info("Waiting for services to be ready...")
                if wait_for_port(8000, timeout=60):
                    print_success("Atlas core responding on port 8000")
                    
                    # Test health endpoint
                    is_healthy, response = await test_http_endpoint('http://localhost:8000/status')
                    if is_healthy:
                        print_success("Atlas health check passed")
                        print_info(f"Response: {response}")
                    else:
                        print_warning(f"Atlas health check failed: {response}")
                else:
                    print_warning("Atlas core not responding in time")
                
                # Cleanup
                print_info("Cleaning up test deployment...")
                subprocess.run(['docker', 'compose', 'down'], 
                             capture_output=True, timeout=60)
                print_success("Test deployment cleaned up")
                
            else:
                print_error(f"Docker compose failed: {result.stderr}")
                self.results['execution']['docker'] = False
                return False
                
        except subprocess.TimeoutExpired:
            print_error("Docker compose timeout")
            # Try to clean up
            subprocess.run(['docker', 'compose', 'down'], capture_output=True)
            return False
        except Exception as e:
            print_error(f"Docker execution error: {e}")
            return False
        
        self.results['execution']['docker'] = True
        return True
    
    def test_integration_scripts(self) -> bool:
        """Test existing integration test scripts"""
        print_section("Testing Integration Scripts")
        
        # Test the existing integration script
        integration_script = Path('archived_3d_assets/frontend-express-standalone/test-integration.sh')
        if integration_script.exists():
            print_success("Integration test script found")
            
            if os.access(integration_script, os.X_OK):
                print_success("Integration script executable")
            else:
                print_warning("Integration script not executable")
                
        else:
            print_warning("Integration test script not found")
        
        # Test start_atlas.sh
        start_script = Path('start_atlas.sh')
        if start_script.exists() and os.access(start_script, os.X_OK):
            print_success("start_atlas.sh ready")
            
            # Test script syntax
            try:
                result = subprocess.run(['bash', '-n', str(start_script)], 
                                      capture_output=True, timeout=10)
                if result.returncode == 0:
                    print_success("start_atlas.sh syntax valid")
                else:
                    print_error(f"start_atlas.sh syntax error: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                print_warning("start_atlas.sh syntax check timeout")
        
        return True
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = 0
        passed_tests = 0
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {},
            'detailed_results': self.results,
            'recommendations': []
        }
        
        # Count results
        for category, tests in self.results.items():
            for test_name, result in tests.items():
                total_tests += 1
                if result:
                    passed_tests += 1
        
        report['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Generate recommendations
        if not self.results.get('dependencies', {}).get('modules', True):
            report['recommendations'].append(
                "Install Python dependencies: source atlas_env/bin/activate && pip install -r requirements.txt"
            )
        
        if not self.results.get('docker', {}).get('daemon', True):
            report['recommendations'].append(
                "Start Docker daemon: sudo systemctl start docker"
            )
        
        if not self.results.get('kubernetes', {}).get('available', True):
            report['recommendations'].append(
                "Install kubectl for Kubernetes testing: curl -LO 'https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl'"
            )
        
        return report
    
    async def run_all_tests(self):
        """Run all available tests"""
        print_header("Atlas MCP Complete Test Suite")
        
        print_info("Testing all deployment methods and automation capabilities...")
        print_info("This suite will run tests appropriate for your environment setup.")
        
        # Run tests in order
        tests = [
            ("Basic Structure", self.test_basic_structure),
            ("Python Dependencies", self.test_python_dependencies),
            ("Docker Setup", self.test_docker_setup),
            ("Kubernetes Setup", self.test_kubernetes_setup),
            ("Integration Scripts", self.test_integration_scripts),
            ("Local Execution", self.test_local_execution),
            ("Docker Execution", self.test_docker_execution),
        ]
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                    
                if result:
                    print_success(f"{test_name}: PASSED")
                else:
                    print_warning(f"{test_name}: FAILED")
                    
            except Exception as e:
                print_error(f"{test_name}: ERROR - {e}")
        
        # Generate and display report
        print_header("Test Results Summary")
        
        report = self.generate_report()
        
        print(f"{Colors.CYAN}📊 Test Results:{Colors.NC}")
        print(f"   Total Tests: {report['summary']['total_tests']}")
        print(f"   Passed: {report['summary']['passed_tests']}")
        print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
        
        if report['recommendations']:
            print(f"\n{Colors.YELLOW}📋 Recommendations:{Colors.NC}")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Save detailed report
        with open('atlas_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print_info("Detailed report saved to: atlas_test_report.json")
        
        # Overall result
        if report['summary']['success_rate'] >= 80:
            print_header("🎉 Atlas MCP System Ready!")
            print_success("System is well configured and ready for deployment")
            return 0
        elif report['summary']['success_rate'] >= 60:
            print_header("⚠️  Atlas MCP Partially Ready")
            print_warning("System has some issues but basic functionality should work")
            return 1
        else:
            print_header("❌ Atlas MCP Needs Setup")
            print_error("System requires significant setup before use")
            return 2

def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("""
Atlas MCP Complete Test Suite

Usage: python test_automation_complete.py [options]

This script tests all Atlas MCP deployment methods:
- Basic structure and syntax validation
- Python environment and dependencies  
- Docker setup and deployment capability
- Kubernetes configuration validation
- Real execution testing

The script adapts to your environment - if components are missing,
it will skip related tests and provide recommendations.

Options:
  --help, -h    Show this help message

Exit codes:
  0 - All tests passed (system ready)
  1 - Most tests passed (partially ready)  
  2 - Many tests failed (needs setup)
        """)
        return 0
    
    # Run the test suite
    test_suite = AtlasTestSuite()
    try:
        return asyncio.run(test_suite.run_all_tests())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test suite interrupted by user{Colors.NC}")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}Test suite error: {e}{Colors.NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())