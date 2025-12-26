@echo off
set "PYTHONIOENCODING=utf-8"
setlocal
cd /d "%~dp0"
title ISP Monitor - POSTGRES SERVER

:: Configuração do Banco
:: As configuracoes sao carregadas automaticamente do arquivo .env (backend/.env)

:: Setup Python e Venv
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [!] Iniciando ISP Monitor com POSTGRESQL
echo [!] Banco: monitor_prod
echo.

echo [!] Iniciando Coletor (Log: collector.log)... >> startup.log
start "ISP Collector" /B "%PYTHON_EXE%" backend/collector.py > collector.log 2>&1

:: Rodar Uvicorn com otimizações
echo [!] Iniciando API Uvicorn (Log: api.log)... >> startup.log
"%PYTHON_EXE%" -m uvicorn backend.app.main:app ^
  --host 0.0.0.0 ^
  --port 8080 ^
  --workers 1 ^
  --http h11 ^
  --limit-concurrency 100 ^
  --timeout-keep-alive 30 > api.log 2>&1

if %errorlevel% neq 0 (
    echo [ERROR] O servidor caiu.
    pause
)
