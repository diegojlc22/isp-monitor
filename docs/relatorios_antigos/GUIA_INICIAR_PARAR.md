# 🛑 GUIA - INICIAR E PARAR O SISTEMA

---

## 🚀 INICIAR O SISTEMA

### Opção 1: Script Principal (Recomendado)
```bash
iniciar_postgres.bat
```

### Opção 2: Reiniciar Tudo (Como Admin)
```bash
# Clicar com botão direito → Executar como Administrador
reiniciar_tudo.bat
```

### Opção 3: Desenvolvimento (Com Reload)
```bash
.venv\Scripts\activate
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## 🛑 PARAR O SISTEMA

### Opção 1: Ctrl+C (Mais Simples)
1. **Clicar no terminal** onde está rodando
2. **Pressionar `Ctrl + C`**
3. **Aguardar** alguns segundos
4. Sistema para gracefully

### Opção 2: Script Automático
```bash
parar_sistema.bat
```

### Opção 3: Manual (Task Manager)
1. **Abrir Task Manager** (`Ctrl + Shift + Esc`)
2. **Procurar por:** `python.exe`
3. **Clicar com botão direito** → Finalizar tarefa

### Opção 4: Linha de Comando
```bash
# Ver processos na porta 8080
netstat -ano | findstr :8080

# Matar processo específico (substituir PID)
taskkill /F /PID 6360
```

---

## 📊 VERIFICAR STATUS

### Sistema está rodando?
```bash
# Ver se porta 8080 está em uso
netstat -ano | findstr :8080

# Testar API
curl http://localhost:8080/api/metrics/system
```

### Ver logs em tempo real
- Olhar o terminal onde executou `iniciar_postgres.bat`

---

## 🔄 REINICIAR O SISTEMA

### Método 1: Parar e Iniciar
```bash
# 1. Parar (Ctrl+C ou parar_sistema.bat)
# 2. Aguardar 5 segundos
# 3. Iniciar novamente
iniciar_postgres.bat
```

### Método 2: Script Automático (Como Admin)
```bash
reiniciar_tudo.bat
```

---

## ⚠️ PROBLEMAS COMUNS

### Erro: "Porta 8080 já em uso"
**Solução:**
```bash
# Opção 1: Executar script
parar_sistema.bat

# Opção 2: Manual
netstat -ano | findstr :8080
taskkill /F /PID [número_do_processo]
```

### Sistema não para com Ctrl+C
**Solução:**
```bash
parar_sistema.bat
```

### PostgreSQL não está rodando
**Solução:**
```bash
# Verificar serviço
Get-Service postgresql*

# Iniciar se necessário
Start-Service postgresql-x64-18
```

---

## 📝 SCRIPTS DISPONÍVEIS

| Script | Função |
|--------|--------|
| `iniciar_postgres.bat` | Iniciar sistema |
| `reiniciar_tudo.bat` | Reiniciar PostgreSQL + Sistema |
| `parar_sistema.bat` | Parar sistema |
| `limpar_projeto.bat` | Limpar arquivos obsoletos |

---

## 🎯 FLUXO NORMAL DE USO

### Desenvolvimento:
```bash
# Manhã
iniciar_postgres.bat

# Trabalhar...

# Noite (parar)
Ctrl + C
```

### Produção (24/7):
```bash
# Iniciar uma vez
iniciar_postgres.bat

# Deixar rodando
# Monitorar via métricas
```

---

## ✅ CHECKLIST

**Antes de parar:**
- [ ] Salvar configurações importantes
- [ ] Verificar se não há operações em andamento
- [ ] Fazer backup se necessário

**Depois de parar:**
- [ ] Verificar se porta 8080 está livre
- [ ] Verificar se processos Python foram finalizados

**Antes de iniciar:**
- [ ] PostgreSQL está rodando
- [ ] Porta 8080 está livre
- [ ] Virtual environment existe (.venv)

---

**Criado:** 25/12/2024  
**Versão:** 2.3
