# Script para Aplicar Otimização no PostgreSQL (Windows)
# Requer execução como ADMINISTRADOR

$ErrorActionPreference = "Stop"

Write-Host "=== OTIMIZADOR DE POSTGRESQL PARA ISP MONITOR ===" -ForegroundColor Cyan

# 1. Detectar Serviço PostgreSQL
Write-Host "[1/5] Detectando serviço PostgreSQL..."
$service = Get-Service | Where-Object { $_.Name -like "postgresql*" } | Select-Object -First 1

if (-not $service) {
    Write-Error "Nenhum serviço PostgreSQL encontrado! Verifique se está instalado."
}

$serviceName = $service.Name
Write-Host "Serviço encontrado: $serviceName" -ForegroundColor Green

# 2. Encontrar Caminho do Config (Lendo do Registro ou Binário)
# Maneira robusta: Consultar binário do serviço
$wmi = Get-CimInstance Win32_Service -Filter "Name='$serviceName'"
$binaryPath = $wmi.PathName
# O path geralmente é ".../bin/pg_ctl.exe runservice -N ... -D "C:\Path\To\Data" ..."
if ($binaryPath -match '-D\s+"?([^"]+)"?') {
    $dataDir = $matches[1]
    Write-Host "Diretório de Dados (Data Dir): $dataDir" -ForegroundColor Green
} else {
    Write-Error "Não foi possível detectar a pasta DATA do Postgres automaticamente."
}

$confPath = Join-Path $dataDir "postgresql.conf"

if (-not (Test-Path $confPath)) {
    Write-Error "Arquivo de configuração não encontrado em: $confPath"
}

# 3. Parar Serviço
Write-Host "[2/5] Parando serviço $serviceName..."
Stop-Service $serviceName -Force
Start-Sleep -Seconds 2

# 4. Backup e Substituição
Write-Host "[3/5] Fazendo backup das configurações..."
Copy-Item $confPath "$confPath.backup.$(Get-Date -Format 'yyyyMMdd-HHmm')" -Force

Write-Host "[4/5] Aplicando novas configurações..."
$sourceOptimized = "c:\diegolima\isp-monitor\postgresql.conf.optimized"

if (-not (Test-Path $sourceOptimized)) {
    Write-Error "Arquivo otimizado não encontrado na origem!"
}

# Ler otimizado e escrever no destino
# Nota: Copiar arquivo direto pode dar problema de permissão ACL, melhor ler conteudo e setar.
$content = Get-Content $sourceOptimized -Raw
Set-Content -Path $confPath -Value $content

Write-Host "Configuração aplicada com sucesso!" -ForegroundColor Green

# 5. Reiniciar Serviço
Write-Host "[5/5] Iniciando serviço $serviceName..."
Start-Service $serviceName

Write-Host "=== CONCLUÍDO! POSTGRESQL OTIMIZADO ===" -ForegroundColor Cyan
Write-Host "Verifique os logs se o serviço não subir."
Write-Host "Pressione ENTER para sair..."
Read-Host
