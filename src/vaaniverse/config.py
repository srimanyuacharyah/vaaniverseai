"""Configuration helpers for Vaaniverse AI.

Reads environment variables and provides project-wide defaults.
"""
import os
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Config:
    # Backend choices: 'local' (pyttsx3) or 'coqui'
    tts_backend: str = os.environ.get('VAANIVERSE_TTS_BACKEND', 'local')
    # Optional model name for Coqui TTS
    coqui_model: str = os.environ.get('VAANIVERSE_COQUI_MODEL', '')
    # Directory to store downloaded models or generated files
    data_dir: str = os.environ.get('VAANIVERSE_DATA_DIR', 'data')


def _load_local_config():
    # project root assumed two levels up from this file (src/vaaniverse)
    root = Path(__file__).resolve().parents[2]
    cfg_path = root / 'vaaniverse.local.json'
    if cfg_path.exists():
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


# Merge environment and local file config
_local = _load_local_config()
if not Config.coqui_model:
    Config.coqui_model = os.environ.get('VAANIVERSE_COQUI_MODEL', _local.get('coqui_model', ''))
if not Config.data_dir:
    Config.data_dir = os.environ.get('VAANIVERSE_DATA_DIR', _local.get('data_dir', 'data'))


cfg = Config()
