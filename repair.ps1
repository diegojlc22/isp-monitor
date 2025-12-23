# Script de Reparo e Inicialização do ISP Monitor
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   ISP MONITOR - DIAGNOSTICO E REPARO (PowerShell)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Versão do Python Instalada
# FORÇAR DOWNLOAD DO PYTHON 3.11 PORTATIL
# Ignoramos o python do sistema pois ele tem se mostrado instavel/corrompido.
Write-Host "[DECISAO] Forcando uso de Python 3.11 Portatil Dedicado." -ForegroundColor Magenta
$global:SystemPythonGood = $false

# ... (Detection block removed/skipped) ...

# 3. Decisão: Usar sistema ou instalar portatil
if (-not $global:SystemPythonGood) {
    Write-Host ""
    Write-Host "[ACAO] Preparando ambiente dedicado..." -ForegroundColor Magenta
    
    $workDir = Get-Location
    $pyDir = Join-Path $workDir "python_bin"
    $installer = Join-Path $workDir "python_installer.exe"
    
    # Se ja existe, nao baixa de novo
    if (Test-Path $pyDir) {
        Write-Host "       Python dedicado ja existe em python_bin."
    }
    else {
        # Download
        $url = "https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
        Write-Host "       Baixando Python 3.11 de: $url"
        try {
            Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
        }
        catch {
            Write-Host "[ERRO FATAL] Nao foi possivel baixar o Python. Verifique a internet." -ForegroundColor Red
            Read-Host "Pressione ENTER para sair..."
            exit 1
        }
        
        # Install
        Write-Host "       Instalando (Uma janela de permissao pode aparecer. ACEITE)..."
        $args = "/quiet InstallAllUsers=0 TargetDir=`"$pyDir`" Include_tcltk=1 Include_test=0 PrependPath=0"
        Start-Process -FilePath $installer -ArgumentList $args -Wait
        
        Remove-Item $installer -ErrorAction SilentlyContinue
    }
    
    # Atualiza variavel para usar o python local
    $pythonExe = Join-Path $pyDir "python.exe"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Host "[ERRO] A instalacao falhou. python.exe nao encontrado em $pyDir" -ForegroundColor Red
        Read-Host "Pressione ENTER para sair..."
        exit 1
    }
    
    Write-Host "[OK] Python dedicado pronto para uso." -ForegroundColor Green
}
else {
    $pythonExe = "python"
}

# 4. Configurar Ambiente Virtual
Write-Host ""
Write-Host "[INFO] Configurando dependencias (.venv)..." -ForegroundColor Yellow

# Remove venv antigo para garantir que usa o python novo
if (Test-Path ".venv") {
    Write-Host "       Removendo ambiente virtual antigo..."
    Remove-Item -Recurse -Force ".venv" -ErrorAction SilentlyContinue
}

Write-Host "       Criando novo ambiente..."
& $pythonExe -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Falha ao criar .venv" -ForegroundColor Red
    Read-Host "Pressione ENTER para sair..."
    exit 1
}

Write-Host "       Instalando bibliotecas (Isso pode demorar um pouco)..."
$pip = ".venv\Scripts\pip.exe"
& $pip install -r backend/requirements.txt | Out-Null

# 5. Lançar Aplicação
Write-Host ""
Write-Host "[SUCESSO] Tudo pronto! Iniciando Launcher..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan

# USAR python.exe COMUM (COM JANELA) PARA VERMOS OS ERROS
$launcher = ".venv\Scripts\python.exe"
if (-not (Test-Path $launcher)) { $launcher = ".venv\Scripts\python.exe" }

Write-Host "Executando: $launcher launcher.pyw"
& $launcher launcher.pyw

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[CRITICO] O Launcher fechou com erro!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Pressione ENTER para fechar esta janela..."
Read-Host
Start-Sleep -Seconds 10
