@echo off
cd /d D:\projects\Saamu\saamu\backend
D:\projects\Saamu\saamu\backend\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:8000 config.wsgi:application