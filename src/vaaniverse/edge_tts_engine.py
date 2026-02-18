"""Edge-TTS engine — high-quality, free text-to-speech via Microsoft Edge.

Provides async and sync wrappers around the ``edge-tts`` library.  Over 300
voices across 45+ languages are available **without** an API key.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

try:
    import edge_tts  # type: ignore
    import edge_tts.communicate
    from xml.sax.saxutils import unescape
except ImportError:
    edge_tts = None
    unescape = None

# ---------------------------------------------------------------------------
# Pre-configured Indian-language voices
# ---------------------------------------------------------------------------

VOICE_MAP: dict[str, dict[str, str]] = {
    # lang_code -> {gender: voice_short_name}
    'hi': {'female': 'hi-IN-SwaraNeural', 'male': 'hi-IN-MadhurNeural'},
    'kn': {'female': 'kn-IN-SapnaNeural', 'male': 'kn-IN-GaganNeural'},
    'ta': {'female': 'ta-IN-PallaviNeural', 'male': 'ta-IN-ValluvarNeural'},
    'te': {'female': 'te-IN-ShrutiNeural', 'male': 'te-IN-MohanNeural'},
    'bn': {'female': 'bn-IN-TanishaaNeural', 'male': 'bn-IN-BashkarNeural'},
    'mr': {'female': 'mr-IN-AarohiNeural', 'male': 'mr-IN-ManoharNeural'},
    'gu': {'female': 'gu-IN-DhwaniNeural', 'male': 'gu-IN-NiranjanNeural'},
    'ml': {'female': 'ml-IN-SobhanaNeural', 'male': 'ml-IN-MidhunNeural'},
    'pa': {'female': 'pa-IN-GurpreetNeural', 'male': 'pa-IN-GurpreetNeural'},
    'ur': {'female': 'ur-PK-UzmaNeural', 'male': 'ur-PK-AsadNeural'},
    'en': {'female': 'en-IN-NeerjaNeural', 'male': 'en-IN-PrabhatNeural'},
}


def is_available() -> bool:
    return edge_tts is not None


def get_voice(lang: str = 'hi', gender: str = 'female') -> str:
    """Return the best Edge-TTS voice for *lang* and *gender*."""
    voices = VOICE_MAP.get(lang, VOICE_MAP['en'])
    return voices.get(gender, voices.get('female', 'en-IN-NeerjaNeural'))


async def _speak_async(text: str, voice: str, out_path: str) -> str:
    """Internal async synthesis."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)
    return out_path


def speak(
    text: str,
    lang: str = 'hi',
    gender: str = 'female',
    voice: Optional[str] = None,
    out_path: Optional[str] = None,
) -> str:
    """Synthesize *text* and save to *out_path*.  Returns the file path.

    If *voice* is given it takes precedence over *lang*/*gender* lookup.
    """
    if not is_available():
        raise ImportError("edge-tts is not installed. Run: pip install edge-tts")
    if not text:
        raise ValueError("text must not be empty")
    v = voice or get_voice(lang, gender)
    if out_path is None:
        out_path = os.path.join(tempfile.gettempdir(), f"edge_tts_{os.getpid()}.mp3")
    # Run the async coroutine in a sync context
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # Already inside an event loop (e.g. FastAPI) — use a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(lambda: asyncio.run(_speak_async(text, v, out_path))).result()
    else:
        asyncio.run(_speak_async(text, v, out_path))
    return out_path


