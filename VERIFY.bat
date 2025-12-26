@echo off
:: Verificador de Instalação - ISP Monitor

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║      VERIFICADOR DE INSTALACAO - ISP MONITOR              ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0verify-setup.ps1"

if %errorLevel% neq 0 (
    echo.
    echo [ERRO] Ocorreu um erro durante a verificacao.
    echo.
    pause
    exit /b 1
)

pause
