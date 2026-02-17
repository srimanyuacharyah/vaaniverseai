"""Consent capture and verification utilities.

Creates HMAC-signed consent artifacts tied to an audio sample. Consent files
are JSON objects saved next to the sample (or in `data_dir`) and include the
signer, timestamp, sample filename, sample SHA256, and an HMAC signature.

Set `VAANIVERSE_CONSENT_KEY` env var to enable HMAC signing. If not set, the
module will still produce consent files but signatures will be empty.
"""
import os
import json
import hmac
import hashlib
from datetime import datetime
from pathlib import Path
from .config import cfg


def _consent_key() -> bytes:
    k = os.environ.get('VAANIVERSE_CONSENT_KEY', '')
    return k.encode('utf-8') if k else b''


def sample_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _hmac_for_payload(payload: bytes) -> str:
    key = _consent_key()
    if not key:
        return ''
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return sig


def make_consent(sample_path: str, signer: str, notes: str = '') -> str:
    """Create and save a consent JSON for `sample_path`. Returns consent path."""
    sample = Path(sample_path)
    if not sample.exists():
        raise FileNotFoundError(sample_path)
    s_hash = sample_hash(str(sample))
    payload = {
        'signer': signer,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'sample': sample.name,
        'sample_hash': s_hash,
        'notes': notes,
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
    sig = _hmac_for_payload(payload_bytes)
    payload['hmac'] = sig

    # Save next to sample if data_dir not configured else in data_dir
    out_dir = Path(os.environ.get('VAANIVERSE_DATA_DIR', cfg.data_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    consent_path = out_dir / f"consent_{sample.name}.json"
    with open(consent_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    return str(consent_path)


def verify_consent_for_sample(sample_path: str) -> bool:
    """Verify a consent file exists and matches the sample hash and HMAC."""
    sample = Path(sample_path)
    data_dir = Path(os.environ.get('VAANIVERSE_DATA_DIR', cfg.data_dir))
    consent_path = data_dir / f"consent_{sample.name}.json"
    if not consent_path.exists():
        return False
    with open(consent_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    expected_hash = sample_hash(str(sample))
    if payload.get('sample_hash') != expected_hash:
        return False
    # Verify HMAC if key present
    hmac_val = payload.get('hmac', '')
    if not hmac_val and not _consent_key():
        # unsigned but acceptable in no-key mode
        return True
    # Recompute HMAC over same canonical payload (without hmac)
    payload_copy = {k: payload[k] for k in payload if k != 'hmac'}
    payload_bytes = json.dumps(payload_copy, sort_keys=True).encode('utf-8')
    expected_sig = _hmac_for_payload(payload_bytes)
    return hmac.compare_digest(expected_sig, hmac_val)


def list_consents() -> list:
    """Return a list of consent payloads found in the configured data dir.

    Each entry is a dict with keys: path, payload (dict), verified (bool).
    """
    out = []
    d = Path(os.environ.get('VAANIVERSE_DATA_DIR', cfg.data_dir))
    if not d.exists():
        return out
    for p in d.glob('consent_*.json'):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception:
            continue
        # try to find sample next to data dir or absolute path
        sample_name = payload.get('sample')
        # sample path is relative to data_dir if exists
        sample_path = d / sample_name
        if not sample_path.exists():
            # try same dir as payload
            sample_path = p.parent / sample_name
        verified = False
        try:
            verified = verify_consent_for_sample(str(sample_path))
        except Exception:
            verified = False
        out.append({'path': str(p), 'payload': payload, 'verified': verified})
    return out
