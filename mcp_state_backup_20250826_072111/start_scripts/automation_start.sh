#!/bin/bash
cd "$(dirname "$0")/automation-mcp"
exec bun run index.ts --stdio