def _run_sync(coro):
    """Run an async coroutine from sync context, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Monkeypatch edge-tts to support custom SSML
# ---------------------------------------------------------------------------
_original_mkssml = edge_tts.communicate.mkssml


def _patched_mkssml(tc, escaped_text):
    """Bypass edge-tts auto-wrapping if we detect our own SSML."""
    if isinstance(escaped_text, bytes):
        raw_str = escaped_text.decode("utf-8")
    else:
        raw_str = escaped_text

    raw = unescape(raw_str)
    if raw.strip().startswith("<speak"):
        return raw
    return _original_mkssml(tc, escaped_text)


# Apply the patch
edge_tts.communicate.mkssml = _patched_mkssml


# ---------------------------------------------------------------------------
# Singing-style SSML synthesis
# ---------------------------------------------------------------------------

# Pitch patterns in semitones for a more musical feel
_PITCH_PATTERNS = [
    '+1st', '+3st', '+5st', '+4st', '+2st', '+0st', '+4st', '+2st',
    '+1st', '+5st', '+7st', '+3st', '+2st', '+6st', '+4st', '+1st',
]

_CHORUS_PITCH = '+6st'
_BRIDGE_PITCH = '+3st'


def _build_singing_ssml(text: str, voice: str) -> str:
    """Convert lyrics text into SSML with prosody variations for singing.

    - Each line gets a different pitch offset (in semitones)
    - Rate is slowed to -25% for a drawn-out singing pace
    - Chorus / bridge / outro sections get emphasized
    - Pauses are inserted between structural markers
    - Emojis and metadata are stripped for synthesis
    """
    # Pre-process: remove emojis and non-lyric indicators
    clean_text = text.replace('🎵', '').replace('🎶', '')
    
    lines = clean_text.split('\n')
    ssml_parts = []
    # Detect lang from voice name (e.g. hi-IN-SwaraNeural -> hi-IN)
    voice_lang = 'en-US'
    if '-' in voice:
        parts = voice.split('-')
        if len(parts) >= 2:
            voice_lang = f"{parts[0]}-{parts[1]}"

    ssml_parts.append(
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{voice_lang}">'
    )
    ssml_parts.append(f'<voice name="{voice}">')

    pitch_idx = 0
    in_chorus = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            ssml_parts.append('<break time="500ms"/>')
            continue

        # Detect structural markers (Standard ones like --- Verse --- or labels like Chorus:)
        lower = stripped.lower()
        if (stripped.startswith('---') and stripped.endswith('---')) or \
           lower.startswith('chorus:') or lower.startswith('verse:') or \
           lower.startswith('bridge:') or lower.startswith('outro:'):
            
            ssml_parts.append('<break time="800ms"/>')
            in_chorus = 'chorus' in lower
            if 'outro' in lower:
                ssml_parts.append('<break time="1000ms"/>')
            continue

        # Pick pitch for this line
        if in_chorus:
            pitch = _CHORUS_PITCH
            rate = '-30%'
        elif 'bridge' in lower:
            pitch = _BRIDGE_PITCH
            rate = '-20%'
        else:
            pitch = _PITCH_PATTERNS[pitch_idx % len(_PITCH_PATTERNS)]
            rate = '-25%'
            pitch_idx += 1

        # Escape XML special chars
        safe = (
            stripped
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
        )

        ssml_parts.append(
            f'<prosody rate="{rate}" pitch="{pitch}" volume="+10%">'
            f'{safe}'
            f'</prosody>'
        )
        ssml_parts.append('<break time="400ms"/>')

    ssml_parts.append('</voice>')
    ssml_parts.append('</speak>')
    return '\n'.join(ssml_parts)


async def speak_singing_async(
    text: str,
    lang: str = 'hi',
    gender: str = 'female',
    voice: Optional[str] = None,
    out_path: Optional[str] = None,
) -> str:
    """Async version of speak_singing."""
    if not is_available():
        raise ImportError("edge-tts is not installed.")
    if not text:
        raise ValueError("text must not be empty")

    v = voice or get_voice(lang, gender)
    if out_path is None:
        out_path = os.path.join(tempfile.gettempdir(), f"song_melodic_{os.getpid()}.mp3")

    ssml = _build_singing_ssml(text, v)

    try:
        communicate = edge_tts.Communicate(ssml)
        await communicate.save(out_path)
    except Exception:
        # Fallback: plain melodic synthesis
        communicate = edge_tts.Communicate(text, v, rate='-15%', pitch='+5Hz')
        await communicate.save(out_path)

    return out_path


def speak_singing(
    text: str,
    lang: str = 'hi',
    gender: str = 'female',
    voice: Optional[str] = None,
    out_path: Optional[str] = None,
) -> str:
    """Sync wrapper for speak_singing_async."""
    return _run_sync(speak_singing_async(text, lang=lang, gender=gender, voice=voice, out_path=out_path))


async def _speak_plain_melodic(
    text: str, voice: str, out_path: str,
    rate: str = '-15%', pitch: str = '+5Hz',
) -> str:
    """Fallback: synthesize with global rate/pitch without SSML."""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)
    return out_path


async def speak_async(
    text: str,
    lang: str = 'hi',
    gender: str = 'female',
    voice: Optional[str] = None,
    out_path: Optional[str] = None,
) -> str:
    """Async version of :func:`speak`."""
    if not is_available():
        raise ImportError("edge-tts is not installed. Run: pip install edge-tts")
    v = voice or get_voice(lang, gender)
    if out_path is None:
        out_path = os.path.join(tempfile.gettempdir(), f"edge_tts_{os.getpid()}.mp3")
    await _speak_async(text, v, out_path)
    return out_path


async def list_voices_async() -> list[dict]:
    """Return all available Edge-TTS voices."""
    if not is_available():
        return []
    voices = await edge_tts.list_voices()
    return voices


def list_voices() -> list[dict]:
    """Sync wrapper around :func:`list_voices_async`."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(list_voices_async())).result()
    return asyncio.run(list_voices_async())
