@echo off
set PY=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe
set NODE=%~dp0.node\node-v20.11.0-win-x64
set PATH=%NODE%;%PATH%

echo Starting SereneMind services...
echo.

start "SereneMind AI" /D "%~dp0services\ai-service" cmd /k "%PY% -m uvicorn main:app --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak >nul

start "SereneMind Avatar" /D "%~dp0services\avatar-service" cmd /k "%PY% -m uvicorn main:app --host 127.0.0.1 --port 8001"
timeout /t 3 /nobreak >nul

start "SereneMind Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo Services starting. Ensure Ollama is running on port 11434.
echo   SereneMind:  http://localhost:3001/dashboard
echo   Main site:   http://localhost:3000  (unchanged)
echo   Avatar:    http://127.0.0.1:8001/health/ready
echo   AI:        http://127.0.0.1:8000/health
echo.
