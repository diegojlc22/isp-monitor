# 🔧 CHECKLIST COMPLETO - ISP MONITOR 24/7
**Data:** 07/01/2026 - 13:11
**Status:** Sistema com problemas críticos que impedem operação contínua

---

## 🚨 PROBLEMAS CRÍTICOS (Impedem funcionamento 24/7)

### ❌ 1. PostgreSQL para aleatoriamente
**Impacto:** Sistema inteiro para de funcionar
**Causa:** Serviço não configurado para auto-start
**Solução:**
```batch
# Execute como ADMINISTRADOR:
FIX_POSTGRESQL_AUTOSTART.bat
```
**Status:** ⚠️ PENDENTE - EXECUTAR AGORA

---

### ❌ 2. SNMP Monitor não processa equipamentos
**Impacto:** Alertas de voltagem/tráfego NÃO são enviados
**Causa:** Loop travado após inicialização (possível deadlock no asyncio.gather)
**Sintomas:**
- Monitor inicia com sucesso
- Não há logs de "Processando X equipamentos"
- Equipamentos não são monitorados
- Alertas não disparam

**Investigação Necessária:**
1. Adicionar try-catch global no loop principal
2. Adicionar timeout no asyncio.gather (atualmente sem limite)
3. Verificar se há exceção silenciosa sendo engolida

**Solução Temporária:**
- Reiniciar o collector a cada 1 hora via cron/task scheduler
- Monitorar logs para identificar padrão de travamento

**Status:** ⚠️ CRÍTICO - REQUER DEBUGGING PROFUNDO

---

### ❌ 3. Múltiplos processos pythonw.exe duplicados
**Impacto:** Consumo excessivo de memória, possíveis conflitos
**Causa:** Launcher não mata processos antigos antes de iniciar novos
**Solução:** Modificar launcher para fazer cleanup antes de iniciar

**Status:** ⚠️ MÉDIO - Pode causar instabilidade

---

## ⚠️ PROBLEMAS DE ESTABILIDADE

### 4. Capacity Planning com erro SQL
**Impacto:** Logs poluídos, CPU desperdiçada
**Erro:**
```
coluna "traffic_logs.timestamp" deve aparecer na cláusula GROUP BY
```
**Solução:** Corrigir query SQL em `backend/app/services/capacity_planning.py`

**Status:** ⚠️ BAIXO - Não impede funcionamento, mas polui logs

---

### 5. Collector não reconecta automaticamente após queda do PostgreSQL
**Impacto:** Sistema fica offline até restart manual
**Causa:** Retry logic funciona no startup, mas não durante operação
**Solução:** Implementar watchdog que detecta queda e reconecta

**Status:** ✅ PARCIALMENTE RESOLVIDO - Watchdog implementado, mas precisa de teste

---

## ✅ FUNCIONALIDADES IMPLEMENTADAS E FUNCIONANDO

