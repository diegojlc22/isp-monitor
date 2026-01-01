# 🚀 PLANO DE IMPLEMENTAÇÃO - ISP MONITOR v2.0

## 📋 ESCOPO DO PROJETO

Implementar melhorias de UX, monitoramento avançado e inteligência, EXCETO o Wizard de Setup Inicial.

---

## 🎯 FASE 1: UX IMEDIATA (Prioridade ALTA)

### 1.1 Botão "Auto-Detectar Tudo" ✅ CRÍTICO
**Localização:** Formulário de Novo Equipamento / Editar Equipamento

**Funcionalidade:**
- Detecta marca automaticamente (Mikrotik/Ubiquiti/Intelbras/etc)
- Detecta interface de sinal wireless
- Detecta interface de tráfego (com mais Mbps)
- Preenche todos os campos automaticamente
- Mostra progresso visual (loading spinner)
- Feedback de sucesso/erro

**Backend:**
- ✅ Endpoint já existe: `/api/equipments/detect-brand`
- ✅ Endpoint já existe: `/api/equipments/{id}/auto-configure-traffic`
- ⚠️ Precisa criar: `/api/equipments/auto-detect-all` (combina os 2)

**Frontend:**
- Adicionar botão "🔍 Auto-Detectar Tudo" no formulário
- Modal de progresso com steps:
  1. Testando conexão...
  2. Detectando marca...
  3. Detectando interface de sinal...
  4. Detectando interface de tráfego...
  5. ✅ Concluído!

**Estimativa:** 4-6 horas

---

### 1.2 Health Check Dashboard ✅ IMPORTANTE
**Localização:** Nova página `/health` ou widget no Dashboard

**Funcionalidade:**
- Status do Collector (🟢 Rodando / 🔴 Parado)
- Status do SNMP (X/Y equipamentos respondendo)
- Status do Banco (conexões ativas, latência)
- Últimos 10 erros do sistema
- Tempo de uptime
- Versão do sistema

**Backend:**
- Novo endpoint: `/api/system/health`
- Retorna:
  ```json
  {
    "collector": {"status": "running", "uptime": "2h 30m"},
    "snmp": {"responding": 35, "total": 41},
    "database": {"connections": 5, "latency_ms": 12},
    "errors": [...],
    "version": "2.0.0"
  }
  ```

**Frontend:**
- Cards visuais com status
- Gráfico de disponibilidade (últimas 24h)
- Lista de erros recentes

**Estimativa:** 6-8 horas

---

### 1.3 Feedback Visual de Erros ✅ IMPORTANTE
**Localização:** Todo o sistema

**Funcionalidade:**
- Toast notifications mais claras
- Mensagens de erro específicas (não genéricas)
- Sugestões de solução
- Botão "Tentar Novamente"

**Exemplos:**
```
❌ ANTES: "Erro ao salvar equipamento"
✅ DEPOIS: "Não foi possível salvar o equipamento
           Causa: IP 192.168.1.1 já está em uso
           Solução: Use outro IP ou edite o equipamento existente"

❌ ANTES: "Erro SNMP"
✅ DEPOIS: "SNMP não respondeu
           Causa: Community 'public' incorreta ou SNMP desabilitado
           Solução: Verifique a community ou habilite SNMP no equipamento"
```

**Estimativa:** 3-4 horas

---

## 📊 FASE 2: MONITORAMENTO AVANÇADO (Prioridade ALTA)

### 2.1 Gráfico Multi-Interface ✅ MUITO ÚTIL
**Localização:** Modal de detalhes do equipamento

**Funcionalidade:**
- Mostrar tráfego de TODAS as interfaces
- Gráfico de linhas comparativo
- Tabela com valores atuais
- Útil para troubleshooting

**Backend:**
- Novo endpoint: `/api/equipments/{id}/all-interfaces-traffic`
- Coleta tráfego de todas as interfaces (não só a configurada)
- Retorna array com todas as interfaces

**Frontend:**
- Botão "Ver Todas as Interfaces" no Live Monitor
- Modal com gráfico Chart.js
- Atualização em tempo real

**Estimativa:** 8-10 horas

---

### 2.2 Dashboard de Tráfego Agregado ✅ IMPORTANTE
**Localização:** Nova página `/traffic-dashboard`

