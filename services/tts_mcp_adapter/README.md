Local TTS MCP Adapter

Purpose: Provide a lightweight FastAPI service exposing a minimal TTS MCP contract for Atlas core, routing to Google TTS by default with Coqui TTS as fallback.

Endpoints
- GET /health -> { status: "ok" }
- GET /voices -> { voices: string[] }
- POST /speak { text, voice?, agent?, provider? } -> { url, provider }

Providers
- google_tts (default): requires GOOGLE_TTS_API_KEY and GOOGLE_TTS_LANGUAGE (e.g., uk-UA)
- coqui_tts (fallback): uses COQUI_TTS_BASE_URL (e.g., http://coqui-tts:5002)

Environment
- MCP_PORT (default 4004)
- TTS_DEFAULT_PROVIDER (default google_tts)
- TTS_PROVIDERS (comma-separated, order = fallback chain)
- GOOGLE_TTS_API_KEY, GOOGLE_TTS_LANGUAGE
- COQUI_TTS_BASE_URL (default http://coqui-tts:5002)
- ATLAS_TTS_LANG (optional, default uk)
- TTS_OUTPUT_DIR (default /data/tts)

Notes
- Audio files are saved as mp3 and served statically from /audio/...
- Simple in-memory list of voices; extend as needed.
