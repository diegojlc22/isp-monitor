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

:: 5. Inicializa Schema do Banco de Dados
echo [4/6] Verificando schema do banco...
python scripts\init_database.py >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Schema do banco verificado!
) else (
    echo [!] Aviso: Erro ao verificar schema do banco
)

:: 6. Inicia Launcher
echo [5/6] Abrindo Launcher...
start pythonw launcher.pyw

echo.
echo [6/6] Sistema iniciado com sucesso!
echo [OK] Tudo pronto! Esta janela fechara em 5 segundos.
timeout /t 5 /nobreak >nul
exit
