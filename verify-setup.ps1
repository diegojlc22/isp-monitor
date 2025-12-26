<#
.SYNOPSIS
    Verificador de Instalação - ISP Monitor
.DESCRIPTION
    Verifica se todas as dependências foram instaladas corretamente
#>

$ErrorActionPreference = "Continue"

function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Fail { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }

Clear-Host
Write-Host @"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║        VERIFICADOR DE INSTALAÇÃO - ISP MONITOR            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host "`nVerificando dependências...`n" -ForegroundColor Yellow

$allOk = $true

# Verificar Python
Write-Host "1. Python:" -ForegroundColor Magenta
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+\.\d+\.\d+)") {
        $version = $matches[1]
        Write-Success "Python $version instalado"
    }
    else {
        Write-Fail "Python não encontrado"
        $allOk = $false
    }
}
catch {
    Write-Fail "Python não encontrado"
    $allOk = $false
}

# Verificar Node.js
Write-Host "`n2. Node.js:" -ForegroundColor Magenta
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match "v(\d+\.\d+\.\d+)") {
        $version = $matches[1]
        Write-Success "Node.js $version instalado"
    }
    else {
        Write-Fail "Node.js não encontrado"
        $allOk = $false
    }
}
catch {
    Write-Fail "Node.js não encontrado"
    $allOk = $false
}

# Verificar NPM
Write-Host "`n3. NPM:" -ForegroundColor Magenta
try {
    $npmVersion = npm --version 2>&1
    if ($npmVersion) {
        Write-Success "NPM $npmVersion instalado"
    }
    else {
        Write-Fail "NPM não encontrado"
        $allOk = $false
    }
}
catch {
    Write-Fail "NPM não encontrado"
    $allOk = $false
}

# Verificar PostgreSQL
Write-Host "`n4. PostgreSQL:" -ForegroundColor Magenta
try {
    $pgVersion = psql --version 2>&1
    if ($pgVersion -match "(\d+\.\d+)") {
        $version = $matches[1]
        Write-Success "PostgreSQL $version instalado"
    }
    else {
        Write-Fail "PostgreSQL não encontrado"
        $allOk = $false
    }
}
catch {
    Write-Fail "PostgreSQL não encontrado"
    $allOk = $false
}

# Verificar Git
Write-Host "`n5. Git:" -ForegroundColor Magenta
try {
    $gitVersion = git --version 2>&1
    if ($gitVersion -match "(\d+\.\d+\.\d+)") {
        $version = $matches[1]
        Write-Success "Git $version instalado"
    }
    else {
        Write-Fail "Git não encontrado"
        $allOk = $false
    }
}
catch {
    Write-Fail "Git não encontrado"
    $allOk = $false
}

# Verificar pip
Write-Host "`n6. Pip (Python Package Manager):" -ForegroundColor Magenta
try {
    $pipVersion = python -m pip --version 2>&1
    if ($pipVersion -match "pip (\d+\.\d+\.\d+)") {
        $version = $matches[1]
        Write-Success "Pip $version instalado"
    }
    else {
        Write-Fail "Pip não encontrado"
        $allOk = $false
    }
}
catch {
    Write-Fail "Pip não encontrado"
    $allOk = $false
}

# Verificar pacotes Python
Write-Host "`n7. Pacotes Python:" -ForegroundColor Magenta
$pythonPackages = @("fastapi", "uvicorn", "sqlalchemy", "pydantic")
foreach ($package in $pythonPackages) {
    try {
        $result = python -m pip show $package 2>&1
        if ($result -match "Name: $package") {
            Write-Success "$package instalado"
        }
        else {
            Write-Fail "$package não encontrado"
            $allOk = $false
        }
    }
    catch {
        Write-Fail "$package não encontrado"
        $allOk = $false
    }
}

# Verificar node_modules do frontend
Write-Host "`n8. Pacotes Frontend:" -ForegroundColor Magenta
$frontendNodeModules = Join-Path $PSScriptRoot "frontend\node_modules"
if (Test-Path $frontendNodeModules) {
    $packageCount = (Get-ChildItem $frontendNodeModules -Directory).Count
    Write-Success "Frontend: $packageCount pacotes instalados"
}
else {
    Write-Fail "Frontend: node_modules não encontrado"
    $allOk = $false
}

# Verificar node_modules do mobile
Write-Host "`n9. Pacotes Mobile:" -ForegroundColor Magenta
$mobileNodeModules = Join-Path $PSScriptRoot "mobile\node_modules"
if (Test-Path $mobileNodeModules) {
    $packageCount = (Get-ChildItem $mobileNodeModules -Directory).Count
    Write-Success "Mobile: $packageCount pacotes instalados"
}
else {
    Write-Fail "Mobile: node_modules não encontrado"
    $allOk = $false
}

# Verificar arquivo .env
Write-Host "`n10. Configuração (.env):" -ForegroundColor Magenta
$envFile = Join-Path $PSScriptRoot "backend\.env"
if (Test-Path $envFile) {
    Write-Success "Arquivo .env encontrado"
}
else {
    Write-Fail "Arquivo .env não encontrado"
    $allOk = $false
}

# Verificar Ngrok
Write-Host "`n11. Ngrok:" -ForegroundColor Magenta
$ngrokExe = Join-Path $PSScriptRoot "tools\ngrok\ngrok.exe"
if (Test-Path $ngrokExe) {
    Write-Success "Ngrok instalado"
}
else {
    Write-Fail "Ngrok não encontrado"
    $allOk = $false
}

# Verificar serviço PostgreSQL
Write-Host "`n12. Serviço PostgreSQL:" -ForegroundColor Magenta
try {
    $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
    if ($pgService) {
        if ($pgService.Status -eq "Running") {
            Write-Success "PostgreSQL está rodando"
        }
        else {
            Write-Info "PostgreSQL instalado mas não está rodando"
            Write-Info "Execute: Start-Service $($pgService.Name)"
        }
    }
    else {
        Write-Fail "Serviço PostgreSQL não encontrado"
        $allOk = $false
    }
}
catch {
    Write-Fail "Erro ao verificar serviço PostgreSQL"
    $allOk = $false
}

# Resultado final
Write-Host "`n" + ("=" * 60) -ForegroundColor Gray
if ($allOk) {
    Write-Host "`n✅ TODAS AS DEPENDÊNCIAS ESTÃO INSTALADAS!" -ForegroundColor Green
    Write-Host "`nPróximos passos:" -ForegroundColor Cyan
    Write-Host "  1. Execute: .\LAUNCHER.bat" -ForegroundColor White
    Write-Host "  2. Acesse: http://localhost:5173" -ForegroundColor White
    Write-Host "`n"
}
else {
    Write-Host "`n⚠️ ALGUMAS DEPENDÊNCIAS ESTÃO FALTANDO!" -ForegroundColor Yellow
    Write-Host "`nSolução:" -ForegroundColor Cyan
    Write-Host "  1. Execute novamente: .\SETUP.bat (como Administrador)" -ForegroundColor White
    Write-Host "  2. Ou instale manualmente as dependências faltantes" -ForegroundColor White
    Write-Host "`n"
}

Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
