@echo off
cd /d "%~dp0"
echo ========================================
echo  DEBUG LAUNCHER - Verificando Erros
echo ========================================
echo.

:: Tenta rodar com python normal para ver erros no console
python launcher.pyw

if %errorLevel% neq 0 (
    echo.
    echo [!] O Launcher fechou com código de erro: %errorLevel%
    echo Verifique as mensagens acima.
)

echo.
echo Presione qualquer tecla para fechar...
pause >nul
