# 🚀 Instalador Inteligente - ISP Monitor

## 📋 Descrição

Este é um instalador inteligente que verifica e instala automaticamente todas as dependências necessárias para executar o projeto ISP Monitor.

## ✨ Características

- ✅ **Verificação Inteligente**: Detecta o que já está instalado e pula essas etapas
- 📦 **Download Automático**: Baixa apenas o que é necessário
- 🧹 **Limpeza Automática**: Remove arquivos temporários após a instalação
- 📝 **Logging Completo**: Registra todas as ações em `setup.log`
- 🎯 **Execução Única**: Execute apenas uma vez, na primeira configuração

## 🛠️ O que o instalador faz?

### Dependências Principais
1. **Python 3.12** - Backend da aplicação
2. **Node.js 22 LTS** - Frontend e Mobile
3. **PostgreSQL 17** - Banco de dados
4. **Git** - Controle de versão

### Configurações do Projeto
5. **Pacotes Python** - Instala todas as dependências do `requirements.txt`
6. **Pacotes Frontend** - Instala dependências do React/Vite
7. **Pacotes Mobile** - Instala dependências do Expo
8. **Banco de Dados** - Cria o banco `isp_monitor` e arquivo `.env`
9. **Ngrok** - Ferramenta para túneis HTTP (mobile)

## 📖 Como Usar

### Método 1: Arquivo Batch (Recomendado)

1. **Clique com o botão direito** em `SETUP.bat`
2. Selecione **"Executar como Administrador"**
3. Aguarde a conclusão da instalação
4. Pronto! 🎉

### Método 2: PowerShell Direto

```powershell
# Abra o PowerShell como Administrador
Set-ExecutionPolicy Bypass -Scope Process -Force
.\setup.ps1
```

## ⚠️ Requisitos

- **Windows 10/11** (64-bit)
- **Privilégios de Administrador**
- **Conexão com a Internet** (para downloads)
- **~5 GB de espaço livre** em disco

## 📊 Tempo Estimado

- **Primeira Instalação**: 15-30 minutos (dependendo da internet)
- **Instalações Subsequentes**: 2-5 minutos (apenas pacotes)

## 🔍 Verificação de Instalação

Após a instalação, você pode verificar se tudo está correto:

```powershell
# Verificar Python
python --version  # Deve mostrar Python 3.12.x

# Verificar Node.js
node --version    # Deve mostrar v22.x.x

# Verificar PostgreSQL
psql --version    # Deve mostrar PostgreSQL 17.x

# Verificar Git
git --version     # Deve mostrar git version 2.x.x
```

## 📁 Estrutura de Arquivos

```
isp-monitor/
├── SETUP.bat              # Executável principal (use este!)
├── setup.ps1              # Script PowerShell do instalador
├── setup.log              # Log de instalação (criado automaticamente)
├── .setup-state.json      # Estado da instalação (criado automaticamente)
└── backend/
    └── .env               # Configurações (criado automaticamente)
```

## 🐛 Solução de Problemas

### Erro: "Não é possível executar scripts"

**Solução**: Execute o PowerShell como Administrador e rode:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Erro: "PostgreSQL já existe"

**Solução**: Isso é normal! O instalador detecta que já está instalado e pula esta etapa.

### Erro: "Falha ao baixar arquivo"

**Solução**: 
1. Verifique sua conexão com a internet
2. Desative temporariamente o antivírus/firewall
3. Tente novamente

### Erro: "Banco de dados não foi criado"

**Solução**:
1. Verifique se o PostgreSQL está rodando:
   ```powershell
   Get-Service postgresql*
   ```
2. Se não estiver, inicie o serviço:
   ```powershell
   Start-Service postgresql-x64-17
   ```

## 🔐 Configurações Padrão

Após a instalação, você precisará configurar:

### 1. Banco de Dados
- **Usuário**: `postgres`
- **Senha**: `postgres` (⚠️ **ALTERE EM PRODUÇÃO!**)
- **Porta**: `5432`
- **Database**: `isp_monitor`

### 2. Telegram (Opcional)
Edite o arquivo `backend\.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

## 🚀 Próximos Passos

Após a instalação bem-sucedida:

1. **Inicie o sistema**:
   ```bash
   .\LAUNCHER.bat
   ```

2. **Acesse a aplicação**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Documentação API: http://localhost:8000/docs

3. **Login padrão**:
   - Usuário: `admin`
   - Senha: `admin` (altere após primeiro login!)

## 📝 Logs e Diagnóstico

- **setup.log**: Log completo da instalação
- **startup.log**: Log de inicialização do sistema
- **api.log**: Log da API backend

## 🔄 Reinstalação

Se precisar reinstalar tudo do zero:

1. Delete o arquivo `.setup-state.json`
2. Execute `SETUP.bat` novamente como Administrador

## 💡 Dicas

- ✅ Execute o instalador apenas **uma vez**
- ✅ Mantenha o arquivo `.setup-state.json` para evitar reinstalações
- ✅ Verifique o `setup.log` em caso de erros
- ✅ Use o `LAUNCHER.bat` para iniciar o sistema após a instalação

## 🆘 Suporte

Se encontrar problemas:

1. Verifique o arquivo `setup.log`
2. Certifique-se de estar executando como Administrador
3. Verifique sua conexão com a internet
4. Desative temporariamente antivírus/firewall

## 📜 Licença

Este instalador faz parte do projeto ISP Monitor.

---

**Desenvolvido com ❤️ pela equipe ISP Monitor**
