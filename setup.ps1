<#
.SYNOPSIS
    Instalador Inteligente - ISP Monitor
.DESCRIPTION
    Verifica e instala automaticamente todas as dependencias necessarias.
#>

# Requer privilegios de administrador
#Requires -RunAsAdministrator

# Configuracoes
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Cores para output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Step { Write-Host "`n===> $args" -ForegroundColor Magenta }

# Variaveis globais
$ProjectRoot = $PSScriptRoot
$TempDir = Join-Path $env:TEMP "isp-monitor-setup"
$LogFile = Join-Path $ProjectRoot "setup.log"
$InstallationState = Join-Path $ProjectRoot ".setup-state.json"

# Estado da instalacao
$State = @{
    Python           = $false
    NodeJS           = $false
    PostgreSQL       = $false
    Git              = $false
    PythonPackages   = $false
    FrontendPackages = $false
    MobilePackages   = $false
    Database         = $false
    Ngrok            = $false
}

# Versoes minimas requeridas
$MinVersions = @{
    Python     = [version]"3.11.0"
    NodeJS     = [version]"20.0.0"
    PostgreSQL = [version]"15.0.0"
    Git        = [version]"2.30.0"
}

# Funcao para logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $LogMessage
    
    switch ($Level) {
        "SUCCESS" { Write-Success $Message }
        "WARNING" { Write-Warning $Message }
        "ERROR" { Write-Error $Message }
        default { Write-Info $Message }
    }
}

# Funcao para criar diretorio temporario
function Initialize-TempDirectory {
    Write-Step "Inicializando diretorio temporario..."
    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    Write-Log "Diretorio temporario criado: $TempDir" "SUCCESS"
}

# Funcao para limpar diretorio temporario
function Remove-TempDirectory {
    Write-Step "Limpando arquivos temporarios..."
    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force
        Write-Log "Diretorio temporario removido" "SUCCESS"
    }
}

# Funcao para verificar se esta rodando como administrador
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Funcao para atualizar o PATH da sessao atual
function Update-SessionPath {
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = ($MachinePath + ";" + $UserPath);
}

# Funcao para verificar Python
function Test-Python {
    Write-Step "Verificando Python..."
    try {
        $pythonVersion = python --version 2>&1 | Select-String -Pattern "Python (\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
        if ($pythonVersion) {
            $version = [version]$pythonVersion
            if ($version -ge $MinVersions.Python) {
                Write-Log "Python $pythonVersion encontrado" "SUCCESS"
                return $true
            }
            else {
                Write-Log "Python $pythonVersion encontrado, mas versao minima eh $($MinVersions.Python)" "WARNING"
                return $false
            }
        }
    }
    catch {
        Write-Log "Python nao encontrado" "WARNING"
    }
    return $false
}

# Funcao para instalar Python
function Install-Python {
    Write-Step "Instalando Python 3.12..."
    $pythonUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
    $pythonInstaller = Join-Path $TempDir "python-installer.exe"
    
    Write-Log "Baixando Python..."
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
    
    Write-Log "Instalando Python..."
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait
    
    Update-SessionPath
    
    Write-Log "Python instalado com sucesso!" "SUCCESS"
    $State.Python = $true
}

# Funcao para verificar Node.js
function Test-NodeJS {
    Write-Step "Verificando Node.js..."
    try {
        $nodeVersion = node --version 2>&1 | Select-String -Pattern "v(\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
        if ($nodeVersion) {
            $version = [version]$nodeVersion
            if ($version -ge $MinVersions.NodeJS) {
                Write-Log "Node.js $nodeVersion encontrado" "SUCCESS"
                return $true
            }
            else {
                Write-Log "Node.js $nodeVersion encontrado, mas versao minima eh $($MinVersions.NodeJS)" "WARNING"
                return $false
            }
        }
    }
    catch {
        Write-Log "Node.js nao encontrado" "WARNING"
    }
    return $false
}

