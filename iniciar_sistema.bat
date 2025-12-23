@echo off
cd /d "%~dp0"
title ISP Monitor - Boot
echo Iniciando script de reparo via PowerShell...
:: -NoExit mantem a janela aberta para vermos o erro
PowerShell -NoProfile -ExecutionPolicy Bypass -NoExit -File "repair.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERRO CRITICO] O script PowerShell falhou.
    pause
)
