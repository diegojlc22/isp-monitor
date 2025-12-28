@echo off
:: Check for Admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run_commands
) else (
    echo.
    echo ==========================================================
    echo  ESTE SCRIPT PRECISA DE PERMISSOES DE ADMINISTRADOR!
    echo ==========================================================
    echo.
    echo O Windows bloqueia a criacao de regras de Firewall por seguranca.
    echo.
    echo POR FAVOR:
    echo 1. Feche esta janela.
    echo 2. Clique com o botao DIREITO no arquivo 'CONFIGURAR_REDE.bat'
    echo 3. Escolha 'Executar como Administrador'
    echo.
    echo.
    pause
    exit
)

:run_commands
echo.
echo ==========================================================
echo      CONFIGURANDO FIREWALL DO WINDOWS (PORTA 8080)
echo ==========================================================
echo.
echo [1/3] Removendo regras antigas (se existirem)...
powershell -Command "Remove-NetFirewallRule -DisplayName 'ISP Monitor Backend' -ErrorAction SilentlyContinue"

echo [2/3] Criando nova regra de entrada TCP 8080...
powershell -Command "New-NetFirewallRule -DisplayName 'ISP Monitor Backend' -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow"

echo [3/3] Verificando...
powershell -Command "Get-NetFirewallRule -DisplayName 'ISP Monitor Backend' | Select-Object DisplayName, Enabled, Profile, Direction, Action"

echo.
echo ==========================================================
echo                SUCESSO! ACESSO LIBERADO
echo ==========================================================
echo Agora voce pode acessar o painel pelo celular usando o IP do PC.
echo Exemplo: http://192.168.X.X:8080
echo.
pause