# Funcao para instalar Node.js
function Install-NodeJS {
    Write-Step "Instalando Node.js 22 LTS..."
    $nodeUrl = "https://nodejs.org/dist/v22.13.1/node-v22.13.1-x64.msi"
    $nodeInstaller = Join-Path $TempDir "node-installer.msi"
    
    Write-Log "Baixando Node.js..."
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller -UseBasicParsing
    
    Write-Log "Instalando Node.js..."
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", $nodeInstaller, "/quiet", "/norestart" -Wait
    
    Update-SessionPath
    
    Write-Log "Node.js instalado com sucesso!" "SUCCESS"
    $State.NodeJS = $true
}

# Funcao para verificar PostgreSQL
function Test-PostgreSQL {
    Write-Step "Verificando PostgreSQL..."
    
    $psqlPath = $null
    $psqlFound = $false
    
    # Verificar se psql esta no PATH
    $psqlCommand = Get-Command "psql" -ErrorAction SilentlyContinue
    if ($psqlCommand) {
        $psqlPath = $psqlCommand.Source
        $psqlFound = $true
        Write-Log "psql encontrado no PATH: $psqlPath" "INFO"
    }
    else {
        # Se nao estiver no path, procurar em locais comuns
        $possiblePaths = @(
            "C:\Program Files\PostgreSQL\18\bin\psql.exe",
            "C:\Program Files\PostgreSQL\17\bin\psql.exe",
            "C:\Program Files\PostgreSQL\16\bin\psql.exe",
            "C:\Program Files\PostgreSQL\15\bin\psql.exe",
            "C:\Program Files (x86)\PostgreSQL\18\bin\psql.exe",
            "C:\Program Files (x86)\PostgreSQL\17\bin\psql.exe",
            "C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe",
            "C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe"
        )
        foreach ($path in $possiblePaths) {
            if (Test-Path $path) {
                $psqlPath = $path
                $psqlFound = $true
                Write-Log "psql encontrado em: $path" "INFO"
                break
            }
        }
    }

    # Se nao encontrou psql, retornar false
    if (-not $psqlFound) {
        Write-Log "PostgreSQL nao encontrado (psql.exe nao localizado)" "WARNING"
        return $false
    }

    try {
        # Executar psql --version e capturar a saida
        $versionOutput = & $psqlPath --version 2>&1
        
        # Extrair versao no formato X.Y ou X.Y.Z
        if ($versionOutput -match "(\d+)\.(\d+)(?:\.(\d+))?") {
            $major = $matches[1]
            $minor = $matches[2]
            $patch = if ($matches[3]) { $matches[3] } else { "0" }
            
            $pgVersion = "$major.$minor.$patch"
            $version = [version]$pgVersion
            
            Write-Log "PostgreSQL versao detectada: $pgVersion" "INFO"
            
            if ($version -ge $MinVersions.PostgreSQL) {
                Write-Log "PostgreSQL $pgVersion encontrado (versao compativel)" "SUCCESS"
                return $true
            }
            else {
                Write-Log "PostgreSQL $pgVersion encontrado, mas versao minima eh $($MinVersions.PostgreSQL)" "WARNING"
                return $false
            }
        }
        else {
            Write-Log "Nao foi possivel extrair a versao do PostgreSQL da saida: $versionOutput" "WARNING"
            return $false
        }
    }
    catch {
        Write-Log "Erro ao verificar versao do PostgreSQL: $_" "WARNING"
        return $false
    }
}

# Funcao para instalar PostgreSQL
function Install-PostgreSQL {
    Write-Step "Instalando PostgreSQL 17..."
    $pgUrl = "https://get.enterprisedb.com/postgresql/postgresql-17.2-1-windows-x64.exe"
    $pgInstaller = Join-Path $TempDir "postgresql-installer.exe"
    
    Write-Log "Baixando PostgreSQL..."
    Invoke-WebRequest -Uri $pgUrl -OutFile $pgInstaller -UseBasicParsing
    
    Write-Log "Instalando PostgreSQL..."
    Write-Warning "IMPORTANTE: Anote a senha do PostgreSQL que voce definir!"
    
    Start-Process -FilePath $pgInstaller -ArgumentList "--mode", "unattended", "--superpassword", "postgres", "--serverport", "5432" -Wait
    
    Update-SessionPath
    
    Write-Log "PostgreSQL instalado com sucesso!" "SUCCESS"
    Write-Warning "Senha padrao definida: postgres (ALTERE ISSO EM PRODUCAO!)"
    $State.PostgreSQL = $true
}

