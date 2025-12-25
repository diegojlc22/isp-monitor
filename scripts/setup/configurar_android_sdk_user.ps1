# Script para Configurar Android SDK (Usuario Atual - Nao precisa Admin)

Write-Host "Configurando Android SDK..." -ForegroundColor Cyan
Write-Host ""

# Caminho encontrado
$androidSdkPath = "C:\Users\DiegoLima\AppData\Local\Android\Sdk"

Write-Host "Android SDK: $androidSdkPath" -ForegroundColor Green
Write-Host ""

# Configurar ANDROID_HOME (Usuario)
Write-Host "Configurando ANDROID_HOME..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $androidSdkPath, "User")
Write-Host "ANDROID_HOME configurado!" -ForegroundColor Green

Write-Host ""

# Adicionar ao PATH (Usuario)
Write-Host "Adicionando ao PATH..." -ForegroundColor Yellow
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if (-not $currentPath) {
    $currentPath = ""
}

$pathsToAdd = @(
    "$androidSdkPath\platform-tools",
    "$androidSdkPath\tools"
)

foreach ($pathToAdd in $pathsToAdd) {
    if ($currentPath -notlike "*$pathToAdd*") {
        if ($currentPath) {
            $currentPath = "$currentPath;$pathToAdd"
        }
        else {
            $currentPath = $pathToAdd
        }
        Write-Host "Adicionado: $pathToAdd" -ForegroundColor Green
    }
}

[Environment]::SetEnvironmentVariable("Path", $currentPath, "User")
Write-Host "PATH atualizado!" -ForegroundColor Green

Write-Host ""
Write-Host "Configuracao concluida!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE: Feche este terminal e abra um NOVO!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para testar, abra um novo PowerShell e digite:" -ForegroundColor Cyan
Write-Host "  adb --version" -ForegroundColor White
Write-Host ""
Write-Host "Pressione Enter para sair..."
Read-Host
