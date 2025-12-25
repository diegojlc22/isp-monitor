# Arquivos e Pastas que Podem Ser Deletados

## ✅ Seguro para Deletar

### **Pastas:**
- `backup_limpeza/` - Backup antigo de limpeza
- `scripts/deprecated/` - Scripts antigos não mais utilizados
- `logs/` - Logs e databases temporários (serão recriados)
- `mobile/android/` - Pasta gerada pelo prebuild (será recriada se necessário)
- `.venv/` - Ambiente virtual Python (será recriado com `python -m venv .venv`)

### **Arquivos:**
- `organizar_projeto.ps1` - Script de organização (já foi executado)
- `collector.log` - Log antigo
- `startup.log` - Log de inicialização
- `api.log` - Log da API
- `monitor.db` - Database SQLite temporário
- `postgresql.conf.optimized` - Configuração antiga do PostgreSQL
- `tools/ngrok/ngrok.zip` - Arquivo ZIP do ngrok (já descompactado)

---

## ⚠️ NÃO Deletar

### **Pastas Essenciais:**
- `backend/` - Código do backend
- `frontend/` - Código do frontend
- `mobile/` - Código do app mobile
- `docs/` - Documentação
- `scripts/setup/` - Scripts de configuração
- `scripts/database/` - Scripts de manutenção do BD
- `tools/ngrok/ngrok.exe` - Executável do ngrok
- `.git/` - Repositório Git
- `.github/` - Workflows do GitHub
- `.agent/` - Configurações do agente

### **Arquivos Essenciais:**
- `README.md` - Documentação principal
- `.gitignore` - Regras do Git
- `.env.example` - Exemplo de variáveis de ambiente
- `LAUNCHER.bat` - Iniciar sistema
- `iniciar_postgres.bat` - Iniciar PostgreSQL
- `launcher.py` / `launcher.pyw` - Launcher Python

---

## 🗑️ Como Deletar

### **Opção 1: Manual**
Simplesmente delete as pastas e arquivos listados acima.

### **Opção 2: Script Automático**
Execute o script abaixo (CUIDADO: Não tem volta!)

```powershell
# ATENÇÃO: Este script DELETA arquivos permanentemente!
# Revise antes de executar!

cd C:\Users\DiegoLima\.gemini\antigravity\scratch\isp_monitor

# Deletar pastas
Remove-Item -Recurse -Force backup_limpeza -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force scripts\deprecated -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force logs -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force mobile\android -ErrorAction SilentlyContinue

# Deletar arquivos
Remove-Item -Force organizar_projeto.ps1 -ErrorAction SilentlyContinue
Remove-Item -Force *.log -ErrorAction SilentlyContinue
Remove-Item -Force monitor.db -ErrorAction SilentlyContinue
Remove-Item -Force postgresql.conf.optimized -ErrorAction SilentlyContinue
Remove-Item -Force tools\ngrok\ngrok.zip -ErrorAction SilentlyContinue

Write-Host "Limpeza concluída!" -ForegroundColor Green
```

---

## 📊 Espaço Liberado

Deletando os arquivos acima, você vai liberar aproximadamente:

- `backup_limpeza/` - ~5 MB
- `logs/` - ~1 MB
- `mobile/android/` - ~50-100 MB (se existir)
- `ngrok.zip` - ~11 MB
- Outros arquivos - ~1 MB

**Total: ~70-120 MB**

---

## 💡 Recomendação

**Mantenha por enquanto:**
- `scripts/deprecated/` - Pode ser útil para referência
- `logs/` - Útil para debug

**Delete com segurança:**
- `backup_limpeza/` - Não é mais necessário
- `ngrok.zip` - Já está descompactado
- `mobile/android/` - Será recriado se necessário

---

**Última atualização:** 25/12/2024
