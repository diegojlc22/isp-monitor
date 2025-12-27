$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path "$PSScriptRoot\..\.."
$PythonBin = "$ProjectRoot\python_bin"
$PythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

Write-Host "-> Diretorio Alvo: $PythonBin" -ForegroundColor Cyan

# 1. Limpar pasta antiga (se existir)
if (Test-Path $PythonBin) {
    Write-Host "   [LIMPEZA] Removendo python_bin corrompido..." -ForegroundColor Yellow
    Remove-Item $PythonBin -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $PythonBin | Out-Null

# 2. Baixar Python Zip
$ZipPath = "$env:TEMP\python_embed.zip"
Write-Host "   [DOWNLOAD] Baixando Python 3.11 ($PythonUrl)..."
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $PythonUrl -OutFile $ZipPath -UseBasicParsing
}
catch {
    Write-Host "   [ERRO] Falha no download: $_" -ForegroundColor Red
    exit 1
}

# 3. Extrair
Write-Host "   [EXTRACAO] Descompactando..."
Expand-Archive -Path $ZipPath -DestinationPath $PythonBin -Force
Remove-Item $ZipPath -ErrorAction SilentlyContinue

# 4. Habilitar 'import site' (Crucial para Pip)
# O python embedded vem com um arquivo ._pth que bloqueia o pip se não editar
$PthFile = Get-ChildItem "$PythonBin\*._pth" | Select-Object -First 1
if ($PthFile) {
    $Content = Get-Content $PthFile.FullName
    # Descomenta a linha 'import site'
    $Content = $Content -replace "#import site", "import site"
    $Content | Set-Content $PthFile.FullName
    Write-Host "   [CONFIG] Arquivo ._pth alterado para permitir modulos."
}

# 5. Instalar PIP
Write-Host "   [PIP] Baixando instalador do Pip..."
$GetPipPath = "$PythonBin\get-pip.py"
Invoke-WebRequest -Uri $GetPipUrl -OutFile $GetPipPath -UseBasicParsing

Write-Host "   [PIP] Instalando Pip..."
$PyExe = "$PythonBin\python.exe"
$Proc = Start-Process -FilePath $PyExe -ArgumentList "$GetPipPath --no-warn-script-location" -Wait -PassThru -NoNewWindow

if ($Proc.ExitCode -ne 0) {
    Write-Host "   [ERRO] Falha ao instalar Pip." -ForegroundColor Red
    exit 1
}

# Limpeza
Remove-Item $GetPipPath -ErrorAction SilentlyContinue

Write-Host "   [OK] Python Base pronto." -ForegroundColor Green
exit 0
