import sys
import os
from pathlib import Path
sys.path.insert(0, 'src')

from vaaniverse import consent


def test_make_and_verify_consent(tmp_path, monkeypatch):
    sample = tmp_path / 'sample.wav'
    sample.write_bytes(b'RIFFDATA')

    # ensure data_dir points to tmp
    monkeypatch.setenv('VAANIVERSE_DATA_DIR', str(tmp_path))
    # no key set: unsigned consent should be accepted
    consent_path = consent.make_consent(str(sample), signer='Tester')
    assert Path(consent_path).exists()
    assert consent.verify_consent_for_sample(str(sample))


def test_signed_consent_verification(tmp_path, monkeypatch):
    sample = tmp_path / 'sample2.wav'
    sample.write_bytes(b'RIFFDATA2')
    monkeypatch.setenv('VAANIVERSE_DATA_DIR', str(tmp_path))
    # set a key
    monkeypatch.setenv('VAANIVERSE_CONSENT_KEY', 'secretkey')
    consent_path = consent.make_consent(str(sample), signer='Signer')
    assert Path(consent_path).exists()
    assert consent.verify_consent_for_sample(str(sample))
    # tamper with sample -> verification fails
    sample.write_bytes(b'CHANGED')
    assert not consent.verify_consent_for_sample(str(sample))
