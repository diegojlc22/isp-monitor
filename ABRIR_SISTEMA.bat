@echo off
:: ISP Monitor Launcher
echo Iniciando ISP Monitor...

:: Tenta rodar como Admin
net session >nul 2>&1
if %errorLevel% == 0 (
    :: Já é Admin - roda direto
    start pythonw launcher.pyw
    exit
) else (
    :: Não é Admin - solicita elevação
    echo Solicitando privilegios de Administrador...
    powershell -Command "Start-Process pythonw -ArgumentList 'launcher.pyw' -Verb RunAs -WorkingDirectory '%CD%'"
    exit
)
