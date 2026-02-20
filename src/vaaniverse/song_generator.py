"""Song generator with multi-language lyrics, audio output, and instrumental backing.

Supports:
- Template-based lyrics generation in Indian languages
- **Custom lyrics** — user provides their own text or description
- Audio synthesis via edge-tts (2–3 minute tracks)
- **Instrumental backing** — genre-specific configs for client-side Web Audio API
"""
from __future__ import annotations

import os
import random
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from . import edge_tts_engine

# ---------------------------------------------------------------------------
# Genre / Instrumental Presets
# ---------------------------------------------------------------------------

GENRES = {
    'bollywood': {
        'name': 'Bollywood',
        'emoji': '🎬',
        'description': 'Bollywood film-style music with tabla, sitar vibes',
        'default_bpm': 120,
        'key': 'C',
        'scale': 'minor',
        'chord_progression': ['Am', 'F', 'C', 'G'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.7, 'pattern': 'bollywood'},
            'bass': {'enabled': True, 'volume': 0.6, 'pattern': 'rhythmic'},
            'piano': {'enabled': True, 'volume': 0.5, 'pattern': 'chords'},
            'synth': {'enabled': True, 'volume': 0.4, 'pattern': 'pad'},
            'guitar': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
        },
        'effects': {'reverb': 0.4, 'delay': 0.2},
    },
    'pop': {
        'name': 'Pop',
        'emoji': '🎤',
        'description': 'Modern pop with catchy beats and synths',
        'default_bpm': 110,
        'key': 'G',
        'scale': 'major',
        'chord_progression': ['G', 'D', 'Em', 'C'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.8, 'pattern': 'pop'},
            'bass': {'enabled': True, 'volume': 0.6, 'pattern': 'walking'},
            'piano': {'enabled': True, 'volume': 0.4, 'pattern': 'arpeggiate'},
            'synth': {'enabled': True, 'volume': 0.5, 'pattern': 'lead'},
            'guitar': {'enabled': True, 'volume': 0.3, 'pattern': 'strum'},
        },
        'effects': {'reverb': 0.3, 'delay': 0.15},
    },
    'rock': {
        'name': 'Rock',
        'emoji': '🎸',
        'description': 'Powerful rock with driving guitar and drums',
        'default_bpm': 130,
        'key': 'E',
        'scale': 'minor',
        'chord_progression': ['Em', 'C', 'G', 'D'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.9, 'pattern': 'rock'},
            'bass': {'enabled': True, 'volume': 0.7, 'pattern': 'driving'},
            'piano': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
            'synth': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
            'guitar': {'enabled': True, 'volume': 0.8, 'pattern': 'power'},
        },
        'effects': {'reverb': 0.2, 'delay': 0.1},
    },
    'lofi': {
        'name': 'Lo-fi',
        'emoji': '🌙',
        'description': 'Chill lo-fi beats to relax/study to',
        'default_bpm': 75,
        'key': 'D',
        'scale': 'minor',
        'chord_progression': ['Dm7', 'G7', 'Cmaj7', 'Fmaj7'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.5, 'pattern': 'lofi'},
            'bass': {'enabled': True, 'volume': 0.4, 'pattern': 'mellow'},
            'piano': {'enabled': True, 'volume': 0.6, 'pattern': 'jazzy'},
            'synth': {'enabled': True, 'volume': 0.3, 'pattern': 'ambient'},
            'guitar': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
        },
        'effects': {'reverb': 0.6, 'delay': 0.3},
    },
    'classical': {
        'name': 'Classical',
        'emoji': '🎻',
        'description': 'Indian classical raga-inspired composition',
        'default_bpm': 90,
        'key': 'C',
        'scale': 'raga_yaman',
        'chord_progression': ['C', 'F', 'G', 'C'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.4, 'pattern': 'tabla'},
            'bass': {'enabled': True, 'volume': 0.3, 'pattern': 'tanpura'},
            'piano': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
            'synth': {'enabled': True, 'volume': 0.5, 'pattern': 'sitar'},
            'guitar': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
        },
        'effects': {'reverb': 0.5, 'delay': 0.25},
    },
    'devotional': {
        'name': 'Devotional',
        'emoji': '🙏',
        'description': 'Peaceful devotional bhajan-style music',
        'default_bpm': 80,
        'key': 'A',
        'scale': 'major',
        'chord_progression': ['A', 'D', 'E', 'A'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.3, 'pattern': 'dholak'},
            'bass': {'enabled': True, 'volume': 0.3, 'pattern': 'tanpura'},
            'piano': {'enabled': True, 'volume': 0.5, 'pattern': 'harmonium'},
            'synth': {'enabled': True, 'volume': 0.4, 'pattern': 'pad'},
            'guitar': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
        },
        'effects': {'reverb': 0.6, 'delay': 0.2},
    },
    'hiphop': {
        'name': 'Hip-Hop',
        'emoji': '🎧',
        'description': 'Trap-style hip-hop with 808 bass and crisp hi-hats',
        'default_bpm': 140,
        'key': 'F',
        'scale': 'minor',
        'chord_progression': ['Fm', 'Db', 'Ab', 'Eb'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.9, 'pattern': 'trap'},
            'bass': {'enabled': True, 'volume': 0.85, 'pattern': '808'},
            'piano': {'enabled': True, 'volume': 0.3, 'pattern': 'dark_keys'},
            'synth': {'enabled': True, 'volume': 0.5, 'pattern': 'lead'},
            'guitar': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
        },
        'effects': {'reverb': 0.2, 'delay': 0.3},
    },
    'indian_classical': {
        'name': 'Indian Classical',
        'emoji': '🪷',
        'description': 'Traditional raga with sitar, tabla and tanpura drone',
        'default_bpm': 70,
        'key': 'C',
        'scale': 'raga_bhairavi',
        'chord_progression': ['Cm', 'Fm', 'Gm', 'Cm'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.5, 'pattern': 'tabla_taal'},
            'bass': {'enabled': True, 'volume': 0.6, 'pattern': 'tanpura_drone'},
            'piano': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
            'synth': {'enabled': True, 'volume': 0.7, 'pattern': 'sitar_melody'},
            'guitar': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
        },
        'effects': {'reverb': 0.7, 'delay': 0.15},
    },
    'refreshing': {
        'name': 'Refreshing',
        'emoji': '🌊',
        'description': 'Upbeat, breezy feel-good vibes like a summer day',
        'default_bpm': 115,
        'key': 'D',
        'scale': 'major',
        'chord_progression': ['D', 'A', 'Bm', 'G'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.5, 'pattern': 'bossa'},
            'bass': {'enabled': True, 'volume': 0.4, 'pattern': 'walking'},
            'piano': {'enabled': True, 'volume': 0.6, 'pattern': 'bright_chords'},
            'synth': {'enabled': True, 'volume': 0.5, 'pattern': 'shimmer'},
            'guitar': {'enabled': True, 'volume': 0.5, 'pattern': 'acoustic_strum'},
        },
        'effects': {'reverb': 0.4, 'delay': 0.2},
    },
    'romantic': {
        'name': 'Romantic',
        'emoji': '💕',
        'description': 'Soft, dreamy love ballad with gentle piano and strings',
        'default_bpm': 85,
        'key': 'Bb',
        'scale': 'major',
        'chord_progression': ['Bb', 'Gm', 'Eb', 'F'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 0.3, 'pattern': 'soft_brush'},
            'bass': {'enabled': True, 'volume': 0.35, 'pattern': 'mellow'},
            'piano': {'enabled': True, 'volume': 0.7, 'pattern': 'ballad_arpeggiate'},
            'synth': {'enabled': True, 'volume': 0.6, 'pattern': 'strings_pad'},
            'guitar': {'enabled': True, 'volume': 0.4, 'pattern': 'fingerpick'},
        },
        'effects': {'reverb': 0.6, 'delay': 0.25},
    },
    'mass': {
        'name': 'Mass',
        'emoji': '🔥',
        'description': 'High-energy action/mass hero entry style BGM',
        'default_bpm': 150,
        'key': 'E',
        'scale': 'minor',
        'chord_progression': ['Em', 'Am', 'B7', 'Em'],
        'instruments': {
            'drums': {'enabled': True, 'volume': 1.0, 'pattern': 'heavy_action'},
            'bass': {'enabled': True, 'volume': 0.8, 'pattern': 'power_bass'},
            'piano': {'enabled': False, 'volume': 0.0, 'pattern': 'none'},
            'synth': {'enabled': True, 'volume': 0.7, 'pattern': 'brass_hit'},
            'guitar': {'enabled': True, 'volume': 0.9, 'pattern': 'distortion'},
        },
        'effects': {'reverb': 0.3, 'delay': 0.1},
    },
}

