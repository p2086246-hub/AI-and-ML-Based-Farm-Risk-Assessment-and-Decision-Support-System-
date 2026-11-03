@echo off
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
  echo First-time setup is missing. Run START_HERE_FIRST_TIME.bat
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo Frontend dependencies are missing. Run START_HERE_FIRST_TIME.bat
  pause
  exit /b 1
)

start "AgriTech Backend - KEEP OPEN" cmd /k "cd /d ""%~dp0backend"" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 3 /nobreak >nul
start "AgriTech Frontend - KEEP OPEN" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 127.0.0.1"
timeout /t 4 /nobreak >nul
start "" "http://localhost:5173"
exit /b 0
