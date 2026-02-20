"""Unified AI Service for Vaaniverse — Gemini-powered with graceful fallbacks.

When a GOOGLE_API_KEY (or GEMINI_API_KEY) environment variable is set, all
methods use the Gemini generative-AI API.  When it is absent, improved local
logic provides reasonable results without any external dependency.
"""
from __future__ import annotations

import os
import random
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Gemini SDK setup (optional)
# ---------------------------------------------------------------------------
_genai = None
_model = None
_API_KEY = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY') or ''

if _API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=_API_KEY)
        _genai = genai
        _model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        print(f"[ai_service] Gemini init failed: {e}")

# ---------------------------------------------------------------------------
# Language metadata
# ---------------------------------------------------------------------------
LANG_NAMES = {
    'en': 'English', 'hi': 'Hindi', 'kn': 'Kannada', 'ta': 'Tamil',
    'te': 'Telugu', 'bn': 'Bengali', 'mr': 'Marathi', 'gu': 'Gujarati',
    'ml': 'Malayalam', 'pa': 'Punjabi', 'ur': 'Urdu', 'sa': 'Sanskrit',
    'fr': 'French', 'es': 'Spanish', 'de': 'German', 'ja': 'Japanese',
    'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'pt': 'Portuguese',
}


def _lang(code: str) -> str:
    return LANG_NAMES.get(code, code)


def _ask_gemini(prompt: str, fallback: str = '') -> str:
    """Send a prompt to Gemini and return the text response."""
    if not _model:
        return fallback
    try:
        response = _model.generate_content(prompt)
        return response.text.strip() if response.text else fallback
    except Exception as e:
        print(f"[ai_service] Gemini error: {e}")
        return fallback


# ═══════════════════════════════════════════════════════════════════════════
# 1) TRANSLATION
# ═══════════════════════════════════════════════════════════════════════════

def translate(text: str, src: str = 'auto', tgt: str = 'hi') -> str:
    """Translate text using Gemini (primary) → deep-translator (fallback)."""
    if not text:
        return ''

    # Try Gemini first
    if _model:
        src_name = _lang(src) if src != 'auto' else 'the source language'
        tgt_name = _lang(tgt)
        prompt = (
            f"Translate the following text from {src_name} to {tgt_name}. "
            f"Return ONLY the translated text, nothing else.\n\n{text}"
        )
        result = _ask_gemini(prompt)
        if result and result != text:
            return result

    # Fallback: deep-translator
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source=src, target=tgt)
        return t.translate(text)
    except Exception:
        pass

    return f"[{tgt}] {text}"


def batch_translate(text: str, targets: Optional[List[str]] = None) -> Dict[str, str]:
    """Translate text into multiple target languages."""
    if targets is None:
        targets = ['hi', 'kn', 'ta', 'te', 'bn', 'mr', 'gu', 'ml', 'pa', 'ur']

    # Try bulk Gemini translation
    if _model:
        lang_list = ', '.join([_lang(t) for t in targets])
        prompt = (
            f"Translate the following text into these languages: {lang_list}.\n"
            f"Return the result as one translation per line in this exact format:\n"
            f"LANG_CODE: translated text\n\n"
            f"Text to translate: {text}"
        )
        result = _ask_gemini(prompt)
        if result:
            translations = {}
            for line in result.split('\n'):
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    code = parts[0].strip().lower()
                    translated = parts[1].strip()
                    # Match against requested targets
                    for t in targets:
                        if t in code or _lang(t).lower() in code.lower():
                            translations[t] = translated
                            break
            if len(translations) >= len(targets) // 2:
                # Fill any missing with individual calls
                for t in targets:
                    if t not in translations:
                        translations[t] = translate(text, 'auto', t)
                return translations

    # Fallback: translate individually
    return {t: translate(text, 'auto', t) for t in targets}


# ═══════════════════════════════════════════════════════════════════════════
# 2) STORY GENERATION
# ═══════════════════════════════════════════════════════════════════════════

