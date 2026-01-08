# ⚙️ MUDANÇAS PARA POSTGRESQL.CONF

**IMPORTANTE:** Faça backup antes de editar!
```powershell
copy "C:\Program Files\PostgreSQL\15\data\postgresql.conf" "C:\Program Files\PostgreSQL\15\data\postgresql.conf.backup"
```

---

## 📝 MUDANÇAS A FAZER

### 1. MEMÓRIA (Linha ~128)

**PROCURE POR:**
```ini
shared_buffers = 128MB			# min 128kB
```

**MUDE PARA:**
```ini
shared_buffers = 2GB			# min 128kB (OTIMIZADO)
```

---

### 2. WORK MEMORY (Linha ~145)

**PROCURE POR:**
```ini
#work_mem = 4MB				# min 64kB
```

**MUDE PARA (remova o #):**
```ini
work_mem = 16MB				# min 64kB (OTIMIZADO)
```

---

### 3. MAINTENANCE MEMORY (Linha ~148)

**PROCURE POR:**
```ini
#maintenance_work_mem = 64MB		# min 64kB
```

**MUDE PARA (remova o #):**
```ini
maintenance_work_mem = 512MB		# min 64kB (OTIMIZADO)
```

---

### 4. EFFECTIVE CACHE SIZE (Linha ~509)

**PROCURE POR:**
```ini
#effective_cache_size = 4GB
```

**MUDE PARA (remova o #):**
```ini
effective_cache_size = 6GB		# (OTIMIZADO para 16GB RAM)
```

---

### 5. WAL BUFFERS (Linha ~259)

**PROCURE POR:**
```ini
#wal_buffers = -1			# min 32kB, -1 sets based on shared_buffers
```

**MUDE PARA (remova o #):**
```ini
wal_buffers = 16MB			# min 32kB (OTIMIZADO)
```

---

### 6. CHECKPOINT TARGET (Linha ~271)

**PROCURE POR:**
```ini
#checkpoint_completion_target = 0.9	# checkpoint target duration, 0.0 - 1.0
```

**MUDE PARA (remova o #):**
```ini
checkpoint_completion_target = 0.9	# checkpoint target duration (OTIMIZADO)
```

---

### 7. MAX WAL SIZE (Linha ~274 - JÁ EXISTE!)

**ESTÁ ASSIM:**
```ini
max_wal_size = 1GB
```

**MUDE PARA:**
```ini
max_wal_size = 4GB			# (OTIMIZADO)
```

---

### 8. MIN WAL SIZE (Linha ~275 - JÁ EXISTE!)

**ESTÁ ASSIM:**
```ini
min_wal_size = 80MB
```

**MUDE PARA:**
```ini
min_wal_size = 1GB			# (OTIMIZADO)
```

---

### 9. RANDOM PAGE COST (Linha ~497 - Para SSD)

**PROCURE POR:**
```ini
#random_page_cost = 4.0			# same scale as above
```

**MUDE PARA (remova o #):**
```ini
random_page_cost = 1.1			# same scale as above (OTIMIZADO para SSD)
```

---

### 10. EFFECTIVE IO CONCURRENCY (Linha ~207 - Para SSD)

**PROCURE POR:**
```ini
#effective_io_concurrency = 16		# 1-1000; 0 disables issuing multiple simultaneous IO requests
```

**MUDE PARA (remova o #):**
```ini
effective_io_concurrency = 200		# 1-1000 (OTIMIZADO para SSD)
```

---

### 11. DEFAULT STATISTICS TARGET (Linha ~530)

**PROCURE POR:**
```ini
#default_statistics_target = 100	# range 1-10000
```

**MUDE PARA (remova o #):**
```ini
default_statistics_target = 100		# range 1-10000 (OTIMIZADO)
```

---

## ✅ RESUMO DAS MUDANÇAS

Total de **11 linhas** para modificar:

1. ✅ `shared_buffers = 2GB` (linha ~128)
2. ✅ `work_mem = 16MB` (linha ~145)
3. ✅ `maintenance_work_mem = 512MB` (linha ~148)
4. ✅ `effective_cache_size = 6GB` (linha ~509)
5. ✅ `wal_buffers = 16MB` (linha ~259)
6. ✅ `checkpoint_completion_target = 0.9` (linha ~271)
7. ✅ `max_wal_size = 4GB` (linha ~274)
8. ✅ `min_wal_size = 1GB` (linha ~275)
9. ✅ `random_page_cost = 1.1` (linha ~497)
10. ✅ `effective_io_concurrency = 200` (linha ~207)
11. ✅ `default_statistics_target = 100` (linha ~530)

---

## 🔄 APÓS EDITAR

### 1. Salve o arquivo (Ctrl+S)

### 2. Reinicie o PostgreSQL

**Opção 1 - Via Interface:**
1. Pressione `Win + R`
2. Digite `services.msc`
3. Procure "postgresql-x64-15"
4. Clique direito → Reiniciar

**Opção 2 - PowerShell (como Admin):**
```powershell
Restart-Service postgresql-x64-15
```

### 3. Verifique se funcionou

**Abra pgAdmin ou psql e execute:**
```sql
SHOW shared_buffers;
SHOW work_mem;
SHOW effective_cache_size;
```

**Deve retornar:**
```
shared_buffers: 2GB ✅
work_mem: 16MB ✅
effective_cache_size: 6GB ✅
```

---

## 🎯 GANHO ESPERADO

- ✅ Queries 20-30% mais rápidas
- ✅ Menos disk I/O
- ✅ Melhor uso de memória
- ✅ Sistema mais estável sob carga

---

## ⚠️ SE DER ERRO

Se o PostgreSQL não iniciar após as mudanças:

1. **Restaure o backup:**
```powershell
copy "C:\Program Files\PostgreSQL\15\data\postgresql.conf.backup" "C:\Program Files\PostgreSQL\15\data\postgresql.conf"
```

2. **Reinicie o serviço**

3. **Revise as mudanças** (provavelmente erro de digitação)

---

**Tempo estimado:** 5-10 minutos  
**Dificuldade:** ⭐⭐ (Fácil)  
**Risco:** Baixo (valores conservadores)
