@echo off
cd /d "%~dp0"
echo =================================================
echo   INSTALACAO DO WHATSAPP GATEWAY
echo =================================================
echo.
echo 1. Verificando Node.js...
node --version
if %errorlevel% neq 0 (
    echo [ERRO] Node.js nao encontrado! Instale o Node.js primeiro.
    pause
    exit
)

echo.
echo 2. Instalando dependencias (pode demorar para baixar o Chromium)...
cd tools\whatsapp
call npm install

echo.
echo 3. Iniciando Servidor...
echo.
echo FIQUE ATENTO: Quando aparecer "QR Code salvo...", abra o arquivo
echo "tools\whatsapp\whatsapp-qr.png" e escaneie com seu celular.
echo.
echo Pressione ENTER para iniciar...
pause

node server.js
pause
