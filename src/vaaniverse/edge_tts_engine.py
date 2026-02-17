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
except ImportError:
    edge_tts = None

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
# Singing-style SSML synthesis
# ---------------------------------------------------------------------------

# Pitch patterns per line to create a melodic contour
_PITCH_PATTERNS = [
    '+3Hz', '+5Hz', '+8Hz', '+6Hz', '+4Hz', '+2Hz', '+7Hz', '+5Hz',
    '+1Hz', '+6Hz', '+9Hz', '+4Hz', '+3Hz', '+7Hz', '+5Hz', '+2Hz',
]

_CHORUS_PITCH = '+10Hz'
_BRIDGE_PITCH = '+6Hz'


def _build_singing_ssml(text: str, voice: str) -> str:
    """Convert lyrics text into SSML with prosody variations for singing.

    - Each line gets a different pitch offset to create a melodic feel
    - Rate is slowed to -15% for a musical pace
    - Chorus / bridge / outro sections get emphasised
    - Pauses are inserted between structural markers (--- Verse, etc.)
    """
    lines = text.split('\n')
    ssml_parts = []
    ssml_parts.append(
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="en-US">'
    )
    ssml_parts.append(f'<voice name="{voice}">')

    pitch_idx = 0
    in_chorus = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Empty line → short pause
            ssml_parts.append('<break time="400ms"/>')
            continue

        # Detect structural markers
        if stripped.startswith('---') and stripped.endswith('---'):
            # Section header: Verse / Chorus / Bridge / Outro
            ssml_parts.append('<break time="700ms"/>')
            lower = stripped.lower()
            in_chorus = 'chorus' in lower
            if 'outro' in lower:
                ssml_parts.append('<break time="500ms"/>')
            continue

        # Pick pitch for this line
        if in_chorus:
            pitch = _CHORUS_PITCH
            rate = '-20%'
        elif 'bridge' in stripped.lower():
            pitch = _BRIDGE_PITCH
            rate = '-10%'
        else:
            pitch = _PITCH_PATTERNS[pitch_idx % len(_PITCH_PATTERNS)]
            rate = '-15%'
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
            f'<prosody rate="{rate}" pitch="{pitch}" volume="+5%">'
            f'{safe}'
            f'</prosody>'
        )
        ssml_parts.append('<break time="250ms"/>')

    ssml_parts.append('</voice>')
    ssml_parts.append('</speak>')
    return '\n'.join(ssml_parts)


async def _speak_singing_async(ssml: str, voice: str, out_path: str) -> str:
    """Synthesize SSML singing content."""
    communicate = edge_tts.Communicate(ssml, voice)
    await communicate.save(out_path)
    return out_path


def speak_singing(
    text: str,
    lang: str = 'hi',
    gender: str = 'female',
    voice: Optional[str] = None,
    out_path: Optional[str] = None,
) -> str:
    """Synthesize *text* as a **melodious song** with pitch & rate variations.

    Uses SSML prosody tags to make the voice rise and fall like singing.
    Each lyric line gets a different pitch offset; choruses are higher
    and slower; pauses separate structural sections.
    """
    if not is_available():
        raise ImportError("edge-tts is not installed. Run: pip install edge-tts")
    if not text:
        raise ValueError("text must not be empty")

    v = voice or get_voice(lang, gender)
    if out_path is None:
        out_path = os.path.join(tempfile.gettempdir(), f"song_melodic_{os.getpid()}.mp3")

    ssml = _build_singing_ssml(text, v)

    # Try SSML first; fall back to plain prosody if SSML not supported
    try:
        _run_sync(_speak_singing_async(ssml, v, out_path))
    except Exception:
        # Fallback: use plain text with global rate/pitch adjustments
        communicate_args = {'rate': '-15%', 'pitch': '+5Hz'}
        _run_sync(_speak_plain_melodic(text, v, out_path, **communicate_args))

    return out_path


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
