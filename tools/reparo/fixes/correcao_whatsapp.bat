@echo off
echo [REPARO] Iniciando protocolo de correcao do WhatsApp...

:: 1. Matar processos do Node (WhatsApp)
taskkill /F /IM node.exe /T >nul 2>&1

:: 2. Limpar Sessao (Crucial para erro No LID)
if exist "..\..\tools\whatsapp\.wwebjs_auth" (
    rmdir /S /Q "..\..\tools\whatsapp\.wwebjs_auth"
)
if exist "..\..\tools\whatsapp\.wwebjs_cache" (
    rmdir /S /Q "..\..\tools\whatsapp\.wwebjs_cache"
)
if exist "..\..\tools\whatsapp\session" (
    rmdir /S /Q "..\..\tools\whatsapp\session"
)

:: 3. Limpar Tokens de Status
if exist "..\..\tools\whatsapp\whatsapp_is_ready.txt" (
    del "..\..\tools\whatsapp\whatsapp_is_ready.txt"
)
if exist "..\..\tools\whatsapp\whatsapp-qr.png" (
    del "..\..\tools\whatsapp\whatsapp-qr.png"
)

echo [REPARO] WhatsApp limpo. Reinicie o servico pelo Launcher.
exit /b 0
