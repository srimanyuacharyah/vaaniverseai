import os
import sys
sys.path.insert(0, 'src')

from vaaniverse import translation, song_generator, voice_clone, tts


def test_translate_fallback():
    out = translation.translate('Hello', src='en', tgt='hi')
    assert isinstance(out, str)


def test_generate_song_structure():
    song = song_generator.generate_song(theme='love', lang='hi')
    assert isinstance(song, dict)
    assert 'lyrics' in song and 'melody' in song
    assert isinstance(song['lyrics'], str)
    assert isinstance(song['melody'], list)


def test_voice_clone_consent(tmp_path):
    sample = tmp_path / 'sample.wav'
    sample.write_bytes(b'RIFF')
    # without consent, should raise
    try:
        voice_clone.clone_voice(str(sample), 'xvoice', consent=False)
        raised = False
    except Exception:
        raised = True
    assert raised
    # with consent should return a path string
    out = voice_clone.clone_voice(str(sample), 'xvoice2', consent=True)
    assert isinstance(out, str)


def test_list_voices_returns_iterable():
    v = tts.list_voices()
    assert hasattr(v, '__iter__')
