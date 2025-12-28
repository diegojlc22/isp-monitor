@echo off
:: Reparo de Dependências - Modo Administrador
cd /d "%~dp0"

:: Solicita Admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Solicitando privilegios de Administrador para instalar pacotes...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo ========================================
echo  ISP Monitor - Reparo de Dependencias
echo ========================================
echo.
echo [1/2] Instalando requisitos globais...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo [2/2] Verificando instalacao...
python -c "import pysnmp.hlapi.asyncio; print('OK: pysnmp detectado')"

echo.
echo ========================================
echo  Concluido! Pressione qualquer tecla...
echo ========================================
pause >nul
exit
