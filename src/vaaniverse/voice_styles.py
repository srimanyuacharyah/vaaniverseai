"""Voice age/style presets for TTS output.

Apply pitch and rate adjustments via SSML prosody to simulate how text
would sound when spoken by a toddler, teenager, adult, or elderly person.
"""
from __future__ import annotations

from typing import Dict, Optional
import os, tempfile

from . import edge_tts_engine

# ---------------------------------------------------------------------------
# Age Presets
# ---------------------------------------------------------------------------

AGE_PRESETS: Dict[str, Dict] = {
    'toddler': {
        'id': 'toddler',
        'name': 'Toddler',
        'emoji': '👶',
        'description': 'High-pitched, baby-like voice with fast happy speech',
        'age_range': '2-4 years',
        'ssml': {'rate': '+15%', 'pitch': '+6st', 'volume': '+0%'},
        'preferred_gender': 'female',  # child-like voice
    },
    'kid': {
        'id': 'kid',
        'name': 'Kid',
        'emoji': '🧒',
        'description': 'Playful child voice, slightly high pitched',
        'age_range': '5-10 years',
        'ssml': {'rate': '+8%', 'pitch': '+4st', 'volume': '+0%'},
        'preferred_gender': 'female',
    },
    'teenager': {
        'id': 'teenager',
        'name': 'Teenager',
        'emoji': '🧑‍🎓',
        'description': 'Young, energetic voice with natural tone',
        'age_range': '13-19 years',
        'ssml': {'rate': '+3%', 'pitch': '+1st', 'volume': '+0%'},
        'preferred_gender': None,  # use whatever user picks
    },
    'adult': {
        'id': 'adult',
        'name': 'Adult',
        'emoji': '🧑‍💼',
        'description': 'Natural adult speaking voice, clear and professional',
        'age_range': '25-45 years',
        'ssml': {'rate': '+0%', 'pitch': '+0Hz', 'volume': '+0%'},
        'preferred_gender': None,
    },
    'middle_aged': {
        'id': 'middle_aged',
        'name': 'Middle-Aged',
        'emoji': '🧔',
        'description': 'Mature, deeper voice with measured pace',
        'age_range': '45-60 years',
        'ssml': {'rate': '-5%', 'pitch': '-2st', 'volume': '+3%'},
        'preferred_gender': None,
    },
    'elderly': {
        'id': 'elderly',
        'name': 'Elderly',
        'emoji': '👴',
        'description': 'Slower, deeper voice with warm grandparent quality',
        'age_range': '65+ years',
        'ssml': {'rate': '-12%', 'pitch': '-4st', 'volume': '+5%'},
        'preferred_gender': None,
    },
}


# ---------------------------------------------------------------------------
# Voice selection per language + gender
# ---------------------------------------------------------------------------

_VOICE_MAP = {
    ('hi', 'male'):   'hi-IN-MadhurNeural',
    ('hi', 'female'): 'hi-IN-SwaraNeural',
    ('en', 'male'):   'en-US-GuyNeural',
    ('en', 'female'): 'en-US-JennyNeural',
    ('ta', 'male'):   'ta-IN-ValluvarNeural',
    ('ta', 'female'): 'ta-IN-PallaviNeural',
    ('te', 'male'):   'te-IN-MohanNeural',
    ('te', 'female'): 'te-IN-ShrutiNeural',
    ('kn', 'male'):   'kn-IN-GaganNeural',
    ('kn', 'female'): 'kn-IN-SapnaNeural',
    ('ml', 'male'):   'ml-IN-MidhunNeural',
    ('ml', 'female'): 'ml-IN-SobhanaNeural',
}


def _pick_voice(lang: str, gender: str, preset_id: str) -> str:
    """Choose an edge-tts voice based on language, gender, and age preset."""
    preset = AGE_PRESETS.get(preset_id, AGE_PRESETS['adult'])
    g = preset.get('preferred_gender') or gender
    return _VOICE_MAP.get((lang, g), _VOICE_MAP.get(('en', g), 'en-US-GuyNeural'))


def list_age_presets():
    """Return a list of age presets for the frontend."""
    return [
        {k: v for k, v in p.items() if k != 'ssml'}
        for p in AGE_PRESETS.values()
    ]


async def speak_with_age_async(
    text: str,
    lang: str = 'hi',
    gender: str = 'female',
    age_preset: str = 'adult',
    out_path: Optional[str] = None,
) -> str:
    """Generate TTS audio styled with an age preset using SSML prosody.

    Returns the path to the generated MP3 file.
    """
    preset = AGE_PRESETS.get(age_preset, AGE_PRESETS['adult'])
    ssml_cfg = preset['ssml']
    voice = _pick_voice(lang, gender, age_preset)

    if out_path is None:
        out_path = os.path.join(
            tempfile.gettempdir(),
            f"age_{age_preset}_{os.getpid()}.mp3",
        )

    # Build SSML with prosody
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
        f'<voice name="{voice}">'
        f'<prosody rate="{ssml_cfg["rate"]}" pitch="{ssml_cfg["pitch"]}" volume="{ssml_cfg["volume"]}">'
        f'{text}'
        f'</prosody></voice></speak>'
    )

    try:
        communicate = edge_tts_engine.edge_tts.Communicate(ssml)
        await communicate.save(out_path)
    except Exception:
        # Fallback to non-SSML with rate/pitch params
        communicate = edge_tts_engine.edge_tts.Communicate(
            text, voice,
            rate=ssml_cfg.get('rate', '+0%'),
            pitch=ssml_cfg.get('pitch', '+0Hz'),
        )
        await communicate.save(out_path)

    return out_path
