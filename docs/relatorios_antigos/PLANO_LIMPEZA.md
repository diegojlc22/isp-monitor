# 🧹 PLANO DE LIMPEZA - ISP MONITOR

**Data:** 25/12/2024  
**Objetivo:** Remover código morto, arquivos obsoletos e funcionalidades não utilizadas

---

## 📋 ARQUIVOS IDENTIFICADOS PARA REMOÇÃO

### 🔴 ARQUIVOS OBSOLETOS (SQLite - não usado mais)

**Raiz do projeto:**
1. ❌ `monitor.db` - Banco SQLite antigo (usando PostgreSQL agora)
2. ❌ `monitor.db-shm` - Shared memory do SQLite
3. ❌ `monitor.db-wal` - Write-ahead log do SQLite
4. ❌ `monitor.db-shm.old` - Backup antigo
5. ❌ `monitor.db-wal.old` - Backup antigo
6. ❌ `monitor.db.old` - Backup antigo
7. ❌ `migrate_db.py.OLD` - Script de migração antigo
8. ❌ `venv/` - Virtual env duplicado (usando .venv)

**Total:** ~800 KB de arquivos obsoletos

---

### 🟡 SCRIPTS DE MIGRAÇÃO (Já executados)

**scripts/**
1. ⚠️ `init_postgres.py` - Inicialização já feita
2. ⚠️ `migrar_sqlite_para_postgres.py` - Migração já feita

**Ação:** Mover para `scripts/archive/` (manter por segurança)

---

### 🟢 ARQUIVOS TEMPORÁRIOS/DUPLICADOS

**Raiz:**
1. ❌ `iniciar_sistema.bat` - Duplicado (usar `iniciar_postgres.bat`)
2. ❌ `launcher.pyw` - GUI não usada
3. ❌ `setup_gui.py` - Setup GUI não usado
4. ❌ `repair.ps1` - Script de reparo antigo

**backend/**
1. ❌ `diagnose_firewall.ps1` - Diagnóstico não necessário

---

### 📁 DIRETÓRIOS OBSOLETOS

1. ❌ `venv/` - Duplicado do `.venv`
2. ⚠️ `backend/tools/` - Verificar se tem ferramentas úteis

---

## ✅ ARQUIVOS A MANTER

### Essenciais:
- ✅ `.venv/` - Virtual environment ativo
- ✅ `backend/` - Código do backend
- ✅ `frontend/` - Código do frontend
- ✅ `docs/` - Documentação
- ✅ `scripts/` - Scripts úteis (verificação, índices)
- ✅ `postgresql.conf.optimized` - Configuração otimizada
- ✅ `iniciar_postgres.bat` - Script principal
- ✅ `reiniciar_tudo.bat` - Script de reinício
- ✅ `deploy.bat` - Deploy do frontend
- ✅ `README.md` - Documentação principal
- ✅ `.env.example` - Exemplo de configuração

### Documentação:
- ✅ `SUCESSO_COMPLETO.md` - Status atual
- ✅ `docs/OTIMIZACOES_FINAIS.md` - Resumo das otimizações
- ✅ `docs/SPRINT*.md` - Documentação dos sprints

---

## 🎯 PLANO DE AÇÃO

### Fase 1: Backup (Segurança)
```bash
# Criar backup antes de deletar
mkdir backup_limpeza
copy monitor.db* backup_limpeza\
copy *.OLD backup_limpeza\
```

### Fase 2: Remover Arquivos SQLite
```bash
del monitor.db
del monitor.db-shm
del monitor.db-wal
del monitor.db-shm.old
del monitor.db-wal.old
del monitor.db.old
del migrate_db.py.OLD
```

### Fase 3: Remover Scripts/GUI Não Usados
```bash
del launcher.pyw
del setup_gui.py
del repair.ps1
del iniciar_sistema.bat
del backend\diagnose_firewall.ps1
```

### Fase 4: Arquivar Scripts de Migração
```bash
mkdir scripts\archive
move scripts\init_postgres.py scripts\archive\
move scripts\migrar_sqlite_para_postgres.py scripts\archive\
```

### Fase 5: Remover venv Duplicado
```bash
rmdir /s /q venv
```

---

## 📊 GANHOS ESPERADOS

### Espaço em Disco:
- SQLite files: ~800 KB
- venv duplicado: ~100 MB
- Scripts obsoletos: ~50 KB
- **Total:** ~100 MB liberados

### Organização:
- ✅ Apenas arquivos necessários
- ✅ Estrutura limpa
- ✅ Fácil manutenção
- ✅ Sem confusão

---

## ⚠️ ARQUIVOS A REVISAR MANUALMENTE

### backend/tools/
Verificar conteúdo antes de decidir:
- Pode ter ferramentas úteis
- Verificar se são usadas no código

---

## ✅ ESTRUTURA FINAL

```
isp_monitor/
├── .venv/              ✅ Virtual environment
├── backend/            ✅ Código backend
│   ├── app/           ✅ Aplicação
│   └── requirements.txt ✅ Dependências
├── frontend/           ✅ Código frontend
├── docs/              ✅ Documentação
├── scripts/           ✅ Scripts úteis
│   ├── criar_indices.py
│   ├── verificar_indices.py
│   ├── verificar_postgres_config.py
│   └── archive/       ✅ Scripts antigos
├── .env.example       ✅ Config exemplo
├── .gitignore         ✅ Git ignore
├── README.md          ✅ Documentação
├── deploy.bat         ✅ Deploy frontend
├── iniciar_postgres.bat ✅ Iniciar sistema
├── reiniciar_tudo.bat ✅ Reiniciar tudo
└── postgresql.conf.optimized ✅ Config PostgreSQL
```

---

## 🚀 EXECUTAR LIMPEZA?

**Opções:**

1. **Automática** - Executar script de limpeza
2. **Manual** - Seguir plano acima
3. **Revisar** - Verificar arquivos antes

**Recomendação:** Fazer backup primeiro, depois executar limpeza automática.

---

**Status:** Aguardando confirmação para executar limpeza
