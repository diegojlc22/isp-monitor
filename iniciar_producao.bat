@echo off
setlocal
cd /d "%~dp0"
title ISP Monitor - SERVER (Producao)

:: Setup Python e Venv (Reutiliza logica simplificada)
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [!] Iniciando ISP Monitor em MODO PRODUCAO
echo [!] Frontend integrado (sem terminal extra)
echo [!] Logs simplificados
echo.

:: Rodar Uvicorn sem reload, permitindo acesso externo e servindo frontend estatico
:: --workers 1 garante estabilidade do SQLite (ja que nao usamos WAL com multiprocess writer seguro em config simples)
"%PYTHON_EXE%" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --workers 1

if %errorlevel% neq 0 (
    echo [ERROR] O servidor caiu.
    pause
)