**Funcionalidade:**
- Tráfego total da rede (soma de todos)
- Top 10 equipamentos (mais tráfego)
- Gráfico de evolução (últimas 24h)
- Alertas de saturação (>80% da capacidade)
- Filtros por torre

**Backend:**
- Endpoint: `/api/analytics/traffic-summary`
- Agregação de dados
- Cache de 30 segundos

**Frontend:**
- Cards com totais
- Gráfico de pizza (distribuição)
- Tabela top 10
- Filtros interativos

**Estimativa:** 10-12 horas

---

### 2.3 WebSocket para Live Monitor ✅ PERFORMANCE
**Localização:** Live Monitor

**Funcionalidade:**
- Substituir polling (a cada 3s) por WebSocket
- Push em tempo real quando há mudança
- Menos carga no servidor
- Mais responsivo

**Backend:**
- Implementar WebSocket com FastAPI
- Broadcast quando equipamento muda
- Heartbeat para manter conexão

**Frontend:**
- Conectar ao WebSocket
- Atualizar UI quando recebe dados
- Reconectar automaticamente se cair

**Estimativa:** 12-15 horas

---

## 🧠 FASE 3: INTELIGÊNCIA (Prioridade MÉDIA)

### 3.1 Alertas Customizáveis ✅ ÚTIL
**Localização:** Configurações de Equipamento

**Funcionalidade:**
- Threshold de tráfego personalizado por equipamento
- Horários de silêncio (não alertar à noite)
- Escalonamento (técnico → supervisor → gerente)
- Tipos de alerta (ping, tráfego, sinal)

**Backend:**
- Nova tabela: `alert_rules`
- Lógica de escalonamento
- Integração com notifier

**Frontend:**
- Formulário de regras de alerta
- Preview de como vai funcionar

**Estimativa:** 15-18 horas

---

### 3.2 Relatórios Automáticos ✅ PROFISSIONAL
**Localização:** Nova página `/reports`

**Funcionalidade:**
- Relatório diário de disponibilidade (SLA)
- Relatório semanal de tráfego
- Relatório mensal consolidado
- Envio automático por email/WhatsApp
- Exportar PDF

**Backend:**
- Endpoint: `/api/reports/generate`
- Geração de PDF com ReportLab
- Agendamento com APScheduler
- Envio automático

**Frontend:**
- Visualização de relatórios
- Configuração de envio
- Download PDF

**Estimativa:** 20-25 horas

---

### 3.3 Previsão de Saturação (ML) ✅ AVANÇADO
**Localização:** Dashboard / Alertas

**Funcionalidade:**
- Análise de tendência de tráfego
- Previsão de quando vai saturar
- Alertas proativos
- Recomendações de upgrade

**Backend:**
- Modelo ML simples (regressão linear)
- Análise de histórico (últimos 30 dias)
- Previsão para próximos 7 dias

**Frontend:**
- Gráfico com linha de tendência
- Alerta: "Equipamento X vai saturar em 5 dias"

**Estimativa:** 25-30 horas

---

## 📅 CRONOGRAMA SUGERIDO

### Semana 1-2: FASE 1 (UX Imediata)
- Dia 1-2: Botão Auto-Detectar Tudo
- Dia 3-4: Health Check Dashboard
- Dia 5: Feedback Visual de Erros

### Semana 3-4: FASE 2 (Monitoramento)
- Dia 1-3: Gráfico Multi-Interface
- Dia 4-6: Dashboard de Tráfego Agregado
- Dia 7-10: WebSocket para Live Monitor

### Semana 5-7: FASE 3 (Inteligência)
- Dia 1-4: Alertas Customizáveis
- Dia 5-9: Relatórios Automáticos
- Dia 10-14: Previsão de Saturação (ML)

**TOTAL ESTIMADO:** 6-7 semanas

---

## 🎯 ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

1. **Botão Auto-Detectar Tudo** ← COMEÇAR AQUI (maior impacto imediato)
2. **Health Check Dashboard**
3. **Feedback Visual de Erros**
4. **Dashboard de Tráfego Agregado**
5. **Gráfico Multi-Interface**
6. **WebSocket para Live Monitor**
7. **Alertas Customizáveis**
8. **Relatórios Automáticos**
9. **Previsão de Saturação**

---

## 📝 NOTAS

- Cada feature será commitada separadamente
- Testes em ambiente de desenvolvimento primeiro
- Documentação atualizada a cada feature
- Feedback do usuário após cada fase

---

**Pronto para começar?** 🚀
