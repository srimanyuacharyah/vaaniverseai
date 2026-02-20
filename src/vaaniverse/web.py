"""Vaaniverse AI — FastAPI web application.

Provides a modern web UI for translation, text-to-speech, voice
translation (text + audio upload), song generation (custom lyrics + instrumentals),
voice cloning, and legendary voice features.
"""
from __future__ import annotations

import json
import asyncio
import shutil
import os
from pathlib import Path

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from vaaniverse import translation, tts, song_generator, voice_clone
from vaaniverse import voice_models, config, edge_tts_engine, voice_translator
from vaaniverse import consent as consent_mod
from vaaniverse import job_queue
from vaaniverse import voice_styles, audio_editor, auth, database as db
from vaaniverse import ai_service
import tempfile

app = FastAPI(title="Vaaniverse AI")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount('/static', StaticFiles(directory=str(Path(__file__).parent / 'static')), name='static')

# ── Server-Side Auth Middleware ─────────────────────────────────────────────
PUBLIC_PATHS = {'/', '/login', '/register', '/me', '/docs', '/openapi.json'}
PUBLIC_PREFIXES = ('/static/',)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse as StarletteJSON

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Allow public paths
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)
        # Check auth token
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            # Check query param fallback
            token = request.query_params.get('token', '')
        if not token:
            return StarletteJSON({'ok': False, 'error': 'Authentication required'}, status_code=401)
        user = auth.get_current_user(token)
        if not user:
            return StarletteJSON({'ok': False, 'error': 'Invalid or expired token'}, status_code=401)
        # Attach user to request state
        request.state.user = user
        return await call_next(request)

app.add_middleware(AuthMiddleware)


# ── Pages ───────────────────────────────────────────────────────────────────

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    backends = ['edge', 'local']
    if voice_models.is_coqui_available():
        backends.append('coqui')
    cons = consent_mod.list_consents()
    jobs = job_queue.manager.list()
    return templates.TemplateResponse('index.html', {
        'request': request,
        'backends': backends,
        'coqui_model': config.cfg.coqui_model,
        'consents': cons,
        'jobs': jobs,
        'languages': translation.ALL_LANGUAGES,
        'indian_languages': translation.INDIAN_LANGUAGES,
        'voices': edge_tts_engine.VOICE_MAP,
        'sr_available': voice_translator.is_speech_recognition_available(),
        'genres': song_generator.GENRES,
        'instruments': song_generator.INSTRUMENT_LIST,
        'legendary_voices': voice_clone.list_legendary_voices(),
        'age_presets': voice_styles.list_age_presets(),
        'audio_effects': audio_editor.list_effects(),
    })


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_user_from_request(request: Request) -> Optional[Dict]:
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.cookies.get('vaaniverse_token', '')
    return auth.get_current_user(token)


def _save_history(request: Request, entry_type: str, title: str, data: Dict = None, audio_path: str = ''):
    user = _get_user_from_request(request)
    if user:
        try:
            db.save_history(user['id'], entry_type, title=title, data=data, audio_path=audio_path)
        except Exception as e:
            print(f"Error saving history: {e}")


# ── Translation ─────────────────────────────────────────────────────────────

@app.post('/translate')
def web_translate(request: Request, text: str = Form(...), src: str = Form('auto'), tgt: str = Form('hi')):
    out = ai_service.translate(text, src=src, tgt=tgt)
    _save_history(request, 'translate', text[:30], {'original': text, 'translated': out, 'src': src, 'tgt': tgt})
    return JSONResponse({'original': text, 'translated': out, 'src': src, 'tgt': tgt})


@app.post('/batch-translate')
def web_batch_translate(text: str = Form(...)):
    results = ai_service.batch_translate(text)
    return JSONResponse({'original': text, 'translations': results})


import tempfile

# ── Text-to-Speech ──────────────────────────────────────────────────────────