_LOCAL_STORIES = {
    'adventure': {
        'en': """Once upon a time, in a land where mountains touched the clouds and rivers sang ancient melodies, there lived a brave young explorer named Arya. Every night, the stars would whisper tales of hidden treasures buried deep within the Enchanted Forest.

One moonlit evening, Arya discovered a glowing map tucked inside an old banyan tree. The map revealed the path to the Crystal Cave, where the legendary Moonstone waited — a gem said to grant wisdom to the pure of heart.

Armed with courage and a lantern made of fireflies, Arya ventured into the forest. Along the way, they befriended a talking peacock named Nila, who knew every secret trail.

Together, they crossed the Whispering Bridge, outsmarted the Riddle Sphinx, and finally reached the Crystal Cave. Inside, the Moonstone shimmered with a thousand colors.

"The greatest treasure," the Moonstone spoke, "is not what you find, but who you become on the journey."

Arya returned home, wiser and kinder, sharing stories that would echo through generations. And the Enchanted Forest? It continued to guard its secrets, waiting for the next brave soul.

The End.""",
    },
    'friendship': {
        'en': """In the colorful village of Rangpur, where every house was painted a different shade of the rainbow, two friends — Meera and Kabir — were inseparable.

Meera loved painting. Her canvases captured sunsets that made even the sun jealous. Kabir loved music. His flute could make flowers bloom in winter.

One day, a terrible storm swept through Rangpur, washing away all the colors from the village. The houses turned grey, the flowers wilted, and even the rainbow disappeared.

"We must bring the colors back!" declared Meera. Kabir nodded, raising his flute.

Meera painted while Kabir played. With every stroke of her brush and every note of his flute, colors slowly returned. The walls blushed pink, the grass turned emerald, and golden sunflowers sprouted.

But the rainbow remained hidden. "We need something more," whispered Meera.

Then, all the villagers joined in — the baker kneaded saffron into his bread, the weaver spun threads of indigo, and the gardener planted marigolds of amber.

Together, their combined creativity called forth the most magnificent rainbow the world had ever seen — one that never faded.

"Colors are beautiful," said the wise village elder, "but the bonds of friendship make them eternal."

The End.""",
    },
    'magic': {
        'en': """Deep in the heart of ancient Bharat, where rivers carried prayers and winds sang mantras, there existed a school unlike any other — the Vidya Mandala.

At Vidya Mandala, children didn't learn from books alone. They learned to speak with animals, to hear the stories that rain told, and to dance with firelight.

Young Diya was the newest student, shy and uncertain. "I don't have any special power," she confessed to her teacher, Guru Chandra.

Guru Chandra smiled mysteriously. "Every soul has magic, child. You just haven't discovered yours yet."

For months, Diya watched her classmates: Raj could make plants grow with a touch, Priya could paint pictures in the air with light, and little Vikram could make rivers change direction.

One evening, during the annual Festival of Stars, a darkness crept over the school. The stars began to disappear one by one, stolen by the Shadow Weaver — an ancient entity that fed on forgotten dreams.

As panic spread, Diya felt something stir inside her. She began to tell a story — softly at first, then with growing confidence. Her words became visible, glowing threads of golden light that wove through the darkness.

Every story she told — of bravery, kindness, laughter, and love — became a star that returned to the sky. The Shadow Weaver, overwhelmed by the power of stories, dissolved into nothingness.

"Your magic," Guru Chandra whispered with pride, "is the most powerful of all — the magic of storytelling."

And from that night on, Diya became the keeper of stories, ensuring no dream was ever forgotten.

The End.""",
    },
}


def generate_story(theme: str, lang: str = 'en') -> str:
    """Generate a full-length story using Gemini or local templates."""
    # Try Gemini
    if _model:
        lang_name = _lang(lang)
        prompt = (
            f"Write a beautiful, immersive children's bedtime story about '{theme}' "
            f"in {lang_name} language. The story should be:\n"
            f"- At least 250 words long (aim for 300-400 words)\n"
            f"- Have vivid descriptions and dialogue\n"
            f"- Include a moral or life lesson\n"
            f"- Be culturally rich and engaging\n"
            f"- Written entirely in {lang_name}\n"
            f"- End with 'The End' (in {lang_name})\n\n"
            f"Write the story now:"
        )
        result = _ask_gemini(prompt)
        if result and len(result) > 100:
            return result

    # Fallback: local stories
    category = 'adventure'
    theme_lower = theme.lower()
    if any(w in theme_lower for w in ['friend', 'love', 'together', 'bond']):
        category = 'friendship'
    elif any(w in theme_lower for w in ['magic', 'wizard', 'spell', 'enchant']):
        category = 'magic'

    story = _LOCAL_STORIES.get(category, _LOCAL_STORIES['adventure'])
    base = story.get('en', story.get(list(story.keys())[0]))

    if lang != 'en':
        translated = translate(base, 'en', lang)
        if translated and not translated.startswith('['):
            return translated

    return base


# ═══════════════════════════════════════════════════════════════════════════
# 3) MOOD / EMOTION DETECTION
# ═══════════════════════════════════════════════════════════════════════════

