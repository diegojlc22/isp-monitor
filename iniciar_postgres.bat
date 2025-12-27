@echo off
cd /d "%~dp0"
TITLE ISP Monitor - Enterprise System
CLS

:: -------------------------------------------------------------------------
:: AMBIENTE PURO (Standalone Mode)
:: -------------------------------------------------------------------------

:: 1. Limpar variáveis de ambiente tóxicas
set PYTHONHOME=
set PYTHONPATH=
set PYTHONEXECUTABLE=
set PYTHONUTF8=1

:: 2. Selecionar Python (Prioridade absoluta para python_bin portátil)
if exist "python_bin\python.exe" (
    :: Caminho absoluto para evitar problemas de PATH
    for %%I in ("python_bin\python.exe") do set "PY=%%~fI"
    echo [LAUNCHER] Usando Python Portatil: "%PY%"
) else (
    if exist ".venv\Scripts\python.exe" (
        for %%I in (".venv\Scripts\python.exe") do set "PY=%%~fI"
        echo [LAUNCHER] Usando Python Venv: "%PY%"
    ) else (
        set "PY=python"
        echo [LAUNCHER] Usando Python do Sistema
    )
)

:: 3. Verificacao de Segurança (Instalar libs se faltar)
if not exist ".boot_python_ready" (
    echo [LAUNCHER] Garantindo integridade do ambiente Python...
    "%PY%" -m pip install -r backend/requirements.txt --quiet --no-warn-script-location
    
    :: Criar flag de sucesso
    echo OK > .boot_python_ready
)

:: 4. INICIAR SISTEMA
echo.
echo [1/3] Backend API (Porta 8080)...
start "ISP Backend" /b "%PY%" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --log-level info > api.log 2>&1

echo [2/3] Pinger V2 (Turbo)...
start "ISP Pinger" /b "%PY%" -m backend.app.services.pinger_fast > collector.log 2>&1

echo [3/3] Frontend Interface...
if not exist "frontend\node_modules" (
    echo [INFO] Instalando modulos do Frontend...
    cd frontend && npm install --silent && cd ..
)
:: Frontend em background com logs
start "ISP Frontend" /b cmd /c "npm run dev --prefix frontend > frontend.log 2>&1"

echo.
echo [SUCESSO] Sistema Iniciado.
timeout /t 3 >nul
exit