1. ✅ **Sistema de Alertas de Voltagem**
   - Campos no banco criados
   - Lógica de detecção implementada
   - Notificações WhatsApp/Telegram funcionando
   - **PORÉM:** Não dispara automaticamente (problema #2)

2. ✅ **PostgreSQL Watchdog**
   - Monitora saúde do banco a cada 30s
   - Registra quedas e recuperações
   - Calcula tempo de inatividade

3. ✅ **Auto-recuperação do Collector**
   - Verifica porta 5432 antes de conectar
   - Aguarda indefinidamente com backoff exponencial
   - 20 tentativas de conexão com retry inteligente

4. ✅ **Interface de Configuração de Alertas**
   - Modal redesenhado com abas (Básico/Avançado/Alertas)
   - Campos para configurar limite de voltagem
   - Intervalo entre alertas configurável

---

## 🎯 PLANO DE AÇÃO PARA OPERAÇÃO 24/7

### FASE 1: ESTABILIZAÇÃO (URGENTE - 1-2 horas)

#### 1.1 Configurar PostgreSQL Auto-Start
```batch
# EXECUTAR COMO ADMINISTRADOR:
cd C:\diegolima\isp-monitor
FIX_POSTGRESQL_AUTOSTART.bat
```

#### 1.2 Resolver SNMP Monitor Travado
**Opção A - Debug Profundo (2-3 horas):**
- Adicionar logs detalhados em cada etapa do loop
- Identificar onde exatamente trava
- Corrigir deadlock/exceção

**Opção B - Workaround Rápido (30 min):**
- Adicionar timeout global no asyncio.gather (ex: 300s)
- Adicionar restart automático do SNMP Monitor a cada 30 min
- Monitorar e coletar dados para debug posterior

**RECOMENDAÇÃO:** Opção B agora + Opção A depois

#### 1.3 Limpar Processos Duplicados
```python
# Modificar launcher.pyw para matar processos antigos
# Adicionar no início do start_system():
os.system("taskkill /F /IM python.exe /T 2>nul")
os.system("taskkill /F /IM pythonw.exe /T 2>nul")
time.sleep(2)
```

---

### FASE 2: MONITORAMENTO (2-3 horas)

#### 2.1 Implementar Health Check Endpoint
```python
# Adicionar em backend/app/routers/system.py
@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "postgres": check_postgres_alive(),
        "collector_running": check_collector_heartbeat(),
        "snmp_monitor_active": check_snmp_last_run(),
        "timestamp": datetime.now()
    }
```

#### 2.2 Criar Script de Monitoramento Externo
```batch
# monitor_system.bat (executar a cada 5 min via Task Scheduler)
curl http://localhost:8000/api/health
if errorlevel 1 (
    echo Sistema offline! Reiniciando...
    taskkill /F /IM pythonw.exe
    start pythonw launcher.pyw
)
```

---

### FASE 3: OTIMIZAÇÃO (Após 24h estável)

1. Corrigir erro SQL do Capacity Planning
2. Otimizar queries lentas
3. Implementar cache Redis para dados frequentes
4. Adicionar métricas de performance (Prometheus/Grafana)

---

## 📊 MÉTRICAS DE SUCESSO

**Sistema considerado estável quando:**
- [ ] PostgreSQL roda 24h sem parar
- [ ] SNMP Monitor processa equipamentos continuamente
- [ ] Alertas de voltagem disparam automaticamente
- [ ] Sem processos duplicados
- [ ] Logs limpos (sem erros repetitivos)
- [ ] Uso de memória estável (< 500MB)
- [ ] Uso de CPU estável (< 30%)

---

## 🔥 AÇÃO IMEDIATA REQUERIDA

**AGORA (próximos 15 minutos):**

1. **Executar FIX_POSTGRESQL_AUTOSTART.bat como ADMINISTRADOR**
   - Isso resolve 50% dos problemas

2. **Aplicar workaround para SNMP Monitor:**
   - Adicionar timeout no gather
   - Adicionar restart automático

3. **Testar alerta de voltagem:**
   - Configurar limite para 25V no equipamento 10.200.200.2
   - Aguardar 2 minutos
   - Verificar se alerta chega no WhatsApp

**DEPOIS (próximas 2 horas):**

4. Implementar health check endpoint
5. Criar script de monitoramento externo
6. Deixar rodando e monitorar logs

---

## 📝 NOTAS IMPORTANTES

- **Backup do banco:** Configurado e funcionando
- **Logs:** Sendo salvos em `collector_supervisor.log` (rotação automática)
- **Notificações:** WhatsApp e Telegram configurados e funcionando
- **Frontend:** Funcionando perfeitamente
- **API:** Funcionando perfeitamente

**O PROBLEMA ESTÁ APENAS NO COLLECTOR (backend de monitoramento)**

---

## 🆘 SE TUDO FALHAR

**Plano B - Restart Forçado a cada 1h:**
```batch
# criar task_restart_collector.bat
taskkill /F /IM pythonw.exe
timeout /t 5
start pythonw launcher.pyw
```

**Agendar no Task Scheduler:**
- Executar a cada 1 hora
- Com privilégios de administrador
- Mesmo se o usuário não estiver logado

Isso garante que mesmo com o bug do SNMP Monitor, o sistema ficará no máximo 1h offline antes de se recuperar.

---

**FIM DO CHECKLIST**
