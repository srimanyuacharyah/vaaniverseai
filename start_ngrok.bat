@echo off
echo Starting ngrok tunnel to port 8000...
echo.
echo Make sure 'start_web.bat' is running in another terminal window first!
echo.
ngrok http 8000
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] ngrok command failed.
    echo Please download ngrok from https://ngrok.com/download
    echo and ensure it is in your PATH or in this folder.
    pause
)
