# 🚀 APLICAR AUTOVACUUM - GUIA PASSO A PASSO

**IMPORTANTE:** Precisa executar como Administrador

---

## ✅ PASSO 1: Backup JÁ FEITO

✅ Backup criado em:
```
C:\Program Files\PostgreSQL\18\data\postgresql.conf.backup
```

---

## ✅ PASSO 2: Configuração JÁ APLICADA

✅ Arquivo otimizado copiado para:
```
C:\Program Files\PostgreSQL\18\data\postgresql.conf
```

---

## ⚠️ PASSO 3: REINICIAR POSTGRESQL (MANUAL)

**Opção 1: Via PowerShell (como Administrador)**

1. Abrir PowerShell como Administrador
2. Executar:
```powershell
Restart-Service postgresql-x64-18
```

**Opção 2: Via Serviços do Windows**

1. Pressionar `Win + R`
2. Digitar: `services.msc`
3. Procurar: `postgresql-x64-18`
4. Clicar com botão direito → Reiniciar

**Opção 3: Via pg_ctl**

1. Abrir PowerShell como Administrador
2. Executar:
```powershell
cd "C:\Program Files\PostgreSQL\18\bin"
.\pg_ctl restart -D "C:\Program Files\PostgreSQL\18\data"
```

---

## ✅ PASSO 4: VERIFICAR SE APLICOU

Após reiniciar PostgreSQL, executar:

```bash
# No projeto
.venv\Scripts\python.exe scripts/verificar_postgres_config.py
```

**Deve mostrar:**
```
✅ autovacuum_vacuum_scale_factor
   Atual: 0.05
   Recomendado: 0.05

✅ autovacuum_analyze_scale_factor
   Atual: 0.02
   Recomendado: 0.02
```

---

## 🚀 PASSO 5: REINICIAR APLICAÇÃO

Após PostgreSQL reiniciar:

```bash
iniciar_postgres.bat
```

---

## ✅ VALIDAÇÃO

Sistema deve:
- ✅ Iniciar sem erros
- ✅ Logs mostram intervalo dinâmico
- ✅ Logs mostram concorrência adaptativa
- ✅ CPU ~30%
- ✅ Dashboard rápido

---

## 📊 TESTAR MÉTRICAS

```bash
curl http://localhost:8080/api/metrics/system
```

---

**Status:** Aguardando reinício manual do PostgreSQL
