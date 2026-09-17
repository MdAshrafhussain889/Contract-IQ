@echo off
rem ============================================================
rem  Contract-IQ - Windows start script
rem  Loads the venv and starts the FastAPI server
rem ============================================================

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found. Run setup.bat first.
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"
python main.py