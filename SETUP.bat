@echo off
setlocal enabledelayedexpansion
title ISP Monitor - Setup Unificado (Instalar/Atualizar)

:: ISP Monitor - SETUP UNIFICADO v3.0
:: Detecta automaticamente se é INSTALACAO ou ATUALIZACAO

cd /d "%~dp0"
echo.
echo  ================================================
echo   [ISP Monitor] SETUP INTELIGENTE v3.0
echo  ================================================
echo.

:: 1. Verificacoes Preliminares (Admin)
:: -----------------------------------
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] ERRO: Preciso de privilegios de Administrador.
    echo     Solicitando elevacao agora...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %~dp0 && %~nx0' -Verb RunAs"
    exit
)

:: Definir Variaveis Globais
set "INSTALL_BASE=C:\ISP-Monitor"
set "APP_DIR=C:\ISP-Monitor\app"
set "DATA_DIR=C:\ISP-Monitor\data"
set "SOURCE_DIR=%~dp0"

:: 2. Decidir Modo de Operacao
:: --------------------------
if exist "%APP_DIR%\ABRIR_SISTEMA.bat" (
    goto :MODE_UPDATE
) else (
    goto :MODE_INSTALL
)

:: ==============================================================================
:: MODO INSTALACAO (Primeira vez)
:: ==============================================================================
:MODE_INSTALL
cls
echo  ================================================
echo   [NOVA INSTALACAO DETECTADA]
echo  ================================================
echo.
echo  1. Criando diretorios em C:\ISP-Monitor...
if not exist "%INSTALL_BASE%" mkdir "%INSTALL_BASE%"
if not exist "%APP_DIR%" mkdir "%APP_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%DATA_DIR%\logs" mkdir "%DATA_DIR%\logs"
if not exist "%DATA_DIR%\backups" mkdir "%DATA_DIR%\backups"

echo  2. Copiando arquivos do sistema...
:: Copia robusta ignorando lixo
robocopy "%SOURCE_DIR%." "%APP_DIR%" /MIR /XD ".git" ".venv" "venv" "node_modules" "logs" "__pycache__" "data" "python_bin" "dist" "build" /XF "SETUP.bat" "INSTALL.bat" "UPDATE.bat" ".env" "*.pyc" "*.pyd" "*.pyx" "*.log" /NFL /NDL /NJH /NJS >nul 2>&1

echo  3. Configurando ambiente (.env)...
if not exist "%DATA_DIR%\.env" (
    if exist "%APP_DIR%\.env.example" (
        copy /Y "%APP_DIR%\.env.example" "%DATA_DIR%\.env" >nul
        echo     - Arquivo .env inicial criado.
    )
)
:: Linkar .env e logs
if exist "%APP_DIR%\.env" del /F /Q "%APP_DIR%\.env" >nul 2>&1
mklink "%APP_DIR%\.env" "%DATA_DIR%\.env" >nul 2>&1
if exist "%APP_DIR%\logs" rmdir /S /Q "%APP_DIR%\logs" >nul 2>&1
mklink /D "%APP_DIR%\logs" "%DATA_DIR%\logs" >nul 2>&1

echo  4. Criando atalho na Area de Trabalho...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ISP Monitor.lnk'); $Shortcut.TargetPath = '%APP_DIR%\ABRIR_SISTEMA.bat'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.IconLocation = '%APP_DIR%\icon.ico'; $Shortcut.Save()"

echo.
echo  [SUCESSO] Instalacao concluida!
echo.
echo  Deseja abrir o sistema agora? (S/N)
set /p OPEN_NOW=
if /i "%OPEN_NOW%"=="S" (
    start "" "%APP_DIR%\ABRIR_SISTEMA.bat"
)
exit


:: ==============================================================================
:: MODO ATUALIZACAO (Sistema ja existe)
:: ==============================================================================
:MODE_UPDATE
cls
echo  ================================================
echo   [ATUALIZACAO DETECTADA]
echo  ================================================
echo.
echo  O sistema ja esta instalado em: %APP_DIR%
echo  Iniciando processo de atualizacao...
echo.

:: Preparar Timestamps
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set "BACKUP_DIR=%DATA_DIR%\backups\backup_%TIMESTAMP%"
set "TEMP_DIR=%TEMP%\isp-monitor-update-%TIMESTAMP%"

echo  [1/4] Parando servicos...
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo  [2/4] Criando Backup de Seguranca...
mkdir "%BACKUP_DIR%" >nul 2>&1
robocopy "%APP_DIR%" "%BACKUP_DIR%" /E /XD ".git" ".venv" "venv" "node_modules" "logs" "__pycache__" "data" "python_bin" "dist" "build" /XF "*.pyc" "*.pyd" "*.pyx" /NFL /NDL /NJH /NJS >nul 2>&1
echo      - Backup salvo em: backpus\backup_%TIMESTAMP%

echo  [3/4] Baixando Atualizacao (Git)...
echo      - Verificando conexao...
ping github.com -n 1 -w 2000 >nul 2>&1
if %errorLevel% neq 0 (
    echo      [ERRO] Sem internet ou GitHub off.
    echo      [ROLLBACK] Nenhuma alteracao feita.
    pause
    exit
)
if exist "%TEMP_DIR%" rmdir /S /Q "%TEMP_DIR%"
git clone https://github.com/diegojlc22/isp-monitor.git "%TEMP_DIR%" --depth 1 >nul 2>&1
if %errorLevel% neq 0 (
    echo      [ERRO] Falha no Download do Git.
    pause
    exit
)

echo  [4/4] Instalando nova versao...
echo      - Sincronizando arquivos (modo Mirror)...
echo      - (Arquivos que voce deletou do GitHub serao removidos aqui)

:: Limpeza preventiva de arquivos legados (para nao confundir)
if exist "%APP_DIR%\INSTALL.bat" (
    echo      - Removendo legado: INSTALL.bat
    del /F /Q "%APP_DIR%\INSTALL.bat" >nul 2>&1
)
if exist "%APP_DIR%\UPDATE.bat" (
    echo      - Removendo legado: UPDATE.bat
    del /F /Q "%APP_DIR%\UPDATE.bat" >nul 2>&1
)

:: Preservar arquivo .env e SETUP.bat
robocopy "%TEMP_DIR%" "%APP_DIR%" /MIR /XD ".git" ".venv" "venv" "node_modules" "logs" "__pycache__" "data" "python_bin" "dist" "build" /XF "SETUP.bat" ".env" "*.pyc" "*.pyd" "*.pyx" /NFL /NDL /NJH /NJS >nul 2>&1

:: Limpar Temp
rmdir /S /Q "%TEMP_DIR%"

echo.
echo  [SUCESSO] Sistema Atualizado com Sucesso!
echo.
echo  Deseja abrir o sistema agora? (S/N)
set /p OPEN_NOW=
if /i "%OPEN_NOW%"=="S" (
    start "" "%APP_DIR%\ABRIR_SISTEMA.bat"
)
exit
