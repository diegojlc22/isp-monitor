@echo off
cd /d "%~dp0"
title ISP Monitor - Backend & Services

:: Forçar uso do Python 3.12 (Blindado)
set PYTHON_CMD=py -3.12

echo [BOOT] Iniciando Servicos em Background (Modo Invisivel)...

:: 1. Migracao/Setup de Banco (Rapido e Sincrono)
%PYTHON_CMD% -c "from backend.app.database import init_db; import asyncio; asyncio.run(init_db())" >nul 2>&1

:: 2. Iniciar API (Uvicorn)
:: Usa /B para rodar na mesma janela (que ja esta oculta pelo launcher)
echo [1/3] Iniciando API...
start /b "" %PYTHON_CMD% -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --workers 1 > logs\api.log 2>&1

:: 3. Iniciar Coletor (Pinger)
echo [2/3] Iniciando Coletor Pinger...
start /b "" %PYTHON_CMD% -m backend.app.services.pinger_fast > logs\collector.log 2>&1

:: 3.1. Iniciar Monitor SNMP (Trafego/Wireless)
echo [2.5/3] Iniciando Monitor SNMP...
start /b "" %PYTHON_CMD% -m backend.app.services.snmp_monitor > logs\snmp.log 2>&1

:: 4. Iniciar Frontend
echo [3/3] Iniciando Frontend...
cd frontend
if exist "node_modules" (
    start /b "" npm run dev > ..\logs\frontend.log 2>&1
) else (
    echo [AVISO] Node_modules faltando. Instalando...
    call npm install
    start /b "" npm run dev > ..\logs\frontend.log 2>&1
)

:: 5. Iniciar Gateway WhatsApp
echo [4/4] Iniciando Gateway WhatsApp...
if exist "tools\whatsapp" (
    cd tools\whatsapp
    if not exist "node_modules" (
        echo [ZAP] Instalando dependencias...
        call npm install >nul 2>&1
    )
    start /b "" npm start > ..\..\logs\whatsapp.log 2>&1
    cd ..\..
) else (
    echo [AVISO] Pasta tools\whatsapp nao encontrada.
)

:: IMPORTANTE:
:: Como usamos start /b, se este script fechar, os processos morrem.
:: Mantemos ele vivo indefinidamente em loop de espera economica.
:: O Launcher vai matar este processo (e filhos) quando fechar.
cd ..
echo [SISTEMA] Aguardando terminacao...
cmd /c "exit /b" 2>nul & pause >nul
