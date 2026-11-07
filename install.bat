@echo off
setlocal
cd /d "%~dp0"
py -m venv .venv
if errorlevel 1 goto error
call .venv\Scripts\activate.bat
py -m pip install --upgrade pip
if errorlevel 1 goto error
py -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo Setup complete. Run run.bat to start.
pause
exit /b 0
:error
echo.
echo Setup failed. Read the error above and check README.md.
pause
exit /b 1