@app.post('/speak')
@app.post('/tts')
async def web_speak(request: Request, text: str = Form(...), lang: str = Form('hi'), gender: str = Form('female'), backend: str = Form('edge')):
    out_path = os.path.join(tempfile.gettempdir(), f"spoken_{lang}_{os.getpid()}.mp3")
    try:
        if backend == 'edge':
            await edge_tts_engine.speak_async(text, lang=lang, out_path=out_path, gender=gender)
        else:
            tts.speak(text, lang=lang, out_path=out_path, gender=gender, backend=backend)
        
        # Save to history
        _save_history(request, 'tts', text[:30], {'text': text, 'lang': lang, 'gender': gender}, out_path)
        return FileResponse(out_path, media_type='audio/mpeg', filename=f'vaaniverse_{lang}.mp3')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# ── Voice Translation ──────────────────────────────────────────────────────

@app.post('/voice-translate')
async def web_voice_translate(
    request: Request,
    text: str = Form(...),
    src_lang: str = Form('en'),
    tgt_lang: str = Form('hi'),
    gender: str = Form('female'),
):
    try:
        result = await voice_translator.translate_voice_async(
            text, src_lang=src_lang, tgt_lang=tgt_lang, gender=gender,
        )
        audio_path = result.get('audio_path')
        if audio_path and os.path.exists(audio_path):
            import urllib.parse
            _save_history(request, 'voice_translate', text[:30], {'text': text, 'translated': result['translated']}, audio_path)
            response = FileResponse(audio_path, media_type='audio/mpeg', filename=f'translated_{tgt_lang}.mp3')
            response.headers['X-Translated-Text'] = urllib.parse.quote(result['translated'])
            return response
        return JSONResponse({'error': 'Audio generation failed', 'translated': result.get('translated', '')}, status_code=500)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/voice-translate-audio')
async def web_voice_translate_audio(
    request: Request,
    file: UploadFile = File(...),
    src_lang: str = Form('auto'),
    tgt_lang: str = Form('hi'),
    gender: str = Form('female'),
):
    """Upload an audio file → transcribe → translate → re-speak."""
    tmp = Path(tempfile.gettempdir()) / "vaaniverse_uploads"
    tmp.mkdir(exist_ok=True)
    dest = tmp / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    try:
        result = await voice_translator.translate_voice_from_audio_async(
            str(dest), src_lang=src_lang, tgt_lang=tgt_lang, gender=gender,
        )
        audio_path = result.get('audio_path')
        if audio_path and os.path.exists(audio_path):
            import urllib.parse
            _save_history(request, 'voice_translate_audio', file.filename, {'transcribed': result.get('transcribed'), 'translated': result.get('translated')}, audio_path)
            response = FileResponse(audio_path, media_type='audio/mpeg', filename=f'translated_{tgt_lang}.mp3')
            response.headers['X-Transcribed-Text'] = urllib.parse.quote(result.get('transcribed', ''))
            response.headers['X-Translated-Text'] = urllib.parse.quote(result.get('translated', ''))
            return response
        return JSONResponse({
            'error': 'Audio generation failed',
            'transcribed': result.get('transcribed', ''),
            'translated': result.get('translated', ''),
        }, status_code=500)
    except ValueError as e:
        # User error: bad audio, unrecognizable speech
        return JSONResponse({'error': str(e)}, status_code=400)
    except Exception as e:
        # Server error: ffmpeg missing, other crashes
        print(f"Error in voice-translate-audio: {e}") # Log it
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/voice-translate-text')
async def web_voice_translate_text(
    text: str = Form(...),
    src_lang: str = Form('en'),
    tgt_lang: str = Form('hi'),
):
    translated = translation.translate(text, src=src_lang, tgt=tgt_lang)
    return JSONResponse({'original': text, 'translated': translated, 'tgt_lang': tgt_lang})


# ── Song Generation ─────────────────────────────────────────────────────────

