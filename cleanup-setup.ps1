<#
.SYNOPSIS
    Desinstalador - ISP Monitor
.DESCRIPTION
    Remove o estado de instalação para permitir reinstalação completa
.NOTES
    NÃO remove as dependências instaladas (Python, Node, PostgreSQL, Git)
    Apenas limpa o estado e permite reinstalar pacotes do projeto
#>

$ErrorActionPreference = "Stop"

function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }

Clear-Host
Write-Host @"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           LIMPEZA DE INSTALAÇÃO - ISP MONITOR             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host "`n"
Write-Warning "Este script irá:"
Write-Host "  • Remover node_modules (frontend e mobile)" -ForegroundColor Yellow
Write-Host "  • Limpar cache do pip" -ForegroundColor Yellow
Write-Host "  • Remover arquivo .setup-state.json" -ForegroundColor Yellow
Write-Host "  • Remover logs de instalação" -ForegroundColor Yellow
Write-Host "`n"
Write-Info "NÃO será removido:"
Write-Host "  • Python, Node.js, PostgreSQL, Git" -ForegroundColor White
Write-Host "  • Banco de dados" -ForegroundColor White
Write-Host "  • Arquivo .env" -ForegroundColor White
Write-Host "`n"

$confirm = Read-Host "Deseja continuar? (S/N)"
if ($confirm -ne "S" -and $confirm -ne "s") {
    Write-Info "Operação cancelada."
    exit 0
}

Write-Host "`n"
$ProjectRoot = $PSScriptRoot

# Remover node_modules do frontend
Write-Info "Removendo node_modules do frontend..."
$frontendNodeModules = Join-Path $ProjectRoot "frontend\node_modules"
if (Test-Path $frontendNodeModules) {
    Remove-Item $frontendNodeModules -Recurse -Force
    Write-Success "Frontend: node_modules removido"
}
else {
    Write-Info "Frontend: node_modules não encontrado"
}

# Remover node_modules do mobile
Write-Info "Removendo node_modules do mobile..."
$mobileNodeModules = Join-Path $ProjectRoot "mobile\node_modules"
if (Test-Path $mobileNodeModules) {
    Remove-Item $mobileNodeModules -Recurse -Force
    Write-Success "Mobile: node_modules removido"
}
else {
    Write-Info "Mobile: node_modules não encontrado"
}

# Limpar cache do pip
Write-Info "Limpando cache do pip..."
try {
    python -m pip cache purge 2>&1 | Out-Null
    Write-Success "Cache do pip limpo"
}
catch {
    Write-Warning "Não foi possível limpar cache do pip"
}

# Remover arquivo de estado
Write-Info "Removendo arquivo de estado..."
$stateFile = Join-Path $ProjectRoot ".setup-state.json"
if (Test-Path $stateFile) {
    Remove-Item $stateFile -Force
    Write-Success "Arquivo .setup-state.json removido"
}
else {
    Write-Info "Arquivo .setup-state.json não encontrado"
}

# Remover logs
Write-Info "Removendo logs de instalação..."
$logFile = Join-Path $ProjectRoot "setup.log"
if (Test-Path $logFile) {
    Remove-Item $logFile -Force
    Write-Success "Arquivo setup.log removido"
}
else {
    Write-Info "Arquivo setup.log não encontrado"
}

Write-Host "`n"
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "║              LIMPEZA CONCLUÍDA COM SUCESSO!                ║" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`n"

Write-Success "✓ Estado de instalação limpo"
Write-Success "✓ Pronto para reinstalar"
Write-Host "`n"
Write-Info "Próximo passo: Execute SETUP.bat novamente para reinstalar"
Write-Host "`n"

Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
