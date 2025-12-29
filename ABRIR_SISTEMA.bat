@echo off
cd /d "%~dp0"

:: 1. Verificacao Simples de Admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ISP Monitor] Preciso de permissao de Administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo.
echo  [ISP Monitor] Inicializando...
echo.

:: 2. Iniciar Banco de Dados (PostgreSQL)
powershell -ExecutionPolicy Bypass -File "start_postgres.ps1"

:: 3. Verificar Schema Rapidinho (Silencioso)
powershell -Command "$env:PGPASSWORD='110812'; & 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -U postgres -d isp_monitor -f 'scripts\schema_check.sql' >$null 2>&1"

:: 4. ABRIR O SISTEMA (Finalmente)
echo.
echo  [OK] Abrindo Launcher...
start "" pythonw launcher.pyw

:: Fecha o console rapido
exit