# Funcao para verificar Git
function Test-Git {
    Write-Step "Verificando Git..."
    try {
        $gitVersion = git --version 2>&1 | Select-String -Pattern "(\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
        if ($gitVersion) {
            $version = [version]$gitVersion
            if ($version -ge $MinVersions.Git) {
                Write-Log "Git $gitVersion encontrado" "SUCCESS"
                return $true
            }
        }
    }
    catch {
        Write-Log "Git nao encontrado" "WARNING"
    }
    return $false
}

# Funcao para instalar Git
function Install-Git {
    Write-Step "Instalando Git..."
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.48.1.windows.1/Git-2.48.1-64-bit.exe"
    $gitInstaller = Join-Path $TempDir "git-installer.exe"
    
    Write-Log "Baixando Git..."
    Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller -UseBasicParsing
    
    Write-Log "Instalando Git..."
    Start-Process -FilePath $gitInstaller -ArgumentList "/VERYSILENT", "/NORESTART" -Wait
    
    Update-SessionPath
    
    Write-Log "Git instalado com sucesso!" "SUCCESS"
    $State.Git = $true
}

# Funcao para instalar pacotes Python
function Install-PythonPackages {
    Write-Step "Instalando pacotes Python..."
    
    $requirementsFile = Join-Path $ProjectRoot "backend\requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        Write-Log "Arquivo requirements.txt nao encontrado!" "ERROR"
        return
    }
    
    Write-Log "Atualizando pip..."
    python -m pip install --upgrade pip --quiet
    
    Write-Log "Instalando dependencias do backend..."
    python -m pip install -r $requirementsFile --quiet
    
    Write-Log "Pacotes Python instalados com sucesso!" "SUCCESS"
    $State.PythonPackages = $true
}

# Funcao para instalar pacotes do Frontend
function Install-FrontendPackages {
    Write-Step "Instalando pacotes do Frontend..."
    
    $frontendDir = Join-Path $ProjectRoot "frontend"
    if (-not (Test-Path $frontendDir)) {
        Write-Log "Diretorio frontend nao encontrado!" "ERROR"
        return
    }
    
    Push-Location $frontendDir
    Write-Log "Instalando dependencias do frontend..."
    npm install --silent
    Pop-Location
    
    Write-Log "Pacotes do Frontend instalados com sucesso!" "SUCCESS"
    $State.FrontendPackages = $true
}

# Funcao para instalar pacotes do Mobile
function Install-MobilePackages {
    Write-Step "Instalando pacotes do Mobile..."
    
    $mobileDir = Join-Path $ProjectRoot "mobile"
    if (-not (Test-Path $mobileDir)) {
        Write-Log "Diretorio mobile nao encontrado!" "WARNING"
        return
    }
    
    Push-Location $mobileDir
    Write-Log "Instalando dependencias do mobile..."
    npm install --silent
    Pop-Location
    
    Write-Log "Pacotes do Mobile instalados com sucesso!" "SUCCESS"
    $State.MobilePackages = $true
}

# Funcao para instalar pacotes do WhatsApp
function Install-WhatsappPackages {
    Write-Step "Instalando pacotes do WhatsApp..."
    
    $whatsappDir = Join-Path $ProjectRoot "tools\whatsapp"
    if (-not (Test-Path $whatsappDir)) {
        Write-Log "Diretorio whatsapp nao encontrado!" "WARNING"
        return
    }
    
    Push-Location $whatsappDir
    Write-Log "Instalando dependencias do whatsapp..."
    npm install --silent
    Pop-Location
    
    Write-Log "Pacotes do WhatsApp instalados com sucesso!" "SUCCESS"
}