@app.get('/genres')
def get_genres():
    """Return all available genre presets."""
    return JSONResponse({'genres': song_generator.GENRES})


@app.post('/generate-song')
async def web_generate_song(
    request: Request,
    theme: str = Form('love'),
    lang: str = Form('hi'),
    gender: str = Form('female'),
    with_audio: str = Form('on'),
    custom_lyrics: str = Form(''),
    genre_description: str = Form(''),
    full_length: str = Form('on'),
    genre: str = Form('bollywood'),
    bpm: int = Form(0),
    instruments_drums: str = Form('on'),
    instruments_bass: str = Form('on'),
    instruments_guitar: str = Form('off'),
    instruments_piano: str = Form('on'),
    instruments_synth: str = Form('on'),
    duration: int = Form(120),
    instrumental_only: str = Form('off'),
):
    is_full = full_length == 'on'
    has_custom = bool(custom_lyrics.strip()) or bool(genre_description.strip())
    is_instrumental = instrumental_only == 'on'

    # Parse instrument toggles
    instruments = {
        'drums': instruments_drums == 'on',
        'bass': instruments_bass == 'on',
        'guitar': instruments_guitar == 'on',
        'piano': instruments_piano == 'on',
        'synth': instruments_synth == 'on',
    }

    if with_audio == 'on' or is_instrumental:
        song = await song_generator.generate_song_audio_async(
            theme=theme, lang=lang, gender=gender,
            custom_lyrics=custom_lyrics,
            genre_description=genre_description,
            full_length=(is_full or has_custom),
            genre=genre, bpm=bpm, instruments=instruments,
            duration=duration,
            instrumental_only=is_instrumental,
        )
    else:
        song = song_generator.generate_full_song(
            theme=theme, lang=lang,
            custom_lyrics=custom_lyrics,
            genre_description=genre_description,
            genre=genre, bpm=bpm, instruments=instruments,
            duration=duration,
        )

    _save_history(request, 'song', song.get('theme', theme), {
        'lyrics': song['lyrics'],
        'has_audio': song.get('audio_path') is not None,
    }, song.get('audio_path', ''))

    return JSONResponse({
        'ok': True,
        'lyrics': song['lyrics'],
        'melody': song['melody'],
        'theme': song.get('theme', theme),
        'lang': song.get('lang', lang),
        'audio_path': f"/song-audio?lang={song.get('lang', lang)}&t={os.getpid()}",
        'has_audio': song.get('audio_path') is not None,
        'instrumental_config': song.get('instrumental_config', {}),
        'instrumental_only': song.get('instrumental_only', False),
    })


@app.post('/sing-lyrics')
async def web_sing_lyrics(
    request: Request,
    lyrics: str = Form(...),
    lang: str = Form('hi'),
    gender: str = Form('female'),
    genre: str = Form('bollywood'),
    bpm: int = Form(0),
):
    """Re-sing existing lyrics with instrumental backing."""
    try:
        song = await song_generator.generate_song_audio_async(
            custom_lyrics=lyrics,
            lang=lang,
            gender=gender,
            genre=genre,
            bpm=bpm,
            full_length=True
        )
        
        _save_history(request, 'sing_lyrics', 'Re-sing Lyrics', {'lang': lang}, song.get('audio_path', ''))
        
        return JSONResponse({
            'ok': True,
            'audio_path': f"/song-audio?lang={lang}&t={os.getpid()}",
            'has_audio': song.get('audio_path') is not None
        })
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=400)


@app.post('/generate-story')
async def web_generate_story(request: Request, theme: str = Form(...), lang: str = Form(...)):
    """Generate a bedtime story with AI narration."""
    user = getattr(request.state, 'user', None)
    if not user:
        return JSONResponse({'error': 'Login required'}, status_code=401)

    story_text = ai_service.generate_story(theme=theme, lang=lang)

    _save_history(request, 'story', f"Story about {theme}", {'text': story_text[:200]})

    return JSONResponse({'ok': True, 'text': story_text})


