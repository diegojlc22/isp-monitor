@echo off
set PGPASSWORD=110812
set PGUSER=postgres
set PGDATABASE=isp_monitor
set BACKUP_DIR=backups
set DATE_STR=%date:~6,4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set DATE_STR=%DATE_STR: =0%
set BACKUP_FILE=%BACKUP_DIR%\backup_full_%DATE_STR%.sql

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo [BACKUP] Adicionando PostgreSQL ao PATH...
set PATH=%PATH%;C:\Program Files\PostgreSQL\14\bin;C:\Program Files\PostgreSQL\15\bin;C:\Program Files\PostgreSQL\16\bin;C:\Program Files\PostgreSQL\17\bin

echo [BACKUP] Iniciando backup de %PGDATABASE%...
echo [BACKUP] Arquivo: %BACKUP_FILE%

pg_dump -h localhost -U %PGUSER% -F c -b -v -f "%BACKUP_FILE%" %PGDATABASE%

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCESSO] Backup concluido com sucesso!
    echo Arquivo salvo em: %BACKUP_FILE%
) else (
    echo.
    echo [ERRO] Falha ao realizar backup. Verifique se o PostgreSQL esta instalado e rodando.
)

pause
