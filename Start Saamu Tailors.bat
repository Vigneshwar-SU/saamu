@echo off
title Saamu Tailors ERP

echo ========================================
echo        SAAMU TAILORS ERP
echo           Since 1954
echo ========================================
echo.
echo Starting Saamu Tailors ERP...
echo Please wait...

cd /d "D:\projects\Saamu\saamu"

REM Start Django Backend
start "Saamu Backend" /min cmd /c "cd /d D:\projects\Saamu\saamu\backend && .venv\Scripts\python.exe manage.py runserver 8001"

REM Wait for backend
timeout /t 4 /nobreak >nul

REM Start React Frontend
start "Saamu Frontend" /min cmd /c "cd /d D:\projects\Saamu\saamu\frontend && npm.cmd run dev"

REM Wait for frontend
timeout /t 5 /nobreak >nul

REM Open Saamu Tailors
start "" "http://localhost:5173"

exit