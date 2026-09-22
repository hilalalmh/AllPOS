@echo off
wmic process where "name='python.exe' and commandline like '%%uvicorn%%'" call terminate >nul 2>&1
timeout /t 2 /nobreak >nul
cd /d "%~dp0..\backend"
start "SistemPOS-Backend" /min cmd /k "call .venv\Scripts\activate.bat && set PYTHONPATH=D:\Freelance\AllPOS\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"