@echo off
cd /d "%~dp0"
title ISP Monitor - Boot

:: ==========================================
:: AUTO-UPDATE (GITHUB)
:: ==========================================
if exist ".git" (
    echo [UPDATE] Verificando atualizacoes no GitHub...
    git pull origin main
    echo.
) else (
    echo [INFO] Repositorio Git nao detectado. Pulando atualizacao automatica.
)

echo Iniciando script de reparo via PowerShell...
:: Script de boot automatico
PowerShell -NoProfile -ExecutionPolicy Bypass -File "repair.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERRO CRITICO] O script PowerShell falhou.
    pause
)
