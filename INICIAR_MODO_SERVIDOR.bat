@echo off
cd /d "%~dp0"

echo.
echo ===================================================
echo   ISP MONITOR - MODO SERVIDOR (HEADLESS)
echo ===================================================
echo.
echo  Este modo roda o sistema em background, ideal para
echo  servidores ou maquinas dedicadas.
echo.
echo  [INFO] O Watchdog (self_heal.py) cuidara de tudo.
echo  [INFO] Feche esta janela para encerrar o servico.
echo.

python scripts/self_heal.py

pause
