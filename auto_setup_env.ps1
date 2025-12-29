# Auto-Setup Script - Cria .env se não existir
# Detecta PostgreSQL e configura automaticamente com verificação inteligente

$envFile = ".env"

Write-Host "[Setup] Verificando configuração..." -ForegroundColor Cyan

# Se .env já existe, não faz nada
if (Test-Path $envFile) {
    Write-Host "[OK] Arquivo .env já existe." -ForegroundColor Green
    exit 0
}

Write-Host "[!] Arquivo .env não encontrado. Criando automaticamente..." -ForegroundColor Yellow

# ===== DETECÇÃO INTELIGENTE DE POSTGRESQL =====
$dbUrl = "sqlite+aiosqlite:///./isp_monitor_v2.db"
$dbType = "SQLite"
$usePostgres = $false

# Nome do banco de dados (configurável via variável de ambiente)
$dbName = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "isp_monitor" }
Write-Host "[Setup] Nome do banco: $dbName" -ForegroundColor Cyan

# 1. Verificar se o serviço PostgreSQL existe
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1

if ($null -ne $pgService) {
    $pgVersion = $pgService.Name -replace "postgresql-x64-", ""
    Write-Host "[OK] PostgreSQL $pgVersion detectado." -ForegroundColor Green
    
    # 2. Verificar se o serviço está rodando
    if ($pgService.Status -ne 'Running') {
        Write-Host "[!] PostgreSQL parado. Tentando iniciar..." -ForegroundColor Yellow
        try {
            Start-Service -Name $pgService.Name -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Host "[OK] PostgreSQL iniciado." -ForegroundColor Green
        }
        catch {
            Write-Host "[AVISO] Não foi possível iniciar PostgreSQL. Usando SQLite." -ForegroundColor Yellow
        }
    }
    
    # 3. Verificar se a porta 5432 está acessível
    if ($pgService.Status -eq 'Running') {
        Write-Host "[Setup] Testando conexão PostgreSQL..." -ForegroundColor Cyan
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.Connect("127.0.0.1", 5432)
            $tcpClient.Close()
            
            # 4. Tentar encontrar psql para verificar se o banco existe
            $psqlPath = $null
            $possiblePaths = @(
                "C:\Program Files\PostgreSQL\$pgVersion\bin\psql.exe",
                "C:\Program Files\PostgreSQL\17\bin\psql.exe",
                "C:\Program Files\PostgreSQL\16\bin\psql.exe",
                "C:\Program Files (x86)\PostgreSQL\$pgVersion\bin\psql.exe"
            )
            
            foreach ($path in $possiblePaths) {
                if (Test-Path $path) {
                    $psqlPath = $path
                    break
                }
            }
            
            if ($psqlPath) {
                Write-Host "[OK] psql encontrado: $psqlPath" -ForegroundColor Green
                
                # Tentar detectar senha do PostgreSQL
                # Prioridade: 1. Variável de ambiente, 2. Arquivo .pgpass, 3. Senhas comuns
                $pgPassword = $null
                
                # 1. Verificar variável de ambiente
                if ($env:POSTGRES_PASSWORD) {
                    $pgPassword = $env:POSTGRES_PASSWORD
                    Write-Host "[Setup] Usando senha da variável POSTGRES_PASSWORD" -ForegroundColor Cyan
                }
                # 2. Verificar arquivo .pgpass (padrão PostgreSQL)
                elseif (Test-Path "$env:APPDATA\postgresql\pgpass.conf") {
                    Write-Host "[Setup] Arquivo .pgpass encontrado" -ForegroundColor Cyan
                    # Não precisa configurar PGPASSWORD, psql vai usar automaticamente
                }
                # 3. Testar senhas comuns
                else {
                    Write-Host "[Setup] Testando senhas comuns do PostgreSQL..." -ForegroundColor Cyan
                    $commonPasswords = @("postgres", "110812", "admin", "password", "")
                    
                    foreach ($testPass in $commonPasswords) {
                        $env:PGPASSWORD = $testPass
                        $testCmd = "& `"$psqlPath`" -U postgres -c `"SELECT 1;`" 2>&1"
                        $result = Invoke-Expression $testCmd
                        
                        if ($result -match "1 row" -or $result -notmatch "password") {
                            $pgPassword = $testPass
                            Write-Host "[OK] Senha detectada automaticamente!" -ForegroundColor Green
                            break
                        }
                    }
                    
                    if (-not $pgPassword) {
                        Write-Host "[AVISO] Não foi possível detectar senha do PostgreSQL." -ForegroundColor Yellow
                        Write-Host "        Configure a variável POSTGRES_PASSWORD ou use SQLite." -ForegroundColor Yellow
                        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
                    }
                }
                
                # Se conseguiu senha, configurar PGPASSWORD
                if ($pgPassword) {
                    $env:PGPASSWORD = $pgPassword
                }
                
                # 5. Verificar se o banco já existe
                $checkDbCmd = "& `"$psqlPath`" -U postgres -lqt"
                $databases = Invoke-Expression $checkDbCmd 2>$null
                
                if ($databases -match $dbName) {
                    Write-Host "[OK] Banco '$dbName' já existe! Usando PostgreSQL." -ForegroundColor Green
                    $usePostgres = $true
                    $dbType = "PostgreSQL (banco existente)"
                }
                else {
                    Write-Host "[!] Banco '$dbName' não existe." -ForegroundColor Yellow
                    Write-Host "[Setup] Criando banco '$dbName'..." -ForegroundColor Cyan
                    
                    # Criar banco
                    $createDbCmd = "& `"$psqlPath`" -U postgres -c `"CREATE DATABASE $dbName;`""
                    try {
                        Invoke-Expression $createDbCmd 2>$null
                        Write-Host "[OK] Banco '$dbName' criado com sucesso!" -ForegroundColor Green
                        $usePostgres = $true
                        $dbType = "PostgreSQL (banco criado)"
                    }
                    catch {
                        Write-Host "[AVISO] Erro ao criar banco. Usando SQLite." -ForegroundColor Yellow
                    }
                }
                
                # Limpar senha da memória
                Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
                
                # Salvar senha para uso no .env (se detectada)
                if ($pgPassword -and $usePostgres) {
                    $script:detectedPassword = $pgPassword
                }
            }
            else {
                Write-Host "[AVISO] psql não encontrado. Assumindo que banco existe. Usando PostgreSQL." -ForegroundColor Yellow
                $usePostgres = $true
                $dbType = "PostgreSQL (sem verificação)"
            }
            
        }
        catch {
            Write-Host "[AVISO] PostgreSQL não está aceitando conexões. Usando SQLite." -ForegroundColor Yellow
        }
    }
}

