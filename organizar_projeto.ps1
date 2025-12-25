# Script de Organizacao do Projeto ISP Monitor
# Este script move arquivos para pastas organizadas

Write-Host "Organizando projeto ISP Monitor..." -ForegroundColor Cyan
Write-Host ""

$baseDir = "C:\Users\DiegoLima\.gemini\antigravity\scratch\isp_monitor"
cd $baseDir

# Criar estrutura de pastas
Write-Host "Criando estrutura de pastas..." -ForegroundColor Yellow

$folders = @(
    "docs\guias",
    "scripts\setup",
    "scripts\database",
    "scripts\deprecated",
    "tools\ngrok",
    "logs"
)

foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-Host "Criado: $folder" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Movendo arquivos..." -ForegroundColor Yellow

# Mover guias para docs/guias
Move-Item -Path "GUIA_*.md" -Destination "docs\guias\" -Force -ErrorAction SilentlyContinue

# Mover scripts de setup
Move-Item -Path "configurar_*.ps1" -Destination "scripts\setup\" -Force -ErrorAction SilentlyContinue
Move-Item -Path "gerar_apk.ps1" -Destination "scripts\setup\" -Force -ErrorAction SilentlyContinue

# Mover scripts de database
Move-Item -Path "fix_db*.py" -Destination "scripts\database\" -Force -ErrorAction SilentlyContinue
Move-Item -Path "update_*.py" -Destination "scripts\database\" -Force -ErrorAction SilentlyContinue

# Mover scripts deprecated
Move-Item -Path "limpar_projeto.bat" -Destination "scripts\deprecated\" -Force -ErrorAction SilentlyContinue
Move-Item -Path "deploy.bat" -Destination "scripts\deprecated\" -Force -ErrorAction SilentlyContinue
Move-Item -Path "parar_sistema.bat" -Destination "scripts\deprecated\" -Force -ErrorAction SilentlyContinue
Move-Item -Path "reiniciar_tudo.bat" -Destination "scripts\deprecated\" -Force -ErrorAction SilentlyContinue

# Mover ngrok
Move-Item -Path "ngrok.exe" -Destination "tools\ngrok\" -Force -ErrorAction SilentlyContinue
Move-Item -Path "ngrok.zip" -Destination "tools\ngrok\" -Force -ErrorAction SilentlyContinue

# Mover logs
Move-Item -Path "*.log" -Destination "logs\" -Force -ErrorAction SilentlyContinue
Move-Item -Path "monitor.db" -Destination "logs\" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Organizacao concluida!" -ForegroundColor Green
Write-Host ""
Write-Host "Estrutura final:" -ForegroundColor Cyan
Write-Host "  docs/guias/          - Guias de uso" -ForegroundColor Gray
Write-Host "  scripts/setup/       - Scripts de configuracao" -ForegroundColor Gray
Write-Host "  scripts/database/    - Scripts de banco de dados" -ForegroundColor Gray
Write-Host "  scripts/deprecated/  - Scripts antigos (pode deletar)" -ForegroundColor Gray
Write-Host "  tools/ngrok/         - Ngrok executavel" -ForegroundColor Gray
Write-Host "  logs/                - Logs e databases temporarios" -ForegroundColor Gray
Write-Host ""
Write-Host "Pressione Enter para sair..."
Read-Host