_MOOD_DATA = {
    'happy':        ('😊', 'Joyful and upbeat — radiating positivity and warmth'),
    'sad':          ('😢', 'Melancholic and emotional — a deep, reflective sadness'),
    'angry':        ('😡', 'Intense and passionate — burning with fierce emotion'),
    'calm':         ('😌', 'Peaceful and composed — a serene state of mind'),
    'energetic':    ('⚡', 'High energy and dynamic — ready to conquer the world'),
    'romantic':     ('💕', 'Romantic and tender — overflowing with love'),
    'mysterious':   ('🌙', 'Mysterious and intriguing — wrapped in enigma'),
    'inspirational':('✨', 'Inspiring and uplifting — a call to greatness'),
    'anxious':      ('😰', 'Anxious and restless — a mind in turmoil'),
    'nostalgic':    ('🥺', 'Nostalgic and wistful — yearning for the past'),
    'grateful':     ('🙏', 'Grateful and thankful — appreciating life\'s blessings'),
    'confused':     ('😵‍💫', 'Confused and uncertain — searching for clarity'),
    'neutral':      ('😐', 'Balanced and neutral — steady and composed'),
}

_MOOD_KEYWORDS = {
    'happy': ['happy', 'joy', 'excited', 'amazing', 'wonderful', 'great', 'love',
              'beautiful', 'fantastic', 'awesome', 'celebrate', 'laugh', 'smile',
              'delighted', 'cheerful', 'bliss', 'ecstatic', 'thrilled'],
    'sad': ['sad', 'cry', 'tears', 'miss', 'lost', 'alone', 'lonely', 'painful',
            'hurt', 'broken', 'depressed', 'grief', 'sorrow', 'melancholy', 'weep'],
    'angry': ['angry', 'mad', 'furious', 'hate', 'rage', 'annoying', 'frustrated',
              'irritated', 'outraged', 'livid', 'disgusted', 'hostile'],
    'calm': ['calm', 'peace', 'serene', 'quiet', 'gentle', 'soft', 'relax',
             'meditate', 'tranquil', 'soothing', 'zen', 'mindful', 'stillness'],
    'energetic': ['energy', 'power', 'strong', 'fierce', 'fast', 'wild', 'intense',
                  'fire', 'electric', 'dynamic', 'pump', 'adrenaline', 'unstoppable'],
    'romantic': ['romance', 'love', 'heart', 'darling', 'kiss', 'embrace',
                 'together', 'forever', 'passion', 'desire', 'soulmate', 'beloved'],
    'mysterious': ['mystery', 'secret', 'dark', 'shadow', 'unknown', 'hidden',
                   'fog', 'enigma', 'curious', 'eerie', 'whisper'],
    'inspirational': ['inspire', 'dream', 'hope', 'believe', 'courage', 'strength',
                      'rise', 'overcome', 'achieve', 'persevere', 'determination'],
    'anxious': ['anxious', 'worry', 'nervous', 'panic', 'stress', 'fear',
                'dread', 'uneasy', 'tense', 'restless', 'overthink'],
    'nostalgic': ['remember', 'memory', 'past', 'childhood', 'old', 'nostalgia',
                  'miss', 'used to', 'those days', 'back then', 'wish'],
    'grateful': ['grateful', 'thankful', 'blessed', 'appreciate', 'fortunate',
                 'privilege', 'gratitude', 'count blessings'],
}


