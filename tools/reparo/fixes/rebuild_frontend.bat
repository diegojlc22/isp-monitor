@echo off
echo [DOCTOR] Frontend com problemas. Iniciando recompilacao...

cd /d "%~dp0..\..\..\frontend"

echo [DOCTOR] Instalando dependencias do frontend...
call npm install --silent

echo [DOCTOR] Compilando assets (Build)...
call npm run build

if exist "dist\index.html" (
    echo [DOCTOR] Build concluido com sucesso!
) else (
    echo [DOCTOR] FALHA no build. Verifique os logs.
)

exit /b 0
