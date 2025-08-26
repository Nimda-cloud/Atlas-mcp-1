# Atlas-mcp: Блок-схеми та діаграми 📊

## 1. Загальна архітектура системи

```
                    ┌─────────────────────────────────────────┐
                    │         ATLAS-MCP SYSTEM               │
                    │              🚀 v2.0                   │
                    └─────────────────────────────────────────┘
                                       │
                    ┌─────────────────────────────────────────┐
                    │           🌐 User Interface             │
                    │         POST /chat (Ukrainian)          │
                    └─────────────────┬───────────────────────┘
                                      │
               ┌──────────────────────┼──────────────────────┐
               │                      │                      │
               ▼                      ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   🧠 LLM1       │    │   🧠 LLM2       │    │   🛡️ LLM3       │
    │   Interface     │    │   Orchestra     │    │   Security      │
    │   Port: 8000    │    │   (Legacy)      │    │   Monitor       │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
               │                      │                      │
               └──────────────────────┼──────────────────────┘
                                      │
                        ┌─────────────────────────────┐
                        │    🎯 Task Orchestrator     │
                        │       Port: 4006            │
                        │   • Plan & Execute          │
                        │   • Intelligent Routing     │
                        │   • Result Synthesis        │
                        └─────────────┬───────────────┘
                                      │
                        ┌─────────────────────────────┐
                        │      🌉 MCP Proxy           │
                        │       Port: 9090            │
                        │   • 107 Tools Available     │
                        │   • Service Routing         │
                        │   • Load Balancing          │
                        └─────────────┬───────────────┘
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        │             │               │               │             │
        ▼             ▼               ▼               ▼             ▼
  ┌─────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  ┌─────────┐
  │   🔊    │  │      🤖     │  │     🌐      │  │   🍎    │  │   📁    │
  │  TTS    │  │ Automation  │  │ Playwright  │  │AppleScr │  │  File   │
  │Ukrainian│  │   macOS     │  │   Browser   │  │  ipt    │  │ Manager │
  └─────────┘  └─────────────┘  └─────────────┘  └─────────┘  └─────────┘
        │             │               │               │             │
        └─────────────┴───────────────┴───────────────┴─────────────┘
                                      │
                              ┌───────────────┐
                              │  🎧 Audio     │
                              │   Output      │
                              │ 🔊 Ukrainian  │
                              └───────────────┘
```

## 2. Потік виконання запиту

```
   📱 USER INPUT                      🔄 PROCESSING FLOW                    📤 OUTPUT
┌─────────────────┐              ┌─────────────────────────────────────┐       ┌─────────────┐
│  "Зроби знімок  │              │                                     │       │ ✅ Success   │
│   екрану"       │──────────────▶│  1. LLM1: Ukrainian → English      │──────▶│    +        │
│  (Ukrainian)    │              │     "Take a screenshot"             │       │ 🔊 Audio    │
└─────────────────┘              │                                     │       │  Response   │
                                 │  2. LLM3: Security Check ✅         │       └─────────────┘
                                 │     - Keyword filter                │
                                 │     - Semantic analysis             │
                                 │     - Whitelist validation          │
                                 │                                     │
                                 │  3. Task Orchestrator:              │
                                 │     ┌─────────────────────────────┐ │
                                 │     │ a) initialize_session       │ │
                                 │     │ b) plan_task → subtasks     │ │
                                 │     │ c) execute_task:            │ │
                                 │     │    └─ call MCP Proxy        │ │
                                 │     │       └─ route to Auto      │ │
                                 │     │          └─ screenshot      │ │
                                 │     │ d) synthesize_results       │ │
                                 │     └─────────────────────────────┘ │
                                 │                                     │
                                 │  4. LLM1: Generate final report     │
                                 │     English → Ukrainian             │
                                 │                                     │
                                 │  5. TTS: say_tts(ukrainian_text)    │
                                 └─────────────────────────────────────┘
```

## 3. Безпека та валідація

```
🛡️ SECURITY LAYERS
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REQUEST VALIDATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🔍 LAYER 1: Keyword Filter                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Blocked: "rm -rf", "sudo", "delete", "format", "shutdown"          │   │
│  │ Allowed: "screenshot", "volume", "notification", "browser"         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  🧠 LAYER 2: Semantic Analysis (LLM3)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ "Analyze intent and context"                                       │   │
│  │ "Detect malicious patterns"                                        │   │
│  │ "Check for social engineering"                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  📋 LAYER 3: Whitelist/Blacklist                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✅ Whitelist: TTS, Screenshot, Browser, Notifications             │   │
│  │ ❌ Blacklist: System admin, File deletion, Network attacks        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ⏱️ LAYER 4: Execution Limits                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Timeout: 30 seconds max                                          │   │
│  │ • Rate limiting: 10 requests/minute                               │   │
│  │ • Resource limits: CPU/Memory monitoring                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                             ✅ APPROVED REQUEST
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │  🚀 EXECUTE TASK    │
                          │  with monitoring    │
                          └─────────────────────┘
```

## 4. MCP Proxy маршрутизація

```
           🌉 MCP PROXY (Port 9090)
    ┌─────────────────────────────────────────┐
    │         REQUEST ROUTER                  │
    └─────────────────┬───────────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
      ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│    TTS     │  │ Automation │  │ Playwright │
│   🔊       │  │    🤖      │  │    🌐      │
│ 6 tools    │  │ 19 tools   │  │ 26 tools   │
└────────────┘  └────────────┘  └────────────┘
      │               │               │
      ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│ AppleScript│  │Task Orches │  │   System   │
│     🍎     │  │    📋      │  │     ⚙️     │
│ 25 tools   │  │ 16 tools   │  │ 15 tools   │
└────────────┘  └────────────┘  └────────────┘

Total: 107 tools available through unified proxy (canonical count; деталі в `LOGIC.md`)
```