INSTRUMENT_LIST = ['drums', 'bass', 'guitar', 'piano', 'synth']

# ---------------------------------------------------------------------------
# Multilingual phrase templates  (expanded for longer songs)
# ---------------------------------------------------------------------------
_lang_phrases = {
    'hi': {
        'love': [
            "दिल मेरा", "तेरे लिए", "मुस्कान तेरी", "सपनों का सफ़र",
            "प्यार की राहों में", "तू ही मेरी मंज़िल", "तेरी आँखों में खो जाऊँ",
            "इश्क़ की बारिश", "तेरा साथ हो", "ज़िंदगी संवर जाए",
            "तुझसे मिला हूँ", "रातों की चाँदनी", "दिल की धड़कन तू",
            "तेरे बिना अधूरा", "प्यार का मौसम", "हम तुम साथ साथ",
            "चाँद सितारे तुझमें", "तेरी यादों में", "दिल ने कहा", "मोहब्बत की कहानी",
        ],
        'home': [
            "घर की राह", "सुख चैन", "माँ की दुआ", "अपना आँगन", "छत के नीचे",
            "घर की खुशबू", "बचपन की यादें", "पापा का हाथ", "अपनों का साथ",
            "गाँव की गलियाँ", "आँगन में धूप", "चूल्हे की आग", "रोटी और प्यार",
        ],
        'devotion': [
            "ॐ नमः शिवाय", "राम राम जय राम", "भक्ति की धारा", "प्रभु के चरणों में",
            "हरि ॐ", "सब ईश्वर की कृपा", "मंदिर के दीये", "श्रद्धा और विश्वास",
            "भजन सुनाओ", "कृष्ण कन्हैया", "राधे राधे", "गंगा की लहरें",
        ],
        'nature': [
            "बहती नदी", "हरे भरे मैदान", "सूरज की किरणें", "पहाड़ों की गोद",
            "बारिश की बूँदें", "फूलों की महक", "चिड़ियों का गीत", "हवा का झोंका",
            "झरने की आवाज़", "खेतों में लहलहाती फसल", "तारों भरा आसमान",
        ],
        'celebration': [
            "नाचो गाओ ख़ुशी मनाओ", "बधाई हो बधाई", "दीपों का त्योहार",
            "ढोल की थाप", "रंगों की होली", "मिठाई और खुशियाँ", "ज़िंदगी एक उत्सव",
            "सबके चेहरे पर हँसी", "गाओ मंगल गीत", "आज का दिन ख़ास है",
        ],
    },
    'kn': {
        'love': [
            "ನನ್ನ ಹೃದಯ", "ನಿನಗಾಗಿ", "ನಿನ್ನ ನಗು", "ಪ್ರೀತಿಯ ಹಾಡು", "ಮನಸ್ಸಿನ ಮಾತು",
            "ನಿನ್ನ ಕಣ್ಣಲ್ಲಿ ಕನಸು", "ಪ್ರೀತಿಯ ಮಳೆ", "ನೀನೇ ನನ್ನ ಜೀವ",
            "ಹೂವಿನ ಮುಗುಳು", "ಚಂದ್ರನ ಬೆಳಕು", "ಮನಸಿನ ಮಾಲೆ",
        ],
        'home': [
            "ಮನೆ ಮಾರ್ಗ", "ಶಾಂತಿ", "ಅಮ್ಮನ ಆಶೀರ್ವಾದ", "ಹಳ್ಳಿ ಹಸಿರು",
            "ಅಪ್ಪನ ಪ್ರೀತಿ", "ಬಾಲ್ಯದ ನೆನಪು", "ಮನೆಯ ಬೆಳಕು",
        ],
        'devotion': [
            "ಓಂ ನಮಃ ಶಿವಾಯ", "ದೇವರ ಕೃಪೆ", "ಭಕ್ತಿಯ ಹಾಡು",
            "ದೇವರ ದಯೆ", "ಪೂಜೆಯ ಹೂವು", "ಶ್ರದ್ಧೆ ಮತ್ತು ಭಕ್ತಿ",
        ],
        'nature': [
            "ಮಳೆಯ ಹನಿ", "ಹಸಿರು ಬಯಲು", "ನದಿಯ ಹರಿವು",
            "ಬೆಟ್ಟದ ಗಾಳಿ", "ಹೂವಿನ ಕಂಪು", "ಹಕ್ಕಿಗಳ ಹಾಡು",
        ],
        'celebration': [
            "ಸಂಭ್ರಮ ಸಡಗರ", "ಹಬ್ಬದ ಸಂತೋಷ", "ನಲಿವಿನ ಹಾಡು",
            "ಹಣತೆಯ ಬೆಳಕು", "ಕುಣಿದು ಹಾಡೋಣ",
        ],
    },
    'ta': {
        'love': [
            "என் இதயம்", "உனக்காக", "உன் புன்னகை", "காதல் மழை",
            "உன் கண்களில் கனவு", "நெஞ்சின் பாடல்", "காதல் நிலா",
            "உன்னோடு வாழ்க்கை", "இதயத்தின் ராகம்",
        ],
        'home': ["வீட்டின் வழி", "அமைதி", "அம்மா ஆசி", "அப்பா அன்பு", "குழந்தை நாட்கள்"],
        'devotion': ["ஓம் நமச்சிவாய", "பக்தி பாடல்", "இறை அருள்", "கோவில் மணி", "வேத ஒலி"],
        'nature': ["நீர் ஓடை", "பசுமை வெளி", "சூரிய ஒளி", "மலையின் அழகு", "பறவைகள் பாடல்"],
        'celebration': ["கொண்டாட்டம்", "திருவிழா சிறப்பு", "ஆடி பாடி கொண்டாடு"],
    },
    'te': {
        'love': [
            "నా హృదయం", "నీ కోసం", "నీ నవ్వు", "ప్రేమ వాన",
            "నీ కళ్ళలో కలలు", "మనసు పాట", "నీవే నా ప్రాణం",
        ],
        'home': ["ఇంటి దారి", "శాంతి", "అమ్మ ఆశీస్సులు", "నాన్న ప్రేమ"],
        'devotion': ["ఓం నమః శివాయ", "భక్తి గీతం", "దైవ కృప", "గుడి గంటలు"],
        'nature': ["నదీ ప్రవాహం", "పచ్చని మైదానం", "సూర్య కిరణాలు"],
        'celebration': ["ఉత్సవ సంబరం", "పండుగ సంతోషం", "ఆడి పాడి సంతోషం"],
    },
    'bn': {
        'love': ["আমার হৃদয়", "তোমার জন্য", "তোমার হাসি", "ভালোবাসার বৃষ্টি", "মনের গান"],
        'home': ["ঘরের পথ", "শান্তি", "মায়ের আশীর্বাদ", "বাবার ভালোবাসা"],
        'devotion': ["ওঁ নমঃ শিবায়", "ভক্তি গান", "ঈশ্বরের কৃপা"],
        'nature': ["নদীর ধারা", "সবুজ মাঠ", "সূর্যের আলো"],
        'celebration': ["উৎসবের আনন্দ", "নাচো গাও আনন্দে"],
    },
    'en': {
        'love': [
            "my heart", "for you", "your smile", "dreamy streets", "love without end",
            "lost in your eyes", "rain of love", "you are my world", "heartbeat song",
            "moonlight dance", "forever yours", "whisper of love", "star-crossed hearts",
            "love like the ocean", "until the end of time", "holding your hand",
        ],
        'home': ["the road home", "warm hearth", "mother's blessing", "father's embrace", "childhood days"],
        'devotion': ["divine grace", "songs of faith", "higher calling", "temple bells", "sacred chants"],
        'nature': ["flowing river", "green meadows", "golden sunrise", "mountain breeze", "birdsong melody"],
        'celebration': ["dance and rejoice", "festival of lights", "sing and celebrate", "joy of togetherness"],
    },
}

