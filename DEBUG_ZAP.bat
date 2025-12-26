@echo off
cd /d "%~dp0"
echo =================================================
echo   DEBUG WHATSAPP GATEWAY
echo =================================================
echo.
cd tools\whatsapp
echo Iniciando server.js direto no console...
echo Se der erro, vai aparecer aqui.
echo.
node server.js
pause
