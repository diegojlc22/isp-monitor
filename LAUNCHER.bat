@echo off
:: Launcher GUI - ISP Monitor (SEM CONSOLE)

cd /d "%~dp0"

:: Usar pythonw.exe para não mostrar console
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" launcher.pyw
) else (
    start "" pythonw launcher.pyw
)

exit
