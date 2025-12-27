@echo off
cd /d "%~dp0"
title ISP Monitor - Bootloader (v4.0 Final)

:: ==============================================
:: FASE 1: VERIFICAÇÃO RELÂMPAGO (Milisegundos)
:: ==============================================

:: 1. Verifica se temos o Python 3.12 (A versão oficial do projeto)
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 ( goto :RECOVERY_MODE )

:: 2. Verifica integridade do Launcher (Código e Libs) usando o 'Cirurgião'
py -3.12 "tools\repair\doctor_launcher.py" >nul 2>&1
if %errorlevel% neq 0 ( goto :RECOVERY_MODE )

:: ==============================================
:: FASE 2: LANÇAMENTO SEGURO
:: ==============================================
:: Se chegou aqui, está tudo 100%. Lança sem janela preta.
start "" "launcher.pyw"
exit

:: ==============================================
:: FASE 3: MODO DE RECUPERAÇÃO AUTOMÁTICA
:: ==============================================
:RECOVERY_MODE
cls
color 4f
echo =======================================================
echo [SISTEMA] DIAGNOSTICO DE FALHA AUTOMATICO
echo =======================================================
echo O Launcher nao pode iniciar. Motivo possivel:
echo  - Python 3.12 ausente
echo  - Bibliotecas corrompidas
echo  - Erro no codigo
echo.
echo [AUTO] Iniciando reparo...
timeout /t 2 >nul
call REPARAR_TUDO.bat
exit
