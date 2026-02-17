import random
from typing import Dict, List

# Simple multilingual word fragments for Indian languages (placeholder)
_lang_phrases = {
    'hi': {
        'love': ["दिल मेरा", "तेरे लिए", "मुस्कान तेरी", "सपनों का सफ़र"],
        'home': ["घर की राह", "सुख चैन", "माँ की दुआ"],
    },
    'kn': {
        'love': ["ನನ್ನ ಹೃದಯ", "ನಿನಗಾಗಿ", "ನಿನ್ನ ನಗು"],
        'home': ["ಮನೆ ಮಾರ್ಗ", "ಶಾಂತಿ", "ಅಮ್ಮನ ಆಶೀರ್ವಾದ"],
    },
    'en': {
        'love': ["my heart", "for you", "your smile", "dreamy streets"],
    }
}


def _pick_lines_for_lang(theme: str, lang: str, lines: int) -> List[str]:
    pool = []
    lang_map = _lang_phrases.get(lang, {})
    if theme in lang_map:
        pool = lang_map[theme]
    else:
        # fallback: collect any available phrases
        for vals in lang_map.values():
            pool.extend(vals)
    if not pool:
        pool = [f"({lang}) line {i+1}" for i in range(max(4, lines))]
    chosen = random.sample(pool, min(lines, len(pool)))
    return chosen


def generate_lyrics(theme: str = 'love', lang: str = 'hi', lines: int = 4) -> str:
    """Generate simple lyrics in `lang` for a `theme`.

    This is a placeholder generator meant to demonstrate structure and
    multilingual capability. Replace with a trained language model for
    production-quality lyrics.
    """
    lines_chosen = _pick_lines_for_lang(theme, lang, lines)
    chorus = lines_chosen[-1] if lines_chosen else "La la"
    body = "\n".join(lines_chosen)
    return f"{body}\n\nChorus: {chorus}"


def generate_melody(length: int = 8) -> List[int]:
    """Generate a placeholder melody as a sequence of MIDI-like note numbers.

    This is a toy melody generator; replace with a proper melody model or
    symbolic music generator for real use.
    """
    base = 60  # middle C
    return [base + random.choice([0,2,3,5,7,9,11]) for _ in range(length)]


def generate_song(theme: str = 'love', lang: str = 'hi', lines: int = 4) -> Dict:
    """Return a song dictionary with `lyrics` and `melody`.

    Keys: 'lyrics' (str), 'melody' (List[int])
    """
    lyrics = generate_lyrics(theme=theme, lang=lang, lines=lines)
    melody = generate_melody()
    return {'lyrics': lyrics, 'melody': melody}


def save_song(song: Dict, prefix: str = 'song') -> Dict[str, str]:
    """Save song components to disk and return paths.

    Writes `prefix`.txt for lyrics and `prefix`.melody.txt for melody data.
    """
    lyrics_path = f"{prefix}.txt"
    melody_path = f"{prefix}.melody.txt"
    with open(lyrics_path, 'w', encoding='utf-8') as f:
        f.write(song['lyrics'])
    with open(melody_path, 'w', encoding='utf-8') as f:
        f.write(' '.join(map(str, song['melody'])))
    return {'lyrics': lyrics_path, 'melody': melody_path}
