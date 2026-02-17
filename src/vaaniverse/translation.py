"""Translation utilities.

This module tries to use `googletrans` when available. If importing or using it
fails (dependency issues on some Python versions), the `translate` function
falls back to a safe placeholder that prefixes the text with the target
language code. Replace with a proper translation provider for production use.
"""
try:
    from googletrans import Translator
except Exception:
    Translator = None

_translator = None
if Translator is not None:
    try:
        _translator = Translator()
    except Exception:
        _translator = None


def translate(text: str, src: str = 'auto', tgt: str = 'hi') -> str:
    """Translate `text` from `src` to `tgt` language codes (ISO 639-1).

    If a real translator is not available, returns a placeholder string that
    indicates the intended target language.
    """
    if not text:
        return ""
    if _translator is not None:
        try:
            res = _translator.translate(text, src=src, dest=tgt)
            return res.text
        except Exception:
            return f"[{tgt}] {text}"
    # Fallback placeholder
    return f"[{tgt}] {text}"