# Funcao para configurar Ngrok
function Install-Ngrok {
    Write-Step "Configurando Ngrok..."
    
    $ngrokDir = Join-Path $ProjectRoot "tools\ngrok"
    $ngrokExe = Join-Path $ngrokDir "ngrok.exe"
    
    if (Test-Path $ngrokExe) {
        Write-Log "Ngrok ja esta instalado" "SUCCESS"
        $State.Ngrok = $true
        return
    }
    
    Write-Log "Baixando Ngrok..."
    $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $ngrokZip = Join-Path $TempDir "ngrok.zip"
    
    Invoke-WebRequest -Uri $ngrokUrl -OutFile $ngrokZip -UseBasicParsing
    
    Write-Log "Extraindo Ngrok..."
    New-Item -ItemType Directory -Path $ngrokDir -Force | Out-Null
    Expand-Archive -Path $ngrokZip -DestinationPath $ngrokDir -Force
    
    Write-Log "Ngrok instalado com sucesso!" "SUCCESS"
    $State.Ngrok = $true
}

# Funcao para configurar banco de dados
function Initialize-Database {
    Write-Step "Configurando banco de dados..."
    
    $envFile = Join-Path $ProjectRoot "backend\.env"

    if (-not (Test-Path $envFile)) {
        Write-Log "Criando arquivo .env..."
        
        $guid = New-Guid
        $lines = @(
            "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/isp_monitor",
            "SECRET_KEY=$guid",
            "TELEGRAM_BOT_TOKEN=",
            "TELEGRAM_CHAT_ID="
        )
        $envContent = $lines -join [Environment]::NewLine
        
        Set-Content -Path $envFile -Value $envContent
        Write-Log "Arquivo .env criado" "SUCCESS"
    }
    
    Write-Log "Criando banco de dados isp_monitor..."
    
    # Localizar psql
    $psqlPath = "psql"
    if (-not (Get-Command "psql" -ErrorAction SilentlyContinue)) {
        $possiblePaths = @(
            "C:\Program Files\PostgreSQL\18\bin\psql.exe",
            "C:\Program Files\PostgreSQL\17\bin\psql.exe",
            "C:\Program Files\PostgreSQL\16\bin\psql.exe",
            "C:\Program Files\PostgreSQL\15\bin\psql.exe"
        )
        foreach ($path in $possiblePaths) {
            if (Test-Path $path) {
                $psqlPath = $path
                Write-Log "psql encontrado em: $path" "INFO"
                break
            }
        }
    }

    $password = "postgres"
    $dbConfigured = $false
    $attempts = 0

    while (-not $dbConfigured -and $attempts -lt 3) {
        $attempts++
        $env:PGPASSWORD = $password
        $createDbCommand = "CREATE DATABASE isp_monitor;"
        $output = ""
        
        try {
            if (Test-Path $psqlPath) {
                $output = & $psqlPath -U postgres -c $createDbCommand 2>&1
            }
            else {
                $output = psql -U postgres -c $createDbCommand 2>&1
            }
            
            # Converter output para string para verificacao
            $outputStr = $output | Out-String
            
            # Verificar se houve erro de senha
            if ($outputStr -match "password authentication failed" -or $outputStr -match "autenticacao do tipo senha falhou") {
                Write-Warning "Senha '$password' incorreta para o usuario 'postgres'."
                if ($attempts -lt 3) {
                    $password = Read-Host "Por favor, digite a senha correta para o usuario 'postgres'"
                }
                else {
                    Write-Error "Falha na autenticacao apos 3 tentativas. O banco nao foi criado."
                }
            }
            else {
                # Se nao foi erro de senha, consideramos sucesso (mesmo que ja exista)
                if ($outputStr -match "already exists" -or $outputStr -match "ja existe") {
                    Write-Log "Banco de dados ja existe." "INFO"
                }
                else {
                    Write-Log "Banco de dados configurado com sucesso!" "SUCCESS"
                }
                
                $dbConfigured = $true
                
                # Atualizar .env se a senha for diferente do padrao
                if ($password -ne "postgres") {
                    $envContent = Get-Content $envFile
                    $envContent = $envContent -replace "postgres:postgres@", "postgres:${password}@"
                    Set-Content -Path $envFile -Value $envContent
                    Write-Log "Arquivo .env atualizado com a nova senha." "SUCCESS"
                }
            }
        }
        catch {
            $err = "$_"
            # Detectar erro de senha (considerando caracteres estranhos de encoding)
            if ($err -match "jiol" -or $err -match "password authentication failed" -or ($err -match "FATAL" -and $err -match "senha")) {
                Write-Warning "Senha '$password' incorreta."
                if ($attempts -lt 3) {
                    $password = Read-Host "Por favor, digite a senha correta para o usuario 'postgres'"
                    continue
                }
                else {
                    Write-Error "Falha na autenticacao apos 3 tentativas."
                }
            }
            
            Write-Log "Banco de dados ja existe ou erro ao criar: $_" "WARNING"
            
            # Se o erro for "ja existe", significa que a senha estava correta!
            if ("$_" -match "exists" -or "$_" -match "existe") {
                # Atualizar .env se a senha for diferente do padrao
                if ($password -ne "postgres") {
                    $envContent = Get-Content $envFile
                    $envContent = $envContent -replace "postgres:postgres@", "postgres:${password}@"
                    Set-Content -Path $envFile -Value $envContent
                    Write-Log "Arquivo .env atualizado com a senha correta." "SUCCESS"
                }
            }
            
            $dbConfigured = $true # Nao bloquear instalacao por erro desconhecido
        }
    }
    
    $State.Database = $true
}

