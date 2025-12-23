@echo off
setlocal
cd /d "%~dp0"
title ISP Monitor - Bootstrapper

:: 1. Tenta detectar Python (comando python ou py)
python --version >nul 2>&1
if %errorlevel% equ 0 goto :LAUNCH

py --version >nul 2>&1
if %errorlevel% equ 0 goto :LAUNCH

:: 2. Se chegou aqui, nao achou Python. Instalação:
echo [!] Python nao detectado no sistema.
echo [!] Iniciando download do instalador (isso pode levar alguns segundos)...

:: Remove arquivo antigo se existir
if exist "python_installer.exe" del "python_installer.exe"

:: Download via Curl (com flag -L para seguir redirects)
curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe

:: Verifica se baixou
if not exist "python_installer.exe" (
    echo.
    echo [ERROR] Falha no download do Python.
    echo O arquivo instalador nao foi criado.
    pause
    exit /b
)

echo [!] Download concluido. Instalando Python...
echo [!] Uma janela de permissao pode aparecer. Por favor, aceite.

:: Instala (Wait garante esperar terminar)
start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: Limpeza
if exist "python_installer.exe" del "python_installer.exe"

echo [!] Python instalado.
echo [!] Tentando iniciar o sistema...

:LAUNCH
:: Verifica se setup_gui.py existe
if not exist "setup_gui.py" (
   echo [ERROR] Arquivo setup_gui.py nao encontrado!
   pause
   exit /b
)

:: Tenta rodar com python ou py
python setup_gui.py >nul 2>&1
if %errorlevel% neq 0 (
    py setup_gui.py >nul 2>&1
)

exit /b
