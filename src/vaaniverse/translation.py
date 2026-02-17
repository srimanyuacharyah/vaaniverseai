"""Translation utilities using deep-translator.

Uses ``deep-translator`` (GoogleTranslator) as the primary backend.
Falls back to a placeholder when the library is unavailable or the
request fails.
"""
from typing import Optional

_GoogleTranslator = None
try:
    from deep_translator import GoogleTranslator as _GoogleTranslator  # type: ignore
except Exception:
    pass

# Supported Indian languages (ISO-639-1 codes)
INDIAN_LANGUAGES = {
    'hi': 'Hindi',
    'kn': 'Kannada',
    'ta': 'Tamil',
    'te': 'Telugu',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'ur': 'Urdu',
}

ALL_LANGUAGES = {
    'en': 'English',
    **INDIAN_LANGUAGES,
}


def translate(text: str, src: str = 'auto', tgt: str = 'hi') -> str:
    """Translate *text* from *src* to *tgt* language codes (ISO 639-1).

    If a real translator is not available, returns a placeholder string.
    """
    if not text:
        return ""
    if _GoogleTranslator is not None:
        try:
            t = _GoogleTranslator(source=src, target=tgt)
            return t.translate(text)
        except Exception:
            return f"[{tgt}] {text}"
    return f"[{tgt}] {text}"


def detect_and_translate(text: str, tgt: str = 'hi') -> dict:
    """Auto-detect source language, translate to *tgt*, and return both."""
    translated = translate(text, src='auto', tgt=tgt)
    return {'original': text, 'translated': translated, 'target': tgt}


def batch_translate(text: str, targets: list[str] | None = None) -> dict:
    """Translate *text* into multiple target languages at once."""
    if targets is None:
        targets = list(INDIAN_LANGUAGES.keys())
    results = {}
    for tgt in targets:
        results[tgt] = translate(text, src='auto', tgt=tgt)
    return results
