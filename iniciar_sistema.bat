@echo off
cd /d "%~dp0"
title ISP Monitor - Boot

:: ==========================================
:: VERIFICACAO DE AMBIENTE E AUTO-UPDATE
:: ==========================================

:: 1. Verificar se o Git esta instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO FATAL] O Git nao esta instalado ou nao esta no PATH.
    echo Por favor, instale o Git para Windows: https://git-scm.com/download/win
    echo Apos instalar, reabra este arquivo.
    pause
    exit
)

:: 2. Verificar se e a primeira vez (Instalacao)
if not exist ".git" (
    echo [SETUP] Detectado primeira execucao (Repositorio ausente).
    echo [SETUP] Baixando sistema completo do GitHub...
    
    :: Clona para pasta temporaria _install_tmp
    git clone https://github.com/diegojlc22/isp-monitor.git _install_tmp
    
    if exist "_install_tmp" (
        echo [SETUP] Configurando arquivos...
        :: Copia tudo, incluindo ocultos (/H) e subpastas (/E), subscrevendo (/Y)
        xcopy /E /Y /H "_install_tmp\*" "." >nul
        
        :: Remove pasta temporaria
        rmdir /S /Q "_install_tmp"
        
        echo [SETUP] Instalacao concluida!
        echo.
    ) else (
        echo [ERRO] Falha ao baixar do GitHub. Verifique sua conexao internet.
        pause
        exit
    )
) else (
    :: 3. Se ja existe, apenas atualiza
    echo [UPDATE] Buscando atualizacoes...
    git pull origin main
    echo.
)

echo Iniciando script de reparo via PowerShell...
:: Script de boot automatico
PowerShell -NoProfile -ExecutionPolicy Bypass -File "repair.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERRO CRITICO] O script PowerShell falhou.
    pause
)
