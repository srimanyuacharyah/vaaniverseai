"""Song generator with multi-language lyrics and audio output.

Supports:
- Template-based lyrics generation in Indian languages
- **Custom lyrics** — user provides their own text or description
- Audio synthesis via edge-tts (2–3 minute tracks)
"""
from __future__ import annotations

import os
import random
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from . import edge_tts_engine

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

    Produces ~25–35 lines with verse/chorus/bridge structure so that
    edge-tts synthesis lasts 2–3 minutes.
    """
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
) -> Dict:
    """Generate a full-length song (~2–3 min).

    If *custom_lyrics* is provided, uses that text directly.
    If *genre_description* is given but no custom_lyrics, weaves the
    description into the generated structure.
    """
    if custom_lyrics and custom_lyrics.strip():
        # User provided their own lyrics — use them as-is
        lyrics = custom_lyrics.strip()
    elif genre_description and genre_description.strip():
        # Use the description as a creative seed — prepend it, then generate
        generated = generate_long_lyrics(theme=theme, lang=lang)
        lyrics = f"🎵 {genre_description.strip()}\n\n{generated}"
    else:
        lyrics = generate_long_lyrics(theme=theme, lang=lang)

    melody = generate_melody(length=24)  # longer melody
    return {'lyrics': lyrics, 'melody': melody, 'theme': theme, 'lang': lang}


async def generate_song_audio_async(
    theme: str = 'love',
    lang: str = 'hi',
    lines: int = 4,
    gender: str = 'female',
    out_path: Optional[str] = None,
    custom_lyrics: str = '',
    genre_description: str = '',
    full_length: bool = False,
) -> Dict:
    """ASync version of generate_song_audio."""
    if full_length or custom_lyrics or genre_description:
        song = generate_full_song(
            theme=theme, lang=lang,
            custom_lyrics=custom_lyrics,
            genre_description=genre_description,
        )
    else:
        song = generate_song(theme=theme, lang=lang, lines=lines)

    if out_path is None:
        out_path = os.path.join(tempfile.gettempdir(), f"song_{lang}_{os.getpid()}.mp3")
    try:
        # Synthesize the lyrics as a melodious song (awaiting the async version)
        audio = await edge_tts_engine.speak_singing_async(song['lyrics'], lang=lang, gender=gender, out_path=out_path)
        song['audio_path'] = audio
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
        # This is a bit risky but we keep it for backward compatibility if someone calls it from sync
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
