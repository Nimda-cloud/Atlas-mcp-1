ASCII блок‑схемa.

## 1. Логический поток /chat
1. Пользователь → POST /chat (FastAPI).
2. LLM1 (Interface):
   - Генерирует короткий ответ на украинском.
   - Определяет: есть ли признаки действия (ключевые слова).
3. Если действий нет → TTS (say_tts) → ответ пользователю.
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

## 6. Виявленні проблеми / риски [ВИПРАВЛЕНО]

1. ✅ **ВИПРАВЛЕНО**: Рекурсія TTS fallback - додано internal_call флаг та _handle_tts_direct метод
2. ✅ **ВИПРАВЛЕНО**: Реалізована функціональність proxy інструментів через _execute_proxy_tool
3. ✅ **ВИПРАВЛЕНО**: Додано централізований timeout (60s) для subtasks через asyncio.wait_for
4. ✅ **ВИПРАВЛЕНО**: Security check покращений з whitelist/blacklist + нормалізацією
5. ✅ **ВИПРАВЛЕНО**: Task Orchestrator API - використання правильних параметрів (title, description, task_type)
6. ✅ **ВИПРАВЛЕНО**: Thread safety для log_buffer через asyncio.Lock
7. ✅ **ВИПРАВЛЕНО**: Додано ExecutionContext для трассировки (session_id, correlation_id)
8. ✅ **ВИПРАВЛЕНО**: Видалено дублюючий код - legacy методи тепер перенаправляють до Task Orchestrator
9. Набор ключевых слов для action detection прост — легко пропустить задачи или наоборот сработать ложноположительно (рекомендуется классификатор).
10. В proxy режиме health_url для 'proxy' жёстко привязан к /tts/sse — если TTS модуль мёртв, общий статус будет ложным "down" (лучше агрегировать).


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

## 9. Итоговая оценка
Архитектурно структура согласованная: чёткое разделение ролей, safety gate, многоуровневая оркестрация, мониторинг. Основные недочёты — неполная реализация proxy инструментов, риск рекурсии TTS, дублирующий устаревший код оркестрации, упрощённые эвристики безопасности и определения задач. Исправления не требуют кардинальной перестройки — локальные рефакторинги.

Нужны правки кода? Скажи — подготовлю патч.