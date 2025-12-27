@echo off
cd /d "%~dp0"

:: Usar pythonw.exe (Windowless) agora que temos logging interno
if exist "python_bin\pythonw.exe" (
    :: Inicia o processo sem janela de console
    start "ISP Monitor Launcher" "python_bin\pythonw.exe" "launcher.pyw"
) else (
    echo [ERRO] Python nao encontrado em python_bin
    pause
)

exit
