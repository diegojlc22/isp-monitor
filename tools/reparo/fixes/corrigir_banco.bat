@echo off
echo [DOCTOR] Verificando e Corrigindo Banco de Dados...
cd /d "%~dp0..\..\.."

echo Aplicando migrations/patches...
python update_db.py

echo Resetando servicos...
taskkill /F /IM python.exe /T 2>nul
start LAUNCHER.bat

echo Pronto.
pause
