@echo off
cd /d "%~dp0"
title ISP Monitor - Database Init

set PYTHON_CMD=py -3.12

echo [BOOT] Limpando logs antigos...
if not exist logs mkdir logs
type nul > logs\api.log
type nul > logs\collector.log
type nul > logs\snmp.log
type nul > logs\whatsapp.log
type nul > logs\frontend.log
type nul > logs\self_heal.log

echo [BOOT] Inicializando Banco de Dados...
%PYTHON_CMD% -c "from backend.app.database import init_db; import asyncio; asyncio.run(init_db())" > logs\db_init.log 2>&1

echo [BOOT] Banco OK. O Doctor assumira o restante.
exit