# Song structure templates for building longer songs
_song_structures = {
    'verse': "--- Verse {n} ---",
    'chorus': "--- Chorus ---",
    'bridge': "--- Bridge ---",
    'outro': "--- Outro ---",
}


def _pick_lines_for_lang(theme: str, lang: str, lines: int) -> List[str]:
    pool = []
    lang_map = _lang_phrases.get(lang, {})
    if theme in lang_map:
        pool = list(lang_map[theme])
    else:
        for vals in lang_map.values():
            pool.extend(vals)
    if not pool:
        pool = [f"({lang}) line {i+1}" for i in range(max(4, lines))]
    # Allow repeats if we need more lines than available
    chosen = []
    while len(chosen) < lines:
        batch = random.sample(pool, min(lines - len(chosen), len(pool)))
        chosen.extend(batch)
    return chosen


def generate_lyrics(theme: str = 'love', lang: str = 'hi', lines: int = 4) -> str:
    """Generate simple lyrics in *lang* for a *theme*."""
    lines_chosen = _pick_lines_for_lang(theme, lang, lines)
    chorus = lines_chosen[-1] if lines_chosen else "La la"
    body = "\n".join(lines_chosen)
    return f"{body}\n\n--- Chorus ---\n{chorus}"


def generate_long_lyrics(theme: str = 'love', lang: str = 'hi') -> str:
    """Generate a full-length song (2–3 minutes when spoken).

    Uses Gemini AI for creative lyrics when available, otherwise falls back
    to the template system producing ~25–35 lines with verse/chorus/bridge
    structure so that edge-tts synthesis lasts 2–3 minutes.
    """
    # Try AI-generated lyrics first
    try:
        from . import ai_service
        ai_lyrics = ai_service.generate_lyrics(theme=theme, lang=lang, genre='bollywood', lines=30)
        if ai_lyrics and len(ai_lyrics) > 100:
            return ai_lyrics
    except Exception:
        pass

    # Fallback: template-based generation
    verse_lines = 5
    chorus_lines = 3
    all_lines: list[str] = []

    # Verse 1
    all_lines.append(_song_structures['verse'].format(n=1))
    all_lines.extend(_pick_lines_for_lang(theme, lang, verse_lines))
    all_lines.append("")

    # Chorus
    chorus = _pick_lines_for_lang(theme, lang, chorus_lines)
    all_lines.append(_song_structures['chorus'])
    all_lines.extend(chorus)
    all_lines.append("")

    # Verse 2
    all_lines.append(_song_structures['verse'].format(n=2))
    all_lines.extend(_pick_lines_for_lang(theme, lang, verse_lines))
    all_lines.append("")

    # Chorus repeat
    all_lines.append(_song_structures['chorus'])
    all_lines.extend(chorus)
    all_lines.append("")

    # Bridge
    all_lines.append(_song_structures['bridge'])
    all_lines.extend(_pick_lines_for_lang(theme, lang, 4))
    all_lines.append("")

    # Verse 3
    all_lines.append(_song_structures['verse'].format(n=3))
    all_lines.extend(_pick_lines_for_lang(theme, lang, verse_lines))
    all_lines.append("")

    # Final Chorus
    all_lines.append(_song_structures['chorus'])
    all_lines.extend(chorus)
    all_lines.append("")

    # Outro
    all_lines.append(_song_structures['outro'])
    all_lines.extend(_pick_lines_for_lang(theme, lang, 2))

    return "\n".join(all_lines)


