# 🤖 Atlas Autonomous CI/CD & Auto-Healing Guide

## Overview

Atlas now supports a complete autonomous development cycle with automatic code fixes, testing, and deployment. The system can detect issues, fix them automatically, and continuously improve through cyclical processes.

## 🔄 Complete Automation Workflow

### 1. Agent Development Cycle
```
Agent makes changes → Creates PR → Automatic labeling → CI tests → Auto-merge → Post-merge verification
```

### 2. Auto-Healing Cycle  
```
Post-merge failure → Issue creation → Agent analysis → Fix generation → Fix PR → Auto-merge → Verification
```

### 3. Cyclical Improvement
```
User reports bug → Web interface debugging → Real-time fixes → Deployment → Monitoring → Continuous optimization
```

## 🚀 Deployment Methods

### Native macOS Execution
```bash
# Install and start natively
curl -fsSL https://raw.githubusercontent.com/oleg121203/Atlas-mcp/main/install_macos.sh | bash
cd ~/Atlas
./start_atlas.sh --local

# Access web interface
open http://localhost:8000
```

### Docker Deployment
```bash
# Full stack with monitoring
./start_atlas.sh --docker

# Or manually
docker compose --profile monitoring --profile mcp --profile macos up -d
```

### Kubernetes Production
```bash
# Development environment
make install-dev
make status-dev

# Production deployment
make install-prod
make logs-prod
```

## 🔧 GitHub Workflow Configuration

### Required Workflows

1. **`pr-agent-ci.yml`** - CI/CD pipeline with auto-merge
2. **`post-merge-local.yml`** - Post-merge verification on macOS
3. **`atlas-auto-healing.yml`** - Automated issue fixing

### Self-hosted macOS Runner Setup

1. **Add runner to GitHub:**
   - Go to: Repository Settings → Actions → Runners → New self-hosted runner
   - Choose: macOS x64
   - Labels: `self-hosted`, `macOS`, `X64`

2. **Install prerequisites:**
   ```bash
   # Xcode Command Line Tools
   xcode-select --install
   
   # Docker Desktop (optional)
   brew install --cask docker
   
   # kubectl (optional)
   brew install kubectl
   ```

3. **Start runner service:**
   ```bash
   # In runner directory
   ./run.sh
   
   # Or as daemon
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```

## 🌐 Web Interface Features

### Real-time Chat Interface
- **URL:** http://localhost:8000
- **Ukrainian support:** Full bilingual interface
- **Commands:** Natural language commands in Ukrainian/English
- **Features:** 
  - Live system monitoring
  - Direct macOS automation 
  - Code debugging assistance
  - Task orchestration

### API Endpoints

#### Core Endpoints
```bash
# System status
GET /status

# Chat with agent
POST /chat
{
  "message": "відкрий мені програму Safari"
}

# Execute actions
POST /action  
{
  "action": "system_info"
}
```

#### GitHub Integration
```bash
# Auto-healing trigger
POST /github/auto-heal
{
  "issue_number": "123",
  "issue_title": "Post-merge verification failed",
  "issue_body": "Detailed error description",
  "workflow_url": "https://github.com/owner/repo/actions/runs/123"
}

# GitHub integration status
GET /github/status
```

## 🩹 Auto-Healing Process

### Automatic Trigger Flow

1. **Post-merge verification fails** on self-hosted macOS runner
2. **Issue created automatically** with labels: `bug`, `ci`, `auto-healing`, `atlas-agent`
3. **Auto-healing workflow triggered** by issue creation
4. **Atlas agent analyzes** failure logs and generates fix
5. **Fix PR created** with `automerge` and `auto-healing` labels
6. **CI tests run** on Linux and macOS
7. **Auto-merge on success** and automatic issue closure
8. **Continuous monitoring** for new failures

### Manual Triggering

#### Via GitHub Issue
```markdown
Title: Need auto-healing for [problem description]
Labels: auto-healing, atlas-agent
Body: 
Detailed description of the issue that needs automatic fixing.
/cc @atlas-agent
```

