$ErrorActionPreference = "Stop"
$TargetVersion = "3.12.3"
$InstallerUrl = "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   PADRONIZADOR DE AMBIENTE (Python $TargetVersion)   " -ForegroundColor Cyan
Write-Host "==================================================="

# 1. Verificar se Python 3.12 existe via 'py' launcher (Infalivel)
try {
    # py -3.12 --version retorna algo como "Python 3.12.3"
    # Redirecionamos erro para nul para nao sujar a tela se falhar
    $Process = Start-Process -FilePath "py" -ArgumentList "-3.12", "--version" -NoNewWindow -PassThru -Wait -ErrorAction SilentlyContinue
    
    if ($Process.ExitCode -eq 0) {
        Write-Host "   [OK] Python 3.12 detectado via Launcher." -ForegroundColor Green
        exit 0
    }
} catch {
    # Se 'py' nao existir, continua para instalacao
}

Write-Host "   [AVISO] Python 3.12 nao encontrado." -ForegroundColor Yellow

# 2. Baixar Instalador
$InstallerPath = "$env:TEMP\python_setup.exe"
Write-Host "`n[DOWNLOAD] Baixando Python Oficial..."
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $InstallerUrl -OutFile $InstallerPath -UseBasicParsing
    Write-Host "   [OK] Download concluido." -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Falha ao baixar: $_" -ForegroundColor Red
    exit 1
}

# 3. Instalar
Write-Host "`n[INSTALACAO] Instalando Python $TargetVersion..."
# InstallAllUsers=1 : Instala para todos
# PrependPath=1     : Adiciona ao PATH
# Include_tcltk=1   : GARANTE TKINTER (Interface)
# Include_launcher=1: GARANTE O COMANDO 'py'
$Args = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_tcltk=1 Include_launcher=1"

$Proc = Start-Process -FilePath $InstallerPath -ArgumentList $Args -Wait -PassThru -Verb RunAs

if ($Proc.ExitCode -eq 0) {
    Write-Host "   [SUCESSO] Python Instalado!" -ForegroundColor Green
} else {
    Write-Host "   [ERRO] Instalacao falhou (Codigo: $($Proc.ExitCode))" -ForegroundColor Red
    exit 1
}

Remove-Item $InstallerPath -ErrorAction SilentlyContinue
exit 0
