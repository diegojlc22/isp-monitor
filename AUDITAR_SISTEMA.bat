@echo off
title ISP Monitor - Auditoria de Sistema
color 0f
cd /d "%~dp0"

echo [INIT] Iniciando Auditoria...
:: Usa o launcher py para garantir versao correta (3.12)
py -3.12 "tools\audit\system_audit.py"

if %errorlevel% neq 0 (
    echo.
    echo [FALHA] Nao foi possivel rodar a auditoria (Python nao encontrado?)
    echo Tentando abrir o REPARADOR...
    timeout /t 3
    start "" "REPARAR_TUDO.bat"
)
exit
