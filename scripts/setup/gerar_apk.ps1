# Script Completo para Gerar APK
# Execute este script e aguarde (10-15 minutos)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GERANDO APK - ISP Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"
$mobileDir = "C:\Users\DiegoLima\.gemini\antigravity\scratch\isp_monitor\mobile"

# Passo 1: Configurar JAVA_HOME
Write-Host "[1/5] Configurando JAVA_HOME..." -ForegroundColor Yellow
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:Path = "$env:Path;$env:JAVA_HOME\bin"
Write-Host "JAVA_HOME: $env:JAVA_HOME" -ForegroundColor Green
Write-Host ""

# Passo 2: Configurar ANDROID_HOME
Write-Host "[2/5] Configurando ANDROID_HOME..." -ForegroundColor Yellow
$env:ANDROID_HOME = "C:\Users\DiegoLima\AppData\Local\Android\Sdk"
$env:Path = "$env:Path;$env:ANDROID_HOME\platform-tools"
Write-Host "ANDROID_HOME: $env:ANDROID_HOME" -ForegroundColor Green
Write-Host ""

# Passo 3: Limpar build anterior (se existir)
Write-Host "[3/5] Limpando builds anteriores..." -ForegroundColor Yellow
cd $mobileDir
if (Test-Path "android") {
    Write-Host "Removendo pasta android..." -ForegroundColor Gray
    Remove-Item -Recurse -Force android -ErrorAction SilentlyContinue
}
Write-Host "Limpeza concluida!" -ForegroundColor Green
Write-Host ""

# Passo 4: Executar prebuild
Write-Host "[4/5] Executando prebuild (pode demorar 2-3 min)..." -ForegroundColor Yellow
npx expo prebuild --platform android --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO no prebuild!" -ForegroundColor Red
    exit 1
}
Write-Host "Prebuild concluido!" -ForegroundColor Green
Write-Host ""

# Passo 5: Compilar APK
Write-Host "[5/5] Compilando APK (vai demorar 10-15 min)..." -ForegroundColor Yellow
Write-Host "Aguarde... O Gradle vai baixar muitas dependencias na primeira vez." -ForegroundColor Gray
Write-Host ""

cd android
.\gradlew assembleRelease --no-daemon

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERRO ao compilar APK!" -ForegroundColor Red
    Write-Host "Verifique os erros acima." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  APK GERADO COM SUCESSO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$apkPath = "$mobileDir\android\app\build\outputs\apk\release\app-release.apk"
if (Test-Path $apkPath) {
    $apkSize = (Get-Item $apkPath).Length / 1MB
    Write-Host "Localizacao: $apkPath" -ForegroundColor Cyan
    Write-Host "Tamanho: $([math]::Round($apkSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Abra a pasta do APK? (S/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "S" -or $response -eq "s") {
        explorer.exe (Split-Path $apkPath)
    }
}
else {
    Write-Host "APK nao encontrado em: $apkPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "Pressione Enter para sair..."
Read-Host
