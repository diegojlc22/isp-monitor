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

:: 2. Garante PostgreSQL
echo [1/3] Iniciando PostgreSQL...
powershell -ExecutionPolicy Bypass -File "start_postgres.ps1"

:: 3. Garante Dependências (Caso falte algo no ambiente Admin)
echo [2/3] Verificando dependencias...
python -c "import pysnmp.hlapi.asyncio" >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Dependencias faltando no ambiente Administrador. Instalando...
    python -m pip install -r requirements.txt >nul
)

:: 4. Inicia Launcher
echo [3/3] Abrindo Launcher...
start pythonw launcher.pyw

echo.
echo [OK] Tudo pronto! Esta janela fechara em 5 segundos.
timeout /t 5 /nobreak >nul
exit
