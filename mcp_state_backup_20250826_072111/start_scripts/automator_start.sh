#!/bin/bash
cd "$(dirname "$0")/macos-automator-mcp"
exec node dist/server.js
