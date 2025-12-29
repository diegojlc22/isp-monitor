@echo off
:: ISP Monitor - Atualizador Inteligente v2.0
:: Foco: Robustez, Segurança e Rollback Automático

setlocal enabledelayedexpansion
cd /d "%~dp0"
title ISP Monitor - Atualizador Inteligente

echo.
echo  [ISP Monitor] SISTEMA DE ATUALIZACAO AUTOMATICA
echo  ================================================
echo.

:: 1. VERIFICACOES PRELIMINARES
:: ---------------------------
echo [1/7] Verificando ambiente...

:: Verificar Admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Precisa de privilegios de Administrador!
    echo Solicitando elevacao...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %~dp0 && UPDATE.bat' -Verb RunAs"
    exit
)

:: Verificar Instalação
if not exist "app\" (
    echo [ERRO] Estrutura de pasta invalida.
    echo Este script deve rodar em C:\ISP-Monitor\ (ou onde instalou)
    pause
    exit /b 1
)

:: Verificar Internet e Git
echo [*] Testando conexao com GitHub...
ping github.com -n 1 -w 3000 >nul
if %errorLevel% neq 0 (
    echo [ERRO] Sem conexao com a internet ou GitHub inacessivel.
    echo Atualizacao cancelada. Nenhuma alteracao foi feita.
    pause
    exit /b 1
)

:: Definir Diretorios
set "APP_DIR=%~dp0app"
set "DATA_DIR=%~dp0data"
set "TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_DIR=%DATA_DIR%\backups\backup_%TIMESTAMP%"
set "TEMP_DIR=%TEMP%\isp-monitor-update-%TIMESTAMP%"

:: 2. PARAR SISTEMA COM SEGURANCA
:: -----------------------------
echo [2/7] Parando o sistema...
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

:: Aguardar processos liberarem arquivos
echo [*] Aguardando liberacao de arquivos...
timeout /t 3 /nobreak >nul

:: 3. BACKUP DE SEGURANCA (CRITICO)
:: -------------------------------
echo [3/7] Criando ponto de restauracao...
mkdir "%BACKUP_DIR%" >nul 2>&1
robocopy "%APP_DIR%" "%BACKUP_DIR%" /E /NFL /NDL /NJH /NJS >nul
if %errorLevel% geq 8 (
    echo [ERRO CRITICO] Falha ao criar backup!
    echo codigo de erro: %errorLevel%
    echo Atualizacao abortada para seguranca.
    pause
    exit /b 1
)
echo [OK] Backup salvo em: %BACKUP_DIR%

:: 4. DOWNLOAD DA ATUALIZACAO
:: -------------------------
echo [4/7] Baixando nova versao...
if exist "%TEMP_DIR%" rmdir /S /Q "%TEMP_DIR%"
git clone https://github.com/diegojlc22/isp-monitor.git "%TEMP_DIR%" --depth 1 >nul
if %errorLevel% neq 0 (
    echo [ERRO] Falha no download do Git.
    goto :ROLLBACK
)

:: 5. APLICAR ATUALIZACAO
:: ---------------------
echo [5/7] Instalando arquivos...

:: Backup da configuração local
copy "%APP_DIR%\.env" "%TEMP%\.env.preserve" >nul 2>&1

:: Copiar arquivos novos usando Robocopy (Mais seguro)
:: /MIR = Espelhar (remove arquivos que não existem mais na origem)
:: /XD = Excluir diretórios (logs, venv, node_modules)
robocopy "%TEMP_DIR%" "%APP_DIR%" /MIR /XD ".git" ".venv" "venv" "node_modules" "logs" "__pycache__" /XF ".env" /NFL /NDL /NJH /NJS 
if %errorLevel% geq 8 (
    echo [ERRO] Falha na copia de arquivos.
    goto :ROLLBACK
)

:: Restaurar .env
if exist "%TEMP%\.env.preserve" (
    copy "%TEMP%\.env.preserve" "%APP_DIR%\.env" >nul
    del "%TEMP%\.env.preserve"
) else (
    echo [AVISO] .env nao encontrado, criando novo...
    copy "%APP_DIR%\.env.example" "%APP_DIR%\.env" >nul
)

:: Limpar temp
rmdir /S /Q "%TEMP_DIR%"

:: 6. ATUALIZAR DEPENDENCIAS E BANCO
:: --------------------------------
echo [6/7] Atualizando dependencias e banco...
cd /d "%APP_DIR%"

:: Python
echo [*] Python pip...
python -m pip install -r requirements.txt --quiet --upgrade
if %errorLevel% neq 0 (
    echo [AVISO] Falha ao atualizar libs Python.
    :: Não faz rollback por isso, pode ser leve
)

:: WhatsApp
if exist "tools\whatsapp\package.json" (
    echo [*] WhatsApp modules...
    cd tools\whatsapp
    call npm install --no-audit --no-fund --loglevel=error >nul 2>&1
    cd ..\..
)

:: Banco de Dados (Fix Schema)
echo [*] Verificando Banco de Dados...
powershell -ExecutionPolicy Bypass -Command "$env:PGPASSWORD='110812'; if (Test-Path 'C:\Program Files\PostgreSQL\17\bin\psql.exe') { & 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -U postgres -d isp_monitor -c 'ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_ping FLOAT; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_latency FLOAT; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_traffic_in BIGINT; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_traffic_out BIGINT; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS signal_dbm INTEGER; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS ccq INTEGER; ALTER TABLE equipments ADD COLUMN IF NOT EXISTS connected_clients INTEGER;' 2>$null }"

:: 7. FINALIZACAO
:: -------------
echo.
echo ========================================
echo  [SUCESSO] SISTEMA ATUALIZADO!
echo ========================================
echo.
echo O sistema foi atualizado para a ultima versao.
echo Seus dados foram preservados.
echo.
echo Deseja iniciar o ISP Monitor agora? (S/N)
set /p START_NOW=
if /i "%START_NOW%"=="S" (
    start "" "%APP_DIR%\ABRIR_SISTEMA.bat"
)
exit

:: ==========================================
:: ROTINA DE ROLLBACK (EMERGENCIA)
:: ==========================================
:ROLLBACK
echo.
echo ========================================
echo  [ERRO CRITICO] INICIANDO ROLLBACK...
echo ========================================
echo.
echo Uma falha ocorreu. Restaurando versao anterior...
timeout /t 2 /nobreak >nul

robocopy "%BACKUP_DIR%" "%APP_DIR%" /MIR /NFL /NDL /NJH /NJS
echo.
echo [OK] Sistema restaurado para a versao anterior.
echo [FAIL] A atualizacao falhou e foi revertida.
echo.
pause
exit /b 1
