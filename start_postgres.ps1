# Script para iniciar PostgreSQL com privilégios elevados e aguardar prontidão
# Auto-detecta qualquer versão do PostgreSQL instalada
$port = 5432

Write-Host "[PostgreSQL] Detectando serviço instalado..." -ForegroundColor Cyan

# Busca qualquer serviço PostgreSQL (postgresql-x64-16, 17, 18, etc)
$service = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1

if ($null -eq $service) {
    Write-Host "[ERRO] Nenhum serviço PostgreSQL encontrado!" -ForegroundColor Red
    Write-Host "       Procurado: postgresql-x64-* (qualquer versão)" -ForegroundColor Yellow
    Write-Host "       Instale o PostgreSQL ou use SQLite (automático)" -ForegroundColor Yellow
    exit 1
}

$serviceName = $service.Name
Write-Host "[OK] Detectado: $serviceName" -ForegroundColor Green

if ($service.Status -ne 'Running') {
    Write-Host "[!] Iniciando PostgreSQL..." -ForegroundColor Yellow
    try {
        Start-Service -Name $serviceName -ErrorAction Stop
        Write-Host "[OK] Serviço iniciado via Windows Service Manager." -ForegroundColor Green
    }
    catch {
        Write-Host "[ERRO] Falha ao iniciar PostgreSQL: $_" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "[OK] Serviço já está rodando." -ForegroundColor Green
}

# --- AGUARDAR PORTA 5432 ---
Write-Host "[PostgreSQL] Aguardando banco aceitar conexões (porta $port)..." -ForegroundColor Cyan
$maxRetries = 15
$retryCount = 0
$connected = $false

while ($retryCount -lt $maxRetries -and -not $connected) {
    $tcpConnection = New-Object System.Net.Sockets.TcpClient
    try {
        $tcpConnection.Connect("127.0.0.1", $port)
        $connected = $true
        $tcpConnection.Close()
        Write-Host "[OK] PostgreSQL pronto!" -ForegroundColor Green
    }
    catch {
        $retryCount++
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
}

if (-not $connected) {
    Write-Host "`n[AVISO] Timeout aguardando PostgreSQL. O sistema pode falhar ao conectar." -ForegroundColor Yellow
}
exit 0
