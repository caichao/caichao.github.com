@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

rem ============================================================
rem  update_photos.bat  -- one-click photo gallery updater
rem  (all human messages are printed by build_photos.py in Chinese)
rem ============================================================

rem --- find Python: try py, python, python3 ---
set "PY="
for %%P in (py python python3) do (
    if not defined PY (
        where %%P >nul 2>nul
        if not errorlevel 1 set "PY=%%P"
    )
)
if not defined PY (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b 1
)

rem --- run the builder; it prints status in Chinese and does git add/commit/push ---
!PY! build_photos.py --publish
set "RC=!errorlevel!"

echo.
pause
exit /b !RC!