@app.post('/analyze-sentiment')
async def web_analyze_sentiment(request: Request, text: str = Form(...)):
    """Analyze emotional tone of text."""
    user = getattr(request.state, 'user', None)
    if not user:
        return JSONResponse({'error': 'Login required'}, status_code=401)

    result = ai_service.analyze_sentiment(text)

    _save_history(request, 'sentiment', f"Analysis: {text[:20]}...", {'sentiment': result.get('sentiment', 'Neutral')})

    return JSONResponse({
        'ok': True,
        'sentiment': result.get('sentiment', 'Neutral'),
        'score': result.get('score', 0.5),
        'explanation': result.get('explanation', ''),
    })


@app.get('/song-audio')
def get_song_audio(lang: str = 'hi'):
    import tempfile as _tmp, glob
    tmp = _tmp.gettempdir()
    # Look for vocal MP3s and instrumental WAVs
    files = []
    for pattern in [
        os.path.join(tmp, f"song_{lang}_*.mp3"),
        os.path.join(tmp, "song_instrumental_*.wav"),
    ]:
        files.extend(glob.glob(pattern))
    files = sorted(files, key=os.path.getmtime, reverse=True)
    if files:
        f = files[0]
        media = 'audio/wav' if f.endswith('.wav') else 'audio/mpeg'
        return FileResponse(f, media_type=media, filename=os.path.basename(f))
    return JSONResponse({'error': 'No audio found'}, status_code=404)


# ── Voice Cloning ───────────────────────────────────────────────────────────

@app.post('/clone-voice')
async def web_clone_voice(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    consent: str = Form(None),
    lang: str = Form('hi'),
    gender: str = Form('female'),
):
    tmp = Path(tempfile.gettempdir()) / "vaaniverse_uploads"
    tmp.mkdir(exist_ok=True)
    dest = tmp / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    try:
        if consent == 'on':
            consent_mod.make_consent(str(dest), signer=name, notes='Recorded via web UI')
        out = voice_clone.clone_voice(
            str(dest), name, consent=(consent == 'on'),
            preferred_lang=lang, preferred_gender=gender,
        )
        profile = voice_clone.get_profile(name)
        _save_history(request, 'clone', name, {'profile': profile}, str(dest))
        return JSONResponse({
            'success': True,
            'profile_path': out,
            'profile': profile,
        })
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)


@app.post('/upload-recording')
async def web_upload_recording(
    file: UploadFile = File(...),
    name: str = Form('recording'),
):
    """Save an in-browser recorded audio file."""
    tmp = Path(tempfile.gettempdir()) / "vaaniverse_uploads"
    tmp.mkdir(exist_ok=True)
    dest = tmp / f"{name}.webm"
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    return JSONResponse({
        'success': True,
        'path': str(dest),
        'filename': f"{name}.webm",
    })


@app.get('/voice-profiles')
async def web_voice_profiles():
    profiles = voice_clone.list_profiles()
    return JSONResponse({'profiles': profiles})


@app.post('/speak-with-profile')
async def web_speak_with_profile(
    request: Request,
    name: str = Form(...),
    text: str = Form(...),
    lang: str = Form(''),
):
    try:
        audio = await voice_clone.speak_with_profile_async(name, text, lang=lang or None)
        _save_history(request, 'clone_speak', name, {'text': text}, audio)
        return FileResponse(audio, media_type='audio/mpeg', filename=f'clone_{name}.mp3')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)


# ── Legendary Voices ───────────────────────────────────────────────────────

@app.get('/legendary-voices')
def get_legendary_voices():
    """Return all legendary voice presets."""
    return JSONResponse({'voices': voice_clone.list_legendary_voices()})


