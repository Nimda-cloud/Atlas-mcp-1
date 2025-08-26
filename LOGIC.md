ASCII блок‑схемa.

## 1. Логический поток /chat
1. Пользователь → POST /chat (FastAPI).
2. LLM1 (Interface):
   - Генерирует короткий ответ на украинском.
   - Определяет: есть ли признаки действия (клю**🟢 ВСІ ПРОБЛЕМИ ВИПРАВЛЕНІ!**

✅ **ВСІХ 10 критичних проблем успішно виправлено:**

1. TTS рекурсія - додано internal_call прапор  
2. Proxy tools заглушки - реалізовано HTTP виклики
3. Відсутні timeouts - додано asyncio.wait_for(30s)
4. Слабка безпека - створено whitelist/blacklist
5. API параметри - зведено у відповідність  
6. Thread safety - додано asyncio.Lock
7. Execution context - створено трасування
8. Дублюючий код - рефакторинг legacy методів
9. Простий action detection - LLM класифікатор ✅
10. Health check одного сервісу - агрегація всіх ✅

**АНАЛІЗ ДУБЛЮВАННЯ З MCP TASK ORCHESTRATOR:**

- ✅ Health checks: Task Orchestrator перевіряє внутрішні компоненти (БД, репозиторії), Atlas - зовнішні MCP сервіси  
- ✅ Action detection: Task Orchestrator класифікує типи завдань, Atlas - розпізнає потребу в діях з користувацького запиту
- ✅ НЕМАЄ КОНФЛІКТІВ: Функціонал унікальний та не дублюється

Система тепер значно стабільніша, безпечніша та функціональніша!и действий нет → TTS (say_tts) → ответ пользователю.
4. Если действия есть:
   - LLM1 переводит пользовательский украинский запрос в английское задание для планирования.
   - LLM3 (Monitor) выполняет security_check_llm3 (семантическая + keyword оценка).
   - Если отклонено → финальный украинский отказ.
   - Если одобрено → Ветка виконання (новая архитектура):
     a. Инициализация сессии orchestrator_initialize_session (Task Orchestrator MCP).
     b. Планирование orchestrator_plan_task → subtasks.
     c. Поочерёдное выполнение subtasks orchestrator_execute_task (+ complete).
     d. Синтез orchestrator_synthesize_results.
   - LLM1 формирует финальный звіт українською (generate_final_report_llm1).
   - TTS озвучивание (say_tts).
5. Логи шагов складываются в log_buffer → периодически анализируются LLM1 (фоновая петля) → голосовой статус.

## 2. Альтернативный (legacy) путь
Методы execute_task_with_llm2 и execute_orchestrated_task (JSON план от LLM2) остаются как устаревшие fallback механизмы.

## 3. MCP уровни
- Прямой режим (direct): отдельные эндпоинты (automation, macos-automator, tts, playwright, task-orchestrator).
- Proxy режим: единый MCP Proxy (mcp-proxy) маршрутизирует namespaces /{service}/...
- Автообнаружение инструментов (discover_mcp_tools_real) + кеш.

## 4. Вспомогательные подсистемы
- Лог-мониторинг (LLM1) каждые 10–15 сек с голосовой сводкой.
- Prometheus метрики /metrics.
- Безопасность: простая эвристика (LLM3 + keywords).
- AppleScript/macOS операции через MacOSAutomation.
- TTS: приоритет украинского TTS (ukrainian_tts + pygame) → fallback на say.

## 5. Основные сильные стороны
- Чётко отделены роли (Interface / Orchestrator / Monitor).
- Есть safety gate перед выполнением.
- Поддержка двух режимов MCP (proxy / direct).
- Расширяемый список инструментов (playwright, applescript, automation и др.).
- Логический цикл обратной связи (LLM1 мониторинг) повышает наблюдаемость.

### КРИТИЧНІ ПРОБЛЕМИ ТА ЇХ ВИПРАВЛЕННЯ

#### Виправлено ✅

**Проблема 1: TTS Recursion (Лінія 975-981)**
- ✅ **ВИПРАВЛЕНО**: Додано internal_call прапор для запобігання рекурсії TTS в log fallback

**Проблема 2: Stub Methods для Proxy Tools (Лінія 883-889)** 
- ✅ **ВИПРАВЛЕНО**: Реалізовано HTTP проксі виклики замість заглушок

**Проблема 3: Missing Timeouts (Лінія 900-915)**
- ✅ **ВИПРАВЛЕНО**: Додано asyncio.wait_for(timeout=30) для всіх критичних операцій

**Проблема 4: Weak Security Gate (Лінія 1155-1160)**
- ✅ **ВИПРАВЛЕНО**: Додано whitelist/blacklist систему та кращу валідацію в security_check_llm3

**Проблема 5: API Parameter Mismatch (Лінія 920-935)**
- ✅ **ВИПРАВЛЕНО**: Зведено в відповідність параметри між LLM2 і Task Orchestrator

**Проблема 6: Thread Safety Issues (Лінія 1045-1055)**
- ✅ **ВИПРАВЛЕНО**: Додано asyncio.Lock для критичних секцій

**Проблема 7: Lack of Execution Context (Лінія 1105-1125)**
- ✅ **ВИПРАВЛЕНО**: Створено ExecutionContext з session_id та correlation_id для трасування

**Проблема 8: Code Duplication (Лінія 805-825)**
- ✅ **ВИПРАВЛЕНО**: Legacy методи LLM2 перенаправлені до Task Orchestrator

**Проблема 9: Poor Action Detection (Лінія 1065-1075)**
- ✅ **ВИПРАВЛЕНО**: Замінено просте ключове пошук на _classify_action_intent з LLM класифікацією

**Проблема 10: Health Check Issues (Лінія 1194)**
- ✅ **ВИПРАВЛЕНО**: У proxy режимі тепер виявляються всі доступні сервіси замість прив'язки до одного /tts/sse

#### ОЦІНКА ФІНАЛЬНОГО СТАНУ: ✅ АРХІТЕКТУРА ВИПРАВЛЕНА

**Загальна оцінка архітектури:** 🟢 **ДОБРА**
- Критичні проблеми: **0/10** (всі виправлені ✅)
- Безпека: **ПОКРАЩЕНА** (whitelist/blacklist + валідація)  
- Продуктивність: **ПОКРАЩЕНА** (timeouts + thread safety)
- Надійність: **ПОКРАЩЕНА** (ExecutionContext + error handling)
- Код: **ОЧИЩЕНИЙ** (дублікати видалені + рефакторинг)


## 7. Рекомендованные улучшения (приоритет) [ОНОВЛЕНО]

✅ **ВИКОНАНО** (Високий пріоритет):

- ✅ Виправлено рекурсію TTS fallback (додано флаг internal_call і винесено в _handle_tts_direct метод)
- ✅ Реалізовано справжній HTTP виклик для proxy інструментів (_execute_proxy_tool)
- ✅ Введено унифіцированный ExecutionContext (session_id, correlation_id) для трассировки
- ✅ Видалено дублюючий код - legacy методи перенаправляють до Task Orchestrator

🔄 **ЗАЛИШИЛОСЬ** (Середний пріоритет):

- Розширити security_check_llm3: ✅ whitelist/blacklist + ✅ структурована класифікація
- Додати планувальник черги (використовувати task_queue)
- Винести конфіг інструментів в YAML (замість хардкоду)

📅 **НИЗЬКИЙ ПРІОРИТЕТ**:

- Кешування результатів health проб (debounce)
- Точніший аналіз "потрібна дія" (класифікатор)
- Метрики по часу виконання subtasks

## 8. ASCII блок‑схема

```
+------------------+        +------------------------+
|      User        |  HTTP  | FastAPI /chat endpoint |
+--------+---------+  --->  +-----------+------------+
         |                              |
         | message                      |
         v                              |
+----------------------+                |
|   LLM1 Interface     |<---------------+
| (UA dialogue, detect |  progress / logs
|  action keywords)    |
+----+-----------+-----+
     |no action          action?
     |                   |
     |                   v
     |          +----------------------+
     |          | Translate UA -> EN   |
     |          +----------+-----------+
     |                     |
     |                     v
     |          +----------------------+
     |          |  LLM3 Security Gate  |
     |          +----+-----------------+
     |               | approved?
     |  simple TTS    |no
     v               v
+-----------+   +-----------------------------+
|  TTS say  |   |  LLM1 Final refusal (UA)    |
+-----+-----+   +---------------+-------------+
      |                         |
      | (Return response)       |
      +-------------------------+
                                yes
                                v
                      +------------------------------+
                      | Task Orchestrator (MCP tool) |
                      | 1) initialize_session        |
                      | 2) plan_task (subtasks)      |
                      | 3) loop execute + complete   |
                      | 4) synthesize_results        |
                      +---------------+--------------+
                                      |
                                      v
                             +------------------+
                             | Execution Results|
                             +--------+---------+
                                      |
                                      v
                           +-----------------------+
                           | LLM1 Final Report (UA)|
                           +-----------+-----------+
                                       |
                                       v
                                   +-------+
                                   |  TTS  |
                                   +---+---+
                                       |
                               HTTP response to user
```

Фоновая подсистема:
```
+--------------------+
| log_buffer updates |
+----------+---------+
           |
           v (every 10-15s)
   +-------------------------+
   | LLM1 Log Monitor        |
   | analyze recent logs     |
   +------------+------------+
                v
          +-----------+
          |  TTS brief|
          +-----------+
```

Интеграции:
```
Ollama (LLM backend) <--- LLM1/2/3
AppleScript/macOS ----> MacOSAutomation
Prometheus <---------- /metrics middleware
MCP Proxy (optional) <-> tool namespaces (tts, automation, playwright, applescript, task-orchestrator)
```

## 9. Итоговая оценка [ОНОВЛЕНО]

Архитектурно структура значно покращена: чёткое разделение ролей, надійний safety gate, багаторівнева оркестрация через Task Orchestrator, покращений мониторинг з ExecutionContext. 

**✅ ВИПРАВЛЕНО 8 з 10 критичних проблем:**
- Рекурсія TTS, proxy інструменти, timeout, security gate, API інтеграція, thread safety, трассировка, дублюючий код

**� ВСІ ПРОБЛЕМИ ВИПРАВЛЕНІ!**

✅ **ВСІХ 10 критичних проблем успішно виправлено:**
1. TTS рекурсія - додано internal_call прапор  
2. Proxy tools заглушки - реалізовано HTTP виклики
3. Відсутні timeouts - додано asyncio.wait_for(30s)
4. Слабка безпека - створено whitelist/blacklist
5. API параметри - зведено у відповідність  
6. Thread safety - додано asyncio.Lock
7. Execution context - створено трасування
8. Дублюючий код - рефакторинг legacy методів
9. Простий action detection - LLM класифікатор ✅ 
10. Health check одного сервісу - агрегація всіх ✅

**АНАЛІЗ ДУБЛЮВАННЯ З MCP TASK ORCHESTRATOR:**
- ✅ Health checks: Task Orchestrator перевіряє внутрішні компоненти (БД, репозиторії), Atlas - зовнішні MCP сервіси  
- ✅ Action detection: Task Orchestrator класифікує типи завдань, Atlas - розпізнає потребу в діях з користувацького запиту
- ✅ НЕМАЄ КОНФЛІКТІВ: Функціонал унікальний та не дублюється

Система тепер значно стабільніша, безпечніша та функціональніша!