@echo off
cd /d "%~dp0"
echo =================================================
echo      LIMPEZA TOTAL DO SISTEMA - ISP MONITOR
echo =================================================
echo.

echo [1/4] Parando todos os processos...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM java.exe /T >nul 2>&1

echo [2/4] Limpando sessao do WhatsApp (Correcao No LID)...
if exist "tools\whatsapp\.wwebjs_auth" (
    rmdir /S /Q "tools\whatsapp\.wwebjs_auth"
    echo    - Sessao de autenticacao removida.
)
if exist "tools\whatsapp\.wwebjs_cache" (
    rmdir /S /Q "tools\whatsapp\.wwebjs_cache"
    echo    - Cache removido.
)
if exist "tools\whatsapp\session" (
    rmdir /S /Q "tools\whatsapp\session"
    echo    - Pasta session antiga removida.
)
if exist "tools\whatsapp\whatsapp-qr.png" (
    del "tools\whatsapp\whatsapp-qr.png"
)

echo [3/4] Limpando logs antigos...
if exist startup.log del startup.log
if exist api.log del api.log
if exist collector.log del collector.log
if exist setup.log del setup.log

echo [4/4] Verificando dependencias criticas...
.\.venv\Scripts\python.exe -m pip install aiohttp >nul 2>&1

echo.
echo =================================================
echo               LIMPEZA CONCLUIDA!
echo =================================================
echo.
echo AGORA:
echo 1. Abra o LAUNCHER.bat novamente.
echo 2. Va na aba WhatsApp e ligue-o.
echo 3. ESCANIE O NOVO QR CODE (Obrigatorio).
echo.
pause
