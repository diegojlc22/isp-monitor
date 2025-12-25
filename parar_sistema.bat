@echo off
:: Script para Parar o ISP Monitor
:: Mata todos os processos Python relacionados

echo ========================================
echo PARANDO ISP MONITOR
echo ========================================
echo.

echo [1/2] Procurando processos na porta 8080...
netstat -ano | findstr :8080

echo.
echo [2/2] Parando processos Python...

:: Matar processo específico na porta 8080
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    echo Parando processo %%a...
    taskkill /F /PID %%a 2>nul
)

echo.
echo ========================================
echo SISTEMA PARADO!
echo ========================================
echo.
echo Todos os processos foram finalizados.
echo.
pause
