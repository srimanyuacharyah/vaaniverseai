"""Audio editor — signal-processing effects for uploaded audio.

Uses numpy + soundfile for pitch shifting and normalization.
No external heavy models required.
"""
from __future__ import annotations

import os
import tempfile
from typing import Dict, Optional

import numpy as np
import soundfile as sf


# ---------------------------------------------------------------------------
# Effects catalogue (shown in UI)
# ---------------------------------------------------------------------------

EFFECTS = {
    'pitch_up': {
        'id': 'pitch_up',
        'name': 'Chipmunk / Higher Voice',
        'emoji': '🐿️',
        'description': 'Raise pitch to make voice sound higher or child-like',
        'params': {'semitones': 4},
    },
    'pitch_down': {
        'id': 'pitch_down',
        'name': 'Deep / Lower Voice',
        'emoji': '🗿',
        'description': 'Lower pitch for a deeper, bass-like voice',
        'params': {'semitones': -4},
    },
    'speed_up': {
        'id': 'speed_up',
        'name': 'Speed Up',
        'emoji': '⏩',
        'description': 'Make the audio play faster',
        'params': {'factor': 1.3},
    },
    'slow_down': {
        'id': 'slow_down',
        'name': 'Slow Down',
        'emoji': '🐌',
        'description': 'Make the audio play slower',
        'params': {'factor': 0.75},
    },
    'enhance': {
        'id': 'enhance',
        'name': 'Enhance / Normalize',
        'emoji': '✨',
        'description': 'Boost audio levels and normalize volume',
        'params': {},
    },
    'echo': {
        'id': 'echo',
        'name': 'Echo Effect',
        'emoji': '🏔️',
        'description': 'Add an echo / reverb trail to the audio',
        'params': {'delay_ms': 250, 'decay': 0.4},
    },
    'reverse': {
        'id': 'reverse',
        'name': 'Reverse Audio',
        'emoji': '🔄',
        'description': 'Play the audio backwards',
        'params': {},
    },
    'robot': {
        'id': 'robot',
        'name': 'Robot Voice',
        'emoji': '🤖',
        'description': 'Robotic / metallic voice effect with modulation',
        'params': {'mod_freq': 50},
    },
}


def list_effects():
    """Return effect metadata for the frontend."""
    return list(EFFECTS.values())


# ---------------------------------------------------------------------------
# Core processing functions
# ---------------------------------------------------------------------------

def _read_audio(file_path: str):
    """Read audio file and return (data, samplerate)."""
    data, sr = sf.read(file_path, dtype='float64')
    return data, sr


def _write_audio(data, sr: int, out_path: str):
    """Write audio data to file."""
    sf.write(out_path, data, sr)
    return out_path


def pitch_shift(data, sr: int, semitones: int = 4):
    """Shift pitch by resampling (changes speed as side-effect for simplicity)."""
    factor = 2 ** (semitones / 12.0)
    # Resample: change playback rate
    indices = np.round(np.arange(0, len(data), factor)).astype(int)
    indices = indices[indices < len(data)]
    return data[indices]


def speed_change(data, sr: int, factor: float = 1.3):
    """Change playback speed by resampling."""
    indices = np.round(np.arange(0, len(data), factor)).astype(int)
    indices = indices[indices < len(data)]
    return data[indices]


def normalize(data):
    """Normalize audio to maximize volume without clipping."""
    peak = np.max(np.abs(data))
    if peak > 0:
        return data / peak * 0.95
    return data


def add_echo(data, sr: int, delay_ms: int = 250, decay: float = 0.4):
    """Add echo by mixing delayed copy."""
    delay_samples = int(sr * delay_ms / 1000)
    echo = np.zeros(len(data) + delay_samples)
    echo[:len(data)] = data
    if data.ndim == 1:
        echo[delay_samples:delay_samples + len(data)] += data * decay
    else:
        echo[delay_samples:delay_samples + len(data)] += data * decay
    # Trim or keep extended length
    return echo


def reverse_audio(data):
    """Reverse audio data."""
    return data[::-1].copy()


def robot_voice(data, sr: int, mod_freq: int = 50):
    """Apply ring modulation for a robotic effect."""
    t = np.arange(len(data)) / sr
    if data.ndim == 2:
        modulator = np.sin(2 * np.pi * mod_freq * t)[:, np.newaxis]
    else:
        modulator = np.sin(2 * np.pi * mod_freq * t)
    return data * modulator


# ---------------------------------------------------------------------------
# Main process function
# ---------------------------------------------------------------------------

def process_audio(
    file_path: str,
    effect_id: str,
    custom_params: Optional[Dict] = None,
    out_path: Optional[str] = None,
) -> str:
    """Apply an effect to an audio file and return the output path.

    Parameters
    ----------
    file_path : str
        Path to the input audio file (WAV/MP3/OGG).
    effect_id : str
        One of the keys in EFFECTS.
    custom_params : dict, optional
        Override default effect parameters.
    out_path : str, optional
        Output file path.  Auto-generated in temp dir if not given.

    Returns
    -------
    str
        Path to the processed audio file.
    """
    if effect_id not in EFFECTS:
        raise ValueError(f"Unknown effect: {effect_id}")

    effect = EFFECTS[effect_id]
    params = {**effect['params'], **(custom_params or {})}

    data, sr = _read_audio(file_path)

    if effect_id == 'pitch_up':
        data = pitch_shift(data, sr, semitones=params.get('semitones', 4))
    elif effect_id == 'pitch_down':
        data = pitch_shift(data, sr, semitones=params.get('semitones', -4))
    elif effect_id == 'speed_up':
        data = speed_change(data, sr, factor=params.get('factor', 1.3))
    elif effect_id == 'slow_down':
        data = speed_change(data, sr, factor=params.get('factor', 0.75))
    elif effect_id == 'enhance':
        data = normalize(data)
    elif effect_id == 'echo':
        data = add_echo(data, sr, delay_ms=params.get('delay_ms', 250), decay=params.get('decay', 0.4))
    elif effect_id == 'reverse':
        data = reverse_audio(data)
    elif effect_id == 'robot':
        data = robot_voice(data, sr, mod_freq=params.get('mod_freq', 50))

    # Normalize output to prevent clipping
    data = normalize(data)

    if out_path is None:
        out_path = os.path.join(
            tempfile.gettempdir(),
            f"edited_{effect_id}_{os.getpid()}.wav",
        )

    return _write_audio(data, sr, out_path)