@app.post('/speak-legendary')
async def web_speak_legendary(
    voice_id: str = Form(...),
    text: str = Form(...),
    auto_translate: str = Form('off'),
):
    """Speak text using a legendary voice preset."""
    try:
        if auto_translate == 'on':
            # Get target language from voice ID
            profile = voice_clone.LEGENDARY_VOICES.get(voice_id)
            tgt = 'hi'  # default fallback
            if profile:
                # Heuristic: map profile language code
                tgt = profile.get('language', 'hi')
            
            text = translation.translate(text, src='auto', tgt=tgt)
            
        audio = await voice_clone.speak_legendary_async(voice_id, text)
        return FileResponse(audio, media_type='audio/mpeg', filename=f'legendary_{voice_id}.mp3')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)


# ── Voices API ──────────────────────────────────────────────────────────────

@app.get('/voices')
def get_voices():
    return JSONResponse({
        'voice_map': edge_tts_engine.VOICE_MAP,
        'languages': translation.ALL_LANGUAGES,
    })


# ── Synthesize (legacy compatibility) ───────────────────────────────────────

@app.post('/synthesize')
def web_synthesize(text: str = Form(...), backend: str = Form('edge'), model: str = Form('')):
    if backend == 'coqui':
        try:
            out_path = os.path.join(tempfile.gettempdir(), 'web_synth.wav')
            out = voice_models.synthesize_with_coqui(text, speaker=None, out_path=out_path, model_name=(model or None))
            return FileResponse(out, media_type='audio/wav', filename='web_synth.wav')
        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=500)
    elif backend == 'edge':
        try:
            out_path = os.path.join(tempfile.gettempdir(), 'web_synth.mp3')
            out = edge_tts_engine.speak(text, lang='en', out_path=out_path)
            return FileResponse(out, media_type='audio/mpeg', filename='web_synth.mp3')
        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=500)
    else:
        out_path = os.path.join(tempfile.gettempdir(), 'web_synth_local.wav')
        try:
            tts.speak(text, lang='en', out_path=out_path, backend='local')
            return FileResponse(out_path, media_type='audio/wav', filename='web_synth_local.wav')
        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=500)


# ── Jobs ────────────────────────────────────────────────────────────────────

@app.post('/enqueue-synthesize')
def web_enqueue_synthesize(text: str = Form(...), backend: str = Form('edge'), model: str = Form('')):
    params = {'text': text, 'backend': backend, 'model': model}
    job_queue.manager.submit('synthesize', params)
    return RedirectResponse(url='/', status_code=303)


@app.post('/enqueue-download-model')
async def enqueue_download_model(model_id: str = Form(...)):
    job_queue.manager.submit('download_model', {'model_id': model_id})
    return RedirectResponse(url='/', status_code=303)


@app.get('/job-stream')
async def job_stream(request: Request):
    async def event_generator():
        last = None
        while True:
            if await request.is_disconnected():
                break
            jobs = job_queue.manager.list()
            try:
                payload = json.dumps(jobs, default=str)
            except Exception:
                payload = '{}'
            if payload != last:
                yield f"data: {payload}\n\n"
                last = payload
            await asyncio.sleep(1)
 
    return StreamingResponse(event_generator(), media_type='text/event-stream')


@app.post('/enqueue-clone')
def web_enqueue_clone(file: UploadFile = File(...), name: str = Form(...), consent: str = Form(None)):
    tmp = Path(tempfile.gettempdir()) / "vaaniverse_uploads"
    tmp.mkdir(exist_ok=True)
    dest = tmp / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    params = {'sample': str(dest), 'name': name, 'consent': (consent == 'on')}
    job_queue.manager.submit('clone', params)
    return RedirectResponse(url='/', status_code=303)


# ── Voice Age Styles ────────────────────────────────────────────────────────

@app.get('/age-presets')
def get_age_presets():
    """Return all age voice presets."""
    return JSONResponse({'presets': voice_styles.list_age_presets()})


