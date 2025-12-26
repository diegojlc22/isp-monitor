@echo off
:: Launcher ISP Monitor - Otimizado
cd /d "%~dp0"

:: 1. Verificar se Python está instalado (Sistema ou Venv)
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python nao detectado no PATH global. Verificando configuracao...
)

:: 2. Verificar se ambiente virtual (venv) existe e esta pronto
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [PRIMEIRA EXECUCAO] Configurando o sistema automaticamente...
    echo Isso pode levar alguns minutos. Por favor aguarde.
    echo.
    powershell -ExecutionPolicy Bypass -File "setup.ps1"
    echo.
    echo [SETUP CONCLUIDO] Iniciando Launcher...
)

:: 3. Iniciar aplicacao
:: Tenta usar o python do venv se existir, senao usa o global
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "launcher.pyw"
) else (
    start "" "pythonw.exe" "launcher.pyw"
)

exit
