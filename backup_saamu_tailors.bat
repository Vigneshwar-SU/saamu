@echo off
cd /d D:\projects\Saamu\saamu\backend

REM Create and verify a new PostgreSQL backup
D:\projects\Saamu\saamu\backend\.venv\Scripts\python.exe manage.py db_backup

REM Only clean old backups if the backup command succeeded
if %ERRORLEVEL% EQU 0 (
    D:\projects\Saamu\saamu\backend\.venv\Scripts\python.exe manage.py db_cleanup --keep 30 --execute
)

exit /b