@app.post('/speak-age')
async def web_speak_age(
    text: str = Form(...),
    lang: str = Form('hi'),
    gender: str = Form('female'),
    age_preset: str = Form('adult'),
    auto_translate: str = Form('off'),
):
    """Speak text with a specific age voice style."""
    try:
        if auto_translate == 'on':
            text = translation.translate(text, src='auto', tgt=lang)

        audio = await voice_styles.speak_with_age_async(
            text, lang=lang, gender=gender, age_preset=age_preset,
        )
        return FileResponse(audio, media_type='audio/mpeg', filename=f'age_{age_preset}.mp3')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)


# ── Audio Editor / Studio ──────────────────────────────────────────────────

@app.get('/audio-effects')
def get_audio_effects():
    """Return available audio effects."""
    return JSONResponse({'effects': audio_editor.list_effects()})


@app.post('/edit-audio')
async def web_edit_audio(
    request: Request,
    file: UploadFile = File(...),
    effect: str = Form('enhance'),
):
    """Apply an audio effect to an uploaded file."""
    tmp_dir = Path(tempfile.gettempdir()) / 'vaaniverse_studio'
    tmp_dir.mkdir(exist_ok=True)
    src = tmp_dir / file.filename
    with open(src, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    try:
        out = audio_editor.process_audio(str(src), effect)
        _save_history(request, 'studio', file.filename, {'effect': effect}, out)
        return FileResponse(out, media_type='audio/wav', filename=f'edited_{effect}.wav')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)


# ── New Features ─────────────────────────────────────────────────────────

@app.post('/generate-podcast')
async def web_generate_podcast(
    request: Request,
    topic: str = Form(...),
    lang: str = Form('en'),
    duration: str = Form('short'),
):
    """Generate a dual-voice AI podcast on any topic."""
    import asyncio
    try:
        # Generate script
        turn_counts = {'short': 4, 'medium': 8, 'long': 14}
        num_turns = turn_counts.get(duration, 4)
        script_lines = []
        host_topics = [
            f"Let's dive into {topic}. What makes this so fascinating?",
            f"That's a great point about {topic}. But what about the challenges?",
            f"How do you think {topic} will evolve in the future?",
            f"What should our listeners take away from this discussion on {topic}?",
        ]
        cohost_topics = [
            f"Absolutely! {topic} is revolutionizing how we think about things.",
            f"The challenges are real, but the opportunities are incredible.",
            f"I think we'll see massive changes in the next few years.",
            f"The key takeaway is to stay curious and keep exploring!",
        ]
        for i in range(num_turns):
            if i % 2 == 0:
                line = host_topics[i % len(host_topics)] if i < len(host_topics) else f"Interesting perspective on {topic}. Tell us more."
                script_lines.append(f"HOST: {line}")
            else:
                line = cohost_topics[i % len(cohost_topics)] if i < len(cohost_topics) else f"Great question about {topic}. Let me explain."
                script_lines.append(f"CO-HOST: {line}")
        script = '\n'.join(script_lines)

        # Generate audio for each line using edge-tts
        tmp_dir = Path(tempfile.gettempdir()) / 'vaaniverse_podcast'
        tmp_dir.mkdir(exist_ok=True)
        import edge_tts
        segments = []
        voice_map = {
            'en': ('en-US-GuyNeural', 'en-US-JennyNeural'),
            'hi': ('hi-IN-MadhurNeural', 'hi-IN-SwaraNeural'),
            'te': ('te-IN-MohanNeural', 'te-IN-ShrutiNeural'),
            'ta': ('ta-IN-ValluvarNeural', 'ta-IN-PallaviNeural'),
        }
        male_voice, female_voice = voice_map.get(lang, voice_map['en'])

        for idx, line in enumerate(script_lines):
            is_host = line.startswith('HOST:')
            text = line.split(':', 1)[1].strip()
            voice = male_voice if is_host else female_voice
            seg_path = str(tmp_dir / f'seg_{idx}.mp3')
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(seg_path)
            segments.append(seg_path)

        # Merge segments with pydub
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        pause = AudioSegment.silent(duration=500)
        for seg_path in segments:
            try:
                seg = AudioSegment.from_file(seg_path)
                combined += seg + pause
            except Exception:
                pass

        out_path = str(tmp_dir / 'podcast_output.mp3')
        combined.export(out_path, format='mp3')
        _save_history(request, 'podcast', topic, {'lang': lang}, out_path)
        return JSONResponse({'ok': True, 'script': script, 'audio_path': f'/podcast-audio'})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=400)

