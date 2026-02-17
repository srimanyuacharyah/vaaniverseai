"""Vaaniverse AI — FastAPI web application.

Provides a modern web UI for translation, text-to-speech, voice
translation (text + audio upload), song generation (custom lyrics),
and voice cloning features.
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


# ── Text-to-Speech ──────────────────────────────────────────────────────────

@app.post('/speak')
def web_speak(text: str = Form(...), lang: str = Form('hi'), gender: str = Form('female'), backend: str = Form('edge')):
    out_path = f"spoken_{os.getpid()}.mp3"
    try:
        tts.speak(text, lang=lang, out_path=out_path, gender=gender, backend=backend)
        return FileResponse(out_path, media_type='audio/mpeg', filename=f'vaaniverse_{lang}.mp3')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# ── Voice Translation ──────────────────────────────────────────────────────

@app.post('/voice-translate')
def web_voice_translate(
    text: str = Form(...),
    src_lang: str = Form('en'),
    tgt_lang: str = Form('hi'),
    gender: str = Form('female'),
):
    try:
        result = voice_translator.translate_voice(
            text, src_lang=src_lang, tgt_lang=tgt_lang, gender=gender,
        )
        audio_path = result.get('audio_path')
        if audio_path and os.path.exists(audio_path):
            response = FileResponse(audio_path, media_type='audio/mpeg', filename=f'translated_{tgt_lang}.mp3')
            response.headers['X-Translated-Text'] = result['translated']
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
    tmp = Path('uploads')
    tmp.mkdir(exist_ok=True)
    dest = tmp / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    try:
        result = voice_translator.translate_voice_from_audio(
            str(dest), src_lang=src_lang, tgt_lang=tgt_lang, gender=gender,
        )
        audio_path = result.get('audio_path')
        if audio_path and os.path.exists(audio_path):
            response = FileResponse(audio_path, media_type='audio/mpeg', filename=f'translated_{tgt_lang}.mp3')
            response.headers['X-Transcribed-Text'] = result.get('transcribed', '')
            response.headers['X-Translated-Text'] = result.get('translated', '')
            return response
        return JSONResponse({
            'error': 'Audio generation failed',
            'transcribed': result.get('transcribed', ''),
            'translated': result.get('translated', ''),
        }, status_code=500)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/voice-translate-text')
def web_voice_translate_text(
    text: str = Form(...),
    src_lang: str = Form('en'),
    tgt_lang: str = Form('hi'),
):
    translated = translation.translate(text, src=src_lang, tgt=tgt_lang)
    return JSONResponse({'original': text, 'translated': translated, 'tgt_lang': tgt_lang})


# ── Song Generation ─────────────────────────────────────────────────────────

@app.post('/generate-song')
def web_generate_song(
    theme: str = Form('love'),
    lang: str = Form('hi'),
    gender: str = Form('female'),
    with_audio: str = Form('on'),
    custom_lyrics: str = Form(''),
    genre_description: str = Form(''),
    full_length: str = Form('on'),
):
    is_full = full_length == 'on'
    has_custom = bool(custom_lyrics.strip()) or bool(genre_description.strip())

    song = song_generator.generate_song_audio(
        theme=theme, lang=lang, gender=gender,
        custom_lyrics=custom_lyrics,
        genre_description=genre_description,
        full_length=(is_full or has_custom),
    ) if with_audio == 'on' else song_generator.generate_full_song(
        theme=theme, lang=lang,
        custom_lyrics=custom_lyrics,
        genre_description=genre_description,
    )

    return JSONResponse({
        'lyrics': song['lyrics'],
        'melody': song['melody'],
        'theme': song.get('theme', theme),
        'lang': song.get('lang', lang),
        'has_audio': song.get('audio_path') is not None,
    })


@app.get('/song-audio')
def get_song_audio(lang: str = 'hi'):
    import tempfile, glob
    pattern = os.path.join(tempfile.gettempdir(), f"song_{lang}_*.mp3")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if files:
        return FileResponse(files[0], media_type='audio/mpeg', filename=f'song_{lang}.mp3')
    return JSONResponse({'error': 'No audio found'}, status_code=404)


# ── Voice Cloning ───────────────────────────────────────────────────────────

@app.post('/clone-voice')
def web_clone_voice(
    file: UploadFile = File(...),
    name: str = Form(...),
    consent: str = Form(None),
    lang: str = Form('hi'),
    gender: str = Form('female'),
):
    tmp = Path('uploads')
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


@app.get('/voice-profiles')
def web_voice_profiles():
    profiles = voice_clone.list_profiles()
    return JSONResponse({'profiles': profiles})


@app.post('/speak-with-profile')
def web_speak_with_profile(
    name: str = Form(...),
    text: str = Form(...),
    lang: str = Form(''),
):
    try:
        audio = voice_clone.speak_with_profile(name, text, lang=lang or None)
        return FileResponse(audio, media_type='audio/mpeg', filename=f'clone_{name}.mp3')
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
            out = voice_models.synthesize_with_coqui(text, speaker=None, out_path='web_synth.wav', model_name=(model or None))
            return FileResponse(out, media_type='audio/wav', filename='web_synth.wav')
        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=500)
    elif backend == 'edge':
        try:
            out = edge_tts_engine.speak(text, lang='en', out_path='web_synth.mp3')
            return FileResponse(out, media_type='audio/mpeg', filename='web_synth.mp3')
        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=500)
    else:
        out_path = 'web_synth_local.wav'
        try:
            tts.speak(text, lang='en', out_path=out_path, backend='local')
            return FileResponse(out_path, media_type='audio/wav', filename=out_path)
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
    tmp = Path('uploads')
    tmp.mkdir(exist_ok=True)
    dest = tmp / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    params = {'sample': str(dest), 'name': name, 'consent': (consent == 'on')}
    job_queue.manager.submit('clone', params)
    return RedirectResponse(url='/', status_code=303)
