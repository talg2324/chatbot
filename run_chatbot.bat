@echo off
setlocal

REM Step 1: Check if Ollama server is running
tasklist /FI "IMAGENAME eq ollama.exe" | find /I "ollama.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Starting Ollama server...
    start "" /B ollama serve
    timeout /t 3 >nul
) else (
    echo Ollama server already running.
)

REM Step 2: Activate virtual environment
call .venv\Scripts\activate.bat

REM Step 3: Run the script
python main.py

endlocal
pause
