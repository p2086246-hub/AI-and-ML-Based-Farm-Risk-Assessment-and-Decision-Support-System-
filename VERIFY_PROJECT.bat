@echo off
setlocal
cd /d "%~dp0"
title AgriTech V7 - Verify Project

if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] Backend environment missing. Run START_HERE_FIRST_TIME.bat first.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo [ERROR] Frontend packages missing. Run START_HERE_FIRST_TIME.bat first.
  pause
  exit /b 1
)

echo [1/2] Running backend AI self-test...
pushd backend
".venv\Scripts\python.exe" scripts\self_test.py
if errorlevel 1 (popd & goto :fail)
popd

echo [2/2] Building frontend...
pushd frontend
call npm run build
if errorlevel 1 (popd & goto :fail)
popd

echo.
echo ============================================================
echo  AGRITECH V7 VERIFICATION PASSED
 echo ============================================================
pause
exit /b 0

:fail
echo.
echo ============================================================
echo  VERIFICATION FAILED - read the error above.
echo ============================================================
pause
exit /b 1