def generate_melody(length: int = 8) -> List[int]:
    """Generate a placeholder melody as MIDI-like note numbers."""
    base = 60
    return [base + random.choice([0, 2, 3, 5, 7, 9, 11]) for _ in range(length)]


def generate_instrumental_config(
    genre: str = 'bollywood',
    bpm: int = 0,
    instruments: Optional[Dict[str, bool]] = None,
    duration: int = 120,
) -> Dict:
    """Generate an instrumental configuration for client-side Web Audio API.

    Returns a JSON-serializable dict that the frontend uses to create
    procedural backing tracks (drums, bass, synth, guitar, piano).
    """
    preset = GENRES.get(genre, GENRES['bollywood'])

    # Use requested BPM or genre default
    actual_bpm = bpm if bpm > 0 else preset['default_bpm']

    # Start with genre default instruments, then override
    inst_config = {}
    for inst_name, inst_settings in preset['instruments'].items():
        override_enabled = instruments.get(inst_name) if instruments else None
        inst_config[inst_name] = {
            **inst_settings,
            'enabled': override_enabled if override_enabled is not None else inst_settings['enabled'],
        }

    return {
        'genre': genre,
        'genre_name': preset['name'],
        'bpm': actual_bpm,
        'key': preset['key'],
        'scale': preset['scale'],
        'chord_progression': preset['chord_progression'],
        'instruments': inst_config,
        'effects': preset['effects'],
        'duration': duration,
        'bars': max(8, duration // (60 // max(actual_bpm // 4, 1))),
    }


# ---------------------------------------------------------------------------
# Server-side instrumental WAV rendering (numpy)
# ---------------------------------------------------------------------------

NOTE_FREQS = {'C': 261.63, 'D': 293.66, 'E': 329.63, 'F': 349.23,
              'G': 392.00, 'A': 440.00, 'B': 493.88}

def _note_freq(note: str, octave: int = 4) -> float:
    base = NOTE_FREQS.get(note[0], 261.63)
    shift = octave - 4
    freq = base * (2 ** shift)
    if 'm' in note:
        freq *= 0.9438  # minor approximation
    return freq


def render_instrumental_wav(config: Dict, out_path: Optional[str] = None) -> str:
    """Render an instrumental config to an actual WAV file using numpy.

    This mirrors the Web Audio API engine but produces a real audio file.
    """
    import numpy as np
    import soundfile as sf

    sr = 44100
    bpm = config.get('bpm', 120)
    duration = min(config.get('duration', 30), 60)  # cap at 60s for speed
    chords = config.get('chord_progression', ['C', 'G', 'Am', 'F'])
    instruments = config.get('instruments', {})
    beat_dur = 60.0 / bpm
    total_samples = int(sr * duration)
    mix = np.zeros(total_samples, dtype=np.float64)

    # ── Drums ──
    if instruments.get('drums', {}).get('enabled', False):
        for i in range(int(duration / beat_dur)):
            t_start = int(i * beat_dur * sr)
            # Kick on beats 0,2
            if i % 4 in (0, 2):
                length = min(int(0.15 * sr), total_samples - t_start)
                if length > 0:
                    t = np.arange(length) / sr
                    freq = 150 * np.exp(-t * 30)  # pitch sweep down
                    kick = 0.5 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 15)
                    mix[t_start:t_start + length] += kick[:length]
            # Snare on beats 1,3
            if i % 4 in (1, 3):
                length = min(int(0.08 * sr), total_samples - t_start)
                if length > 0:
                    noise = np.random.randn(length) * 0.25 * np.exp(-np.arange(length) / sr * 30)
                    mix[t_start:t_start + length] += noise[:length]
            # Hi-hat every beat
            length = min(int(0.03 * sr), total_samples - t_start)
            if length > 0:
                hh = np.random.randn(length) * 0.12 * np.exp(-np.arange(length) / sr * 80)
                mix[t_start:t_start + length] += hh[:length]

    # ── Bass ──
    bass_vol = instruments.get('bass', {}).get('volume', 0.4)
    if instruments.get('bass', {}).get('enabled', False):
        bar_dur = beat_dur * 4
        total_bars = int(duration / bar_dur)
        for bar in range(total_bars):
            chord = chords[bar % len(chords)]
            freq = _note_freq(chord, 2)
            for beat in range(4):
                t_start = int((bar * bar_dur + beat * beat_dur) * sr)
                note_len = min(int(beat_dur * 0.8 * sr), total_samples - t_start)
                if note_len > 0:
                    t = np.arange(note_len) / sr
                    f = freq if beat % 2 == 0 else freq * 1.5
                    # Sawtooth approximation
                    wave = bass_vol * 0.3 * (2.0 * (f * t % 1.0) - 1.0) * np.exp(-t * 3)
                    mix[t_start:t_start + note_len] += wave[:note_len]

    # ── Piano / Guitar chords ──
    for inst_name in ('piano', 'guitar'):
        inst = instruments.get(inst_name, {})
        if not inst.get('enabled', False):
            continue
        vol = inst.get('volume', 0.3)
        bar_dur = beat_dur * 4
        total_bars = int(duration / bar_dur)
        wave_type = 'triangle' if inst_name == 'piano' else 'sine'
        for bar in range(total_bars):
            chord = chords[bar % len(chords)]
            base_freq = _note_freq(chord, 4)
            t_start = int(bar * bar_dur * sr)
            note_len = min(int(bar_dur * 0.95 * sr), total_samples - t_start)
            if note_len > 0:
                t = np.arange(note_len) / sr
                chord_wave = np.zeros(note_len)
                for mult in (1.0, 1.25, 1.5):  # root, 3rd, 5th
                    f = base_freq * mult
                    if wave_type == 'triangle':
                        chord_wave += (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * f * t))
                    else:
                        chord_wave += np.sin(2 * np.pi * f * t)
                envelope = np.exp(-t * 1.5)
                mix[t_start:t_start + note_len] += vol * 0.12 * chord_wave * envelope

    # ── Synth lead ──
    if instruments.get('synth', {}).get('enabled', False):
        synth_vol = instruments['synth'].get('volume', 0.3)
        scale_mults = [1, 1.125, 1.25, 1.333, 1.5, 1.667, 1.875]
        total_beats = int(duration / beat_dur)
        rng = np.random.RandomState(42)
        for i in range(total_beats):
            if rng.random() > 0.35:
                continue
            bar = i // 4
            chord = chords[bar % len(chords)]
            base_freq = _note_freq(chord, 5)
            f = base_freq * scale_mults[rng.randint(0, len(scale_mults))]
            t_start = int(i * beat_dur * sr)
            note_len = min(int(beat_dur * 0.6 * sr), total_samples - t_start)
            if note_len > 0:
                t = np.arange(note_len) / sr
                wave = np.sign(np.sin(2 * np.pi * f * t))  # square wave
                envelope = np.exp(-t * 8)
                mix[t_start:t_start + note_len] += synth_vol * 0.06 * wave * envelope

    # ── Normalize & save ──
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.85

    if out_path is None:
        out_path = os.path.join(
            tempfile.gettempdir(),
            f"song_instrumental_{os.getpid()}.wav",
        )
    sf.write(out_path, mix, sr)
    return out_path


