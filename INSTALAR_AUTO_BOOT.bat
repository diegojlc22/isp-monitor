@echo off
:: AUTO-START SETUP FOR ISP MONITOR
:: Configures the system to run automatically on Windows Startup (without login)

:: Check Admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ==========================================================
    echo  ESTE SCRIPT PRECISA DE PERMISSOES DE ADMINISTRADOR!
    echo ==========================================================
    echo.
    echo 1. Feche esta janela.
    echo 2. Clique com o botao DIREITO no arquivo 'INSTALAR_AUTO_BOOT.bat'
    echo 3. Escolha 'Executar como Administrador'
    pause
    exit
)

echo.
echo ==========================================================
echo      CONFIGURANDO INICIO AUTOMATICO (AUTO-BOOT)
echo ==========================================================

:: Absolute path to python and script
set "PROJECT_DIR=%~dp0"
:: Remove trailing slash
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "PYTHON_EXE=py"
set "SCRIPT_PATH=%PROJECT_DIR%\scripts\self_heal.py"

echo [1/3] Criando script wrapper de inicializacao...
:: We need a wrapper to cd into the directory first
(
echo @echo off
echo cd /d "%PROJECT_DIR%"
echo echo [AUTO-BOOT] Iniciando ISP Monitor... ^> logs\boot.log
echo "%PYTHON_EXE%" -3.12 "scripts\self_heal.py" ^>^> logs\boot.log 2^>^&1
) > "%PROJECT_DIR%\boot_service.bat"

echo [2/3] Registrando servico no Agendador de Tarefas...
:: Delete old if exists
schtasks /delete /tn "ISP Monitor Boot" /f >nul 2>&1

:: Create new task
:: /sc ONSTART = Run at boot
:: /ru SYSTEM = Run as System (Invisible, no login needed)
:: /rl HIGHEST = Admin rights
:: /tr ... = Command to run
schtasks /create /tn "ISP Monitor Boot" /sc ONSTART /ru SYSTEM /rl HIGHEST /tr "\"%PROJECT_DIR%\boot_service.bat\"" /f

if %errorLevel% equ 0 (
    echo.
    echo ==========================================================
    echo          SUCESSO! O MONITOR ESTA BLINDADO
    echo ==========================================================
    echo.
    echo O sistema vai iniciar sozinho sempre que o Windows ligar.
    echo Voce nao precisa mais fazer login no servidor.
    echo.
    echo Para testar: Reinicie o Windows agora.
) else (
    echo.
    echo [ERRO] Falha ao criar tarefa agendada.
)

pause
