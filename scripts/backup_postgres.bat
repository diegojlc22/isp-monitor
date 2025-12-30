@echo off
cd /d "%~dp0"
cd ..

set PGPASSWORD=110812
set TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_DIR=backups

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo [BACKUP] Iniciando backup do banco de dados isp_monitor...

:: Tenta achar pg_dump automaticamente
if exist "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" (
    set PG_DUMP="C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"
) else if exist "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" (
    set PG_DUMP="C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"
) else (
    echo [ERRO] PostgreSQL nao encontrado.
    exit /b 1
)

%PG_DUMP% -U postgres -h localhost -d isp_monitor -F c -b -v -f "%BACKUP_DIR%\isp_monitor_%TIMESTAMP%.backup"

if %ERRORLEVEL% EQU 0 (
    echo [SUCESSO] Backup salvo em: %BACKUP_DIR%\isp_monitor_%TIMESTAMP%.backup
) else (
    echo [ERRO] Falha ao realizar backup.
)

