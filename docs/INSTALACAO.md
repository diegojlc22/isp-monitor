# 🚀 ISP Monitor - Guia de Instalação e Atualização

## 📋 **NOVA ESTRUTURA (Recomendada)**

### **Separação de Código e Dados:**

```
C:\ISP-Monitor\              ← INSTALAÇÃO (Produção)
├── app\                     ← Código do sistema
├── data\                    ← Seus dados (preservados)
│   ├── .env                 ← Configuração local
│   ├── logs\                ← Logs do sistema
│   └── backups\             ← Backups automáticos
└── UPDATE.bat               ← Atualizador

C:\Dev\isp-monitor\          ← REPOSITÓRIO GIT (Desenvolvimento)
└── (código fonte)
```

---

## 🔧 **INSTALAÇÃO INICIAL**

### **Passo 1: Clone o Repositório**
```bash
cd C:\Dev
git clone https://github.com/diegojlc22/isp-monitor.git
cd isp-monitor
```

### **Passo 2: Execute o Instalador**
```bash
# Clique com botão direito em INSTALL.bat
# Escolha "Executar como Administrador"
INSTALL.bat
```

O instalador vai:
- ✅ Criar `C:\ISP-Monitor\`
- ✅ Copiar código para `app\`
- ✅ Criar pasta `data\` para configurações
- ✅ Instalar dependências
- ✅ Criar atalho na área de trabalho

---

## 🔄 **ATUALIZAÇÃO DO SISTEMA**

### **Método 1: Automático (Recomendado)**

```bash
# Em C:\ISP-Monitor\
UPDATE.bat
```

O atualizador vai:
1. ✅ Parar serviços
2. ✅ Criar backup automático
3. ✅ Baixar última versão do GitHub
4. ✅ Preservar `.env`, logs e dados
5. ✅ Atualizar dependências
6. ✅ Rodar migrations do banco
7. ✅ Perguntar se quer iniciar

### **Método 2: Manual (Desenvolvimento)**

```bash
# No repositório Git
cd C:\Dev\isp-monitor
git pull origin main

# Copiar para instalação
xcopy * C:\ISP-Monitor\app\ /E /I /Y /EXCLUDE:install_exclude.txt
```

---

## 🎯 **FLUXO DE TRABALHO RECOMENDADO**

### **Máquina 1 (Desenvolvimento):**
```bash
# Fazer alterações
cd C:\Dev\isp-monitor
# ... editar código ...
git add .
git commit -m "feat: nova funcionalidade"
git push origin main

# Atualizar instalação local
cd C:\ISP-Monitor
UPDATE.bat
```

### **Máquina 2 (Produção):**
```bash
# Receber atualizações
cd C:\ISP-Monitor
UPDATE.bat  # Baixa e aplica automaticamente
```

---

## 🛡️ **SEGURANÇA E ROLLBACK**

### **Backups Automáticos:**
Toda atualização cria backup em:
```
C:\ISP-Monitor\data\backups\backup_YYYYMMDD_HHMMSS\
```

### **Rollback (Voltar Versão):**
```bash
# Copiar backup de volta
xcopy C:\ISP-Monitor\data\backups\backup_20251229_080000\* C:\ISP-Monitor\app\ /E /I /Y
```

---

## 📝 **ARQUIVOS PRESERVADOS**

Estes arquivos **NUNCA** são sobrescritos:
- ✅ `.env` (configuração local)
- ✅ `logs\*` (logs do sistema)
- ✅ `data\*` (dados locais)
- ✅ `backups\*` (backups)

---

## 🔍 **TROUBLESHOOTING**

### **Erro: "Falha ao baixar atualização"**
- Verifique conexão com internet
- Verifique se tem acesso ao GitHub

### **Erro: "Schema do banco desatualizado"**
```bash
# Execute manualmente
cd C:\ISP-Monitor\app
powershell -ExecutionPolicy Bypass -File "scripts\fix_schema.sql"
```

### **Sistema não inicia após atualização**
```bash
# Voltar para backup
xcopy C:\ISP-Monitor\data\backups\[ULTIMO_BACKUP]\* C:\ISP-Monitor\app\ /E /I /Y
```

---

## 📊 **VANTAGENS DESTA ESTRUTURA**

| Antes | Depois |
|-------|--------|
| ❌ Conflitos Git | ✅ Sem conflitos |
| ❌ Perda de configurações | ✅ Configurações preservadas |
| ❌ Atualização manual | ✅ Atualização automática |
| ❌ Sem backups | ✅ Backups automáticos |
| ❌ Dependências quebradas | ✅ Dependências sempre atualizadas |

---

## 🚀 **INÍCIO RÁPIDO**

```bash
# 1. Instalar (primeira vez)
INSTALL.bat

# 2. Usar
# Clique no atalho "ISP Monitor" na área de trabalho

# 3. Atualizar (quando houver nova versão)
cd C:\ISP-Monitor
UPDATE.bat
```

---

**Pronto! Agora você tem um sistema profissional de instalação e atualização!** 🎉
