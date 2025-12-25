# Script para Configurar Android SDK no Windows
# Execute como Administrador

Write-Host "Configurando Android SDK..." -ForegroundColor Cyan
Write-Host ""

# Procurar Android SDK
Write-Host "Procurando Android SDK..." -ForegroundColor Yellow

$possiblePaths = @(
    "$env:LOCALAPPDATA\Android\Sdk",
    "$env:USERPROFILE\AppData\Local\Android\Sdk",
    "C:\Android\Sdk"
)

$androidSdkPath = $null

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $androidSdkPath = $path
        Write-Host "Android SDK encontrado em: $androidSdkPath" -ForegroundColor Green
        break
    }
}

if (-not $androidSdkPath) {
    Write-Host "Android SDK nao encontrado automaticamente." -ForegroundColor Red
    Write-Host "Digite o caminho manualmente:" -ForegroundColor Yellow
    $androidSdkPath = Read-Host "Caminho do Android SDK"
}

Write-Host ""

# Configurar ANDROID_HOME
Write-Host "Configurando ANDROID_HOME..." -ForegroundColor Yellow

[Environment]::SetEnvironmentVariable("ANDROID_HOME", $androidSdkPath, "Machine")
Write-Host "ANDROID_HOME configurado: $androidSdkPath" -ForegroundColor Green

Write-Host ""

# Adicionar ao PATH
Write-Host "Adicionando ao PATH..." -ForegroundColor Yellow

$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$newPath = "$currentPath;$androidSdkPath\platform-tools;$androidSdkPath\tools"

[Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
Write-Host "PATH atualizado!" -ForegroundColor Green

Write-Host ""
Write-Host "Configuracao concluida!" -ForegroundColor Green
Write-Host "IMPORTANTE: Feche e abra um NOVO terminal!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione Enter para sair..."
Read-Host
