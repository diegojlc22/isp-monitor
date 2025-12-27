@echo off
title ISP Monitor - Instalador Full
color 1f
cd /d "%~dp0"

echo.
echo ========================================================
echo      INSTALACAO COMPLETA (CORRECAO DE GUI)
echo ========================================================
echo.
echo O Launcher Grafico precisa do Python com Tkinter.
echo Vamos instalar a versao oficial agora.
echo.
echo AVISO: Uma janela do Windows pode aparecer pedindo PERMISSAO.
echo.
pause

echo.
echo [1/2] Baixando e Instalando Python System-Wide...
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\repair\install_python_full.ps1"

if %errorlevel% neq 0 (
    color 4f
    echo.
    echo [ERRO] A instalacao falhou.
    pause
    exit /b
)

echo.
echo [2/2] Instalando Dependencias...
python -m pip install -r backend/requirements.txt --quiet --no-warn-script-location

echo.
echo [SUCESSO] Tudo pronto!
echo Abrindo o sistema...
timeout /t 3 >nul
start "" "ABRIR_SISTEMA.bat"
