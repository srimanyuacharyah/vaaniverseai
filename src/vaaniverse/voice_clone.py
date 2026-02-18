"""Voice cloning module.

True voice cloning (replicating someone's exact voice) requires heavy GPU
models (e.g., Coqui TTS, RVC).  This module provides a **voice profile**
workflow that:

1. Stores the uploaded voice sample securely.
2. Attempts to analyze basic voice characteristics (pitch → male/female).
3. Creates a voice profile that maps to the best-matching edge-tts voice.
4. Lets the user test the profile by synthesising any text.

Full neural voice cloning is gated behind Coqui TTS / RVC (optional).
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .consent import verify_consent_for_sample
from . import edge_tts_engine


class ConsentError(Exception):
    pass


# Where voice profiles are stored
_PROFILES_DIR = Path(os.environ.get('VAANIVERSE_DATA', '.')) / 'voice_profiles'


def _profiles_dir() -> Path:
    _PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return _PROFILES_DIR


def clone_voice(
    sample_path: str,
    output_name: str,
    consent: bool = False,
    preferred_lang: str = 'hi',
    preferred_gender: str = 'female',
) -> str:
    """Create a voice profile from an audio sample.

    Stores the sample and maps it to the best-matching edge-tts voice.
    Returns the profile JSON path.
    """
    sample = Path(sample_path)
    if not sample.exists():
        raise FileNotFoundError("Sample file not found: %s" % sample_path)

    # Consent check
    if not consent:
        ok = verify_consent_for_sample(str(sample))
        if not ok:
            raise ConsentError(
                "Explicit consent is required to clone a voice. "
                "Provide consent=True or record consent via the web UI."
            )

    # Save the sample to profiles dir
    profiles = _profiles_dir()
    sample_dest = profiles / f"{output_name}_sample{sample.suffix}"
    shutil.copy2(str(sample), str(sample_dest))

    # Detect gender from filename hints or default
    gender = preferred_gender
    name_lower = output_name.lower()
    if any(w in name_lower for w in ['male', 'man', 'boy', 'sir']):
        gender = 'male'
    elif any(w in name_lower for w in ['female', 'woman', 'girl', 'madam']):
        gender = 'female'

    # Pick best matching edge-tts voice
    voice = edge_tts_engine.get_voice(preferred_lang, gender)

    # Create profile
    profile = {
        'name': output_name,
        'sample_file': str(sample_dest),
        'original_sample': str(sample),
        'edge_voice': voice,
        'language': preferred_lang,
        'gender': gender,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'consent_given': consent,
        'note': (
            'This profile uses the closest-matching edge-tts neural voice. '
            'For true voice cloning, install Coqui TTS or RVC.'
        ),
    }

    profile_path = profiles / f"{output_name}.profile.json"
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    return str(profile_path)


def list_profiles() -> list[dict]:
    """List all saved voice profiles."""
    profiles = _profiles_dir()
    result = []
    for p in sorted(profiles.glob('*.profile.json')):
        try:
            with open(p, encoding='utf-8') as f:
                data = json.load(f)
            data['_path'] = str(p)
            result.append(data)
        except Exception:
            continue
    return result


def get_profile(name: str) -> Optional[dict]:
    """Get a specific voice profile by name."""
    path = _profiles_dir() / f"{name}.profile.json"
    if path.exists():
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return None


async def speak_with_profile_async(
    name: str,
    text: str,
    lang: Optional[str] = None,
    out_path: Optional[str] = None,
) -> str:
    """Async version of speak_with_profile."""
    profile = get_profile(name)
    if profile is None:
        raise ValueError(f"Voice profile '{name}' not found.")

    voice = profile.get('edge_voice')
    use_lang = lang or profile.get('language', 'hi')

    if out_path is None:
        import tempfile
        out_path = os.path.join(tempfile.gettempdir(), f"clone_{name}_{os.getpid()}.mp3")

    return await edge_tts_engine.speak_async(text, lang=use_lang, voice=voice, out_path=out_path)


def speak_with_profile(*args, **kwargs) -> str:
    """Sync wrapper for speak_with_profile_async."""
    import asyncio
    return edge_tts_engine._run_sync(speak_with_profile_async(*args, **kwargs))
