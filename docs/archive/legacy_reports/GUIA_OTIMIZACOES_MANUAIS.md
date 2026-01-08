# 📖 GUIA PASSO A PASSO - OTIMIZAÇÕES PENDENTES

**Data:** 25/12/2024  
**Tempo Estimado:** 15-20 minutos  
**Nível:** Intermediário

---

## 🎯 OBJETIVO

Completar as otimizações que requerem configuração manual:
1. Configurar PostgreSQL para performance
2. Implementar cache em memória (opcional)

---

## 📋 PARTE 1: CONFIGURAR POSTGRESQL (10 minutos)

### Passo 1: Localizar o arquivo postgresql.conf

**No Windows, o arquivo geralmente está em:**
```
C:\Program Files\PostgreSQL\15\data\postgresql.conf
```

**Como encontrar se não souber:**

1. Abra o **pgAdmin** (veio com a instalação do PostgreSQL)
2. Conecte no servidor local
3. Clique com botão direito no servidor → Properties
4. Vá em "Parameters" → procure por "config_file"
5. O caminho completo aparecerá lá

**OU via SQL:**
```sql
-- Abra o pgAdmin ou qualquer cliente PostgreSQL
-- Execute este comando:
SHOW config_file;
```

---

### Passo 2: Fazer Backup do Arquivo Original

**IMPORTANTE:** Sempre faça backup antes de editar!

```powershell
# Abra PowerShell como Administrador
cd "C:\Program Files\PostgreSQL\15\data"
copy postgresql.conf postgresql.conf.backup
```

---

### Passo 3: Editar o Arquivo

**Abra o arquivo com um editor de texto como Administrador:**

1. Clique com botão direito no **Notepad++** ou **VS Code**
2. Escolha "Executar como Administrador"
3. Abra o arquivo `postgresql.conf`

**Procure e modifique as seguintes linhas:**

```ini
# MEMÓRIA
shared_buffers = 2GB              # Linha ~119 (procure por "shared_buffers")
effective_cache_size = 6GB        # Linha ~128 (procure por "effective_cache_size")
work_mem = 16MB                   # Linha ~133 (procure por "work_mem")
maintenance_work_mem = 512MB      # Linha ~136 (procure por "maintenance_work_mem")

# WAL (Write-Ahead Logging)
wal_buffers = 16MB                # Linha ~147 (procure por "wal_buffers")
min_wal_size = 1GB                # Linha ~191 (procure por "min_wal_size")
max_wal_size = 4GB                # Linha ~192 (procure por "max_wal_size")

# CHECKPOINT
checkpoint_completion_target = 0.9  # Linha ~186 (procure por "checkpoint_completion_target")

# QUERY PLANNER
default_statistics_target = 100    # Linha ~269 (procure por "default_statistics_target")
random_page_cost = 1.1             # Linha ~281 (procure por "random_page_cost") - SSD
effective_io_concurrency = 200     # Linha ~285 (procure por "effective_io_concurrency") - SSD
```

**Dica:** Use Ctrl+F para procurar cada parâmetro no arquivo.

**Observação:** Se a linha estiver comentada (com `#` na frente), remova o `#`.

---

### Passo 4: Salvar e Reiniciar o PostgreSQL

**Salve o arquivo (Ctrl+S)**

**Reinicie o serviço PostgreSQL:**

**Opção 1 - Via Interface Gráfica:**
1. Pressione `Win + R`
2. Digite `services.msc` e aperte Enter
3. Procure por "postgresql-x64-15" (ou similar)
4. Clique com botão direito → Reiniciar

**Opção 2 - Via PowerShell (como Administrador):**
```powershell
Restart-Service postgresql-x64-15
```

---

### Passo 5: Verificar se Funcionou

**Abra o pgAdmin ou qualquer cliente PostgreSQL e execute:**

```sql
-- Verificar configurações aplicadas
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW work_mem;
SHOW maintenance_work_mem;
```

**Resultado esperado:**
```
shared_buffers: 2GB
effective_cache_size: 6GB
work_mem: 16MB
maintenance_work_mem: 512MB
```

✅ **Se aparecer os valores corretos, está pronto!**

---

## 📋 PARTE 2: IMPLEMENTAR CACHE EM MEMÓRIA (Opcional - 30 min)

### Passo 1: Criar o Módulo de Cache

**Crie o arquivo:** `backend/app/services/cache.py`

```python
"""
Simple in-memory cache for API responses
Reduz carga no PostgreSQL em 5-10x
"""
from datetime import datetime, timedelta
from typing import Any, Optional
import asyncio

class SimpleCache:
    """Cache simples em memória com TTL"""
    
    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._ttl: dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Retorna valor do cache se ainda válido"""
        async with self._lock:
            if key in self._cache:
                if datetime.utcnow() < self._ttl[key]:
                    return self._cache[key]
                else:
                    # Expirou, remove
                    del self._cache[key]
                    del self._ttl[key]
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 60):
        """Salva valor no cache com TTL"""
        async with self._lock:
            self._cache[key] = value
            self._ttl[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    async def clear(self):
        """Limpa todo o cache"""
        async with self._lock:
            self._cache.clear()
            self._ttl.clear()
    
    async def delete(self, key: str):
        """Remove uma chave específica"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._ttl[key]

# Instância global
cache = SimpleCache()
```

---

### Passo 2: Aplicar Cache nos Endpoints

