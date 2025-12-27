@echo off
title ISP Monitor - Auto Repair Check
color 0e
cd /d "%~dp0"

echo ========================================================
echo      CENTRAL DE AUTO-REPARO (BOOT CHECK)
echo ========================================================
echo [STATUS] Verificando integridade do sistema...

:: 1. Tentar detectar Python via Launcher Oficial (Mais robusto que PATH)
py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python 3.12 detectado.
    goto :INSTALL_LIBS
)

echo.
echo [ALERTA] Python 3.12 nao encontrado!
echo [IA] Iniciando instalacao do ambiente...
echo.

:: 2. Disparar Auto-Setup (PowerShell)
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\repair\auto_setup.ps1"

if %errorlevel% neq 0 (
    color 4f
    echo [FATAL] Nao foi possivel reparar automaticamente.
    pause
    exit
)

:INSTALL_LIBS
echo.
echo [SETUP] Verificando e Instalando Bibliotecas...
:: O comando abaixo garante que as libs existam, sem reinstalar o Python todo
py -3.12 -m pip install -r backend/requirements.txt --quiet --no-warn-script-location
if %errorlevel% neq 0 (
    echo [AVISO] Erro ao instalar libs.
)

:LAUNCH
echo.
echo [OK] Sistema integro.
echo Iniciando...
timeout /t 2 >nul
start "" "ABRIR_SISTEMA.bat"
exit
