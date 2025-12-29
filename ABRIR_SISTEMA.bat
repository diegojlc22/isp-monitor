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

:: 2. Auto-Repair (Dependencias Frontend)
if exist "frontend\package.json" (
    if not exist "frontend\node_modules" (
        echo.
        echo  [ISP Monitor] Instalando dependencias do sistema...
        echo  (Isso acontece apenas na primeira vez)
        echo.
        cd frontend
        call npm install
        cd ..
        echo.
    )
)

:: 2.1 Auto-Repair (Dependencias Backend - Ex: openpyxl)
python -c "import openpyxl" >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo  [ISP Monitor] Atualizando bibliotecas Python...
    pip install -r backend\requirements.txt >nul
    echo  [OK] Python atualizado.
    echo.
)

:: 2.2 Auto-Repair (Dependencias Mobile)
if exist "mobile\package.json" (
    if not exist "mobile\node_modules" (
        echo.
        echo  [ISP Monitor] Configurando modulo Mobile...
        echo  (Isso pode demorar um pouco...)
        echo.
        cd mobile
        call npm install --legacy-peer-deps
        cd ..
        echo.
    )
)

:: 3. Iniciar Banco de Dados (PostgreSQL)
powershell -ExecutionPolicy Bypass -File "start_postgres.ps1"

:: 4. Verificar Schema Rapidinho (Silencioso)
powershell -Command "$env:PGPASSWORD='110812'; & 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -U postgres -d isp_monitor -f 'scripts\schema_check.sql' >$null 2>&1"

:: 5. ABRIR O SISTEMA (Finalmente)
echo.
echo  [OK] Abrindo Launcher...
start "" pythonw launcher.pyw

:: Fecha o console rapido
exit