## 5. Стани сесії Task Orchestrator

```
SESSION LIFECYCLE
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  🎬 START                                                       │
│     │                                                           │
│     ▼                                                           │
│  ┌─────────────────┐                                           │
│  │ initialize_     │                                           │
│  │ session()       │                                           │
│  └─────────┬───────┘                                           │
│            │                                                   │
│            ▼                                                   │
│  ┌─────────────────┐    ❌ Planning failed                     │
│  │ plan_task()     │────────────┐                             │
│  │ • Analyze task  │            │                             │
│  │ • Break down    │            │                             │
│  │ • Create steps  │            │                             │
│  └─────────┬───────┘            │                             │
│            │                    │                             │
│            ▼                    │                             │
│  ┌─────────────────┐            │                             │
│  │ execute_task()  │            │                             │
│  │ ┌─────────────┐ │            │                             │
│  │ │  Subtask 1  │ │            │                             │
│  │ │  Subtask 2  │ │            │                             │
│  │ │  Subtask N  │ │            │                             │
│  │ └─────────────┘ │            │                             │
│  └─────────┬───────┘            │                             │
│            │                    │                             │
│            ▼                    │                             │
│  ┌─────────────────┐            │                             │
│  │ synthesize_     │            │                             │
│  │ results()       │            │                             │
│  │ • Combine data  │            │                             │
│  │ • Generate summary │         │                             │
│  └─────────┬───────┘            │                             │
│            │                    │                             │
│            ▼                    ▼                             │
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │ ✅ SUCCESS      │    │ ❌ ERROR        │                  │
│  │ complete_task() │    │ cleanup()       │                  │
│  └─────────────────┘    └─────────────────┘                  │
│                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 6. Моніторинг та метрики

```
📊 PROMETHEUS METRICS DASHBOARD

┌─────────────────────────────────────────────────────────────────┐
│                    ATLAS SYSTEM METRICS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📈 Request Rate                    🕐 Response Time            │
│  ┌─────────────────────────────┐    ┌─────────────────────────┐ │
│  │ atlas_requests_total        │    │ atlas_response_time_    │ │
│  │                             │    │ seconds                 │ │
│  │    ████████████ 150/min     │    │    ████████████ 2.3s   │ │
│  └─────────────────────────────┘    └─────────────────────────┘ │
│                                                                 │
│  👥 Active Sessions              🔧 Tool Usage                  │
│  ┌─────────────────────────────┐    ┌─────────────────────────┐ │
│  │ atlas_active_sessions       │    │ atlas_tool_usage_total  │ │
│  │                             │    │                         │ │
│  │    ████████████ 12          │    │ TTS:        ████████ 45│ │
│  └─────────────────────────────┘    │ Auto:       ██████ 32  │ │
│                                     │ Browser:    ████ 18    │ │
│  🛡️ Security Blocks              │ Apple:      ██ 8       │ │
│  ┌─────────────────────────────┐    └─────────────────────────┘ │
│  │ atlas_security_blocks_total │                                │
│  │                             │                                │
│  │    ████████████ 3/hour      │                                │
│  └─────────────────────────────┘                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 7. Відновлення після збоїв

```
🚨 FAILURE RECOVERY STRATEGY

Detected Failure
       │
       ▼
┌─────────────────┐
│ Failure Type?   │
└─────────┬───────┘
          │
    ┌─────┼─────┐─────┐
    │     │     │     │
    ▼     ▼     ▼     ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Service │ │Network │ │Timeout │ │Tool    │
│Crash   │ │Error   │ │Error   │ │Error   │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Restart │ │Retry   │ │Fallback│ │Substi- │
│Service │ │Request │ │Legacy  │ │tute    │
│        │ │        │ │Mode    │ │Tool    │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │
    └──────────┼──────────┼──────────┘
               │          │
               ▼          ▼
        ┌─────────────────────┐
        │ Log Incident &      │
        │ Update Monitoring   │
        └─────────────────────┘
               │
               ▼
        ┌─────────────────────┐
        │ Resume Normal       │
        │ Operation           │
        └─────────────────────┘
```

## 8. Розгортання та запуск

```
🚀 DEPLOYMENT PROCEDURE

Prerequisites Check
    │
    ├─ Python 3.8+ ✅
    ├─ Virtual Environment ✅
    ├─ Dependencies installed ✅
    └─ Ports available ✅
    
    ▼
┌─────────────────────────────────────────┐
│           ./start_atlas.sh              │
├─────────────────────────────────────────┤
│                                         │
│  Step 1: Check dependencies            │
│  ┌─────────────────────────────────┐   │
│  │ ✅ Virtual environment active    │   │
│  │ ✅ Requirements installed        │   │
│  │ ✅ Config files present          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Step 2: Start services sequentially   │
│  ┌─────────────────────────────────┐   │
│  │ 1. Task Orchestrator (4006)     │   │
│  │ 2. MCP Proxy (9090)             │   │
│  │ 3. Atlas Core (8000)            │   │
│  │ 4. 3D Viewer (8080)             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Step 3: Health checks              │
│  ┌─────────────────────────────────┐   │
│  │ 🔍 Verify each service          │   │
│  │ 🔍 Test connectivity            │   │
│  │ 🔍 Validate tool discovery      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Result: 🎉 System Ready!              │
└─────────────────────────────────────────┘

Process IDs:
├─ Task Orchestrator: PID 43776
├─ MCP Proxy: PID 43807
├─ Atlas Core: PID 43890
└─ 3D Viewer: PID 43903
```

Ці блок-схеми та діаграми надають повне розуміння архітектури та роботи системи Atlas-mcp! 🎯
