@echo off
setlocal
cd /d "%~dp0"

:: 1. Verificacao de Admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo  [!] ESTE SCRIPT PRECISA DE PRIVILEGIOS DE ADMINISTRADOR
    echo      Solicitando permissao...
    echo.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

:: 2. Executar script PowerShell
if exist "setup.ps1" (
    powershell -ExecutionPolicy Bypass -File "setup.ps1"
) else (
    echo.
    echo  [ERRO] O arquivo 'setup.ps1' nao foi encontrado.
    echo        O sistema pode estar corrompido ou incompleto.
    echo.
    pause
)

exit
