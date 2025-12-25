# Configurar JAVA_HOME automaticamente

Write-Host "Procurando Java JDK..." -ForegroundColor Cyan

# Procurar Java do Android Studio
$possibleJavaPaths = @(
    "C:\Program Files\Android\Android Studio\jbr",
    "C:\Program Files\Android\Android Studio\jre",
    "$env:LOCALAPPDATA\Android\Android Studio\jbr",
    "$env:LOCALAPPDATA\Android\Android Studio\jre"
)

$javaPath = $null

foreach ($path in $possibleJavaPaths) {
    if (Test-Path $path) {
        $javaPath = $path
        Write-Host "Java encontrado em: $javaPath" -ForegroundColor Green
        break
    }
}

if (-not $javaPath) {
    Write-Host "Java nao encontrado!" -ForegroundColor Red
    Write-Host "Digite o caminho do Java manualmente:" -ForegroundColor Yellow
    $javaPath = Read-Host "Caminho do Java"
}

# Configurar JAVA_HOME
Write-Host "Configurando JAVA_HOME..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("JAVA_HOME", $javaPath, "User")
Write-Host "JAVA_HOME configurado: $javaPath" -ForegroundColor Green

# Adicionar ao PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$javaBinPath = "$javaPath\bin"

if ($currentPath -notlike "*$javaBinPath*") {
    $currentPath = "$currentPath;$javaBinPath"
    [Environment]::SetEnvironmentVariable("Path", $currentPath, "User")
    Write-Host "Java adicionado ao PATH!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Configuracao concluida!" -ForegroundColor Green
Write-Host "Feche e abra um NOVO terminal!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para testar, digite: java -version" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Enter para sair..."
Read-Host
