# Script de Reparo e Inicialização do ISP Monitor
Set-Location $PSScriptRoot

# Matar processos Python antigos que podem estar travando a pasta .venv
Write-Host "[INIT] Limpando processos antigos..." -ForegroundColor DarkGray
Get-Process python, pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*isp-monitor*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   ISP MONITOR - DIAGNOSTICO E REPARO (PowerShell)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Versão do Python Instalada
Write-Host "[INFO] Verificando Python do sistema..." -ForegroundColor Yellow

$global:SystemPythonGood = $false
try {
    $sysPy = Get-Command python -ErrorAction SilentlyContinue
    if ($sysPy) {
        # Verificar versão e Tkinter
        $checkCmd = 'import sys; import tkinter; major, minor = sys.version_info[:2]; exit(0) if major == 3 and minor >= 10 else exit(1)'
        python -c $checkCmd 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "       Python do sistema detectado e funcional (com Tkinter)." -ForegroundColor Green
            $global:SystemPythonGood = $true
        }
        else {
            Write-Host "       Python do sistema encontrado, mas incompleto ou antigo." -ForegroundColor DarkGray
        }
    }
    else {
        Write-Host "       Nenhum Python encontrado no PATH." -ForegroundColor DarkGray
    }
}
catch {
    Write-Host "       Erro ao verificar Python do sistema." -ForegroundColor Red
}

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
        # Usando /passive para mostrar barra de progresso e eventuais erros na tela
        $installArgs = "/passive InstallAllUsers=0 TargetDir=`"$pyDir`" Include_tcltk=1 Include_test=0 PrependPath=0"
        Start-Process -FilePath $installer -ArgumentList $installArgs -Wait
        
        Remove-Item $installer -ErrorAction SilentlyContinue
    }
    
    # Atualiza variavel para usar o python local
    $pythonExe = Join-Path $pyDir "python.exe"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Host "[ERRO] A instalacao falhou. python.exe nao encontrado em $pyDir" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] Python dedicado pronto para uso." -ForegroundColor Green
}
else {
    $pythonExe = "python"
}

# 4. Configurar Ambiente Virtual
Write-Host ""
Write-Host "[INFO] Verificando ambiente virtual (.venv)..." -ForegroundColor Yellow

$venvPython = ".venv\Scripts\python.exe"
$envHealthy = $false

if (Test-Path $venvPython) {
    # Tenta importar fastapi como teste de saude
    & $venvPython -c "import fastapi" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $envHealthy = $true
        Write-Host "[OK] Ambiente virtual ja existe e esta saudavel." -ForegroundColor Green
    }
}

if (-not $envHealthy) {
    Write-Host "[INFO] Ambiente inexistente ou corrompido. Configurando do zero..." -ForegroundColor Yellow
    
    # Remove venv antigo se existir
    if (Test-Path ".venv") {
        Write-Host "       Removendo ambiente virtual antigo..."
        Remove-Item -Recurse -Force ".venv" -ErrorAction SilentlyContinue
    }

    Write-Host "       Criando novo ambiente..."
    & $pythonExe -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRO] Falha ao criar .venv" -ForegroundColor Red
        exit 1
    }

    Write-Host "       Instalando bibliotecas (Isso pode demorar um pouco)..."
    $pip = ".venv\Scripts\pip.exe"
    & $pip install -r backend/requirements.txt | Out-Null
}
else {
    Write-Host "[SKIP] Pulando instalacao de dependencias (Fast Path)." -ForegroundColor DarkGray
}

# 5. Lançar Aplicação
Write-Host ""
Write-Host "[SUCESSO] Tudo pronto! Iniciando Launcher..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan

# USAR python.exe COMUM (COM JANELA) PARA VERMOS OS ERROS
# USAR pythonw.exe (SEM JANELA) PARA DEIXAR LIMPO
$launcher = ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $launcher)) { $launcher = ".venv\Scripts\python.exe" }

Write-Host "Iniciando Launcher e fechando este console..."
Start-Process -FilePath $launcher -ArgumentList "launcher.pyw"

# Pequena pausa para garantir que o processo iniciou
Start-Sleep -Seconds 2
exit 0