# Funcao para salvar estado da instalacao
function Save-InstallationState {
    $State | ConvertTo-Json | Set-Content -Path $InstallationState
    Write-Log "Estado da instalacao salvo" "SUCCESS"
}

# Funcao para carregar estado da instalacao
function Get-InstallationState {
    if (Test-Path $InstallationState) {
        $savedState = Get-Content -Path $InstallationState | ConvertFrom-Json
        Write-Log "Estado anterior da instalacao carregado" "INFO"
        return $savedState
    }
    return $null
}

# Funcao principal
function Main {
    Clear-Host
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "         INSTALADOR INTELIGENTE - ISP MONITOR v1.0         " -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "Este instalador verificara e instalara dependencias." -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan

    if (-not (Test-Administrator)) {
        Write-Error "Este script precisa ser executado como Administrador!"
        pause
        exit 1
    }

    Write-Log "Iniciando instalacao..." "INFO"
    
    Initialize-TempDirectory
    
    $savedState = Get-InstallationState
    if ($savedState) {
        $State = $savedState
        Write-Log "Estado anterior carregado." "INFO"
    }
    
    try {
        if (-not (Test-Python)) { Install-Python } else { $State.Python = $true }
        if (-not (Test-NodeJS)) { Install-NodeJS } else { $State.NodeJS = $true }
        if (-not (Test-PostgreSQL)) { Install-PostgreSQL } else { $State.PostgreSQL = $true }
        if (-not (Test-Git)) { Install-Git } else { $State.Git = $true }
        
        Install-PythonPackages
        Install-FrontendPackages
        Install-MobilePackages
        Install-WhatsappPackages  # Adicionado
        Install-Ngrok
        Initialize-Database
        Save-InstallationState
        
        Write-Host "`n==========================================================" -ForegroundColor Green
        Write-Host "              INSTALACAO CONCLUIDA COM SUCESSO!            " -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
        
        Write-Info "Proximos passos:"
        Write-Host "  1. Execute: .\LAUNCHER.bat"
        Write-Host "  2. Configure o Token no backend\.env"
        Write-Host "  3. Acesse: http://localhost:5173"
        Write-Log "Instalacao concluida!" "SUCCESS"
    }
    catch {
        Write-Log "Erro: $_" "ERROR"
        Write-Error "Ocorreu um erro. Verifique setup.log."
    }
    finally {
        Remove-TempDirectory
    }
    
    Write-Host "`nPressione qualquer tecla para sair..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Main
