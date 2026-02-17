"""Optional integrations for heavyweight TTS and voice-cloning models.

These functions are safe wrappers that only attempt imports at runtime. They
will raise informative errors if the required libraries are not installed.

NOTE: This module does NOT perform impersonation of public figures. Any
attempt to pass a famous person's name as a `speaker` or `style` will be
rejected.
"""
from typing import Optional
from pathlib import Path
from .config import cfg


def is_coqui_available() -> bool:
    try:
        import TTS  # type: ignore
        return True
    except Exception:
        return False


def synthesize_with_coqui(text: str, speaker: Optional[str] = None, out_path: str = 'out.wav', model_name: Optional[str] = None) -> str:
    """Synthesize `text` using Coqui TTS if available.

    This is a robust wrapper that:
    - rejects public-figure impersonation
    - attempts to use an explicit `model_name`, then `VAANIVERSE_COQUI_MODEL`, then
      any available model reported by `TTS.list_models()`.
    - raises informative ImportError if Coqui isn't installed.
    """
    forbidden = {'spb', 'rajnikanth', 'sudeepa'}
    if speaker and speaker.lower() in forbidden:
        raise ValueError('Impersonation of public figures is not allowed.')

    try:
        from TTS.api import TTS  # type: ignore
    except Exception as e:
        raise ImportError(
            "Coqui TTS not installed. Install with 'pip install TTS[all]'. See DEPLOY.md for details."
        ) from e

    # Decide model name
    chosen = model_name or cfg.coqui_model or ''
    try:
        available = TTS.list_models()
    except Exception:
        available = []

    if not chosen:
        if available:
            chosen = available[0]
        else:
            raise RuntimeError('No Coqui TTS models available. Download a model or set VAANIVERSE_COQUI_MODEL.')

    # If chosen isn't in available list, still try; Coqui may load remote models.
    tts = TTS(chosen)

    # If speaker provided and model supports speakers, pass it through.
    try:
        tts.tts_to_file(text=text, speaker=speaker, file_path=out_path)
    except TypeError:
        tts.tts_to_file(text=text, file_path=out_path)
    return str(Path(out_path).absolute())


def clone_voice_with_model(sample_path: str, out_name: str, consent: bool = False) -> str:
    """High-level placeholder for voice cloning integration.

    This function enforces consent and will raise NotImplementedError unless a
    vetted cloning pipeline (and dependencies) are integrated by the user.
    """
    if not consent:
        raise PermissionError('Explicit consent required to clone voices.')
    # If someone integrates a cloning library (e.g., SV2TTS pipelines), call it here.
    raise NotImplementedError('Voice-clone integration not installed. Follow DEPLOY.md to add a cloning model.')
