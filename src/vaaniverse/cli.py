import typer
from typing import Optional
from vaaniverse import translation, tts, song_generator, voice_clone
from vaaniverse import voice_models
from vaaniverse import consent
from vaaniverse import consent as consent_mod
from vaaniverse import job_queue
import json
from vaaniverse import rq_adapter

app = typer.Typer()


@app.command()
def translate(text: str, src: str = 'auto', tgt: str = 'hi'):
    """Translate text between languages (ISO 639-1 codes)."""
    out = translation.translate(text, src=src, tgt=tgt)
    typer.echo(out)


@app.command()
def speak(text: str, lang: str = 'en'):
    """Speak text using local TTS."""
    tts.speak(text, lang=lang)


@app.command()
def generate_song(theme: str = 'love', lang: str = 'hi', save: bool = False, prefix: str = 'song', sing: bool = False):
    """Generate simple song (lyrics + melody). Use `--save` to write files.

    `--sing` will speak the lyrics with the selected language voice (placeholder).
    """
    song = song_generator.generate_song(theme=theme, lang=lang)
    typer.echo(song['lyrics'])
    if save:
        paths = song_generator.save_song(song, prefix=prefix)
        typer.echo(f"Saved lyrics to {paths['lyrics']} and melody to {paths['melody']}")
    if sing:
        # singing synthesis is not implemented; use plain TTS to speak lyrics.
        tts.speak(song['lyrics'], lang=lang)


@app.command()
def clone_voice_cmd(sample: str, name: str, consent: bool = False):
    """Attempt to clone a voice sample (requires consent)."""
    try:
        out = voice_clone.clone_voice(sample, name, consent=consent)
        typer.echo(f"Created placeholder clone metadata: {out}")
    except Exception as e:
        typer.echo(f"Error: {e}")


@app.command()
def synthesize(text: str, speaker: str = None, out: str = 'out.wav'):
    """Synthesize speech using an optional model integration (Coqui TTS).

    If the heavyweight model is not installed, this command will explain how
    to install it. The local TTS fallback is still available via `speak`.
    """
    try:
        path = voice_models.synthesize_with_coqui(text, speaker=speaker, out_path=out)
        typer.echo(f"Synthesized to: {path}")
    except ImportError as ie:
        typer.echo("Model integration unavailable: " + str(ie))
        typer.echo("Falling back to local TTS (may have limited language voices).")
        tts.speak(text, lang='en', out_path=out)
        typer.echo(f"Saved fallback audio to: {out}")
    except Exception as e:
        typer.echo(f"Error during synthesis: {e}")


@app.command()
def record_consent(sample: str, signer: str, notes: str = ''):
    """Record consent for an audio sample and save a signed consent artifact."""
    try:
        path = consent.make_consent(sample, signer, notes=notes)
        typer.echo(f"Consent recorded: {path}")
    except Exception as e:
        typer.echo(f"Error recording consent: {e}")


@app.command()
def list_consents():
    """List recorded consent artifacts."""
    try:
        items = consent_mod.list_consents()
        if not items:
            typer.echo("No consent artifacts found in data dir.")
            return
        for it in items:
            p = it['path']
            payload = it['payload']
            ver = it['verified']
            typer.echo(f"{p}: signer={payload.get('signer')} sample={payload.get('sample')} verified={ver}")
    except Exception as e:
        typer.echo(f"Error listing consents: {e}")


@app.command()
def verify_consent(sample: str):
    """Verify consent exists and matches the provided sample file."""
    try:
        ok = consent_mod.verify_consent_for_sample(sample)
        typer.echo(f"Consent verification for {sample}: {ok}")
    except Exception as e:
        typer.echo(f"Error verifying consent: {e}")


@app.command()
def job_submit_synth(text: str, backend: str = 'local', model: str = '', out: str = None, lang: str = 'en'):
    """Submit a background synthesis job."""
    params = {'text': text, 'backend': backend, 'model': model, 'lang': lang}
    if out:
        params['out'] = out
    job_id = job_queue.manager.submit('synthesize', params)
    typer.echo(f"Enqueued synth job: {job_id}")


@app.command()
def job_submit_clone(sample: str, name: str, consent: bool = False):
    """Submit a background voice-clone job (consent required)."""
    params = {'sample': sample, 'name': name, 'consent': consent}
    job_id = job_queue.manager.submit('clone', params)
    typer.echo(f"Enqueued clone job: {job_id}")

    def job_submit_download(model_id: str):
        """Submit a background model download job (HuggingFace repo id)."""
        job = job_queue.manager.submit_job('download_model', {'model_id': model_id})
        typer.echo(f"Submitted download job: {job['id']}")

