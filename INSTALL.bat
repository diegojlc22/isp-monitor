@echo off
:: ISP Monitor - Instalador Automático
:: Instala o sistema em C:\ISP-Monitor

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo  ISP Monitor - Instalador v1.0
echo ========================================
echo.

:: Verificar Admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Este instalador precisa de privilegios de Administrador!
    echo.
    echo Clique com botao direito e escolha "Executar como Administrador"
    pause
    exit /b 1
)

:: Definir diretórios
set "INSTALL_DIR=C:\ISP-Monitor"
set "APP_DIR=%INSTALL_DIR%\app"
set "DATA_DIR=%INSTALL_DIR%\data"
set "SOURCE_DIR=%~dp0"

echo [1/5] Criando estrutura de diretorios...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%APP_DIR%" mkdir "%APP_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%DATA_DIR%\logs" mkdir "%DATA_DIR%\logs"
if not exist "%DATA_DIR%\backups" mkdir "%DATA_DIR%\backups"

echo [2/5] Copiando arquivos do sistema...
xcopy "%SOURCE_DIR%*" "%APP_DIR%\" /E /I /Y /EXCLUDE:%SOURCE_DIR%install_exclude.txt >nul 2>&1

echo [3/5] Configurando ambiente...
:: Copiar .env.example para data se não existir
if not exist "%DATA_DIR%\.env" (
    if exist "%APP_DIR%\.env.example" (
        copy "%APP_DIR%\.env.example" "%DATA_DIR%\.env" >nul
        echo [OK] Arquivo .env criado em %DATA_DIR%
    )
)

:: Criar symlink para .env
if exist "%APP_DIR%\.env" del "%APP_DIR%\.env"
mklink "%APP_DIR%\.env" "%DATA_DIR%\.env" >nul 2>&1

:: Criar symlink para logs
if exist "%APP_DIR%\logs" rmdir "%APP_DIR%\logs" /S /Q >nul 2>&1
mklink /D "%APP_DIR%\logs" "%DATA_DIR%\logs" >nul 2>&1

echo [4/5] Instalando dependencias...
cd /d "%APP_DIR%"
call "%APP_DIR%\ABRIR_SISTEMA.bat"

echo.
echo [5/5] Criando atalhos...
:: Criar atalho na área de trabalho
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\ISP Monitor.lnk'); $Shortcut.TargetPath = '%APP_DIR%\ABRIR_SISTEMA.bat'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.IconLocation = '%APP_DIR%\icon.ico'; $Shortcut.Save()"

echo.
echo ========================================
echo  INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Sistema instalado em: %INSTALL_DIR%
echo Dados locais em: %DATA_DIR%
echo.
echo Para iniciar: Execute "ISP Monitor" na area de trabalho
echo Para atualizar: Execute update.bat em %INSTALL_DIR%
echo.
pause