# Configurar URL do banco
if ($usePostgres) {
    # Usar senha detectada ou fallback para 'postgres'
    $dbPassword = if ($script:detectedPassword) { $script:detectedPassword } else { "postgres" }
    $dbUrl = "postgresql+asyncpg://postgres:$dbPassword@localhost:5432/$dbName"
}

Write-Host "[Setup] Banco de dados selecionado: $dbType" -ForegroundColor Cyan

# Cria .env com configurações inteligentes
$envContent = @"
# ISP Monitor - Auto-Generated Configuration
# Gerado automaticamente em $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Database: $dbType

# ===== Security Configuration =====
ADMIN_EMAIL=diegojlc22@gmail.com
ADMIN_PASSWORD=110812
SECRET_KEY=$(New-Guid)
MSG_SECRET=$(New-Guid)

# CORS allowed origins
CORS_ORIGINS=*

# ===== Database Configuration =====
DATABASE_URL=$dbUrl

# ===== Ping Configuration =====
PING_INTERVAL_SECONDS=30
PING_TIMEOUT_SECONDS=2
PING_CONCURRENT_LIMIT=100

# ===== Log Retention =====
LOG_RETENTION_DAYS=30

# ===== Telegram (Opcional) =====
# TELEGRAM_TOKEN=seu_token_aqui
# TELEGRAM_CHAT_ID=seu_chat_id_aqui

# ===== WhatsApp (Opcional) =====
WHATSAPP_API_URL=http://localhost:3001/send
# WHATSAPP_TARGET_NUMBER=5511999999999
"@

# Salva o arquivo
$envContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

Write-Host "[OK] Arquivo .env criado com sucesso!" -ForegroundColor Green
Write-Host "     Database: $dbUrl" -ForegroundColor Cyan
exit 0
