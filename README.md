# 🤖 Atlas Autonomous System - MCP Multi-Agent Platform

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

## 📦 Installation

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- kubectl and kind (for Kubernetes)
- Ollama (running on host for LLM support)

### Local Installation
```bash
git clone https://github.com/oleg121203/Atlas-mcp.git
cd Atlas-mcp
pip install -r requirements.txt
./start_atlas.sh --local
```

### Docker Installation
```bash
git clone https://github.com/oleg121203/Atlas-mcp.git
cd Atlas-mcp
docker compose up -d
```

### Kubernetes Installation
```bash
git clone https://github.com/oleg121203/Atlas-mcp.git
cd Atlas-mcp
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
