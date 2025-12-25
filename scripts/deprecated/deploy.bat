@echo off
setlocal
cd /d "%~dp0"
title ISP Monitor - Deploy
echo [!] Iniciando Deploy para Producao...

:: 1. Verificar Node.js
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js nao encontrado. Instale o Node.js para compilar o frontend.
    pause
    exit /b
)

:: 2. Instalar dependencias do Frontend (se necessario)
echo [1/3] Verificando dependencias do Frontend...
cd frontend
if not exist "node_modules" (
    echo Instalando dependencias...
    call npm install
)

:: 3. Compilar Frontend (Build)
echo [2/3] Compilando Frontend (Build)...
call npm run build

if %errorlevel% neq 0 (
    echo [ERROR] Falha na compilacao.
    pause
    exit /b
)

cd ..

:: 4. Verificar se a pasta dist foi criada
if not exist "frontend\dist\index.html" (
    echo [ERROR] Arquivo index.html nao encontrado em frontend\dist. Algo deu errado.
    pause
    exit /b
)

echo [3/3] Deploy concluido com sucesso!
echo.
echo Agora voce pode rodar 'iniciar_producao.bat' para usar a nova versao.
echo Se o sistema ja estiver rodando em producao, reinicie-o.
echo.
pause
