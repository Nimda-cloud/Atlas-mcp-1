#!/bin/bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | npx @playwright/mcp --browser firefox --headless
