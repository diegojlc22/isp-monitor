# Script de Reset Completo do Banco de Dados
# Deleta e recria o banco com schema atualizado

Write-Host "[Reset] Iniciando reset do banco de dados..." -ForegroundColor Cyan

# Configurar senha
$env:PGPASSWORD = "110812"

# Encontrar psql
$psqlPath = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
if (-not (Test-Path $psqlPath)) {
    $psqlPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
}

if (-not (Test-Path $psqlPath)) {
    Write-Host "[ERRO] psql.exe não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "[Reset] psql encontrado: $psqlPath" -ForegroundColor Green

# Deletar banco
Write-Host "[Reset] Deletando banco 'isp_monitor'..." -ForegroundColor Yellow
& $psqlPath -U postgres -c "DROP DATABASE IF EXISTS isp_monitor;" 2>$null

# Criar banco
Write-Host "[Reset] Criando banco 'isp_monitor'..." -ForegroundColor Cyan
& $psqlPath -U postgres -c "CREATE DATABASE isp_monitor;"

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Banco 'isp_monitor' recriado com sucesso!" -ForegroundColor Green
    Write-Host "" -ForegroundColor Green
    Write-Host "Próximo passo: Reinicie o sistema com ABRIR_SISTEMA.bat" -ForegroundColor Cyan
    Write-Host "O schema será criado automaticamente na primeira inicialização." -ForegroundColor Cyan
}
else {
    Write-Host "[ERRO] Falha ao criar banco!" -ForegroundColor Red
}

# Limpar senha
Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
