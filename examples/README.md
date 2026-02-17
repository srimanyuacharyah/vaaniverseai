# Examples and quick commands

Run CLI examples:

```bash
python -m vaaniverse.cli translate "Hello" --src en --tgt hi
python -m vaaniverse.cli speak "Namaste" --lang hi
python -m vaaniverse.cli generate-song --theme love --lang hi --save --prefix my_song
python -m vaaniverse.cli clone-voice-cmd sample.wav myvoice --consent True
```

Run the web demo:

```bash
uvicorn vaaniverse.web:app --reload --host 127.0.0.1 --port 8000
```

Run tests:

```bash
pytest -q
```
