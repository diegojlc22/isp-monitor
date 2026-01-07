@echo off
echo ========================================
echo  CONFIGURANDO POSTGRESQL PARA AUTO-START
echo ========================================
echo.

REM Configurar serviço para iniciar automaticamente
sc config postgresql-x64-17 start= auto

REM Iniciar o serviço agora
net start postgresql-x64-17

echo.
echo ✅ PostgreSQL configurado para iniciar automaticamente!
echo.
pause
