@echo off
REM Start FastAPI backend (uvicorn) on port 8000.
cd /d "%~dp0..\backend"
start "SistemPOS-Backend" /min cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"