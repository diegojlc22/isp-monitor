$ErrorActionPreference = "Stop"
$PythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$InstallerPath = "$env:TEMP\python_installer.exe"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   INSTALADOR AUTOMATICO DO PYTHON (FULL) " -ForegroundColor Cyan
Write-Host "==================================================="
Write-Host "Detectamos que falta o suporte a interface grafica."
Write-Host "Baixando o Python Oficial Completo..."

# 1. Download
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $PythonUrl -OutFile $InstallerPath -UseBasicParsing
    Write-Host "[OK] Download concluido." -ForegroundColor Green
}
catch {
    Write-Host "[ERRO] Falha ao baixar: $_" -ForegroundColor Red
    exit 1
}

# 2. Instalar
Write-Host "Iniciando instalacao silenciosa..."
Write-Host "1. Isso pode levar alguns minutos."
Write-Host "2. Se abrir uma janela pedindo permissao, clique em SIM."

# Argumentos para instalacao completa e silenciosa
# InstallAllUsers=1 : Instala para todos (evita problemas de path)
# PrependPath=1     : Coloca no PATH (essencial)
# Include_tcltk=1   : GARANTE O TKINTER (GUI)
$Args = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_tcltk=1"

$Proc = Start-Process -FilePath $InstallerPath -ArgumentList $Args -Wait -PassThru -Verb RunAs

if ($Proc.ExitCode -eq 0) {
    Write-Host "[SUCESSO] Python Instalado!" -ForegroundColor Green
    
    # Atualizar Path na sessao atual para nao precisar reiniciar
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}
else {
    Write-Host "[ERRO] A instalacao falhou ou foi cancelada." -ForegroundColor Red
    Write-Host "Codigo de saida: $($Proc.ExitCode)"
    exit 1
}

# Limpeza
Remove-Item $InstallerPath -ErrorAction SilentlyContinue
exit 0
