@echo off
setlocal
cd /d "%~dp0"
call SETUP_WINDOWS.bat
if errorlevel 1 exit /b 1
echo.
echo Starting AgriTech...
call RUN_PROJECT.bat
