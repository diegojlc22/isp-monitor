# Configuração do PostgreSQL

## Detecção Automática de Senha

O sistema tenta detectar a senha do PostgreSQL automaticamente na seguinte ordem:

### 1. Variável de Ambiente (Recomendado)
```powershell
# Defina a variável de ambiente antes de executar
$env:POSTGRES_PASSWORD = "sua_senha_aqui"
.\ABRIR_SISTEMA.bat
```

### 2. Arquivo .pgpass (Padrão PostgreSQL)
Crie o arquivo: `%APPDATA%\postgresql\pgpass.conf`
```
localhost:5432:*:postgres:sua_senha_aqui
```

### 3. Senhas Comuns (Auto-Teste)
O sistema testa automaticamente:
- `postgres` (padrão)
- `110812` (senha do projeto)
- `admin`
- `password`
- `` (sem senha)

## Configuração Manual

Se a detecção automática falhar, você pode:

### Opção 1: Editar o .env
```env
DATABASE_URL=postgresql+asyncpg://postgres:SUA_SENHA@localhost:5432/isp_monitor
```

### Opção 2: Usar SQLite (Fallback)
O sistema usa SQLite automaticamente se PostgreSQL não estiver disponível:
```env
DATABASE_URL=sqlite+aiosqlite:///./isp_monitor_v2.db
```

## Múltiplas Máquinas

### Máquina 1 (Desenvolvimento)
```powershell
$env:POSTGRES_PASSWORD = "senha_dev"
.\ABRIR_SISTEMA.bat
```

### Máquina 2 (Produção)
```powershell
$env:POSTGRES_PASSWORD = "senha_prod"
.\ABRIR_SISTEMA.bat
```

O sistema detecta automaticamente e configura o `.env` correto para cada máquina!

## Troubleshooting

### Erro: "connection was closed in the middle of operation"
**Causa:** Senha incorreta no `.env`

**Solução:**
1. Delete o arquivo `.env`
2. Configure `$env:POSTGRES_PASSWORD` com a senha correta
3. Execute `.\ABRIR_SISTEMA.bat` novamente

### Erro: "O computador remoto recusou a conexão de rede"
**Causa:** PostgreSQL não está rodando

**Solução:**
```powershell
# Como Administrador
Start-Service postgresql-x64-17
```

Ou use `.\ABRIR_SISTEMA.bat` que inicia automaticamente.
