@echo off
setlocal
cd /d "%~dp0"
title AgriTech V7 - First Time Setup

echo ============================================================
echo  AgriTech V7 - FIRST TIME SETUP
echo ============================================================
echo.

where py >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python launcher "py" was not found.
  echo Install Python 3.11 or 3.12 from python.org and tick "Add Python to PATH".
  pause
  exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js / npm was not found.
  echo Install Node.js LTS, then run this setup again.
  pause
  exit /b 1
)

echo [1/6] Creating Python virtual environment...
if not exist "backend\.venv\Scripts\python.exe" py -m venv "backend\.venv"
if errorlevel 1 goto :fail

echo [2/6] Installing backend dependencies...
"backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :fail

if not exist "backend\.env" copy /Y "backend\.env.example" "backend\.env" >nul

echo [3/6] Testing core AI and image-analysis engine...
pushd backend
".venv\Scripts\python.exe" scripts\self_test.py
if errorlevel 1 (popd & goto :fail)
popd

echo [4/6] Installing optional leaf-specific disease model...
echo       This is about 95 MB and needs internet once.
pushd backend
".venv\Scripts\python.exe" scripts\download_leaf_model.py
if errorlevel 1 (
  echo.
  echo [WARNING] Leaf-specific model could not be downloaded.
  echo AgriTech will STILL analyze leaf/flower/root/stem/fruit photos using its built-in visual triage.
  echo Later run INSTALL_OR_REPAIR_LEAF_AI.bat to enable exact supported-leaf diagnosis.
) else (
  echo Leaf-specific model downloaded. Verifying ONNX inference...
  ".venv\Scripts\python.exe" scripts\self_test.py
  if errorlevel 1 (
    echo [WARNING] The leaf model downloaded but failed its inference check.
    echo Broad plant-part visual triage will still work.
  ) else (
    echo Leaf-specific model installed and tested successfully.
  )
)
popd

echo [5/6] Installing frontend dependencies...
pushd frontend
call npm install
if errorlevel 1 (popd & goto :fail)

echo [6/6] Building frontend production bundle as a syntax check...
call npm run build
if errorlevel 1 (popd & goto :fail)
popd

echo.
echo ============================================================
echo  SETUP COMPLETE
echo  From now on, only double-click RUN_PROJECT.bat
echo ============================================================
pause
exit /b 0

:fail
echo.
echo ============================================================
echo  SETUP FAILED - read the error shown above.
echo ============================================================
pause
exit /b 1
