# Deployment Notes

This document lists options to deploy Vaaniverse AI demo and how to extend it
for better voice cloning or singing synthesis.

Local quick start (Windows):

```powershell
python -m pip install -r requirements.txt
.\start_web.bat
# open http://127.0.0.1:8000
```

Run in Docker:

```bash
docker build -t vaaniverseai:latest .
docker run -p 8000:8000 vaaniverseai:latest
```

Extending for production-quality voice cloning / singing:
- Use dedicated models (Coqui TTS, VITS, Mellotron, etc.) and ensure licensing.
- Implement a consent capture flow (record signed consent, store metadata, hashes).
- For singing synthesis integrate a singing model (e.g., Sinsy, OpenSinger) and a
  vocoder (e.g., HiFi-GAN). These typically require GPU for good performance.

Coqui TTS quick integration
---------------------------
To enable faster, higher-quality TTS synthesis with Coqui TTS:

1. Install dependencies (recommended inside a virtual environment):

```bash
pip install TTS[all]
```

2. Download a compatible model as per Coqui TTS docs, or use `TTS.list_models()`.

3. Use the CLI `synthesize` command:

```bash
python -m vaaniverse.cli synthesize "Hello, this is a test" --speaker <speaker> --out demo.wav
```

If Coqui TTS isn't present, the CLI will fallback to the local `pyttsx3` method
and write `out` to disk if possible.

Voice cloning integration
-------------------------
Full voice-cloning pipelines require multiple components and careful consent
handling. This repo provides a guarded placeholder in `vaaniverse.voice_models`.
If you add an SV2TTS-style pipeline, call it from `clone_voice_with_model` and
ensure you capture signed consent before performing cloning.

Legal / safety notes
- Do NOT deploy impersonation features for public figures without explicit,
  recorded, legal consent. This repo purposefully restricts cloning to
  consent-based personal samples and provides placeholder behavior for
  public-figure names.
