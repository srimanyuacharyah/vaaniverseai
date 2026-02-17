import sys
from pathlib import Path
sys.path.insert(0, 'src')

from vaaniverse import consent


def test_list_consents(tmp_path, monkeypatch):
    # prepare a sample and consent
    sample = tmp_path / 's.wav'
    sample.write_bytes(b'RIFF')
    monkeypatch.setenv('VAANIVERSE_DATA_DIR', str(tmp_path))
    consent.make_consent(str(sample), signer='A')
    items = consent.list_consents()
    assert len(items) == 1
    it = items[0]
    assert it['payload']['signer'] == 'A'
    assert it['verified'] is True