@app.get('/podcast-audio')
def serve_podcast_audio():
    path = Path(tempfile.gettempdir()) / 'vaaniverse_podcast' / 'podcast_output.mp3'
    if path.exists():
        return FileResponse(str(path), media_type='audio/mpeg')
    return JSONResponse({'error': 'No podcast audio'}, status_code=404)


@app.post('/generate-ringtone')
async def web_generate_ringtone(
    request: Request,
    genre: str = Form('bollywood'),
    duration: str = Form('15'),
    bpm: str = Form('120'),
):
    """Generate a short ringtone using the song engine."""
    try:
        import edge_tts
        from pydub import AudioSegment
        from pydub.generators import Sine

        dur_sec = min(int(duration), 30)
        bpm_val = int(bpm)
        beat_dur_ms = int(60000 / bpm_val)

        # Create a simple melodic ringtone
        genre_notes = {
            'bollywood': [523, 587, 659, 698, 784, 698, 659, 587],
            'pop': [440, 494, 523, 587, 659, 587, 523, 494],
            'classical': [262, 294, 330, 349, 392, 440, 494, 523],
            'lofi': [330, 392, 440, 494, 523, 494, 440, 392],
            'rock': [440, 523, 587, 659, 784, 880, 784, 659],
            'hiphop': [262, 330, 392, 523, 392, 330, 262, 330],
        }
        notes = genre_notes.get(genre, genre_notes['pop'])
        ringtone = AudioSegment.empty()
        total_beats = int(dur_sec * 1000 / beat_dur_ms)

        for i in range(total_beats):
            freq = notes[i % len(notes)]
            tone = Sine(freq).to_audio_segment(duration=beat_dur_ms - 50)
            tone = tone.fade_in(20).fade_out(30) - 6  # softer
            ringtone += tone + AudioSegment.silent(duration=50)

        # Trim to exact duration
        ringtone = ringtone[:dur_sec * 1000]

        tmp_dir = Path(tempfile.gettempdir()) / 'vaaniverse_ringtone'
        tmp_dir.mkdir(exist_ok=True)
        out = str(tmp_dir / 'ringtone.mp3')
        ringtone.export(out, format='mp3')
        _save_history(request, 'ringtone', f'{genre} ringtone', {'genre': genre, 'bpm': bpm}, out)
        return JSONResponse({'ok': True, 'audio_path': f'/ringtone-audio'})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=400)

@app.get('/ringtone-audio')
def serve_ringtone_audio():
    path = Path(tempfile.gettempdir()) / 'vaaniverse_ringtone' / 'ringtone.mp3'
    if path.exists():
        return FileResponse(str(path), media_type='audio/mpeg')
    return JSONResponse({'error': 'No ringtone'}, status_code=404)


@app.post('/mashup')
async def web_mashup(
    request: Request,
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    mix: str = Form('50'),
):
    """Mix two audio files together."""
    try:
        from pydub import AudioSegment
        tmp_dir = Path(tempfile.gettempdir()) / 'vaaniverse_mashup'
        tmp_dir.mkdir(exist_ok=True)
        path_a = tmp_dir / file_a.filename
        path_b = tmp_dir / file_b.filename
        with open(path_a, 'wb') as f:
            shutil.copyfileobj(file_a.file, f)
        with open(path_b, 'wb') as f:
            shutil.copyfileobj(file_b.file, f)

        a = AudioSegment.from_file(str(path_a))
        b = AudioSegment.from_file(str(path_b))

        mix_val = int(mix) / 100.0
        # Adjust volumes based on mix balance
        a = a - (mix_val * 12)  # reduce A as mix goes toward B
        b = b - ((1 - mix_val) * 12)  # reduce B as mix goes toward A

        # Make same length (use shorter)
        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]

        mixed = a.overlay(b)
        out = str(tmp_dir / 'mashup_output.wav')
        mixed.export(out, format='wav')
        _save_history(request, 'mashup', 'Audio Mashup', {'mix': mix}, out)
        return JSONResponse({'ok': True, 'audio_path': '/mashup-audio'})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=400)


