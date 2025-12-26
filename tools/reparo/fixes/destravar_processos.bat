@echo off
echo [REPARO] Destravando processos do sistema...

taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM java.exe /T >nul 2>&1

echo [REPARO] Todos os processos foram encerrados.
exit /b 0
