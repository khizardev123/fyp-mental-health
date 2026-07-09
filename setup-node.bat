@echo off
REM Download portable Node.js v20 LTS
echo Downloading Node.js...
set TEMP_DIR=%TEMP%\node-setup
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM Download Node.js (you may need to adjust URL for your system)
cd "%TEMP_DIR%"
powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip' -OutFile 'node.zip'" 2>nul

if not exist "node.zip" (
    echo Failed to download Node.js. Please install Node.js manually from https://nodejs.org/
    pause
    exit /b 1
)

echo Extracting...
powershell -Command "Expand-Archive -Path 'node.zip' -DestinationPath '.' -Force" 2>nul

REM Copy to project
echo Setting up Node.js in frontend...
cd /d "e:\UMT\FYP\Ultimate final version for FYP-1\khizer fyp\khizer fyp\serenemind\frontend"
if exist "%TEMP_DIR%\node-v20.11.1-win-x64" (
    set NODE_PATH=%TEMP_DIR%\node-v20.11.1-win-x64
    echo Node.js ready
) else (
    echo Setup failed
    pause
    exit /b 1
)
