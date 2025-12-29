@echo off
setlocal enabledelayedexpansion

:: ISP Monitor Launcher - Versão de Reparo Automático
cd /d "%~dp0"

:: 1. Tenta iniciar o PostgreSQL (precisa de Admin)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ISP Monitor] Solicitando Administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %~dp0 && ABRIR_SISTEMA.bat' -Verb RunAs"
    exit
)

echo ========================================
echo  ISP Monitor - Iniciando Sistema
echo ========================================
echo.

:: 1. Auto-Setup (Cria .env se não existir)
echo [0/4] Configuracao automatica...
powershell -ExecutionPolicy Bypass -File "auto_setup_env.ps1"

:: 2. Garante PostgreSQL
echo [1/4] Iniciando PostgreSQL...
powershell -ExecutionPolicy Bypass -File "start_postgres.ps1"

:: 3. Garante Dependências Python
echo [2/5] Verificando dependencias Python...
python -c "import pysnmp.hlapi.asyncio" >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Dependencias faltando no ambiente Administrador. Instalando...
    python -m pip install -r requirements.txt >nul
)

:: 4. Garante Dependências WhatsApp (Node.js)
echo [3/6] Verificando dependencias WhatsApp...
if exist "tools\whatsapp\package.json" (
    if not exist "tools\whatsapp\node_modules" (
        echo [!] Instalando dependencias do WhatsApp...
        cd tools\whatsapp
        call npm install >nul 2>&1
        cd ..\..
        echo [OK] Dependencias do WhatsApp instaladas!
    )
)

:: 5. Garante Dependências Frontend (Node.js)
echo [4/7] Verificando dependencias Frontend...
if exist "frontend\package.json" (
    if not exist "frontend\node_modules" (
        echo [!] Instalando dependencias do Frontend...
        cd frontend
        call npm install >nul 2>&1
        cd ..
        echo [OK] Dependencias do Frontend instaladas!
    )
)

:: 6. Inicializa Schema do Banco de Dados (PostgreSQL)
echo [5/7] Verificando schema do banco...
powershell -Command "$env:PGPASSWORD='110812'; if (Test-Path 'C:\Program Files\PostgreSQL\17\bin\psql.exe') { & 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -U postgres -d isp_monitor -c 'ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_ping FLOAT; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_latency FLOAT; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_traffic_in BIGINT; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_traffic_out BIGINT; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS signal_dbm INTEGER; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS ccq INTEGER; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS connected_clients INTEGER;' 2>$null; if ($LASTEXITCODE -eq 0) { Write-Host '[OK] Schema verificado!' -ForegroundColor Green } } else { Write-Host '[!] PostgreSQL nao encontrado, pulando...' -ForegroundColor Yellow }"

:: 7. Inicia Launcher
echo [6/7] Abrindo Launcher...
start pythonw launcher.pyw

echo.
echo [7/7] Sistema iniciado com sucesso!
echo [OK] Tudo pronto! Esta janela fechara em 5 segundos.
timeout /t 5 /nobreak >nul
exit
