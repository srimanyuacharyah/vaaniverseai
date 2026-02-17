from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, StreamingResponse
import json
import asyncio
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
from pathlib import Path

from vaaniverse import translation, tts, song_generator, voice_clone
from vaaniverse import voice_models, config
from vaaniverse import consent as consent_mod
from vaaniverse import job_queue

app = FastAPI(title="Vaaniverse AI (demo)")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

app.mount('/static', StaticFiles(directory=str(Path(__file__).parent / 'static')), name='static')


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    # pass available TTS backends and configured Coqui model to template
    backends = ['local']
    if voice_models.is_coqui_available():
        backends.append('coqui')
    cons = consent_mod.list_consents()
    jobs = job_queue.manager.list()
    return templates.TemplateResponse('index.html', {'request': request, 'backends': backends, 'coqui_model': config.cfg.coqui_model, 'consents': cons, 'jobs': jobs})


@app.post('/translate', response_class=HTMLResponse)
def web_translate(request: Request, text: str = Form(...), src: str = Form('auto'), tgt: str = Form('hi')):
    out = translation.translate(text, src=src, tgt=tgt)
    return templates.TemplateResponse('index.html', {'request': request, 'translate_result': out, 'translate_input': text})


@app.post('/speak')
def web_speak(request: Request, text: str = Form(...), lang: str = Form('en')):
    # save to a temp file and return the path so user can download/play
    out_path = f"spoken_{os.getpid()}.wav"
    try:
        tts.speak(text, lang=lang, out_path=out_path)
        return FileResponse(out_path, media_type='audio/wav', filename=out_path)
    finally:
        # file may remain for user; cleanup handled separately
        pass


@app.post('/synthesize', response_class=HTMLResponse)
def web_synthesize(request: Request, text: str = Form(...), backend: str = Form('local'), model: str = Form('')):
    """Synthesize using chosen backend: 'local' or 'coqui'."""
    if backend == 'coqui':
        try:
            out = voice_models.synthesize_with_coqui(text, speaker=None, out_path='web_synth.wav', model_name=(model or None))
            return FileResponse(out, media_type='audio/wav', filename='web_synth.wav')
        except Exception as e:
            return templates.TemplateResponse('index.html', {'request': request, 'synth_error': str(e)})
    else:
        # local fallback
        out_path = 'web_synth_local.wav'
        try:
            tts.speak(text, lang='en', out_path=out_path)
            return FileResponse(out_path, media_type='audio/wav', filename=out_path)
        except Exception as e:
            return templates.TemplateResponse('index.html', {'request': request, 'synth_error': str(e)})


@app.post('/enqueue-synthesize', response_class=HTMLResponse)
def web_enqueue_synthesize(request: Request, text: str = Form(...), backend: str = Form('local'), model: str = Form('')):
    params = {'text': text, 'backend': backend, 'model': model}
    jid = job_queue.manager.submit('synthesize', params)
    return RedirectResponse(url='/', status_code=303)

@app.post('/enqueue-download-model')
async def enqueue_download_model(request: Request, model_id: str = Form(...)):
    job = job_queue.manager.submit_job('download_model', {'model_id': model_id})
    return RedirectResponse(url='/', status_code=303)

@app.get('/job-stream')
async def job_stream(request: Request):
    async def event_generator():
        last = None
        while True:
            # if client disconnected, stop
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

@app.post('/enqueue-clone', response_class=HTMLResponse)
def web_enqueue_clone(request: Request, file: UploadFile = File(...), name: str = Form(...), consent: str = Form(None)):
    tmp = Path('uploads')
    tmp.mkdir(exist_ok=True)
    dest = tmp / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    params = {'sample': str(dest), 'name': name, 'consent': (consent == 'on')}
    jid = job_queue.manager.submit('clone', params)
    return RedirectResponse(url='/', status_code=303)


@app.post('/generate-song', response_class=HTMLResponse)
def web_generate_song(request: Request, theme: str = Form('love'), lang: str = Form('hi'), save: str = Form(None)):
    song = song_generator.generate_song(theme=theme, lang=lang)
    saved = None
    if save:
        saved = song_generator.save_song(song, prefix='web_song')
    return templates.TemplateResponse('index.html', {'request': request, 'song': song, 'saved': saved})


@app.post('/clone-voice', response_class=HTMLResponse)
def web_clone_voice(request: Request, file: UploadFile = File(...), name: str = Form(...), consent: str = Form(None)):
    tmp = Path('uploads')
    tmp.mkdir(exist_ok=True)
    dest = tmp / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    try:
        # If user checked the consent box, create a consent artifact for this upload
        if consent == 'on':
            consent_path = consent_mod.make_consent(str(dest), signer=name, notes='Recorded via web UI')
        out = voice_clone.clone_voice(str(dest), name, consent=(consent == 'on'))
        return templates.TemplateResponse('index.html', {'request': request, 'clone_out': out})
    except Exception as e:
        return templates.TemplateResponse('index.html', {'request': request, 'clone_error': str(e)})
