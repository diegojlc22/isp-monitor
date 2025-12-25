# Script para Iniciar Ngrok Automaticamente (SEM Admin)
# Adiciona ao Startup do Windows

Write-Host "Configurando Ngrok para iniciar com Windows..." -ForegroundColor Cyan
Write-Host ""

$ngrokPath = "C:\Users\DiegoLima\.gemini\antigravity\scratch\isp_monitor\tools\ngrok\ngrok.exe"
$domain = "uniconoclastic-addedly-yareli.ngrok-free.dev"
$startupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"

# Criar arquivo .bat no Startup
$batContent = @"
@echo off
start /min "" "$ngrokPath" http --domain=$domain 8080
"@

$batPath = "$startupFolder\ISP_Monitor_Ngrok.bat"

try {
    $batContent | Out-File -FilePath $batPath -Encoding ASCII -Force
    Write-Host "Ngrok configurado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Arquivo criado em:" -ForegroundColor Yellow
    Write-Host "  $batPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "O Ngrok vai iniciar automaticamente quando voce fizer login no Windows!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para testar agora, execute:" -ForegroundColor Cyan
    Write-Host "  $batPath" -ForegroundColor White
    Write-Host ""
    Write-Host "Para remover, delete o arquivo:" -ForegroundColor Yellow
    Write-Host "  $batPath" -ForegroundColor Gray
}
catch {
    Write-Host "Erro ao criar arquivo!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Gray
}

Write-Host ""
Write-Host "Pressione Enter para sair..."
Read-Host