@app.get('/mashup-audio')
def serve_mashup_audio():
    path = Path(tempfile.gettempdir()) / 'vaaniverse_mashup' / 'mashup_output.wav'
    if path.exists():
        return FileResponse(str(path), media_type='audio/wav')
    return JSONResponse({'error': 'No mashup audio'}, status_code=404)




@app.post('/detect-mood')
def web_detect_mood(
    request: Request,
    text: str = Form(...),
):
    """Detect mood/emotion from text using AI."""
    result = ai_service.detect_mood(text)

    return JSONResponse({
        'ok': True,
        'mood': result.get('mood', 'Neutral'),
        'emoji': result.get('emoji', '😐'),
        'description': result.get('description', 'Detected emotional state'),
        'tags': result.get('tags', ['neutral']),
        'score': result.get('score', 0.5),
    })


# ── Auth & History ─────────────────────────────────────────────────────────

@app.post('/register')
def web_register(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(''),
):
    result = auth.register(username, password, email)
    status = 200 if result['ok'] else 400
    return JSONResponse(result, status_code=status)


@app.post('/login')
def web_login(
    username: str = Form(...),
    password: str = Form(...),
):
    result = auth.login(username, password)
    status = 200 if result['ok'] else 401
    return JSONResponse(result, status_code=status)


@app.get('/me')
def web_me(request: Request):
    """Get current user info from token."""
    user = getattr(request.state, 'user', None)
    if user:
        return JSONResponse({'ok': True, 'user': user})
    return JSONResponse({'ok': False, 'error': 'Not logged in'}, status_code=401)


@app.post('/save-history')
def web_save_history(
    request: Request,
    entry_type: str = Form(...),
    title: str = Form(''),
    data: str = Form('{}'),
):
    """Save a creation to user history."""
    user = getattr(request.state, 'user', None)
    if not user:
        return JSONResponse({'ok': False, 'error': 'Login required'}, status_code=401)
    try:
        parsed = json.loads(data)
    except Exception:
        parsed = {'raw': data}
    hid = db.save_history(user['id'], entry_type, title=title, data=parsed)
    return JSONResponse({'ok': True, 'id': hid})


@app.get('/history')
def web_history(request: Request):
    """Get user's creation history."""
    user = getattr(request.state, 'user', None)
    if not user:
        return JSONResponse({'ok': False, 'error': 'Login required'}, status_code=401)
    items = db.get_history(user['id'])
    return JSONResponse({'ok': True, 'history': items})


@app.get('/history-audio/{hid}')
def web_history_audio(request: Request, hid: int):
    """Serve audio from a history entry."""
    user = getattr(request.state, 'user', None)
    if not user:
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)
    
    conn = db._get_conn()
    row = conn.execute("SELECT user_id, audio_path FROM history WHERE id = ?", (hid,)).fetchone()
    conn.close()
    
    if not row or row['user_id'] != user['id']:
        return JSONResponse({'error': 'Not found or unauthorized'}, status_code=404)
    
    path = row['audio_path']
    if path and os.path.exists(path):
        media = 'audio/wav' if path.endswith('.wav') else 'audio/mpeg'
        return FileResponse(path, media_type=media)
    return JSONResponse({'error': 'Audio file missing'}, status_code=404)
