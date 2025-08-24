#!/usr/bin/env python3
"""
Kubernetes Deployment Verification for Atlas MCP
================================================

Comprehensive test to identify and fix the specific Kubernetes deployment issues
mentioned in the problem statement:
1. Label Selector Immutable Error
2. Ingress conflict: host "atlas.local" and path "/" already defined
3. Image pull issues with kind cluster

This addresses the goal of achieving 96%+ automation level in Kubernetes deployment.
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class KubernetesDeploymentValidator:
    """Validates and fixes Kubernetes deployment issues for Atlas MCP"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.k8s_dir = self.script_dir / "k8s"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {},
            "fixes_applied": [],
            "recommendations": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def validate_kustomize_configs(self) -> Dict[str, Any]:
        """Validate kustomize configurations for development environment"""
        self.log("🔍 Validating Kubernetes configurations...")
        
        results = {}
        dev_overlay = self.k8s_dir / "overlays" / "development"
        
        # Test kustomize build
        try:
            cmd = ["kubectl", "kustomize", str(dev_overlay)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            results["kustomize_build"] = {
                "status": "success",
                "yaml_size": len(result.stdout),
                "resource_count": result.stdout.count("---")
            }
            self.log("✅ Kustomize configuration builds successfully")
            
            # Check for potential label selector issues
            yaml_content = result.stdout
            results["selector_analysis"] = self._analyze_selectors(yaml_content)
            
            # Check for ingress conflicts
            results["ingress_analysis"] = self._analyze_ingress_conflicts(yaml_content)
            
        except subprocess.CalledProcessError as e:
            results["kustomize_build"] = {
                "status": "failed",
                "error": e.stderr
            }
            self.log(f"❌ Kustomize build failed: {e.stderr}", "ERROR")
            
        return results
        
    def _analyze_selectors(self, yaml_content: str) -> Dict[str, Any]:
        """Analyze deployment selectors for potential immutable field issues"""
        self.log("🔍 Analyzing label selectors...")
        
        analysis = {
            "deployments_found": 0,
            "selector_consistency": True,
            "potential_issues": []
        }
        
        try:
            documents = yaml.safe_load_all(yaml_content)
            deployments = []
            
            for doc in documents:
                if doc and doc.get("kind") == "Deployment":
                    deployments.append(doc)
                    analysis["deployments_found"] += 1
                    
                    # Check selector consistency
                    selector_labels = doc.get("spec", {}).get("selector", {}).get("matchLabels", {})
                    template_labels = doc.get("spec", {}).get("template", {}).get("metadata", {}).get("labels", {})
                    
                    for key, value in selector_labels.items():
                        if template_labels.get(key) != value:
                            analysis["selector_consistency"] = False
                            analysis["potential_issues"].append(f"Selector mismatch in {doc.get('metadata', {}).get('name', 'unknown')}: {key}")
                            
        except Exception as e:
            analysis["potential_issues"].append(f"YAML parsing error: {str(e)}")
            
        if analysis["selector_consistency"]:
            self.log("✅ All deployment selectors are consistent")
        else:
            self.log("⚠️  Found selector consistency issues", "WARNING")
            
        return analysis
        
    def _analyze_ingress_conflicts(self, yaml_content: str) -> Dict[str, Any]:
        """Analyze ingress configurations for conflicts"""
        self.log("🔍 Analyzing ingress configurations...")
        
        analysis = {
            "ingresses_found": 0,
            "host_path_combinations": [],
            "conflicts": []
        }
        
        try:
            documents = yaml.safe_load_all(yaml_content)
            
            for doc in documents:
                if doc and doc.get("kind") == "Ingress":
                    analysis["ingresses_found"] += 1
                    
                    rules = doc.get("spec", {}).get("rules", [])
                    for rule in rules:
                        host = rule.get("host", "")
                        paths = rule.get("http", {}).get("paths", [])
                        
                        for path_config in paths:
                            path = path_config.get("path", "/")
                            combination = f"{host}:{path}"
                            
                            if combination in analysis["host_path_combinations"]:
                                analysis["conflicts"].append(combination)
                            else:
                                analysis["host_path_combinations"].append(combination)
                                
        except Exception as e:
            analysis["conflicts"].append(f"YAML parsing error: {str(e)}")
            
        if not analysis["conflicts"]:
            self.log("✅ No ingress conflicts detected")
        else:
            self.log(f"⚠️  Found {len(analysis['conflicts'])} ingress conflicts", "WARNING")
            
        return analysis
        
    def check_image_pull_policies(self) -> Dict[str, Any]:
        """Check image pull policies for kind cluster compatibility"""
        self.log("🔍 Checking image pull policies...")
        
        results = {
            "never_policies": [],
            "latest_tags": [],
            "recommendations": []
        }
        
        # Check base deployments
        deployment_files = [
            "atlas-core-deployment.yaml",
            "atlas-frontend-deployment.yaml", 
            "mcp-services-deployments.yaml",
            "data-services-deployments.yaml"
        ]
        
        for file_name in deployment_files:
            file_path = self.k8s_dir / "base" / file_name
            if file_path.exists():
                with open(file_path, 'r') as f:
                    try:
                        docs = yaml.safe_load_all(f)
                        for doc in docs:
                            if doc and doc.get("kind") == "Deployment":
                                containers = doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
                                for container in containers:
                                    image = container.get("image", "")
                                    pull_policy = container.get("imagePullPolicy", "")
                                    
                                    if pull_policy == "Never":
                                        results["never_policies"].append({
                                            "deployment": doc.get("metadata", {}).get("name"),
                                            "container": container.get("name"),
                                            "image": image
                                        })
                                        
                                    if image.endswith(":latest"):
                                        results["latest_tags"].append({
                                            "deployment": doc.get("metadata", {}).get("name"),
                                            "image": image
                                        })
                                        
                    except Exception as e:
                        self.log(f"Error reading {file_name}: {e}", "WARNING")
                        
        # Generate recommendations
        if results["never_policies"]:
            results["recommendations"].append(
                "For kind clusters, ensure images are loaded with: kind load docker-image <image-name>"
            )
            
        if results["latest_tags"]:
            results["recommendations"].append(
                "Consider using specific version tags instead of 'latest' for production stability"
            )
            
        self.log(f"Found {len(results['never_policies'])} deployments with imagePullPolicy: Never")
        return results
        
    def validate_docker_images_exist(self) -> Dict[str, Any]:
        """Check if required Docker images exist locally"""
        self.log("🔍 Checking Docker images availability...")
        
        required_images = [
            "atlas-mcp/atlas-core:latest",
            "atlas-mcp/atlas-frontend:latest", 
            "atlas-mcp/mcp-automation:latest",
            "atlas-mcp/mcp-automator:latest",
            "atlas-mcp/mcp-tts:latest"
        ]
        
        results = {
            "available_images": [],
            "missing_images": [],
            "build_commands": []
        }
        
        for image in required_images:
            try:
                result = subprocess.run(
                    ["docker", "image", "inspect", image],
                    capture_output=True,
                    check=True
                )
                results["available_images"].append(image)
                self.log(f"✅ Image available: {image}")
                
            except subprocess.CalledProcessError:
                results["missing_images"].append(image)
                self.log(f"❌ Image missing: {image}", "WARNING")
                
                # Generate build command
                if "atlas-core" in image:
                    results["build_commands"].append("docker build -t atlas-mcp/atlas-core:latest .")
                elif "atlas-frontend" in image:
                    results["build_commands"].append("docker build -t atlas-mcp/atlas-frontend:latest 3d_helmet_viewer/")
                elif "mcp-automation" in image:
                    results["build_commands"].append("docker build -t atlas-mcp/mcp-automation:latest -f Dockerfile.mcp-automation .")
                elif "mcp-automator" in image:
                    results["build_commands"].append("docker build -t atlas-mcp/mcp-automator:latest -f Dockerfile.mcp-automator .")
                elif "mcp-tts" in image:
                    results["build_commands"].append("docker build -t atlas-mcp/mcp-tts:latest services/tts_mcp_adapter/")
                    
        return results
        
    def test_kind_cluster_readiness(self) -> Dict[str, Any]:
        """Test kind cluster configuration and readiness"""
        self.log("🔍 Testing kind cluster configuration...")
        
        results = {
            "kind_available": False,
            "config_valid": False,
            "cluster_exists": False,
            "recommendations": []
        }
        
        # Check if kind is available
        try:
            subprocess.run(["kind", "version"], capture_output=True, check=True)
            results["kind_available"] = True
            self.log("✅ kind CLI is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            results["kind_available"] = False
            self.log("❌ kind CLI not available", "WARNING")
            results["recommendations"].append("Install kind: https://kind.sigs.k8s.io/docs/user/quick-start/")
            
        # Check kind config
        kind_config = self.script_dir / "kind-config.yaml"
        if kind_config.exists():
            results["config_valid"] = True
            self.log("✅ kind configuration file exists")
        else:
            results["config_valid"] = False
            self.log("❌ kind configuration file missing", "WARNING")
            
        # Check for existing cluster
        if results["kind_available"]:
            try:
                result = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True, check=True)
                clusters = result.stdout.strip().split('\n') if result.stdout.strip() else []
                results["cluster_exists"] = "atlas-mcp" in clusters
                if results["cluster_exists"]:
                    self.log("✅ Atlas MCP kind cluster exists")
                else:
                    self.log("⚠️  Atlas MCP kind cluster not found", "WARNING")
            except subprocess.CalledProcessError:
                results["cluster_exists"] = False
                
        return results
        
    def generate_fixes_and_recommendations(self) -> List[str]:
        """Generate specific fixes and recommendations based on validation results"""
        self.log("💡 Generating fixes and recommendations...")
        
        fixes = []
        
        # Label selector fixes
        if not self.results["validation_results"]["selector_analysis"]["selector_consistency"]:
            fixes.append({
                "issue": "Label selector inconsistency",
                "fix": "Ensure deployment selector.matchLabels match template.metadata.labels exactly",
                "command": "Review k8s/base/*-deployment.yaml files for label consistency"
            })
            
        # Ingress conflict fixes
        ingress_conflicts = self.results["validation_results"]["ingress_analysis"]["conflicts"]
        if ingress_conflicts:
            fixes.append({
                "issue": f"Ingress conflicts: {', '.join(ingress_conflicts)}",
                "fix": "Use different hosts or paths, or consolidate into single ingress",
                "command": "kubectl delete ingress atlas-ingress -n atlas-mcp-dev --ignore-not-found=true"
            })
            
        # Image availability fixes
        missing_images = self.results["validation_results"]["docker_images"]["missing_images"]
        if missing_images:
            fixes.append({
                "issue": f"Missing Docker images: {len(missing_images)} images",
                "fix": "Build missing Docker images",
                "commands": self.results["validation_results"]["docker_images"]["build_commands"]
            })
            
        # Kind cluster fixes
        if not self.results["validation_results"]["kind_cluster"]["cluster_exists"]:
            fixes.append({
                "issue": "Kind cluster not available",
                "fix": "Create kind cluster with proper configuration",
                "command": "kind create cluster --name atlas-mcp --config kind-config.yaml"
            })
            
        return fixes
        
    def calculate_automation_score(self) -> float:
        """Calculate automation readiness score for Kubernetes deployment"""
        score = 100.0
        
        # Deduct points for issues
        validation = self.results["validation_results"]
        
        # Configuration issues (-10 points each)
        if validation.get("kustomize_build", {}).get("status") != "success":
            score -= 10
            
        if not validation.get("selector_analysis", {}).get("selector_consistency", True):
            score -= 10
            
        if validation.get("ingress_analysis", {}).get("conflicts"):
            score -= 10
            
        # Image availability issues (-5 points per missing image)
        missing_images = len(validation.get("docker_images", {}).get("missing_images", []))
        score -= missing_images * 5
        
        # Infrastructure readiness (-15 points if kind not ready)
        if not validation.get("kind_cluster", {}).get("kind_available", False):
            score -= 15
            
        return max(score, 0.0)
        
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete Kubernetes deployment validation"""
        self.log("🚀 Starting comprehensive Kubernetes deployment validation...")
        
        # Run all validations
        self.results["validation_results"]["kustomize_configs"] = self.validate_kustomize_configs()
        self.results["validation_results"]["selector_analysis"] = self.results["validation_results"]["kustomize_configs"].get("selector_analysis", {})
        self.results["validation_results"]["ingress_analysis"] = self.results["validation_results"]["kustomize_configs"].get("ingress_analysis", {})
        self.results["validation_results"]["image_policies"] = self.check_image_pull_policies()
        self.results["validation_results"]["docker_images"] = self.validate_docker_images_exist()
        self.results["validation_results"]["kind_cluster"] = self.test_kind_cluster_readiness()
        
        # Generate fixes
        self.results["fixes_applied"] = self.generate_fixes_and_recommendations()
        
        # Calculate automation score
        automation_score = self.calculate_automation_score()
        self.results["automation_score"] = automation_score
        
        # Determine readiness level
        if automation_score >= 95:
            readiness = "production_ready"
        elif automation_score >= 90:
            readiness = "staging_ready"
        elif automation_score >= 80:
            readiness = "development_ready"
        else:
            readiness = "needs_fixes"
            
        self.results["readiness_level"] = readiness
        
        return self.results
        
    def save_report(self):
        """Save validation report to file"""
        report_file = self.script_dir / "kubernetes_deployment_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        self.log(f"📄 Report saved to: {report_file}")
        

def main():
    """Main validation execution"""
    print("🚀 Atlas MCP Kubernetes Deployment Validation")
    print("=" * 60)
    
    validator = KubernetesDeploymentValidator()
    results = validator.run_comprehensive_validation()
    
    # Print summary
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"🎯 Automation Score: {results['automation_score']:.1f}/100")
    print(f"🚀 Readiness Level: {results['readiness_level']}")
    
    # Print issues found
    issues_found = len(results.get("fixes_applied", []))
    if issues_found == 0:
        print("🎉 No issues found! Kubernetes deployment is ready.")
    else:
        print(f"⚠️  Found {issues_found} issues that need attention:")
        for i, fix in enumerate(results.get("fixes_applied", []), 1):
            print(f"  {i}. {fix['issue']}")
            print(f"     Fix: {fix['fix']}")
            if 'command' in fix:
                print(f"     Command: {fix['command']}")
            if 'commands' in fix:
                for cmd in fix['commands']:
                    print(f"     Command: {cmd}")
            print()
    
    # Save report
    validator.save_report()
    
    # Return appropriate exit code
    return 0 if results['automation_score'] >= 90 else 1


if __name__ == "__main__":
    sys.exit(main())