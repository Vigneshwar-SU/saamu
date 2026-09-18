@echo off
cd /d D:\Projects\saamu\backend
D:\Projects\saamu\backend\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:8000 config.wsgi:application