#!/usr/bin/env python3
"""
Atlas MCP Root Directory Cleanup and Refactoring Script
=======================================================

This script performs a comprehensive cleanup and refactoring of the Atlas MCP
root directory, removing temporary files, organizing documentation, and 
optimizing the project structure for production use.
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Dict

class AtlasCleanup:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.cleanup_report = {
            "removed_files": [],
            "moved_files": [],
            "organized_directories": [],
            "preserved_files": [],
            "recommendations": []
        }
    
    def identify_temp_files(self) -> List[Path]:
        """Identify temporary and test report files to remove"""
        temp_patterns = [
            "*_test_report.json",
            "*_automation_*_report.json", 
            "*_validation_report.json",
            "*_assessment.json",
            "*_status.json",
            "test_*.md",
            "*.tmp",
            "__pycache__",
            "*.pyc",
            ".DS_Store",
            "*.log"
        ]
        
        temp_files = []
        for pattern in temp_patterns:
            temp_files.extend(self.root_dir.glob(pattern))
            temp_files.extend(self.root_dir.glob(f"**/{pattern}"))
        
        return temp_files
    
    def identify_duplicate_docs(self) -> List[Path]:
        """Identify duplicate documentation files"""
        # Look for multiple similar markdown files
        docs = list(self.root_dir.glob("*.md"))
        
        # Group by similar names
        doc_groups = {}
        for doc in docs:
            base_name = doc.stem.lower()
            # Group similar names together
            if "kubernetes" in base_name:
                doc_groups.setdefault("kubernetes", []).append(doc)
            elif "deploy" in base_name or "setup" in base_name:
                doc_groups.setdefault("deployment", []).append(doc)
            elif "autonomous" in base_name or "automation" in base_name:
                doc_groups.setdefault("automation", []).append(doc)
            elif "macos" in base_name:
                doc_groups.setdefault("macos", []).append(doc)
        
        # Keep only the most recent or comprehensive ones
        duplicates = []
        for group, files in doc_groups.items():
            if len(files) > 2:  # More than 2 similar docs
                # Sort by file size (keep larger ones) and modification time
                files.sort(key=lambda f: (f.stat().st_size, f.stat().st_mtime), reverse=True)
                duplicates.extend(files[2:])  # Remove all but top 2
        
        return duplicates
    
    def create_organized_structure(self):
        """Create organized directory structure"""
        directories = {
            "docs": "Consolidated documentation",
            "tests": "All test scripts and reports", 
            "scripts": "Utility and setup scripts",
            "configs": "Configuration files"
        }
        
        for dir_name, description in directories.items():
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                self.cleanup_report["organized_directories"].append(f"Created {dir_name}/ - {description}")
    
    def move_files_to_organized_structure(self):
        """Move files to appropriate directories"""
        moves = [
            # Move test files
            ("test_*.py", "tests/"),
            ("*_test.py", "tests/"),
            ("*test*.py", "tests/"),
            
            # Move scripts (but keep core start scripts in root)
            ("atlas_autonomous_*.sh", "scripts/"),
            ("atlas_diagnostic.sh", "scripts/"),
            ("atlas_health_*.sh", "scripts/"),
            ("build_*.sh", "scripts/"),
            ("setup-*.sh", "scripts/"),
            ("k8s-*.sh", "scripts/"),
            
            # Move config files
            ("*.yaml", "configs/"),
            (".env.*", "configs/"),
            ("kind-config*.yaml", "configs/"),
        ]
        
        for pattern, target_dir in moves:
            target_path = self.root_dir / target_dir
            target_path.mkdir(parents=True, exist_ok=True)
            
            files = list(self.root_dir.glob(pattern))
            for file in files:
                if file.is_file() and file.parent == self.root_dir:
                    # Skip essential files that should stay in root
                    if file.name in ['start_atlas.sh', 'install_macos.sh', 'restart_atlas.sh']:
                        continue
                    
                    target_file = target_path / file.name
                    if not target_file.exists():
                        shutil.move(str(file), str(target_file))
                        self.cleanup_report["moved_files"].append(f"{file.name} -> {target_dir}")
    
    def preserve_essential_files(self) -> List[str]:
        """List essential files that should be preserved in root"""
        essential = [
            "atlas_core.py",
            "mcp_automation_server.py", 
            "mcp_macos_automator.py",
            "requirements.txt",
            "docker-compose.yml",
            "Dockerfile*",
            "Makefile",
            "README.md",
            "start_atlas.sh",
            "install_macos.sh", 
            "restart_atlas.sh",
            "docker-entrypoint.sh",
            ".gitignore",
            ".github/",
            "k8s/",
            "services/",
            "monitoring/",
            "3d_helmet_viewer/",
            "archived_3d_assets/"
        ]
        return essential
    
    def generate_summary_readme(self):
        """Generate an updated README with clean structure"""
        readme_content = """# Atlas MCP - Autonomous Multi-Agent System

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue)]()
[![macOS](https://img.shields.io/badge/macOS-automated-orange)]()

Autonomous multi-agent AI system with comprehensive macOS automation, browser control, and Kubernetes deployment.

## 🚀 Quick Start

```bash
# Local development
./start_atlas.sh --local

# Docker deployment  
docker compose up -d

# Kubernetes deployment
make deploy-full
```

## 📁 Project Structure

```
atlas-mcp/
├── atlas_core.py              # Main AI agent system
├── mcp_automation_server.py   # Automation MCP server
├── mcp_macos_automator.py     # macOS automation engine
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Container orchestration
├── Makefile                   # Kubernetes deployment
├── start_atlas.sh            # Main startup script
├── k8s/                      # Kubernetes manifests
├── services/                 # MCP service implementations
├── docs/                     # Documentation
├── tests/                    # Test scripts
├── scripts/                  # Utility scripts
└── configs/                  # Configuration files
```

## 🎯 Features

- **Multi-Agent AI**: LLM1 (Interface), LLM2 (Orchestrator), LLM3 (Monitor)
- **MCP Hub**: Modular automation services (Playwright, macOS, TTS)
- **Kubernetes Ready**: Full production deployment
- **macOS Automation**: Complete system control via AppleScript/Shortcuts
- **Browser Automation**: 28 Playwright tools for web interaction
- **Ukrainian Support**: Native Ukrainian language interface

## 📖 Documentation

- [Kubernetes Deployment Guide](docs/)
- [macOS Automation Features](docs/)
- [API Documentation](http://localhost:8000/docs)

## 🔧 Development

See individual service README files in `services/` directory for development setup.

## 📄 License

Open source - See individual files for specific licensing.
"""
        
        readme_path = self.root_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.cleanup_report["moved_files"].append("Updated README.md with clean structure")
    
    def run_cleanup(self):
        """Execute the complete cleanup process"""
        print("🧹 Starting Atlas MCP root directory cleanup...")
        
        # 1. Identify and remove temporary files
        temp_files = self.identify_temp_files()
        print(f"📋 Found {len(temp_files)} temporary files to clean")
        
        for file in temp_files:
            if file.exists():
                if file.is_dir():
                    shutil.rmtree(file)
                else:
                    file.unlink()
                self.cleanup_report["removed_files"].append(str(file.name))
        
        # 2. Remove duplicate documentation  
        duplicate_docs = self.identify_duplicate_docs()
        print(f"📄 Found {len(duplicate_docs)} duplicate documentation files")
        
        for doc in duplicate_docs:
            if doc.exists():
                doc.unlink()
                self.cleanup_report["removed_files"].append(str(doc.name))
        
        # 3. Create organized structure
        print("📁 Creating organized directory structure...")
        self.create_organized_structure()
        
        # 4. Move files to organized locations
        print("📦 Moving files to organized locations...")
        self.move_files_to_organized_structure()
        
        # 5. Generate updated README
        print("📖 Updating README.md...")
        self.generate_summary_readme()
        
        # 6. Generate cleanup report
        report_path = self.root_dir / "cleanup_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.cleanup_report, f, indent=2)
        
        print(f"✅ Cleanup complete! Report saved to {report_path}")
        self.print_summary()
    
    def print_summary(self):
        """Print cleanup summary"""
        print("\n" + "="*50)
        print("🧹 CLEANUP SUMMARY")
        print("="*50)
        print(f"🗑️  Removed files: {len(self.cleanup_report['removed_files'])}")
        print(f"📦 Moved files: {len(self.cleanup_report['moved_files'])}")
        print(f"📁 Organized directories: {len(self.cleanup_report['organized_directories'])}")
        
        if self.cleanup_report['removed_files']:
            print(f"\n🗑️  Removed temporary files:")
            for file in self.cleanup_report['removed_files'][:10]:  # Show first 10
                print(f"   - {file}")
            if len(self.cleanup_report['removed_files']) > 10:
                print(f"   ... and {len(self.cleanup_report['removed_files']) - 10} more")
        
        print(f"\n✨ Root directory is now clean and organized!")

if __name__ == "__main__":
    cleanup = AtlasCleanup()
    cleanup.run_cleanup()