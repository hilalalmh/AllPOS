@echo off
REM Start React web dashboard (Vite) on port 5173.
cd /d "%~dp0..\web\sistem_pos_dashboard"
start "SistemPOS-Web" /min cmd /k "npm run dev"