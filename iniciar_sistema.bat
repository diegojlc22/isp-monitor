@echo off
cd /d "%~dp0"
title ISP Monitor - Boot
echo Iniciando script de reparo via PowerShell...
:: Script de boot automatico
PowerShell -NoProfile -ExecutionPolicy Bypass -File "repair.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERRO CRITICO] O script PowerShell falhou.
    pause
)
