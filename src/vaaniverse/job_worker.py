"""Job worker functions intended for external workers (RQ/Celery) to call.

These mirror the in-process job handlers so an external worker can import
and call them on Redis job execution.
"""
from pathlib import Path
from . import voice_models, tts, voice_clone, model_downloader


def process_synth(text: str, backend: str = 'local', model: str = '', out: str = None, lang: str = 'en') -> dict:
    out_path = out or 'job_synth.wav'
    if backend == 'coqui' and voice_models.is_coqui_available():
        path = voice_models.synthesize_with_coqui(text, speaker=None, out_path=out_path, model_name=(model or None))
        return {'out': path}
    else:
        tts.speak(text, lang=lang, out_path=out_path)
        return {'out': str(Path(out_path).absolute())}


def process_clone(sample: str, name: str, consent: bool = False) -> dict:
    out = voice_clone.clone_voice(sample, name, consent=consent)
    return {'out': out}


def process_download_model(model_id: str, cache_dir: str = None) -> dict:
    path = model_downloader.download_model(model_id, cache_dir=cache_dir)
    return {'model_path': path}