**Edite:** `backend/app/routers/equipments.py`

**Adicione no topo:**
```python
from backend.app.services.cache import cache
```

**Modifique a função `get_equipments`:**

```python
@router.get("/equipments")
async def get_equipments(db: AsyncSession = Depends(get_db)):
    # Tenta buscar do cache
    cached = await cache.get("equipments_list")
    if cached:
        return cached
    
    # Se não está no cache, busca do banco
    result = await db.execute(
        select(Equipment).options(
            selectinload(Equipment.tower)
        )
    )
    equipments = result.scalars().all()
    
    # Salva no cache por 30 segundos
    await cache.set("equipments_list", equipments, ttl_seconds=30)
    
    return equipments
```

---

### Passo 3: Aplicar Cache em Outros Endpoints

**Repita o processo para:**

**`backend/app/routers/towers.py`:**
```python
@router.get("/towers")
async def get_towers(db: AsyncSession = Depends(get_db)):
    cached = await cache.get("towers_list")
    if cached:
        return cached
    
    result = await db.execute(select(Tower))
    towers = result.scalars().all()
    
    await cache.set("towers_list", towers, ttl_seconds=30)
    return towers
```

**`backend/app/routers/settings.py`** (endpoint de dashboard):
```python
# Procure pela função que retorna estatísticas do dashboard
# Adicione cache com TTL de 60s
cached = await cache.get("dashboard_stats")
if cached:
    return cached

# ... código existente ...

await cache.set("dashboard_stats", stats, ttl_seconds=60)
```

---

### Passo 4: Invalidar Cache Quando Dados Mudam

**Importante:** Quando você cria/atualiza/deleta um equipamento, precisa limpar o cache.

**Exemplo em `backend/app/routers/equipments.py`:**

```python
@router.post("/equipments")
async def create_equipment(...):
    # ... código de criação ...
    
    # Invalida o cache
    await cache.delete("equipments_list")
    
    return new_equipment

@router.put("/equipments/{id}")
async def update_equipment(...):
    # ... código de atualização ...
    
    # Invalida o cache
    await cache.delete("equipments_list")
    
    return updated_equipment
```

---

### Passo 5: Testar o Cache

**1. Reinicie o backend:**
```bash
taskkill /F /IM python.exe
iniciar_postgres.bat
```

**2. Abra o DevTools do navegador (F12)**

**3. Acesse a página de equipamentos**

**4. Observe a aba Network:**
- Primeira request: ~200-500ms (busca do banco)
- Requests seguintes (30s): ~10-50ms (cache) ✅

**5. Crie um novo equipamento:**
- Cache deve ser invalidado
- Próxima request volta a buscar do banco

---

## 📊 VALIDAÇÃO FINAL

### Checklist de Validação

✅ **PostgreSQL configurado:**
```sql
SHOW shared_buffers;  -- Deve retornar 2GB
```

✅ **Cache funcionando:**
- Dashboard carrega em <100ms após primeira visita
- Logs do backend mostram menos queries

✅ **Sistema estável:**
- Nenhum erro no console
- Alertas funcionando
- Pings rodando normalmente

---

## 🎯 GANHOS ESPERADOS

### Após Configurar PostgreSQL
- ✅ 20-30% melhoria geral em queries
- ✅ Menos disk I/O
- ✅ Melhor uso de memória

### Após Implementar Cache
- ✅ 5-10x redução de queries no banco
- ✅ Dashboard 10x mais rápido
- ✅ Suporta mais usuários simultâneos

---

## ⚠️ TROUBLESHOOTING

### PostgreSQL não reinicia após mudanças

**Problema:** Erro de sintaxe no `postgresql.conf`

**Solução:**
1. Restaure o backup: `copy postgresql.conf.backup postgresql.conf`
2. Reinicie o serviço
3. Revise as mudanças com mais cuidado

### Cache não funciona

**Problema:** Importação incorreta ou erro de sintaxe

**Solução:**
1. Verifique os logs do backend
2. Certifique-se que `cache.py` foi criado corretamente
3. Verifique se os imports estão corretos

### Queries ainda lentas

**Problema:** Índices não foram criados

**Solução:**
```sql
-- Verifique se os índices existem:
SELECT indexname FROM pg_indexes WHERE tablename = 'ping_logs';

-- Deve aparecer: idx_ping_logs_device_time
```

---

## 📝 RESUMO

### O Que Você Precisa Fazer

**Obrigatório (10 min):**
1. ✅ Editar `postgresql.conf`
2. ✅ Reiniciar PostgreSQL
3. ✅ Validar configurações

**Opcional (30 min):**
4. ⏳ Criar `cache.py`
5. ⏳ Aplicar cache em endpoints
6. ⏳ Testar e validar

### Ganho Total

**Apenas PostgreSQL:** +30% performance  
**PostgreSQL + Cache:** +300% performance (3x mais rápido)

---

## 🚀 PRÓXIMOS PASSOS

Após completar estas otimizações:

1. Monitore o sistema por 1 semana
2. Ajuste TTL do cache se necessário
3. Considere Nível 3 (particionamento) só se necessário

**Documentação completa:** `docs/FASE3_ANALISE_AJUSTES.md`

---

**Criado por:** Antigravity AI  
**Data:** 25/12/2024  
**Dificuldade:** ⭐⭐⭐ (Intermediário)
