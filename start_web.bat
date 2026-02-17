@echo off
REM Start the Vaaniverse AI demo web server
python -m uvicorn vaaniverse.web:app --reload --host 127.0.0.1 --port 8000
