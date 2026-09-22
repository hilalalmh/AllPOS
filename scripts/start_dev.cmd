@echo off
REM Start both backend and web in separate (minimized) windows.
call "%~dp0start_backend.cmd"
call "%~dp0start_web.cmd"
echo.
echo Backend  -> http://localhost:8000/api/v1/health
echo Web      -> http://localhost:5173