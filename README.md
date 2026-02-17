# Vaaniverse AI

Vaaniverse AI — prototype for multi-language translation, TTS, consent-based voice cloning (placeholder), and a simple song generator focused on Indian languages.

This repository contains a minimal, runnable scaffold. Advanced features such as high-quality singing synthesis and production-grade voice cloning require additional heavy models and GPU setup; placeholders are provided with safe consent checks.

Quick start

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the CLI examples:

```bash
python -m vaaniverse.cli translate "Hello" --src en --tgt hi
python -m vaaniverse.cli speak "Namaste" --lang hi
python -m vaaniverse.cli generate-song "love" --lang hi

Run the web demo (after installing requirements):

```bash
uvicorn vaaniverse.web:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 in your browser.
```

Notes

- Do NOT use this to impersonate public figures without explicit written consent.
- For production-quality singing or voice cloning, replace the placeholder modules with dedicated model implementations (Coqui TTS, VITS, Resemblyzer+SV2TTS, etc.) and follow licensing and consent requirements.
# vaaniverseai