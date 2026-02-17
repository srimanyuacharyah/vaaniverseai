"""Text-to-speech module.

Primary backend: **edge-tts** (300+ voices, no API key).
Fallback backend: **pyttsx3** (offline, limited voices).
"""
from __future__ import annotations

import os
from typing import Optional

# -- edge-tts (primary) --
from . import edge_tts_engine

# -- pyttsx3 (fallback) --
_pyttsx3_engine = None
try:
    import pyttsx3
except Exception:
    pyttsx3 = None


def _get_pyttsx3():
    global _pyttsx3_engine
    if _pyttsx3_engine is None and pyttsx3 is not None:
        _pyttsx3_engine = pyttsx3.init()
    return _pyttsx3_engine


def list_voices():
    """Return available voices from the TTS engine."""
    if edge_tts_engine.is_available():
        return edge_tts_engine.list_voices()
    e = _get_pyttsx3()
    if e:
        return e.getProperty('voices')
    return []


def _select_voice_for_lang(lang: str) -> Optional[str]:
    """Select a pyttsx3 voice id that matches *lang*."""
    e = _get_pyttsx3()
    if e is None:
        return None
    lang = lang.lower()
    for v in (e.getProperty('voices') or []):
        try:
            langs = [l.decode() if isinstance(l, bytes) else l for l in v.languages]
        except Exception:
            langs = []
        name = (v.name or '').lower()
        if lang in name:
            return v.id
        for l in langs:
            if l and lang in l.lower():
                return v.id
    return None


def speak(
    text: str,
    lang: str = 'en',
    out_path: Optional[str] = None,
    gender: str = 'female',
    voice: Optional[str] = None,
    backend: str = 'auto',
) -> Optional[str]:
    """Speak *text*.  If *out_path* is given, save audio and return the path.

    *backend* can be ``'edge'``, ``'local'`` (pyttsx3), or ``'auto'``
    (try edge-tts first, then pyttsx3).
    """
    if not text:
        return None

    use_edge = backend in ('edge', 'auto') and edge_tts_engine.is_available()

    if use_edge:
        try:
            if out_path is None:
                out_path = f"spoken_{os.getpid()}.mp3"
            return edge_tts_engine.speak(text, lang=lang, gender=gender, voice=voice, out_path=out_path)
        except Exception:
            if backend == 'edge':
                raise
            # fall through to pyttsx3

    # pyttsx3 fallback
    e = _get_pyttsx3()
    if e is None:
        raise RuntimeError("No TTS backend available. Install edge-tts or pyttsx3.")
    voice_id = _select_voice_for_lang(lang)
    if voice_id:
        try:
            e.setProperty('voice', voice_id)
        except Exception:
            pass
    if out_path:
        e.save_to_file(text, out_path)
        e.runAndWait()
        return out_path
    else:
        e.say(text)
        e.runAndWait()
        return None


def speak_styled(text: str, style: str = None, lang: str = 'en', out_path: Optional[str] = None) -> Optional[str]:
    """Speak text with a simple style preset.

    Style presets are lightweight adjustments.  This is NOT voice cloning.
    """
    presets = {
        'energetic': {'rate': 180, 'volume': 1.0},
        'soft': {'rate': 120, 'volume': 0.7},
        'deep': {'rate': 140, 'volume': 0.9},
        'legend-inspired': {'rate': 130, 'volume': 0.95},
    }
    if style in (None, ''):
        return speak(text, lang=lang, out_path=out_path)
    if style.lower() in ('spb', 'rajnikanth', 'sudeepa'):
        raise ValueError('Impersonation of public figures is not allowed.')
    # edge-tts does not support rate/volume presets in the same way, use it
    # directly for better quality
    return speak(text, lang=lang, out_path=out_path)