#### Via Web Interface
```bash
curl -X POST http://localhost:8000/github/auto-heal \
  -H "Content-Type: application/json" \
  -d '{
    "issue_number": "123",
    "issue_title": "Custom issue title", 
    "issue_body": "Issue description",
    "workflow_url": "https://github.com/owner/repo/actions/runs/123"
  }'
```

## 🔍 Monitoring & Debugging

### Web Interface Monitoring
- **3D Robot Head Visual:** Real-time system status indicator
- **Live Logs:** Streaming system logs and agent responses
- **Performance Metrics:** System resource usage and response times

### Prometheus Metrics
- **URL:** http://localhost:9090
- **Metrics collected:**
  - HTTP request counts and latency
  - Agent response times
  - System resource usage
  - Auto-healing success rates

### Grafana Dashboards  
- **URL:** http://localhost:3000
- **Credentials:** admin / atlas_admin
- **Dashboards:**
  - Atlas System Overview
  - Agent Performance
  - Auto-healing Metrics
  - macOS System Status

## 🌍 Ukrainian Language Support

### Natural Commands
```bash
# Web interface Ukrainian commands
"відкрий мені програму Safari"
"покажи статус системи"
"запусти тестування"
"виправ помилку в коді"
"створи новий проект"
"зупини всі процеси"
```

### Bilingual Responses
The system responds in both Ukrainian and English for maximum accessibility:
- Interface messages in Ukrainian
- Technical details in English
- Error messages in both languages
- Documentation in both languages

## 🧪 Testing the Complete System

### Run Automation Cycle Test
```bash
# Start Atlas locally
./start_atlas.sh --local

# In another terminal, run full test suite
python test_automation_cycle.py
```

### Manual Testing Steps

1. **Test Native Startup:**
   ```bash
   ./start_atlas.sh --local
   curl http://localhost:8000/status
   ```

2. **Test Ukrainian Interface:**
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Привіт, покажи статус системи"}'
   ```

3. **Test Docker Deployment:**
   ```bash
   ./start_atlas.sh --docker
   docker compose ps
   ```

4. **Test Auto-healing:**
   ```bash
   curl -X POST http://localhost:8000/github/auto-heal \
     -H "Content-Type: application/json" \
     -d '{"issue_number": "999", "issue_title": "Test"}'
   ```

## 🎯 Expected Outcomes

### Successful Setup Indicators

✅ **All basic tests pass:** `python test_basic.py`  
✅ **Web interface accessible:** http://localhost:8000  
✅ **Ukrainian commands work:** Chat interface responds in Ukrainian  
✅ **Docker stack healthy:** All services running  
✅ **GitHub workflows valid:** YAML syntax correct  
✅ **Auto-healing functional:** API responds successfully  
✅ **Self-hosted runner active:** macOS runner registered and online  

### Continuous Improvement Cycle

1. **Real-time issue detection** through monitoring
2. **Automatic analysis** via Atlas agent system  
3. **Intelligent fix generation** using multi-agent coordination
4. **Automated testing** on multiple platforms
5. **Zero-downtime deployment** with rollback capability
6. **Performance optimization** through usage analytics
7. **Predictive maintenance** using ML insights

## 🚨 Troubleshooting

### Common Issues

**Web interface not responding:**
```bash
# Check Atlas is running
ps aux | grep atlas_core
lsof -i :8000

# Restart if needed
./start_atlas.sh --local
```

**Self-hosted runner offline:**
```bash
# Check runner status
./run.sh --check

# Restart runner
sudo ./svc.sh restart
```

**Docker issues:**
```bash
# Check container health
docker compose ps
docker compose logs atlas-core

# Rebuild if needed
docker compose down -v
docker compose up -d --build
```

**Auto-healing not triggering:**
```bash
# Check GitHub webhook delivery
# Verify issue has correct labels: auto-healing, atlas-agent
# Check runner logs for errors
```

For additional support, create an issue with the `help` label and the Atlas agent will automatically assist.

---

**The Atlas Autonomous System is now fully configured for continuous self-improvement!** 🚀