@echo off
REM Site manager launcher for caichao.github.com
REM Uses Python 3 with absolute path. No external deps.
cd /d "%~dp0"

set "PY_EXE="

if exist "C:\Users\chris\.workbuddy\binaries\python\versions\3.13.12\python.exe" (
    set "PY_EXE=C:\Users\chris\.workbuddy\binaries\python\versions\3.13.12\python.exe"
)

if not defined PY_EXE (
    if exist "C:\Users\chris\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" (
        set "PY_EXE=C:\Users\chris\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
    )
)

if not defined PY_EXE (
    if exist "C:\Users\chris\AppData\Local\Programs\Python\Python313\python.exe" (
        set "PY_EXE=C:\Users\chris\AppData\Local\Programs\Python\Python313\python.exe"
    )
)

if not defined PY_EXE (
    echo ERROR: Python not found.
    echo Please install Python 3.x and check "Add Python to PATH".
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Using Python: %PY_EXE%
echo Starting site manager...
"%PY_EXE%" "%~dp0site_manager.py"

if errorlevel 1 (
    echo.
    echo ERROR: Program exited with code %errorlevel%.
    pause
)
