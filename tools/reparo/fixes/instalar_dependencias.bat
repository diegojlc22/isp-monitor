@echo off
echo [REPARO] Verificando e instalando dependencias faltantes...

cd /d "%~dp0..\..\.."

:: Instalar no VENV
if exist ".venv\Scripts\python.exe" (
    echo [REPARO] Instalando no ambiente virtual...
    .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
    .\.venv\Scripts\python.exe -m pip install aiohttp
) else (
    echo [REPARO] VENV nao encontrado, instalando no global...
    pip install -r backend\requirements.txt
    pip install aiohttp
)

echo [REPARO] Dependencias verificadas.
exit /b 0
