@echo off
cd /d "%~dp0backend"
echo WARNING: This deletes all AgriTech local accounts, farms, scans and history.
set /p OK=Type YES to continue: 
if /I not "%OK%"=="YES" exit /b 0
del /Q agritech_v7.db 2>nul
echo Database deleted. It will be recreated on next run.
pause
