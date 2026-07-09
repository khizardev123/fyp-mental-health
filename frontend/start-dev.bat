@echo off
set NODE=%~dp0..\.node\node-v20.11.0-win-x64
set PATH=%NODE%;%PATH%
cd /d "%~dp0"
echo Starting SereneMind Frontend on port 3001...
echo.
npm run dev
