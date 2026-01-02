# ==========================================================
# ISP MONITOR - SETUP & UPDATE AGENT v3.1
# ==========================================================
# Este script gerencia a instalação, atualização e manutenção
# do sistema ISP Monitor.

$ErrorActionPreference = "Continue" # Permite continuar em erros não críticos
$LogFile = "setup.log"

function Write-Log($msg, $type="INFO") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] [$type] $msg"
    
    # Console output
    switch ($type) {
        "INFO" { $color = "Cyan" }
        "SUCCESS" { $color = "Green" }
        "WARN" { $color = "Yellow" }
        "ERROR" { $color = "Red" }
        default { $color = "White" }
    }
    Write-Host $line -ForegroundColor $color
    
    # File output
    try {
        $line | Out-File -FilePath $LogFile -Append -Encoding UTF8
    } catch {}
}

Write-Log "----------------------------------------------------------"
Write-Log "INICIANDO PROCESSO DE MANUTENÇÃO / ATUALIZAÇÃO"
Write-Log "----------------------------------------------------------"

# 1. PARAR PROCESSOS (Evitar Lock de arquivos)
Write-Log "[1/5] Parando processos do ISP Monitor..."
$procs = @("python", "pythonw", "node", "uvicorn")
foreach ($p in $procs) {
    try {
        Get-Process -Name $p -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Log "Processo '$p' finalizado."
    } catch {}
}

# 2. ATUALIZAR CÓDIGO (Git)
Write-Log "[2/5] Verificando atualizações no GitHub..."
if (Test-Path ".git") {
    try {
        $pull = git pull origin main 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Sistema atualizado com sucesso via Git." -SUCCESS
        } else {
            Write-Log "Aviso no Git Pull: $pull" -WARN
        }
    } catch {
        Write-Log "Git não encontrado ou falha na conexão. Pulando etapa Git." -WARN
    }
} else {
    Write-Log "Diretório não é um repositório Git. Pulando atualização automática." -INFO
}

# 3. VERIFICAR DEPENDÊNCIAS (Python & Node)
Write-Log "[3/5] Verificando dependências..."

# Python Packages
if (Test-Path "backend/requirements.txt") {
    Write-Log "Atualizando bibliotecas Python..."
    pip install -r backend/requirements.txt --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Bibliotecas Python [OK]" -SUCCESS
    } else {
        Write-Log "Erro ao atualizar bibliotecas Python." -ERROR
    }
}

# Frontend Packages
if (Test-Path "frontend/package.json") {
    Write-Log "Verificando dependências do Frontend (npm)..."
    Push-Location frontend
    if (-not (Test-Path "node_modules")) {
        Write-Log "Instalando Node Modules (Pode demorar)..."
        npm install --quiet
    } else {
        # Apenas um check rápido
        # npm install --quiet # Comentado para ser rápido no update diário
    }
    Pop-Location
}

# 4. BANCO DE DADOS (Migrations / Init)
Write-Log "[4/5] Sincronizando Banco de Dados..."
try {
    # Chama o init_db via Python
    $db_init = python -c "from backend.app.database import init_db; import asyncio; asyncio.run(init_db())" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Banco de Dados sincronizado." -SUCCESS
    } else {
        Write-Log "Erro ao sincronizar banco: $db_init" -ERROR
    }
} catch {
    Write-Log "Falha técnica ao tentar acessar o módulo de banco de dados." -ERROR
}

# 5. LIMPEZA E FINALIZAÇÃO
Write-Log "[5/5] Finalizando..."

# Limpar caches de build se necessário
if (Test-Path "frontend/.build_hash") {
    Remove-Item "frontend/.build_hash" -Force -ErrorAction SilentlyContinue
    Write-Log "Cache de build limpo (Forçará recompilação no Launcher)."
}

Write-Log "----------------------------------------------------------"
Write-Log "CONCLUÍDO! O SISTEMA ESTÁ PRONTO." -SUCCESS
Write-Log "----------------------------------------------------------"
Write-Log "Pressione qualquer tecla para sair..."

# Fim
