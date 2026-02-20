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
import tempfile

app = FastAPI(title="Vaaniverse AI")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount('/static', StaticFiles(directory=str(Path(__file__).parent / 'static')), name='static')


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


# ── Translation ─────────────────────────────────────────────────────────────

@app.post('/translate')
def web_translate(text: str = Form(...), src: str = Form('auto'), tgt: str = Form('hi')):
    out = translation.translate(text, src=src, tgt=tgt)
    return JSONResponse({'original': text, 'translated': out, 'src': src, 'tgt': tgt})


@app.post('/batch-translate')
def web_batch_translate(text: str = Form(...)):
    results = translation.batch_translate(text)
    return JSONResponse({'original': text, 'translations': results})


import tempfile

# ── Text-to-Speech ──────────────────────────────────────────────────────────

@app.post('/speak')
async def web_speak(text: str = Form(...), lang: str = Form('hi'), gender: str = Form('female'), backend: str = Form('edge')):
    out_path = os.path.join(tempfile.gettempdir(), f"spoken_{lang}_{os.getpid()}.mp3")
    try:
        if backend == 'edge':
            await edge_tts_engine.speak_async(text, lang=lang, out_path=out_path, gender=gender)
        else:
            tts.speak(text, lang=lang, out_path=out_path, gender=gender, backend=backend)
        return FileResponse(out_path, media_type='audio/mpeg', filename=f'vaaniverse_{lang}.mp3')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# ── Voice Translation ──────────────────────────────────────────────────────

@app.post('/voice-translate')
async def web_voice_translate(
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
            response = FileResponse(audio_path, media_type='audio/mpeg', filename=f'translated_{tgt_lang}.mp3')
            response.headers['X-Translated-Text'] = urllib.parse.quote(result['translated'])
            return response
        return JSONResponse({'error': 'Audio generation failed', 'translated': result.get('translated', '')}, status_code=500)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/voice-translate-audio')
async def web_voice_translate_audio(
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

    return JSONResponse({
        'lyrics': song['lyrics'],
        'melody': song['melody'],
        'theme': song.get('theme', theme),
        'lang': song.get('lang', lang),
        'has_audio': song.get('audio_path') is not None,
        'instrumental_config': song.get('instrumental_config', {}),
        'instrumental_only': song.get('instrumental_only', False),
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
    name: str = Form(...),
    text: str = Form(...),
    lang: str = Form(''),
):
    try:
        audio = await voice_clone.speak_with_profile_async(name, text, lang=lang or None)
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
        return FileResponse(out, media_type='audio/wav', filename=f'edited_{effect}.wav')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)


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
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.cookies.get('vaaniverse_token', '')
    user = auth.get_current_user(token)
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
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.cookies.get('vaaniverse_token', '')
    user = auth.get_current_user(token)
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
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.cookies.get('vaaniverse_token', '')
    user = auth.get_current_user(token)
    if not user:
        return JSONResponse({'ok': False, 'error': 'Login required'}, status_code=401)
    items = db.get_history(user['id'])
    return JSONResponse({'ok': True, 'history': items})