def generate_song(theme: str = 'love', lang: str = 'hi', lines: int = 4) -> Dict:
    """Return a song dictionary with ``lyrics`` and ``melody``."""
    lyrics = generate_lyrics(theme=theme, lang=lang, lines=lines)
    melody = generate_melody()
    return {'lyrics': lyrics, 'melody': melody, 'theme': theme, 'lang': lang}


def generate_full_song(
    theme: str = 'love',
    lang: str = 'hi',
    custom_lyrics: str = '',
    genre_description: str = '',
    genre: str = 'bollywood',
    bpm: int = 0,
    instruments: Optional[Dict[str, bool]] = None,
    duration: int = 120,
) -> Dict:
    """Generate a full-length song (~2–3 min) with instrumental config.

    If *custom_lyrics* is provided, uses that text directly.
    If *genre_description* is given but no custom_lyrics, weaves the
    description into the generated structure.
    """
    if custom_lyrics and custom_lyrics.strip():
        lyrics = custom_lyrics.strip()
    elif genre_description and genre_description.strip():
        generated = generate_long_lyrics(theme=theme, lang=lang)
        lyrics = f"🎵 {genre_description.strip()}\n\n{generated}"
    else:
        lyrics = generate_long_lyrics(theme=theme, lang=lang)

    melody = generate_melody(length=24)
    instrumental = generate_instrumental_config(
        genre=genre, bpm=bpm, instruments=instruments, duration=duration,
    )

    return {
        'lyrics': lyrics,
        'melody': melody,
        'theme': theme,
        'lang': lang,
        'instrumental_config': instrumental,
    }




