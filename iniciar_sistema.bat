@echo off
cd /d "%~dp0"
title ISP Monitor - Boot

echo [BOOT] Iniciando ISP Monitor...

if not exist "repair.ps1" (
    echo [ERRO CRITICO] Arquivo 'repair.ps1' nao encontrado!
    echo Verifique se os arquivos do projeto estao completos.
    pause
    exit
)

:: Script de boot automatico (Gerencia Python, Venv e Launcher)
PowerShell -NoProfile -ExecutionPolicy Bypass -File "repair.ps1"

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] O script de inicializacao falhou.
    pause
)
