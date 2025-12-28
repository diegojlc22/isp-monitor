@echo off
cd /d "%~dp0"
title ISP Monitor - Bootloader (v4.1 Fast)

echo [BOOT] Verificando ambiente...
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python 3.12 nao encontrado! Pressione qualquer tecla...
    pause
    exit
)

echo [BOOT] Iniciando Launcher...
start "" "launcher.pyw"
exit
