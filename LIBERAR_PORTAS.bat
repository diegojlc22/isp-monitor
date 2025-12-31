@echo off
setlocal enabledelayedexpansion

TITLE ISP Monitor - Liberador de Portas Firewall
echo ============================================================
echo      ISP MONITOR - CONFIGURADOR DE REDE LOCAL
echo ============================================================
echo.
echo Este script ira liberar as portas necessarias para o 
echo funcionamento do App Mobile e do Painel Web na rede local.
echo.
echo [PORTAS QUE SERAO LIBERADAS]:
echo - 8080 (API Principal / Mobile)
echo - 3001 (Gateway WhatsApp)
echo - 5173 (Painel Web - Vite)
echo - 8081 (Expo Metro Bundler)
echo - 5432 (Banco de Dados Postgres)
echo.
echo ============================================================
echo SOLICITANDO PERMISSAO DE ADMINISTRADOR...

:: Verifica se tem admin
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run_commands
) else (
    echo.
    echo [!] ERRO: VOCE PRECISA EXECUTAR COMO ADMINISTRADOR.
    echo.
    echo Clique com o botao direito neste arquivo e escolha:
    echo "EXECUTAR COMO ADMINISTRADOR"
    echo.
    pause
    exit /b
)

:run_commands
echo [OK] Permissao concedida. Iniciando configuracao...
echo.

:: Porta 8080 (API)
echo [+] Liberando Porta 8080 (API/Mobile)...
powershell -Command "New-NetFirewallRule -DisplayName 'ISP-Monitor-API' -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow -Force" >nul 2>&1

:: Porta 3001 (WhatsApp)
echo [+] Liberando Porta 3001 (WhatsApp)...
powershell -Command "New-NetFirewallRule -DisplayName 'ISP-Monitor-WhatsApp' -Direction Inbound -LocalPort 3001 -Protocol TCP -Action Allow -Force" >nul 2>&1

:: Porta 5173 (Vite/Frontend)
echo [+] Liberando Porta 5173 (Web/Vite)...
powershell -Command "New-NetFirewallRule -DisplayName 'ISP-Monitor-Web' -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow -Force" >nul 2>&1

:: Porta 8081 (Expo)
echo [+] Liberando Porta 8081 (Expo/Metro)...
powershell -Command "New-NetFirewallRule -DisplayName 'ISP-Monitor-Expo' -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow -Force" >nul 2>&1

:: Porta 5432 (Postgres)
echo [+] Liberando Porta 5432 (PostgreSQL)...
powershell -Command "New-NetFirewallRule -DisplayName 'ISP-Monitor-Postgres' -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow -Force" >nul 2>&1

echo.
echo ============================================================
echo [SUCESSO] Todas as portas foram liberadas no Firewall!
echo.
echo Agora o seu celular podera conectar-se ao servidor 192.168.3.10
echo diretamente pela rede Wi-Fi.
echo ============================================================
echo.
pause
exit /b
