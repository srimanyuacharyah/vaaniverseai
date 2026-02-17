import pyttsx3
from typing import Optional

engine = None


def _get_engine():
    global engine
    if engine is None:
        engine = pyttsx3.init()
    return engine


def list_voices():
    """Return available voices from the TTS engine."""
    e = _get_engine()
    return e.getProperty('voices')


def _select_voice_for_lang(lang: str) -> Optional[str]:
    """Select a voice id that appears to match `lang` (ISO 639-1 or name).

    This is a heuristic: it checks voice names and reported languages.
    """
    if not lang:
        return None
    lang = lang.lower()
    for v in list_voices():
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


def speak(text: str, lang: str = 'en', out_path: Optional[str] = None) -> None:
    """Speak `text` using the local TTS engine.

    If `out_path` is provided, save audio to that file using `engine.save_to_file`.
    Note: quality and language coverage depend on installed system voices.
    """
    if not text:
        return
    e = _get_engine()
    voice_id = _select_voice_for_lang(lang)
    if voice_id:
        try:
            e.setProperty('voice', voice_id)
        except Exception:
            pass
    if out_path:
        e.save_to_file(text, out_path)
        e.runAndWait()
    else:
        e.say(text)
        e.runAndWait()


def speak_styled(text: str, style: str = None, lang: str = 'en', out_path: Optional[str] = None) -> None:
    """Speak text with a simple style preset.

    Style presets are lightweight adjustments (rate, volume). This is NOT
    voice cloning or impersonation. Requests to mimic specific public figures
    will be refused by higher-level code; use neutral `legend-inspired` styles
    instead.
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
    preset = presets.get(style, presets['legend-inspired'])
    e = _get_engine()
    # apply preset
    try:
        e.setProperty('rate', preset['rate'])
        e.setProperty('volume', preset['volume'])
    except Exception:
        pass
    # delegate to speak (which will select voice by lang)
    speak(text, lang=lang, out_path=out_path)

