#!/usr/bin/env python3
import os
import uuid
from pathlib import Path
import platform
import subprocess
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
from aiohttp import ClientTimeout

# Minimal FastAPI TTS MCP adapter with Google TTS default and Coqui fallback

MCP_PORT = int(os.getenv("MCP_PORT", "4004"))
# Default to a repository-local folder for local runs; containers can override via env
TTS_OUTPUT_DIR = Path(os.getenv("TTS_OUTPUT_DIR", "data/tts"))
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TTS_DEFAULT_PROVIDER = os.getenv("TTS_DEFAULT_PROVIDER", "ukrainian_tts").strip()
TTS_PROVIDERS = [p.strip() for p in os.getenv(
    "TTS_PROVIDERS",
    "ukrainian_tts,macos_say,google_tts,coqui_tts"
).split(",") if p.strip()]

GOOGLE_TTS_API_KEY = os.getenv("GOOGLE_TTS_API_KEY", "").strip()
GOOGLE_TTS_LANGUAGE = os.getenv("GOOGLE_TTS_LANGUAGE", os.getenv("ATLAS_TTS_LANG", "uk-UA").strip())
COQUI_TTS_BASE_URL = os.getenv("COQUI_TTS_BASE_URL", "http://coqui-tts:5002").strip()
UK_TTS_DEVICE = os.getenv("UK_TTS_DEVICE", "cpu").strip()  # cpu|mps|gpu
UK_TTS_PREFERRED_FORMAT = os.getenv("UK_TTS_PREFERRED_FORMAT", "wav").strip()  # wav|mp3

app = FastAPI(title="Local TTS MCP Adapter", version="0.1.0")
app.mount("/audio", StaticFiles(directory=str(TTS_OUTPUT_DIR)), name="audio")

# naive in-memory voices list; map voices to providers as needed
VOICES = [
    {"name": "uk:Dmytro", "provider": "ukrainian_tts"},
    {"name": "macos:default", "provider": "macos_say"},
    {"name": "google:standard-b", "provider": "google_tts"},
    {"name": "google:standard-c", "provider": "google_tts"},
    {"name": "coqui:xtts_v2", "provider": "coqui_tts"},
]

@app.get("/health")
async def health():
    return {"status": "ok"}

def _list_macos_voices() -> list[str]:
    if platform.system() != "Darwin":
        return []
    try:
        # "say -v ?" outputs lines starting with the voice name
        res = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=True)
        voices = []
        for line in res.stdout.splitlines():
            name = line.split()[0].strip()
            if name and name != "?":
                voices.append(f"macos:{name}")
        return voices
    except Exception:
        return []

@app.get("/voices")
async def voices():
    macos_voices = _list_macos_voices()
    configured = [v["name"] for v in VOICES]
    # de-duplicate preserving order: macOS voices first for local usage
    combined = []
    for name in macos_voices + configured:
        if name not in combined:
            combined.append(name)
    return {"voices": combined}

async def macos_say_speak(text: str, voice: str | None) -> Dict[str, Any]:
    """Synthesize speech offline using macOS 'say' and save as .m4a (AAC)."""
    if platform.system() != "Darwin":
        raise HTTPException(status_code=500, detail="macos_say provider is only available on macOS")
    filename = f"macos_{uuid.uuid4().hex}.m4a"
    out_path = TTS_OUTPUT_DIR / filename
    cmd = ["say", "-o", str(out_path), "--data-format=aac", "--", text]
    # If voice provided like 'macos:Victoria' -> use -v Victoria
    if voice:
        v = voice
        if v.startswith("macos:"):
            v = v.split(":", 1)[1]
        if v:
            cmd = ["say", "-v", v, "-o", str(out_path), "--data-format=aac", "--", text]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="'say' command not found on this system")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"macOS say failed: {e}")
    if not out_path.exists():
        raise HTTPException(status_code=500, detail="macOS say did not produce output file")
    return {"url": f"/audio/{filename}", "provider": "macos_say"}

