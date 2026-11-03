@echo off
cd /d "%~dp0"
if not exist "backend\.venv\Scripts\python.exe" (
  echo Run SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
pushd backend
".venv\Scripts\python.exe" scripts\download_leaf_model.py
if errorlevel 1 (
  echo Download failed. Check internet and run this file again.
) else (
  echo Leaf-specific AI installed successfully.
  ".venv\Scripts\python.exe" scripts\self_test.py
)
popd
pause
