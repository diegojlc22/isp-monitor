@echo off
:: Reiniciar PostgreSQL e Aplicação
:: EXECUTAR COMO ADMINISTRADOR

echo ========================================
echo REINICIANDO POSTGRESQL
echo ========================================
echo.

net stop postgresql-x64-18
timeout /t 3 /nobreak >nul
net start postgresql-x64-18

echo.
echo ========================================
echo POSTGRESQL REINICIADO!
echo ========================================
echo.
echo Aguarde 5 segundos...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo INICIANDO APLICACAO
echo ========================================
echo.

cd /d "%~dp0"
call iniciar_postgres.bat
