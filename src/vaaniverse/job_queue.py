"""Lightweight in-process job queue for long-running tasks.

This provides a minimal background worker without external dependencies.
Jobs are persisted to `data_dir/jobs.json` and processed sequentially by a
daemon thread. Suitable for demo and small deployments; replace with a
real queue (RQ/Celery) for production.
"""
from __future__ import annotations
import threading
import queue
import uuid
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

from .config import cfg
from . import voice_models, tts, voice_clone, model_downloader


class JobManager:
    def __init__(self):
        self._q = queue.Queue()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._data_dir = Path(cfg.data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._jobs_file = self._data_dir / 'jobs.json'
        self._load_jobs()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _load_jobs(self):
        if self._jobs_file.exists():
            try:
                with open(self._jobs_file, 'r', encoding='utf-8') as f:
                    self._jobs = json.load(f)
            except Exception:
                self._jobs = {}

    def _persist_jobs(self):
        try:
            with open(self._jobs_file, 'w', encoding='utf-8') as f:
                json.dump(self._jobs, f, indent=2, default=str)
        except Exception:
            pass

    def submit(self, job_type: str, params: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        job = {
            'id': job_id,
            'type': job_type,
            'params': params,
            'status': 'queued',
            'result': None,
            'error': None,
            'created_at': now,
            'started_at': None,
            'finished_at': None,
        }
        with self._lock:
            self._jobs[job_id] = job
            self._persist_jobs()
            self._q.put(job_id)
        return job_id

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._jobs)

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                job_id = self._q.get(timeout=0.5)
            except Exception:
                continue
            self._run_job(job_id)

    def _run_job(self, job_id: str):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job['status'] = 'running'
            job['started_at'] = datetime.utcnow().isoformat() + 'Z'
            self._persist_jobs()

        try:
            typ = job['type']
            params = job['params']
            if typ == 'synthesize':
                out = params.get('out') or f"job_{job_id}.wav"
                backend = params.get('backend', 'local')
                model = params.get('model')
                text = params.get('text', '')
                if backend == 'coqui' and voice_models.is_coqui_available():
                    res = voice_models.synthesize_with_coqui(text, speaker=None, out_path=out, model_name=model)
                    result = {'out': res}
                else:
                    # local fallback
                    tts.speak(text, lang=params.get('lang', 'en'), out_path=out)
                    result = {'out': str(Path(out).absolute())}
            elif typ == 'clone':
                sample = params['sample']
                name = params['name']
                consent_flag = params.get('consent', False)
                res = voice_clone.clone_voice(sample, name, consent=consent_flag)
                result = {'out': res}
            elif typ == 'download_model':
                model_id = params['model_id']
                # update progress: starting
                with self._lock:
                    job['progress'] = 'starting'
                    self._persist_jobs()
                try:
                    with self._lock:
                        job['progress'] = 'downloading'
                        self._persist_jobs()

                    def _progress_cb(done, total, fname):
                        try:
                            pct = int((done / float(total)) * 100)
                        except Exception:
                            pct = 0
                        with self._lock:
                            job['progress'] = f"{pct}% ({done}/{total})"
                            self._persist_jobs()

                    path = model_downloader.download_model(model_id, cache_dir=str(self._data_dir), progress_callback=_progress_cb)
                    with self._lock:
                        job['progress'] = 'finalizing'
                        self._persist_jobs()
                    result = {'model_path': path}
                except Exception:
                    raise
            else:
                raise ValueError(f"Unknown job type: {typ}")

            with self._lock:
                job['status'] = 'succeeded'
                job['result'] = result
                job['finished_at'] = datetime.utcnow().isoformat() + 'Z'
                self._persist_jobs()

        except Exception as e:
            with self._lock:
                job['status'] = 'failed'
                job['error'] = str(e)
                job['finished_at'] = datetime.utcnow().isoformat() + 'Z'
                self._persist_jobs()

    def stop(self):
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=1.0)


# Singleton manager
manager = JobManager()
