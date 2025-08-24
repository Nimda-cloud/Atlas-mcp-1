# TTS MCP Adapter

Purpose: Provide a lightweight FastAPI service exposing a minimal TTS MCP contract for Atlas core. Supports offline macOS TTS by default, with Google TTS and Coqui TTS as fallbacks.

## Endpoints

- GET /health -> { status: "ok" }
- GET /voices -> { voices: string[] }
- POST /speak { text, voice?, agent?, provider? } -> { url, provider }

## Providers

- macos_say (default on macOS): offline using the system `say` command, outputs .m4a (AAC)
- google_tts: requires GOOGLE_TTS_API_KEY and GOOGLE_TTS_LANGUAGE (e.g., uk-UA)
- coqui_tts: uses COQUI_TTS_BASE_URL (e.g., <http://coqui-tts:5002>)

## Environment

- MCP_PORT (default 4004)
- TTS_DEFAULT_PROVIDER (default macos_say)
- TTS_PROVIDERS (comma-separated, order = fallback chain; default macos_say,google_tts,coqui_tts)
- GOOGLE_TTS_API_KEY, GOOGLE_TTS_LANGUAGE
- COQUI_TTS_BASE_URL (default <http://coqui-tts:5002>)
- ATLAS_TTS_LANG (optional, default uk)
- TTS_OUTPUT_DIR (default /data/tts)

## Notes

- Audio files are saved as mp3 (google/coqui) or m4a (macos_say) and served statically from /audio/...
- Voices endpoint on macOS includes dynamic list from `say -v ?` as `macos:<VoiceName>` entries.
