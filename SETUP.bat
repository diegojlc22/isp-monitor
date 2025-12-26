@echo off
:: Instalador Inteligente - ISP Monitor
:: Execute este arquivo como Administrador

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║         INSTALADOR INTELIGENTE - ISP MONITOR v1.0         ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: Verificar se está rodando como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Este instalador precisa ser executado como Administrador!
    echo.
    echo Por favor, clique com o botao direito no arquivo SETUP.bat
    echo e selecione "Executar como Administrador"
    echo.
    pause
    exit /b 1
)

:: Executar o script PowerShell
echo Iniciando instalacao...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0setup.ps1"

if %errorLevel% neq 0 (
    echo.
    echo [ERRO] Ocorreu um erro durante a instalacao.
    echo Verifique o arquivo setup.log para mais detalhes.
    echo.
    pause
    exit /b 1
)

echo.
echo Instalacao concluida!
pause
