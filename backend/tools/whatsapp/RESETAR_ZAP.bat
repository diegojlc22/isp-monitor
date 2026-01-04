@echo off
cd /d "%~dp0"
echo =================================================
echo   RESETAR WHATSAPP GATEWAY
echo =================================================
echo.
echo 1. Parando processos antigos...
taskkill /F /IM node.exe /T >nul 2>&1

echo.
echo 2. Limpando sessao antiga (Isso resolve 99%% dos erros)...
cd tools\whatsapp
if exist "session" rmdir /s /q "session"
if exist ".wwebjs_auth" rmdir /s /q ".wwebjs_auth"
if exist ".wwebjs_cache" rmdir /s /q ".wwebjs_cache"
if exist "whatsapp-qr.png" del "whatsapp-qr.png"

echo.
echo 3. Iniciando servidor limpo...
echo.
echo AGUARDE o novo QR Code ser gerado e escaneie RAPIDO.
echo.
node server.js
pause