async def ukrainian_tts_speak(text: str, voice: str | None) -> Dict[str, Any]:
    """Synthesize Ukrainian speech locally using robinhad/ukrainian-tts."""
    try:
        from ukrainian_tts.tts import TTS, Voices, Stress
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ukrainian-tts not available: {e}")

    # Select voice
    uk_voice = None
    try:
        uk_voice = getattr(Voices, 'Dmytro').value
    except Exception:
        pass
    if voice and voice.startswith("uk:"):
        name = voice.split(":", 1)[1]
        try:
            uk_voice = getattr(Voices, name).value
        except Exception:
            # fallback keep previous
            pass
    if uk_voice is None:
        raise HTTPException(status_code=500, detail="ukrainian-tts voice not resolved")

    tts = TTS(device=UK_TTS_DEVICE)

    preferred = (UK_TTS_PREFERRED_FORMAT or "wav").lower()
    if preferred == "mp3":
        filename = f"uk_{uuid.uuid4().hex}.mp3"
        out_path = TTS_OUTPUT_DIR / filename
        try:
            import io
            from pydub import AudioSegment
            wav_buf = io.BytesIO()
            # The API writes WAV data to file-like object
            tts.tts(text, uk_voice, Stress.Dictionary.value, wav_buf)
            wav_buf.seek(0)
            audio = AudioSegment.from_file(wav_buf, format="wav")
            audio.export(out_path, format="mp3")
            return {"url": f"/audio/{filename}", "provider": "ukrainian_tts"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to encode mp3: {e}")
    else:
        filename = f"uk_{uuid.uuid4().hex}.wav"
        out_path = TTS_OUTPUT_DIR / filename
        try:
            with open(out_path, "wb") as f:
                # API returns (audio, accented_text); passing file handle writes audio
                tts.tts(text, uk_voice, Stress.Dictionary.value, f)
            return {"url": f"/audio/{filename}", "provider": "ukrainian_tts"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to synthesize wav: {e}")

async def google_tts_speak(text: str, voice: str | None) -> Dict[str, Any]:
    if not GOOGLE_TTS_API_KEY:
        raise HTTPException(status_code=500, detail="Missing GOOGLE_TTS_API_KEY")

    # Use Google Text-to-Speech REST v1beta1 via API key
    # Endpoint: https://texttospeech.googleapis.com/v1/text:synthesize
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    headers = {"X-Goog-Api-Key": GOOGLE_TTS_API_KEY, "Content-Type": "application/json"}

    # Basic voice and audio config
    voice_params = {
        "languageCode": GOOGLE_TTS_LANGUAGE or "uk-UA",
        # Optionally parse voice like google:standard-b
        "name": None,
    }
    if voice and voice.startswith("google:"):
        # map google:standard-b -> en-US-Standard-B like style names if needed; keep None to let API choose
        pass

    payload = {
        "input": {"text": text},
        "voice": {k: v for k, v in voice_params.items() if v},
        "audioConfig": {"audioEncoding": "MP3"},
    }

    timeout = ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                detail = await resp.text()
                raise HTTPException(status_code=502, detail=f"Google TTS error: {resp.status} {detail}")
            data = await resp.json()

    # Save MP3 to file
    audio_b64 = data.get("audioContent")
    if not audio_b64:
        raise HTTPException(status_code=502, detail="Google TTS returned no audio content")
    import base64
    audio_bytes = base64.b64decode(audio_b64)
    filename = f"google_{uuid.uuid4().hex}.mp3"
    out_path = TTS_OUTPUT_DIR / filename
    out_path.write_bytes(audio_bytes)
    return {"url": f"/audio/{filename}", "provider": "google_tts"}

async def coqui_tts_speak(text: str, voice: str | None) -> Dict[str, Any]:
    # Coqui TTS server API: POST /api/tts -> wav bytestream; we save to mp3 for consistency
    tts_url = f"{COQUI_TTS_BASE_URL.rstrip('/')}/api/tts"
    form = {"text": text}
    timeout = ClientTimeout(total=300)
    try:
        print(f"DEBUG: Trying to connect to Coqui TTS at {tts_url}")
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(tts_url, data=form) as resp:
                if resp.status != 200:
                    detail = await resp.text()
                    print(f"ERROR: Coqui TTS error: {resp.status} {detail}")
                    raise HTTPException(status_code=502, detail=f"Coqui TTS error: {resp.status} {detail}")
                wav_bytes = await resp.read()
                print(f"DEBUG: Received {len(wav_bytes)} bytes from Coqui TTS")
    except Exception as e:
        print(f"ERROR: Exception connecting to Coqui TTS: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Exception connecting to Coqui TTS: {str(e)}")

    # Try to convert WAV->MP3 if pydub/ffmpeg available; else save WAV
    filename_mp3 = f"coqui_{uuid.uuid4().hex}.mp3"
    filename_wav = f"coqui_{uuid.uuid4().hex}.wav"
    try:
        from pydub import AudioSegment
        from io import BytesIO
        audio = AudioSegment.from_file(BytesIO(wav_bytes), format="wav")
        mp3_path = TTS_OUTPUT_DIR / filename_mp3
        audio.export(mp3_path, format="mp3")
        return {"url": f"/audio/{filename_mp3}", "provider": "coqui_tts"}
    except Exception:
        wav_path = TTS_OUTPUT_DIR / filename_wav
        wav_path.write_bytes(wav_bytes)
        return {"url": f"/audio/{filename_wav}", "provider": "coqui_tts"}

async def synthesize_via_chain(text: str, voice: str | None, provider: str | None) -> Dict[str, Any]:
    chain = TTS_PROVIDERS if not provider else [provider] + [p for p in TTS_PROVIDERS if p != provider]
    last_error = None
    print(f"DEBUG: TTS chain: {chain} for text: {text}")
    for p in chain:
        try:
            print(f"DEBUG: Trying provider: {p}")
            if p == "ukrainian_tts":
                return await ukrainian_tts_speak(text, voice)
            if p == "google_tts":
                return await google_tts_speak(text, voice)
            if p == "coqui_tts":
                return await coqui_tts_speak(text, voice)
        except HTTPException as e:
            print(f"ERROR: HTTPException from provider {p}: {str(e)}")
            last_error = e
            continue
        except Exception as e:
            print(f"ERROR: Exception from provider {p}: {str(e)}")
            last_error = e
            continue
    if last_error:
        print(f"ERROR: All providers failed, last error: {str(last_error)}")
        raise HTTPException(status_code=502, detail=str(last_error))
    print("ERROR: No TTS providers configured")
    raise HTTPException(status_code=500, detail="No TTS providers configured")

@app.post("/speak")
async def speak(body: Dict[str, Any]):
    text = (body or {}).get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    voice = (body or {}).get("voice")
    provider = (body or {}).get("provider") or TTS_DEFAULT_PROVIDER
    result = await synthesize_via_chain(text=text, voice=voice, provider=provider)
    return JSONResponse(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT)
