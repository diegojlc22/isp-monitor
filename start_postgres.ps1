# Script para iniciar PostgreSQL com privilégios elevados e aguardar prontidão
$serviceName = "postgresql-x64-18"
$port = 5432

Write-Host "[PostgreSQL] Verificando status..." -ForegroundColor Cyan

$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if ($null -eq $service) {
    Write-Host "[ERRO] Serviço PostgreSQL não encontrado!" -ForegroundColor Red
    Write-Host "       Nome esperado: $serviceName" -ForegroundColor Yellow
    exit 1
}

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
