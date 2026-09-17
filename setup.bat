@echo off
rem ============================================================
rem  Contract-IQ - Windows setup script
rem  Creates venv, installs dependencies, prepares .env
rem ============================================================

cd /d "%~dp0"

echo Setting up Contract-IQ...

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Python was not found on PATH.
    echo Install Python 3.10 from https://www.python.org/downloads/
    echo and tick "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python version:
python --version

rem ---- 1. Create venv if missing ----
if not exist "venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
)

rem ---- 2. Activate and install dependencies ----
call "venv\Scripts\activate.bat"

echo.
echo Installing / upgrading dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

rem ---- 3. Prepare .env if missing ----
if not exist ".env" (
    echo.
    echo Creating .env from .env.example...
    copy /y ".env.example" ".env" >nul
    echo.
    echo [IMPORTANT] Open ".env" and set OPENAI_API_KEY=sk-your-key-here
)

echo.
echo ============================================================
echo  Setup complete!
echo   - Run  start.bat  to start the API
echo   - API will be at  http://localhost:8000
echo   - Swagger docs at http://localhost:8000/docs
echo ============================================================
pause