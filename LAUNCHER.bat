@echo off
:: Launcher ISP Monitor - Solucao Definitiva para Janela Oculta
cd /d "%~dp0"

:: Cria um lançador VBScript temporario
:: Isso permite rodar o 'python.exe' (que sabemos que funciona) mas instrui o Windows a esconder a janela do console (0)
echo Set WshShell = CreateObject("WScript.Shell") > launch_monitor.vbs
echo WshShell.Run "python launcher.pyw", 0, False >> launch_monitor.vbs

:: Executa o script invisivel
wscript launch_monitor.vbs

:: Aguarda um momento para garantir a execucao e limpa
timeout /t 1 /nobreak >nul
del launch_monitor.vbs

exit
