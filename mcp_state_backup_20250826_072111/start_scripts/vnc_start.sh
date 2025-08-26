#!/bin/bash
cd "$(dirname "$0")/mcp-vnc"
exec node ./dist/index.js
