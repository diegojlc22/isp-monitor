@echo off
:: Limpeza de Instalação - ISP Monitor

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║         LIMPEZA DE INSTALACAO - ISP MONITOR               ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0cleanup-setup.ps1"

if %errorLevel% neq 0 (
    echo.
    echo [ERRO] Ocorreu um erro durante a limpeza.
    echo.
    pause
    exit /b 1
)

pause
