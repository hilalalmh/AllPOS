@echo off
cd /d D:\Freelance\AllPOS\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000