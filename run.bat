@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. First run install.bat.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py
echo.
pause
