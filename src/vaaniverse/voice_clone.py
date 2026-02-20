"""Voice cloning module with legendary voice presets.

True voice cloning (replicating someone's exact voice) requires heavy GPU
models (e.g., Coqui TTS, RVC).  This module provides a **voice profile**
workflow that:

1. Stores the uploaded voice sample securely.
2. Attempts to analyze basic voice characteristics (pitch → male/female).
3. Creates a voice profile that maps to the best-matching edge-tts voice.
4. Lets the user test the profile by synthesising any text.

Additionally provides **legendary voice presets** — styled edge-tts voices
with custom SSML prosody to approximate famous speaking styles.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List

from .consent import verify_consent_for_sample
from . import edge_tts_engine


class ConsentError(Exception):
    pass


# Where voice profiles are stored
_PROFILES_DIR = Path(os.environ.get('VAANIVERSE_DATA_DIR', '.')) / 'voice_profiles'


def _profiles_dir() -> Path:
    _PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return _PROFILES_DIR


# ---------------------------------------------------------------------------
# Legendary Voice Presets
# ---------------------------------------------------------------------------

LEGENDARY_VOICES: Dict[str, Dict] = {
    'spb': {
        'id': 'spb',
        'name': 'S.P. Balasubrahmanyam',
        'short_name': 'SPB',
        'description': 'Legendary playback singer with a soulful, melodious voice',
        'avatar': '🎶',
        'language': 'ta',
        'gender': 'male',
        'edge_voice': 'ta-IN-ValluvarNeural',
        'style': 'melodious',
        'ssml_config': {
            'rate': '-10%',
            'pitch': '+2st',
            'volume': '+5%',
        },
        'category': 'singer',
        'sample_text': 'இசை என் உயிர், பாடல் என் மூச்சு',
    },
    'modi': {
        'id': 'modi',
        'name': 'Narendra Modi',
        'short_name': 'Modi',
        'description': 'Prime Minister of India — powerful, emphatic Hindi speech',
        'avatar': '🇮🇳',
        'language': 'hi',
        'gender': 'male',
        'edge_voice': 'hi-IN-MadhurNeural',
        'style': 'powerful',
        'ssml_config': {
            'rate': '-15%',
            'pitch': '-2st',
            'volume': '+10%',
        },
        'category': 'leader',
        'sample_text': 'मित्रों, आइए मिलकर भारत को आगे बढ़ाएं!',
    },
    'rahul': {
        'id': 'rahul',
        'name': 'Rahul Gandhi',
        'short_name': 'Rahul G',
        'description': 'Indian politician — conversational, measured Hindi speech',
        'avatar': '🗳️',
        'language': 'hi',
        'gender': 'male',
        'edge_voice': 'hi-IN-MadhurNeural',
        'style': 'conversational',
        'ssml_config': {
            'rate': '-5%',
            'pitch': '+0st',
            'volume': '+0%',
        },
        'category': 'leader',
        'sample_text': 'हमें देश के युवाओं की बात सुननी चाहिए।',
    },
    'yogi': {
        'id': 'yogi',
        'name': 'Yogi Adityanath',
        'short_name': 'Yogi',
        'description': 'Chief Minister of Uttar Pradesh — deep, authoritative voice',
        'avatar': '🕉️',
        'language': 'hi',
        'gender': 'male',
        'edge_voice': 'hi-IN-MadhurNeural',
        'style': 'authoritative',
        'ssml_config': {
            'rate': '-20%',
            'pitch': '-4st',
            'volume': '+8%',
        },
        'category': 'leader',
        'sample_text': 'उत्तर प्रदेश का विकास हमारी प्राथमिकता है।',
    },
    'sudeepa': {
        'id': 'sudeepa',
        'name': 'Kiccha Sudeepa',
        'short_name': 'Kiccha',
        'description': 'Kannada superstar — charismatic, deep Kannada voice',
        'avatar': '🌟',
        'language': 'kn',
        'gender': 'male',
        'edge_voice': 'kn-IN-GaganNeural',
        'style': 'charismatic',
        'ssml_config': {
            'rate': '-8%',
            'pitch': '-3st',
            'volume': '+5%',
        },
        'category': 'actor',
        'sample_text': 'ನಾನು ನಿಮ್ಮ ಕಿಚ್ಚ ಸುದೀಪ, ನಿಮ್ಮೊಂದಿಗೆ ಮಾತನಾಡಲು ಸಂತೋಷವಾಗಿದೆ',
    },
}


def list_legendary_voices() -> List[Dict]:
    """Return all legendary voice presets as a list."""
    return list(LEGENDARY_VOICES.values())


def get_legendary_voice(voice_id: str) -> Optional[Dict]:
    """Get a specific legendary voice preset."""
    return LEGENDARY_VOICES.get(voice_id)


async def speak_legendary_async(
    voice_id: str,
    text: str,
    out_path: Optional[str] = None,
) -> str:
    """Speak text using a legendary voice preset with custom SSML prosody."""
    voice_preset = LEGENDARY_VOICES.get(voice_id)
    if voice_preset is None:
        raise ValueError(f"Legendary voice '{voice_id}' not found.")

    edge_voice = voice_preset['edge_voice']
    ssml_cfg = voice_preset['ssml_config']

    if out_path is None:
        import tempfile
        out_path = os.path.join(tempfile.gettempdir(), f"legendary_{voice_id}_{os.getpid()}.mp3")

    # Build custom SSML with the voice preset's prosody settings
    ssml = _build_legendary_ssml(text, edge_voice, ssml_cfg)

    try:
        communicate = edge_tts_engine.edge_tts.Communicate(ssml)
        await communicate.save(out_path)
    except Exception:
        # Fallback: use plain synthesis with the voice
        communicate = edge_tts_engine.edge_tts.Communicate(
            text, edge_voice,
            rate=ssml_cfg.get('rate', '-5%'),
            pitch=ssml_cfg.get('pitch', '+0Hz'),
        )
        await communicate.save(out_path)

    return out_path


def _build_legendary_ssml(text: str, voice: str, ssml_cfg: dict) -> str:
    """Build SSML with custom prosody for legendary voice."""
    voice_lang = 'en-US'
    if '-' in voice:
        parts = voice.split('-')
        if len(parts) >= 2:
            voice_lang = f"{parts[0]}-{parts[1]}"

    # Escape XML special chars
    safe_text = (
        text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )

    rate = ssml_cfg.get('rate', '-5%')
    pitch = ssml_cfg.get('pitch', '+0st')
    volume = ssml_cfg.get('volume', '+0%')

    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{voice_lang}">'
        f'<voice name="{voice}">'
        f'<prosody rate="{rate}" pitch="{pitch}" volume="{volume}">'
        f'{safe_text}'
        f'</prosody>'
        f'</voice>'
        f'</speak>'
    )
    return ssml


# ---------------------------------------------------------------------------
# Voice Profile Logic
# ---------------------------------------------------------------------------

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

    # Analyze audio to refine voice matching
    voice_analysis = analyze_voice_sample(str(sample_dest))

    # Use analysis to pick gender if possible
    if voice_analysis.get('estimated_gender'):
        gender = voice_analysis['estimated_gender']

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
        'voice_analysis': voice_analysis,
        'note': (
            'This profile uses the closest-matching edge-tts neural voice. '
            'For true voice cloning, install Coqui TTS or RVC.'
        ),
    }

    profile_path = profiles / f"{output_name}.profile.json"
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    return str(profile_path)


def analyze_voice_sample(sample_path: str) -> Dict:
    """Analyze a voice sample for basic characteristics.

    Attempts pitch analysis to determine male/female voice range.
    Returns analysis dict with estimated_gender, pitch_range, etc.
    """
    analysis = {
        'estimated_gender': None,
        'pitch_hz': None,
        'duration_seconds': None,
        'analysis_method': 'file_size_heuristic',
    }

    try:
        import numpy as np
        import soundfile as sf

        data, samplerate = sf.read(sample_path)
        if len(data.shape) > 1:
            data = data[:, 0]  # mono

        analysis['duration_seconds'] = round(len(data) / samplerate, 2)

        # Simple zero-crossing rate for rough pitch estimation
        zero_crossings = np.sum(np.abs(np.diff(np.sign(data))) > 0)
        zcr = zero_crossings / (2 * len(data) / samplerate)

        analysis['pitch_hz'] = round(zcr, 1)
        analysis['analysis_method'] = 'zero_crossing_rate'

        # Male voices: ~85–180 Hz, Female voices: ~165–255 Hz
        if zcr < 170:
            analysis['estimated_gender'] = 'male'
        else:
            analysis['estimated_gender'] = 'female'

    except Exception:
        # Fallback: use file size heuristic
        try:
            file_size = os.path.getsize(sample_path)
            analysis['duration_seconds'] = round(file_size / 32000, 1)  # rough for 16kHz 16-bit
        except Exception:
            pass

    return analysis


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
