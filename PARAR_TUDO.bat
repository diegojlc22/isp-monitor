@echo off
echo ===================================================
echo   MATANDO TODOS OS PROCESSOS DO ISP MONITOR
echo ===================================================
echo.
echo 1. Parando node.exe (WhatsApp)...
taskkill /F /IM node.exe /T >nul 2>&1
if %errorlevel%==0 (echo    [OK] Node Parado.) else (echo    [--] Nenhum processo Node encontrado.)
echo.
echo 2. Parando python.exe / pythonw.exe (Backend/Launcher)...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
if %errorlevel%==0 (echo    [OK] Python Parado.) else (echo    [--] Nenhum processo Python encontrado.)
echo.
echo 3. Parando postgres.exe (Banco de Dados)...
taskkill /F /IM postgres.exe /T >nul 2>&1
if %errorlevel%==0 (echo    [OK] PostgreSQL Parado.) else (echo    [--] Nenhum processo PostgreSQL encontrado.)
echo.
echo 4. Limpando processos órfãos (force kill)...
wmic process where "name='node.exe'" delete >nul 2>&1
wmic process where "name='python.exe'" delete >nul 2>&1
wmic process where "name='pythonw.exe'" delete >nul 2>&1
echo    [OK] Limpeza completa.
echo.
echo ===================================================
echo   SISTEMA LIMPO. ARQUIVOS LIBERADOS.
echo ===================================================
echo.
pause
