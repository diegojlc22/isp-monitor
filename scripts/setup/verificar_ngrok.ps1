# Script para Verificar Status do Ngrok

Write-Host "Verificando status do Ngrok..." -ForegroundColor Cyan
Write-Host ""

# Verificar se ngrok está rodando
$ngrokProcess = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue

if ($ngrokProcess) {
    Write-Host "✅ Ngrok está RODANDO" -ForegroundColor Green
    Write-Host ""
    Write-Host "PID: $($ngrokProcess.Id)" -ForegroundColor Gray
    Write-Host "Tempo rodando: $([math]::Round(($ngrokProcess.StartTime - (Get-Date)).TotalMinutes * -1, 2)) minutos" -ForegroundColor Gray
    Write-Host ""
    
    # Testar conexão
    Write-Host "Testando conexão..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "https://uniconoclastic-addedly-yareli.ngrok-free.dev/api/health" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ Servidor ACESSÍVEL via Ngrok!" -ForegroundColor Green
        Write-Host "Status: $($response.StatusCode)" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Servidor NÃO acessível via Ngrok" -ForegroundColor Red
        Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Gray
    }
}
else {
    Write-Host "❌ Ngrok NÃO está rodando!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para iniciar o Ngrok:" -ForegroundColor Yellow
    Write-Host "  1. Execute: LAUNCHER.bat" -ForegroundColor White
    Write-Host "  2. Ou execute: .\tools\ngrok\ngrok.exe http --domain=uniconoclastic-addedly-yareli.ngrok-free.dev 8080" -ForegroundColor White
}

Write-Host ""
Write-Host "URL Pública: https://uniconoclastic-addedly-yareli.ngrok-free.dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Enter para sair..."
Read-Host