@app.command()
def job_list():
    """List background jobs."""
    items = job_queue.manager.list()
    for jid, job in items.items():
        typer.echo(f"{jid}: type={job['type']} status={job['status']}")


@app.command()
def job_status(job_id: str):
    """Show status for a job id."""
    job = job_queue.manager.get(job_id)
    if not job:
        typer.echo("Job not found")
        return
    typer.echo(json.dumps(job, indent=2, default=str))


@app.command()
def rq_submit_synth(text: str, backend: str = 'local', model: str = '', out: str = None):
    """Enqueue a synth job via RQ (Redis) if available."""
    try:
        jid = rq_adapter.enqueue('vaaniverse.job_worker.process_synth', args=(text,), kwargs={'backend': backend, 'model': model, 'out': out})
        typer.echo(f"Enqueued RQ synth job: {jid}")
    except ImportError as e:
        typer.echo(str(e))
        typer.echo(rq_adapter.instructions())


@app.command()
def rq_submit_clone(sample: str, name: str, consent: bool = False):
    """Enqueue a clone job via RQ (Redis) if available."""
    try:
        jid = rq_adapter.enqueue('vaaniverse.job_worker.process_clone', args=(sample, name), kwargs={'consent': consent})
        typer.echo(f"Enqueued RQ clone job: {jid}")
    except ImportError as e:
        typer.echo(str(e))
        typer.echo(rq_adapter.instructions())


@app.command()
def coqui_setup(auto: bool = False):
    """Show instructions to install Coqui TTS or auto-install when `--auto`.

    Installing Coqui TTS can be large. Use `--auto` to attempt `pip install TTS[all]`.
    """
    if not auto:
        typer.echo("To enable Coqui TTS, run: pip install TTS[all]")
        typer.echo("Then set VAANIVERSE_COQUI_MODEL to a downloaded model name or use TTS.list_models() to choose.")
        return
    import subprocess
    try:
        typer.echo("Attempting to install Coqui TTS (this may take a while)...")
        subprocess.check_call(["python", "-m", "pip", "install", "TTS[all]"])
        typer.echo("Installation complete. You can now use `synthesize` with Coqui models.")
    except Exception as e:
        typer.echo(f"Auto-install failed: {e}")
        typer.echo("Please install manually: pip install TTS[all]")
        return

    # Try to discover available models and optionally download a recommended one
    try:
        from TTS.api import TTS  # type: ignore
    except Exception as e:
        typer.echo(f"Coqui import failed after install: {e}")
        return

    try:
        models = TTS.list_models()
    except Exception:
        models = []

    if models:
        chosen = models[0]
        typer.echo(f"Found available Coqui models; selecting default: {chosen}")
    else:
        # recommended model (common, moderate size)
        recommended = 'tts_models/en/ljspeech/tacotron2-DDC'
        typer.echo(f"No models found locally. Attempting to download recommended model: {recommended}")
        # prefer huggingface_hub snapshot_download when available
        try:
            from vaaniverse import model_downloader
            # use project data dir for caches
            cache_dir = None
            try:
                from vaaniverse.config import cfg
                cache_dir = cfg.data_dir
            except Exception:
                cache_dir = None
            try:
                model_path = model_downloader.download_model(recommended, cache_dir=cache_dir)
                chosen = recommended
                typer.echo(f"Downloaded model to: {model_path}")
            except ImportError:
                # huggingface_hub not installed; fall back to Coqui helper if available
                dl_func = getattr(TTS, 'download_model', None) or getattr(TTS, 'download', None)
                if callable(dl_func):
                    try:
                        dl_func(recommended)
                        chosen = recommended
                        typer.echo(f"Downloaded model via Coqui helper: {recommended}")
                    except Exception as e:
                        typer.echo(f"Model download failed: {e}")
                        typer.echo("Please download a model manually and set VAANIVERSE_COQUI_MODEL or create vaaniverse.local.json with coqui_model.")
                        return
                else:
                    typer.echo("Automatic model download not supported. Install huggingface-hub or download a model manually.")
                    return
        except Exception as e:
            typer.echo(f"Model download failed: {e}")
            typer.echo("Please download a model manually and set VAANIVERSE_COQUI_MODEL or create vaaniverse.local.json with coqui_model.")
            return

    # Persist chosen model to project local config file
    try:
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        cfg_path = root / 'vaaniverse.local.json'
        cfg = { 'coqui_model': chosen }
        with open(cfg_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(cfg, f, indent=2)
        typer.echo(f"Wrote local config: {cfg_path}. The synth CLI will use this model by default.")
    except Exception as e:
        typer.echo(f"Failed to write local config: {e}")


if __name__ == '__main__':
    app()