async def generate_song_audio_async(
    theme: str = 'love',
    lang: str = 'hi',
    lines: int = 4,
    gender: str = 'female',
    out_path: Optional[str] = None,
    custom_lyrics: str = '',
    genre_description: str = '',
    full_length: bool = False,
    genre: str = 'bollywood',
    bpm: int = 0,
    instruments: Optional[Dict[str, bool]] = None,
    duration: int = 120,
    instrumental_only: bool = False,
) -> Dict:
    """ASync version of generate_song_audio.

    When *instrumental_only* is True the function returns an instrumental
    config for the client-side Web Audio engine **without** generating any
    lyrics or edge-tts vocal audio.
    """
    instrumental_cfg = generate_instrumental_config(
        genre=genre, bpm=bpm, instruments=instruments, duration=duration,
    )

    # ── Instrumental-only mode ──────────────────────────────────────────
    if instrumental_only:
        wav_path = render_instrumental_wav(instrumental_cfg)
        return {
            'lyrics': '',
            'melody': [],
            'theme': theme,
            'lang': lang,
            'audio_path': wav_path,
            'instrumental_config': instrumental_cfg,
            'instrumental_only': True,
        }

    # ── Normal mode (vocals + instrumental) ────────────────────────────
    if full_length or custom_lyrics or genre_description:
        song = generate_full_song(
            theme=theme, lang=lang,
            custom_lyrics=custom_lyrics,
            genre_description=genre_description,
            genre=genre, bpm=bpm, instruments=instruments,
            duration=duration,
        )
    else:
        song = generate_song(theme=theme, lang=lang, lines=lines)
        song['instrumental_config'] = instrumental_cfg

    if out_path is None:
        out_path = os.path.join(tempfile.gettempdir(), f"song_{lang}_{os.getpid()}.mp3")
    
    try:
        # 1. Generate Vocal Audio (Melodic synthesis)
        vocal_path = await edge_tts_engine.speak_singing_async(song['lyrics'], lang=lang, gender=gender)
        
        # 2. Render Instrumental Backing
        inst_path = render_instrumental_wav(instrumental_cfg)
        
        # 3. Merge them with pydub
        from pydub import AudioSegment
        vocals = AudioSegment.from_file(vocal_path)
        backing = AudioSegment.from_file(inst_path)
        
        # Mix: decrease backing volume so vocals are clear
        backing = backing - 8
        vocals = vocals + 2
        
        # Match lengths (or at least ensure they overlap)
        combined = backing.overlay(vocals)
        combined.export(out_path, format="mp3")
        
        song['audio_path'] = out_path
    except Exception as e:
        song['audio_path'] = None
        song['audio_error'] = str(e)
    return song


def generate_song_audio(*args, **kwargs) -> Dict:
    """Sync wrapper for generate_song_audio_async."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        return edge_tts_engine._run_sync(generate_song_audio_async(*args, **kwargs))
    else:
        return loop.run_until_complete(generate_song_audio_async(*args, **kwargs))


def save_song(song: Dict, prefix: str = 'song') -> Dict[str, str]:
    """Save song components to disk and return paths."""
    lyrics_path = f"{prefix}.txt"
    melody_path = f"{prefix}.melody.txt"
    with open(lyrics_path, 'w', encoding='utf-8') as f:
        f.write(song['lyrics'])
    with open(melody_path, 'w', encoding='utf-8') as f:
        f.write(' '.join(map(str, song['melody'])))
    return {'lyrics': lyrics_path, 'melody': melody_path}
