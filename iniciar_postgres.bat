@echo off
setlocal
cd /d "%~dp0"
title ISP Monitor - POSTGRES SERVER

:: Configuração do Banco
set "DATABASE_URL=postgresql+asyncpg://postgres:110812@localhost:5432/monitor_prod"

:: Setup Python e Venv
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [!] Iniciando ISP Monitor com POSTGRESQL
echo [!] Banco: monitor_prod
echo.

:: Rodar Uvicorn com otimizações
"%PYTHON_EXE%" -m uvicorn backend.app.main:app ^
  --host 0.0.0.0 ^
  --port 8080 ^
  --workers 1 ^
  --http h11 ^
  --limit-concurrency 100 ^
  --timeout-keep-alive 30

if %errorlevel% neq 0 (
    echo [ERROR] O servidor caiu.
    pause
)
