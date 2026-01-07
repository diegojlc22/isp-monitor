@echo off
cd /d "c:\diegolima\isp-monitor"
set "URL=http://localhost:8080/api/system/health"
set "LOGfile=logs\monitor_external.log"

if not exist logs mkdir logs

REM --- CHECK API ---
curl -f -s %URL% > nul
if %errorlevel% neq 0 (
    echo %date% %time% - [CRITICAL] API inacessível! Tentando reiniciar... >> %LOGfile%
    
    REM Matar todos os processos pythonw
    taskkill /F /IM pythonw.exe /T >> %LOGfile% 2>&1
    taskkill /F /IM python.exe /T >> %LOGfile% 2>&1
    
    REM Aguardar limpeza
    timeout /t 5 /nobreak
    
    REM Iniciar Launcher (modo oculto)
    start pythonw launcher.pyw
    
    echo %date% %time% - Reinicialização disparada. >> %LOGfile%
) else (
    REM Opcional: Logar sucesso apenas se quiser muito verbose.
    REM echo %date% %time% - [OK] API Online. >> %LOGfile%
)
