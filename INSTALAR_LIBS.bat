@echo off
title ISP Monitor - Instalando Bibliotecas
color 0e
cd /d "%~dp0"

echo [1/2] Atualizando PIP...
py -3.12 -m pip install --upgrade pip

echo.
echo [2/2] Instalando Dependencias (Pillow, Requests, Psutil, QRCode)...
py -3.12 -m pip install Pillow requests psutil qrcode tk

echo.
echo [VERIFICACAO] Testando imports...
py -3.12 -c "import PIL, requests, psutil, qrcode; print('SUCESSO')"

if %errorlevel% equ 0 (
    color 2f
    echo.
    echo [OK] Tudo pronto. Abrindo sistema...
    timeout /t 2 >nul
    start "" "ABRIR_SISTEMA.bat"
) else (
    color 4f
    echo.
    echo [ERRO] Falha na instalacao das libs.
    pause
)
