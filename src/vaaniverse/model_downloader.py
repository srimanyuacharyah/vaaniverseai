"""Model downloader helpers.

Prefer `huggingface_hub.snapshot_download` when available; falls back to any
available Coqui TTS download helpers. The downloader returns the path to the
downloaded model directory.
"""
from pathlib import Path
from typing import Optional, Callable
import os


def hf_snapshot_download(model_id: str, cache_dir: Optional[str] = None) -> str:
    try:
        from huggingface_hub import snapshot_download
    except Exception as e:
        raise ImportError("huggingface_hub not available") from e

    kwargs = {}
    if cache_dir:
        kwargs['cache_dir'] = cache_dir
    # snapshot_download handles resumable downloads and caching
    model_path = snapshot_download(repo_id=model_id, **kwargs)
    return model_path


def download_model(model_id: str, cache_dir: Optional[str] = None, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
    """Try to download a model via Hugging Face hub, else raise.

    This function intentionally does not auto-install heavy deps; callers
    should catch ImportError and instruct the user.
    """
    # allow explicit HF IDs or Coqui-style model names
    # First try HF snapshot
    # Prefer a file-by-file download so we can report progress.
    try:
        from huggingface_hub import list_repo_files, hf_hub_download, snapshot_download
    except Exception:
        # fall back to the simple snapshot helper
        try:
            return hf_snapshot_download(model_id, cache_dir=cache_dir)
        except Exception as e:
            raise RuntimeError(f"Failed to download model {model_id}: {e}") from e

    try:
        files = list_repo_files(model_id)
        total = len(files) or 1
        for idx, fname in enumerate(files, start=1):
            # download each file into the cache
            hf_hub_download(repo_id=model_id, filename=fname, cache_dir=cache_dir)
            if progress_callback:
                try:
                    progress_callback(idx, total, fname)
                except Exception:
                    pass

        # After downloading files, return a canonical model path via snapshot_download
        model_path = snapshot_download(repo_id=model_id, cache_dir=cache_dir)
        return model_path
    except Exception as e:
        raise RuntimeError(f"Failed to download model {model_id}: {e}") from e
