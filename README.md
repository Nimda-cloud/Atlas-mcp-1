# 🤖 Atlas Autonomous System

**Intelligent and Autonomous Computer Management for macOS**

Atlas is an advanced autonomous system that uses multiple AI agents to intelligently manage and automate your macOS computer. Built with local LLM processing, modular architecture, and advanced automation capabilities.

![Atlas Demo](https://img.shields.io/badge/Platform-macOS-blue) ![Python](https://img.shields.io/badge/Python-3.11+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### 🧠 Multi-Agent AI System
- **LLM1 (Interface Agent)**: Handles user interactions and maintains conversation memory
- **LLM2 (Orchestrator)**: Plans and coordinates task execution with local processing
- **LLM3 (Monitor)**: Continuously monitors system health and security

### 🖥️ Native macOS Integration
- **AppleScript Automation**: Direct integration with macOS system functions
- **Application Management**: Open, close, and control applications
- **System Information**: Real-time system monitoring and reporting
- **Shortcuts Integration**: Leverage macOS Shortcuts for complex workflows

### 🔒 Privacy-First Design
- **Local LLM Processing**: Uses Ollama for on-device AI processing
- **No Cloud Dependencies**: Core functionality works entirely offline
- **Secure by Design**: All sensitive operations require explicit permission

### 🗣️ Voice Interaction
- **Text-to-Speech**: Multi-provider TTS with local fallback
- **Speech Recognition**: Voice command processing
- **Agent Voices**: Each AI agent has its own voice identity

### 🌐 Web Interface
- **Real-time Dashboard**: Monitor system status and agent activity
- **Chat Interface**: Direct communication with AI agents
- **Control Panel**: Execute predefined actions and workflows

### 🔧 Modular Architecture
- **MCP Servers**: Containerized microservices for different capabilities
- **Plugin System**: Easy to extend with new automation modules
- **Docker Support**: Full containerization for easy deployment
- **Kubernetes Ready**: Production-grade orchestration with professional monitoring

### ☸️ Enterprise Kubernetes Deployment
- **Professional Orchestration**: Full Kubernetes configuration with best practices
- **Auto-scaling**: Horizontal Pod Autoscaler with intelligent resource management
- **High Availability**: Multi-replica deployments with Pod Disruption Budgets
- **Monitoring Stack**: Prometheus + Grafana with custom dashboards and alerts
- **Security**: Network policies, RBAC, secrets management
- **Load Balancing**: NGINX Ingress with SSL/TLS termination
- **Storage**: Persistent volumes for data persistence
- **Development/Production**: Separate overlays for different environments

## 📋 Requirements

### System Requirements
- **Operating System**: macOS 10.15 (Catalina) or later
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space (for models and data)
- **Network**: Internet connection for initial setup and model downloads

### Software Dependencies
- **Python**: 3.11 or later
- **Ollama**: Local LLM runtime
- **Docker**: Optional but recommended for full functionality
- **Homebrew**: For easy dependency management

## 🚀 Quick Start

### Option 1: Automated Installation (Recommended)

1. **Download and run the installation script:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/oleg121203/Atlas-mcp/main/install_macos.sh | bash
   ```

2. **Start Atlas:**
   ```bash
   cd ~/Atlas
   ./start_atlas.sh
   ```

3. **Open the web interface:**
   Navigate to [http://localhost:8000](http://localhost:8000) in your browser

### Option 2: Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/oleg121203/Atlas-mcp.git
   cd Atlas-mcp
   ```

2. **Install dependencies:**
   ```bash
   # Install Homebrew if not installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install system dependencies
   brew install python@3.11 ollama
   
   # Start Ollama service
   brew services start ollama
   
   # Pull required model
   ollama pull llama3.1:8b-instruct
   ```

3. **Setup Python environment:**
   ```bash
   python3.11 -m venv atlas_env
   source atlas_env/bin/activate
   pip install -r requirements.txt
   ```

4. **Run Atlas:**
   ```bash
   python atlas_core.py
   ```

### Option 3: Docker Deployment

1. **Clone and build:**
   ```bash
   git clone https://github.com/oleg121203/Atlas-mcp.git
   cd Atlas-mcp
   docker-compose up -d
   ```

2. **Access the interface:**
   Navigate to [http://localhost:8000](http://localhost:8000)

## 🎯 Usage Guide

### First Time Setup

1. **System Permissions**: Grant necessary permissions when prompted:
   - Accessibility access for automation
   - Microphone access for voice commands
   - Screen recording for visual automation

2. **Configuration**: Edit `data/config/atlas_config.json` to customize behavior:
   ```json
   {
     "automation": {
       "safe_mode": true,
       "require_confirmation": true
     },
     "voice": {
       "tts_enabled": true,
       "stt_enabled": true
     }
   }
   ```

### Basic Commands

**Through Web Interface:**
- Open the dashboard at [http://localhost:8000](http://localhost:8000)
- Type commands in the chat interface
- Use quick action buttons for common tasks

**Example Commands:**
- "Open Safari and navigate to GitHub"
- "Show me system information"
- "Monitor CPU usage and alert if it goes above 80%"
- "Create a reminder for tomorrow at 10 AM"
- "Take a screenshot and save it to Desktop"

**Voice Commands:**
- Say "Hey Atlas" to activate voice mode
- Speak your command clearly
- Confirm actions when prompted

### Advanced Usage

**Custom Automation Scripts:**
```python
# Create custom automation in data/scripts/
import asyncio
from atlas_core import AtlasCore

async def custom_task():
    atlas = AtlasCore()
    await atlas.macos_automation.manage_applications("open", "TextEdit")
    # Your custom logic here
```

**MCP Server Integration:**
```yaml
# Add custom MCP servers in docker-compose.yml
mcp-custom:
  image: your-custom-mcp:latest
  ports: ["4005:4005"]
  environment:
    - MCP_PORT=4005
```

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM1          │    │   LLM2          │    │   LLM3          │
│   Interface     │◄──►│   Orchestrator  │◄──►│   Monitor       │
│   & Memory      │    │   & Planning    │    │   & Security    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MCP Hub       │
                    │   (Modular      │
                    │   Services)     │
                    └─────────────────┘
                             │
        ┌─────────┬─────────┼─────────┬─────────┐
        │         │         │         │         │
    ┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
    │Automation│ │macOS  │ │ TTS   │ │Browser│ │ ...   │
    │   MCP  │ │AutoMCP│ │ MCP   │ │ MCP   │ │ MCP   │
    └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

### Data Flow

1. **User Input** → LLM1 (Interface Agent)
2. **Task Analysis** → LLM2 (Orchestrator Agent)
3. **Action Planning** → MCP Hub
4. **Execution** → macOS Automation
5. **Monitoring** → LLM3 (Monitor Agent)
6. **Feedback** → User Interface

## 🔧 Configuration

### Environment Variables

```bash
# Core Configuration
export ATLAS_DATA_DIR="/path/to/data"
export ATLAS_LOG_LEVEL="INFO"
export ATLAS_WEB_PORT="8000"

# LLM Configuration
export ATLAS_LLM_PROVIDER="ollama"
export ATLAS_LLM_MODEL="llama3.1:8b-instruct"
export OLLAMA_HOST="localhost:11434"

# MCP Configuration
export ATLAS_MCP_SERVERS="automation,macos-automator,tts"
export ATLAS_MCP_AUTOMATION_URL="http://localhost:4002"
export ATLAS_MCP_AUTOMATOR_URL="http://localhost:4003"
export ATLAS_MCP_TTS_URL="http://localhost:4004"

# Voice Configuration
export ATLAS_TTS_PROVIDERS="say_tts,openai_tts,elevenlabs_tts"
export ATLAS_TTS_AGENT_VOICE_LLM1="Alex"
export ATLAS_TTS_AGENT_VOICE_LLM2="Samantha"
export ATLAS_TTS_AGENT_VOICE_LLM3="Daniel"
```

### Configuration Files

**Main Config** (`data/config/atlas_config.json`):
```json
{
  "system": {
    "name": "Atlas Autonomous System",
    "version": "1.0.0",
    "data_dir": "./data",
    "log_level": "INFO"
  },
  "llm": {
    "provider": "ollama",
    "api_base": "http://localhost:11434",
    "default_model": "llama3.1:8b-instruct"
  },
  "automation": {
    "enabled": true,
    "safe_mode": true,
    "require_confirmation": true
  }
}
```

**Agent Registry** (`data/config/agents.json`):
```json
{
  "agents": [
    {
      "name": "Atlas-Interface",
      "role": "interface",
      "model": "llama3.1:8b-instruct",
      "skills": ["conversation", "memory", "user_interaction"]
    }
  ]
}
```

## 📊 Monitoring & Observability

### Web Dashboard
- Real-time system metrics
- Agent activity logs
- Task execution history
- Performance analytics

### Prometheus Metrics
```bash
# Access Prometheus at http://localhost:9090
docker-compose --profile monitoring up -d
```

### Grafana Dashboards
```bash
# Access Grafana at http://localhost:3000
# Default credentials: admin/atlas_admin
```

### Log Files
```bash
# Application logs
tail -f logs/atlas.log

# Agent-specific logs
tail -f logs/llm1_interface.log
tail -f logs/llm2_orchestrator.log
tail -f logs/llm3_monitor.log
```

## 🔒 Security & Privacy

### Privacy Features
- **Local Processing**: All AI inference happens locally via Ollama
- **No Cloud Dependencies**: Core functionality works offline
- **Data Encryption**: Sensitive data encrypted at rest
- **Access Controls**: Role-based permissions for all operations

### Security Measures
- **Safe Mode**: Dangerous operations require explicit confirmation
- **Audit Logging**: All actions logged with timestamps and context
- **Network Isolation**: MCP servers run in isolated containers
- **Permission Management**: Fine-grained control over system access

### Recommended Security Practices

1. **Review Permissions**: Regularly audit system permissions
2. **Monitor Logs**: Check logs for unusual activity
3. **Update Dependencies**: Keep all components up to date
4. **Backup Data**: Regular backups of configuration and data
5. **Network Security**: Use firewall rules to restrict access

## 🛠️ Development

### Project Structure
```
Atlas-mcp/
├── atlas_core.py          # Main application
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Service orchestration
├── install_macos.sh       # Installation script
├── data/                  # Application data
│   ├── config/           # Configuration files
│   ├── memory/           # Agent memory storage
│   └── logs/             # Log files
├── monitoring/           # Observability configuration
└── tests/               # Test suite
```

### Adding Custom MCP Servers

1. **Create MCP Server:**
   ```python
   # custom_mcp.py
   from mcp import MCPServer
   
   class CustomMCPServer(MCPServer):
       def __init__(self):
           super().__init__("custom-mcp", "1.0.0")
           self.add_tool("custom_action", self.custom_action)
       
       async def custom_action(self, params):
           # Your custom logic
           return {"result": "success"}
   ```

2. **Register in Configuration:**
   ```bash
   export ATLAS_MCP_SERVERS="automation,macos-automator,tts,custom"
   export ATLAS_MCP_CUSTOM_URL="http://localhost:4005"
   ```

3. **Add to Docker Compose:**
   ```yaml
   mcp-custom:
     build: ./custom_mcp
     ports: ["4005:4005"]
   ```

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Run end-to-end tests
python -m pytest tests/e2e/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run tests: `pytest`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check this README and the [Wiki](https://github.com/oleg121203/Atlas-mcp/wiki)
- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/oleg121203/Atlas-mcp/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/oleg121203/Atlas-mcp/discussions)

### Common Issues

**Ollama Connection Issues:**
```bash
# Check if Ollama is running
brew services list | grep ollama

# Restart Ollama
brew services restart ollama

# Check available models
ollama list
```

**Permission Denied Errors:**
```bash
# Grant accessibility permissions in System Preferences
# Security & Privacy → Privacy → Accessibility
```

**Port Already in Use:**
```bash
# Check what's using port 8000
lsof -i :8000

# Use a different port
export ATLAS_WEB_PORT=8001
```

## 🚧 Roadmap

### Version 1.1
- [ ] Enhanced voice interaction with wake words
- [ ] Integration with Apple Shortcuts
- [ ] Custom workflow builder
- [ ] Multi-language support

### Version 1.2
- [x] Kubernetes deployment support ✅
- [ ] Advanced security features
- [ ] Plugin marketplace
- [ ] Mobile companion app

### Version 2.0
- [ ] Multi-device synchronization
- [ ] Advanced AI model support
- [ ] Enterprise features
- [ ] Cloud deployment options

## ☸️ Kubernetes Deployment

Atlas MCP включає повну професійну Kubernetes конфігурацію для enterprise розгортання.

### 🚀 Швидкий старт з Kubernetes

```bash
# Клонування репозиторію
git clone <repository>
cd Atlas-mcp

# Інтерактивне встановлення
./setup-k8s.sh

# Або автоматичне встановлення
./setup-k8s.sh development
```

### 🏗️ Що включено

- **Професійна оркестрація**: Повна Kubernetes конфігурація з best practices
- **Автоматичне масштабування**: HPA з розумним управлінням ресурсами
- **Високодоступність**: Multi-replica деплойменти з Pod Disruption Budgets
- **Моніторинг**: Prometheus + Grafana з кастомними дашбордами та алертами
- **Безпека**: Network policies, RBAC, secrets management
- **Балансування навантаження**: NGINX Ingress з SSL/TLS
- **Зберігання**: Persistent volumes для збереження даних
- **Середовища**: Окремі overlay для development/production

### 📊 Компоненти стеку

#### Основні сервіси
- **Atlas Core** (2-3 репліки) - основний AI сервіс
- **Atlas Frontend** (3-5 реплік) - 3D веб-інтерфейс  
- **MCP Services** (по 2-3 репліки кожний):
  - MCP Automation - автоматизація задач
  - MCP Automator - macOS автоматизація
  - MCP TTS - текст-в-мову сервіс
  - MCP Playwright - браузер автоматизація

#### Підтримуючі сервіси
- **Redis** - кешування та черги
- **Qdrant** - векторна база даних для AI
- **Prometheus** - збір метрик
- **Grafana** - візуалізація даних

### 🛠️ Управління кластером

```bash
# Використання make команд
make install-dev          # Встановити development
make install-prod         # Встановити production
make status-dev           # Статус development
make logs-dev             # Логи development
make monitoring-dev       # Моніторинг development
make scale-frontend-dev REPLICAS=5  # Масштабування

# Або безпосередньо через скрипт
./k8s-manage.sh install development
./k8s-manage.sh status development
./k8s-manage.sh logs development atlas-core
./k8s-manage.sh scale development atlas-frontend 5
```

### 📈 Доступ до сервісів

```bash
# Atlas Frontend
make port-forward-atlas-dev
# Відкрийте http://localhost:8080

# Grafana Dashboard
make port-forward-grafana-dev  
# Відкрийте http://localhost:3000 (admin/dev_admin)

# Prometheus Metrics
make port-forward-prometheus-dev
# Відкрийте http://localhost:9090
```

### 🔧 Налаштування

1. **Скопіюйте конфігурацію**:
   ```bash
   cp .env.k8s.example .env.k8s
   # Відредагуйте налаштування за потребою
   ```

2. **Налаштуйте secrets для production**:
   ```bash
   mkdir secrets/
   echo "your-api-key" > secrets/google-tts-api-key.txt
   echo "secure-password" > secrets/grafana-admin-password.txt
   ```

3. **Побудуйте образи**:
   ```bash
   make build-images
   ```

4. **Розгорніть**:
   ```bash
   ./setup-k8s.sh production
   ```

### 📋 Вимоги для Kubernetes

#### Мінімальні
- **CPU**: 4 vCPU
- **RAM**: 8 GB  
- **Storage**: 50 GB
- **Nodes**: 2+

#### Рекомендовані для production
- **CPU**: 12+ vCPU
- **RAM**: 24+ GB
- **Storage**: 200+ GB
- **Nodes**: 3+

### 📚 Документація

Повна документація по Kubernetes розгортанню доступна в [k8s/README.md](k8s/README.md).

## 🙏 Acknowledgments

- **Ollama Team**: For providing excellent local LLM infrastructure
- **FastAPI**: For the robust web framework
- **Apple**: For macOS automation APIs
- **Open Source Community**: For the countless libraries that make this possible

---

**Atlas Autonomous System** - Bringing AI-powered automation to your fingertips 🤖