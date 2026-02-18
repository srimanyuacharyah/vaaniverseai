"""Voice translation pipeline.

Translates text (or transcribed audio) into another language and
re-synthesises it with a target-language voice via edge-tts.

New in v2: **audio upload** — the user speaks in any language,
the audio is transcribed, translated, and re-spoken.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

from . import translation, edge_tts_engine

# ---------- Optional: speech recognition ----------
try:
    import speech_recognition as sr
    _sr_available = True
except ImportError:
    _sr_available = False


def is_speech_recognition_available() -> bool:
    return _sr_available


def transcribe_audio(audio_path: str, lang: str = 'auto') -> str:
    """Transcribe an audio file using Google Speech Recognition (free tier).

    Supports WAV, FLAC, and MP3 (MP3 is converted internally).
    Returns the recognized text.
    """
    if not _sr_available:
        raise ImportError(
            "SpeechRecognition is not installed. Run: pip install SpeechRecognition"
        )

    recognizer = sr.Recognizer()
    path = Path(audio_path)

    # Convert MP3/OGG to WAV if needed (SpeechRecognition expects WAV/FLAC)
    if path.suffix.lower() in ('.mp3', '.ogg', '.m4a'):
        wav_path = str(path.with_suffix('.wav'))
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(path))
            audio.export(wav_path, format='wav')
            audio_path = wav_path
        except ImportError:
            # If pydub is not available, try raw — may or may not work
            pass

    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    # Map language hint
    lang_map = {
        'auto': None, 'hi': 'hi-IN', 'kn': 'kn-IN', 'ta': 'ta-IN',
        'te': 'te-IN', 'bn': 'bn-IN', 'mr': 'mr-IN', 'gu': 'gu-IN',
        'ml': 'ml-IN', 'pa': 'pa-IN', 'ur': 'ur-IN', 'en': 'en-IN',
    }
    lang_hint = lang_map.get(lang)

    try:
        if lang_hint:
            text = recognizer.recognize_google(audio_data, language=lang_hint)
        else:
            text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        raise ValueError("Could not understand the audio. Please try a clearer recording.")
    except sr.RequestError as e:
        raise RuntimeError(f"Speech recognition service error: {e}")

    return text


async def translate_voice_async(
    text: str,
    src_lang: str = 'en',
    tgt_lang: str = 'hi',
    gender: str = 'female',
    out_path: Optional[str] = None,
) -> dict:
    """Async version of translate_voice."""
    translated = translation.translate(text, src=src_lang, tgt=tgt_lang)

    if out_path is None:
        out_path = os.path.join(
            tempfile.gettempdir(),
            f"voice_translate_{tgt_lang}_{os.getpid()}.mp3",
        )

    audio = await edge_tts_engine.speak_async(translated, lang=tgt_lang, gender=gender, out_path=out_path)

    return {
        'original': text,
        'translated': translated,
        'audio_path': audio,
        'src_lang': src_lang,
        'tgt_lang': tgt_lang,
    }


async def translate_voice_from_audio_async(
    audio_path: str,
    src_lang: str = 'auto',
    tgt_lang: str = 'hi',
    gender: str = 'female',
    out_path: Optional[str] = None,
) -> dict:
    """Async version of translate_voice_from_audio."""
    # Step 1 — transcribe (sync, as GSR is blocking but done in a thread by FastAPI/IO)
    # Note: we could wrap this in a thread but for simplicity we keep it as is
    transcribed = transcribe_audio(audio_path, lang=src_lang)

    # Step 2 — translate
    src = src_lang if src_lang != 'auto' else 'auto'
    translated = translation.translate(transcribed, src=src, tgt=tgt_lang)

    # Step 3 — synthesize
    if out_path is None:
        out_path = os.path.join(
            tempfile.gettempdir(),
            f"voice_translate_audio_{tgt_lang}_{os.getpid()}.mp3",
        )
    audio = await edge_tts_engine.speak_async(translated, lang=tgt_lang, gender=gender, out_path=out_path)

    return {
        'transcribed': transcribed,
        'translated': translated,
        'audio_path': audio,
        'src_lang': src_lang,
        'tgt_lang': tgt_lang,
    }


def translate_voice(*args, **kwargs) -> dict:
    """Sync wrapper."""
    return edge_tts_engine._run_sync(translate_voice_async(*args, **kwargs))


def translate_voice_from_audio(*args, **kwargs) -> dict:
    """Sync wrapper."""
    return edge_tts_engine._run_sync(translate_voice_from_audio_async(*args, **kwargs))


def batch_translate_voice(
    text: str,
    src_lang: str = 'en',
    gender: str = 'female',
) -> dict:
    """Translate *text* into all supported Indian languages and produce audio.

    Returns a dict mapping language code → result dict.
    """
    results = {}
    for tgt in translation.INDIAN_LANGUAGES:
        if tgt == src_lang:
            continue
        try:
            r = translate_voice(text, src_lang=src_lang, tgt_lang=tgt, gender=gender)
            results[tgt] = r
        except Exception as e:
            results[tgt] = {'error': str(e)}
    return results
