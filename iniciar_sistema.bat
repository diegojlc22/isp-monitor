@echo off
setlocal
cd /d "%~dp0"
title ISP Monitor

:: ==============================================================================
:: VERIFICAÇÃO RÁPIDA (FAST PATH)
:: Se o ambiente já estiver pronto (venv e node_modules), pula a instalação e abre direto.
:: ==============================================================================

if exist ".venv\Scripts\pythonw.exe" (
    if exist "frontend\node_modules" (
        :: Inicia o Launcher imediatamente de forma oculta (sem terminal)
        start "" ".venv\Scripts\pythonw.exe" launcher.pyw
        exit /b
    )
)

:: ==============================================================================
:: INSTALAÇÃO / CONFIGURAÇÃO (SLOW PATH)
:: Só executa se for a primeira vez ou se as pastas sumirem.
:: ==============================================================================

echo [!] Configurando ambiente de primeira execucao...

:: 1. Tenta detectar Python no sistema
python --version >nul 2>&1
if %errorlevel% equ 0 goto :SETUP
py --version >nul 2>&1
if %errorlevel% equ 0 goto :SETUP

:: 2. Se nao achou Python, baixa e instala
echo [!] Python nao detectado. Baixando instalador portatil...
if exist "python_installer.exe" del "python_installer.exe"
curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe

if not exist "python_installer.exe" (
    echo [ERROR] Falha no download do Python.
    pause
    exit /b
)

echo [!] Instalando Python (aceite a permissao)...
start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
if exist "python_installer.exe" del "python_installer.exe"

:SETUP
:: Executa o assistente de instalacao (GUI) que cria a venv e instala libs
if exist "setup_gui.py" (
    python setup_gui.py >nul 2>&1
    if %errorlevel% neq 0 (
        py setup_gui.py >nul 2>&1
    )
) else (
    echo [ERROR] setup_gui.py nao encontrado.
    pause
)

exit /b