def detect_mood(text: str) -> Dict:
    """Detect mood from text using Gemini or keyword analysis."""
    if not text:
        return {'mood': 'Neutral', 'emoji': '😐', 'description': 'No text provided',
                'tags': ['neutral'], 'score': 0.0}

    # Try Gemini
    if _model:
        prompt = (
            f"Analyze the emotional tone of this text and respond in this EXACT JSON-like format:\n"
            f"MOOD: <one word mood like happy, sad, angry, calm, energetic, romantic, "
            f"mysterious, inspirational, anxious, nostalgic, grateful>\n"
            f"SCORE: <confidence from 0.0 to 1.0>\n"
            f"DESCRIPTION: <one sentence describing the emotional quality>\n"
            f"TAGS: <comma separated emotional tags, 3-5 tags>\n\n"
            f"Text: {text}"
        )
        result = _ask_gemini(prompt)
        if result:
            mood_val = 'neutral'
            score = 0.8
            description = ''
            tags = []

            for line in result.split('\n'):
                line = line.strip()
                upper = line.upper()
                if upper.startswith('MOOD:'):
                    mood_val = line.split(':', 1)[1].strip().lower()
                elif upper.startswith('SCORE:'):
                    try:
                        score = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif upper.startswith('DESCRIPTION:'):
                    description = line.split(':', 1)[1].strip()
                elif upper.startswith('TAGS:'):
                    tags = [t.strip() for t in line.split(':', 1)[1].split(',')]

            emoji, default_desc = _MOOD_DATA.get(mood_val, ('🎭', 'Complex emotional state'))
            return {
                'mood': mood_val.capitalize(),
                'emoji': emoji,
                'description': description or default_desc,
                'tags': tags or [mood_val],
                'score': score,
            }

    # Fallback: keyword analysis (improved)
    text_lower = text.lower()
    scores: Dict[str, float] = {}

    for mood, keywords in _MOOD_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        # Weight by how many keywords matched relative to total
        scores[mood] = count / max(len(keywords) * 0.3, 1)

    best_mood = max(scores, key=scores.get) if max(scores.values()) > 0 else 'neutral'
    best_score = min(scores.get(best_mood, 0), 1.0)

    if best_mood == 'neutral' or best_score < 0.05:
        return {
            'mood': 'Neutral', 'emoji': '😐',
            'description': 'Balanced and neutral — no strong emotional markers detected',
            'tags': ['neutral', 'balanced'], 'score': 0.3,
        }

    emoji, desc = _MOOD_DATA.get(best_mood, ('🎭', 'Detected emotional state'))
    tags = [best_mood] + [kw for kw in _MOOD_KEYWORDS.get(best_mood, []) if kw in text_lower][:4]

    return {
        'mood': best_mood.capitalize(),
        'emoji': emoji,
        'description': desc,
        'tags': tags,
        'score': round(best_score, 2),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4) SONG LYRICS GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_lyrics(theme: str, lang: str = 'hi', genre: str = 'bollywood',
                    lines: int = 25) -> str:
    """Generate song lyrics using Gemini or improved template system."""
    lang_name = _lang(lang)

    if _model:
        prompt = (
            f"Write original song lyrics in {lang_name} language about '{theme}'.\n"
            f"Genre: {genre}\n"
            f"Requirements:\n"
            f"- Write approximately {lines} lines\n"
            f"- Include verse/chorus/bridge structure with markers like:\n"
            f"  --- Verse 1 ---\n  --- Chorus ---\n  --- Bridge ---\n  --- Outro ---\n"
            f"- Make the lyrics emotional, poetic, and singable\n"
            f"- Write entirely in {lang_name} (use the native script)\n"
            f"- Include rhyming where natural\n\n"
            f"Write the lyrics now:"
        )
        result = _ask_gemini(prompt)
        if result and len(result) > 50:
            return result

    # Fallback to None — caller should use the existing template system
    return ''


# ═══════════════════════════════════════════════════════════════════════════
# 5) SENTIMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def analyze_sentiment(text: str) -> Dict:
    """Analyze emotional tone of text using Gemini or local logic."""
    if not text:
        return {'sentiment': 'Neutral', 'score': 0.0}

    if _model:
        prompt = (
            f"Analyze the sentiment of the following text.\n"
            f"Respond in this exact format:\n"
            f"SENTIMENT: <one of: Joyful, Melancholic, Passionate, Calm, Energetic, "
            f"Romantic, Mysterious, Inspirational, Anxious, Nostalgic, Grateful, Neutral>\n"
            f"SCORE: <confidence from 0.0 to 1.0>\n"
            f"EXPLANATION: <brief explanation>\n\n"
            f"Text: {text}"
        )
        result = _ask_gemini(prompt)
        if result:
            sentiment = 'Neutral'
            score = 0.5
            explanation = ''
            for line in result.split('\n'):
                line = line.strip()
                upper = line.upper()
                if upper.startswith('SENTIMENT:'):
                    sentiment = line.split(':', 1)[1].strip()
                elif upper.startswith('SCORE:'):
                    try:
                        score = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif upper.startswith('EXPLANATION:'):
                    explanation = line.split(':', 1)[1].strip()
            return {'sentiment': sentiment, 'score': score, 'explanation': explanation}

    # Fallback: use mood detection
    mood = detect_mood(text)
    return {
        'sentiment': mood['mood'],
        'score': mood['score'],
        'explanation': mood['description'],
    }


# ═══════════════════════════════════════════════════════════════════════════
# Status check
# ═══════════════════════════════════════════════════════════════════════════

def is_gemini_available() -> bool:
    return _model is not None
