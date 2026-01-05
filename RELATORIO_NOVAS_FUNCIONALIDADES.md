# 📋 RELATÓRIO DE NOVAS FUNCIONALIDADES - ISP MONITOR

## Data: 05/01/2026

---

## 1️⃣ SUPRESSÃO DE ALERTAS POR TOPOLOGIA (Inteligência de Raiz)

### Como Funciona:
O sistema agora entende a hierarquia da sua rede. Quando um dispositivo "pai" (Torre ou Equipamento Principal) cai, todos os dispositivos "filhos" que dependem dele são automaticamente silenciados.

### Fluxo de Operação:
1. **Carregamento de Hierarquia**: O Pinger carrega os relacionamentos `parent_id` e `tower_id` de cada equipamento
2. **Detecção de Queda**: Quando um dispositivo fica offline, o sistema verifica:
   - Se ele tem um equipamento pai → Verifica se o pai está online
   - Se ele pertence a uma torre → Verifica se a torre está online
   - Se é uma torre → Verifica se a torre backbone (pai) está online
3. **Supressão Inteligente**: Se o pai/torre estiver offline, o alerta é silenciado e marcado como "(Silenciado por topologia)"
4. **Notificação Focada**: Você recebe apenas **1 alerta** da raiz do problema, não 50 alertas de todos os rádios atrás dela

### Exemplo Prático:
```
Torre Principal (192.168.1.1) CAIU
├─ PTP-Cliente-A (192.168.2.1) ❌ Silenciado
├─ PTP-Cliente-B (192.168.2.2) ❌ Silenciado
└─ PTP-Cliente-C (192.168.2.3) ❌ Silenciado

Você recebe: 1 alerta da Torre Principal
Sem supressão: 4 alertas (torre + 3 clientes)
```

### Benefícios:
- ✅ Menos barulho no celular
- ✅ Foco imediato no problema raiz
- ✅ Histórico completo no banco (todos os eventos são registrados)

---

## 2️⃣ MONITORAMENTO DE SAÚDE DE ENERGIA (Voltage Tracking)

### Como Funciona:
O sistema já coleta dados de voltagem via SNMP dos equipamentos MikroTik. Essa funcionalidade está integrada ao `snmp_monitor.py` e armazena os dados na tabela `traffic_logs`.

### Dados Coletados:
- **Voltagem** (V)
- **Temperatura** (°C)
- **CPU Usage** (%)
- **Memória** (%)
- **Disco** (%)

### Próximos Passos (Sugestão):
Criar um alerta no Agente Inteligente que detecte:
- Queda brusca de voltagem (ex: 27V → 23V em 10 min)
- Temperatura acima de 70°C
- CPU acima de 90% por mais de 5 minutos

### Exemplo de Alerta Futuro:
```
⚠️ ALERTA DE ENERGIA
Torre Buriti (192.168.1.5)
📉 Voltagem caiu de 27.2V para 23.1V
⏰ Provavelmente acabou a energia da rua
🔋 Sistema está na bateria
```

---

## 3️⃣ PREVISÃO DE CAPACIDADE (Capacity Planning)

### Como Funciona:
Analisa o histórico de tráfego dos últimos 30 dias e usa **regressão linear** para prever quando um link chegará no limite.

### Fluxo de Operação:
1. **Coleta de Dados**: Busca os picos diários de tráfego dos últimos 30 dias
2. **Cálculo de Tendência**: Calcula a taxa de crescimento (Mbps/dia) usando regressão linear
3. **Estimativa de Capacidade**: Detecta automaticamente a capacidade do link (100/200/500/1000 Mbps)
4. **Projeção**: Calcula quantos dias faltam para atingir 90% da capacidade
5. **Alerta Semanal**: Envia relatório toda semana com os links mais críticos

### Exemplo de Alerta:
```
📈 ALERTA DE CAPACIDADE

🔴 CRÍTICO - JÁ NO LIMITE!
PTP-PRINCIPAL (192.168.1.10)
📊 Uso atual: 92 Mbps / 100 Mbps (92%)
📈 Crescimento: +0.8 Mbps/dia

🟠 URGENTE
PTP-BACKBONE (192.168.1.20)
📊 Uso atual: 180 Mbps / 200 Mbps (90%)
📈 Crescimento: +1.2 Mbps/dia
⏰ Estimativa: 12 dias até 90% de capacidade

💡 Recomendação: Planeje upgrade de capacidade
```

### Benefícios:
- ✅ Prevenção de saturação de links
- ✅ Planejamento de investimentos
- ✅ Evita reclamações de lentidão

---

## 4️⃣ AUDITORIA DE SEGURANÇA AUTOMÁTICA

### Como Funciona:
Roda **toda semana** e verifica vulnerabilidades comuns em todos os equipamentos online.

### Verificações Realizadas:
1. **Senhas Padrão (SSH)**:
   - Testa: ubnt/ubnt, admin/admin, admin/(vazio), root/root
   - Método: Tentativa real de conexão SSH

2. **SNMP com Community Padrão**:
   - Testa: public, private, admin, community
   - Método: Query SNMP com cada community

3. **Portas Inseguras Abertas**:
   - Telnet (23) - Não criptografado
   - HTTP (80) - Admin sem HTTPS
   - FTP (21) - Transferência insegura
   - Mikrotik API (8728) - Sem criptografia

### Exemplo de Relatório:
```
🔒 RELATÓRIO DE SEGURANÇA SEMANAL

📅 05/01/2026 10:45
⚠️ Encontrados 3 dispositivos com problemas:

PTP-CLIENTE-A (192.168.2.5)
  • ⚠️ Senha padrão detectada (SSH)
  • ⚠️ SNMP com community padrão: public
  • ⚠️ Portas inseguras abertas: Port 23 (Telnet)

PTP-CLIENTE-B (192.168.2.10)
  • ⚠️ Portas inseguras abertas: Port 80 (HTTP)

Torre-Buriti (192.168.1.5)
  • ⚠️ SNMP com community padrão: public, private

🛡️ Recomendação: Altere senhas padrão e desabilite serviços inseguros
```

### Benefícios:
- ✅ Prevenção de invasões
- ✅ Conformidade com boas práticas
- ✅ Identificação proativa de vulnerabilidades

---

## 5️⃣ RELATÓRIO DIÁRIO DE PIORES CLIENTES (Sinal Ruim)

### Como Funciona:
Todo dia às **8h da manhã**, o sistema envia automaticamente um relatório com os rádios que estão com pior desempenho.

### Critérios de Seleção:
- **Pior Sinal**: Sinal < -70 dBm
- **Pior CCQ**: CCQ < 70%
- **Top 10** de cada categoria

### Exemplo de Relatório:
```
📊 RELATÓRIO DIÁRIO DE SINAL

📅 05/01/2026 08:00
📡 Total de estações monitoradas: 145

🔴 TOP 10 PIORES SINAIS:
1. Cliente-João ⏰
   📍 192.168.100.50 | 📶 -86 dBm | CCQ: 45%

2. Cliente-Maria
   📍 192.168.100.75 | 📶 -82 dBm | CCQ: 55%

3. Cliente-Pedro
   📍 192.168.100.90 | 📶 -79 dBm | CCQ: 60%

🟡 TOP 10 PIORES CCQ:
1. Cliente-Ana
   📍 192.168.100.120 | CCQ: 35% | 📶 -75 dBm

2. Cliente-Carlos
   📍 192.168.100.135 | CCQ: 42% | 📶 -73 dBm

⏰ = Dados desatualizados (>24h)
💡 Recomendação: Verifique alinhamento e obstruções
```

### Benefícios:
- ✅ Ação preventiva antes do cliente ligar
- ✅ Priorização de manutenções
- ✅ Melhoria contínua da qualidade do sinal

---

## 6️⃣ MAPA DE CALOR (Heatmap) - PRÓXIMA FASE

### Status: **Planejado** (Não implementado ainda)

### Como Funcionará:
Integração com Google Maps ou Leaflet para visualizar geograficamente:
- 🟢 Verde: Sinal excelente (> -65 dBm)
- 🟡 Amarelo: Sinal médio (-65 a -75 dBm)
- 🟠 Laranja: Sinal fraco (-75 a -85 dBm)
- 🔴 Vermelho: Sinal crítico (< -85 dBm)

### Benefícios Esperados:
- ✅ Decisão visual de onde colocar novas torres
- ✅ Identificação de áreas com cobertura ruim
- ✅ Planejamento de expansão

---

## 📊 RESUMO DE INTEGRAÇÃO

Todas as novas funcionalidades foram integradas ao **Collector Supervisor** (`backend/collector.py`):

```python
Serviços Ativos:
1. Pinger (Monitoramento de Conectividade)
2. SNMP Monitor (Tráfego + Wireless + Saúde)
3. AI Agent (Detecção de Degradação)
4. Topology (Descoberta Automática)
5. Maintenance (Limpeza de Logs)
6. Heartbeat (Status do Coletor)
7. Security Audit (Auditoria Semanal) ← NOVO
8. Daily Report (Relatório Diário 8h) ← NOVO
9. Capacity Planning (Análise Semanal) ← NOVO
```

### Cronograma de Execução:
- **Contínuo**: Pinger, SNMP Monitor
- **A cada 5 min**: AI Agent (configurável)
- **A cada 30 min**: Topology Discovery
- **Diário 8h**: Daily Signal Report
- **Semanal**: Security Audit, Capacity Planning
- **A cada 24h**: Maintenance (Limpeza)

---

## 🚀 PRÓXIMOS PASSOS RECOMENDADOS

1. **Testar as novas funcionalidades**:
   - Reiniciar o Collector para ativar os novos serviços
   - Aguardar os relatórios programados

2. **Configurar hierarquia**:
   - Definir `parent_id` nos equipamentos
   - Definir `tower_id` nos rádios
   - Definir `parent_id` nas torres (backbone)

3. **Ajustar parâmetros**:
   - Horário do relatório diário (padrão: 8h)
   - Thresholds de sinal/CCQ
   - Frequência da auditoria de segurança

4. **Implementar Mapa de Calor** (Fase 2):
   - Adicionar coordenadas GPS nos equipamentos
   - Criar endpoint de API para dados geográficos
   - Desenvolver componente React com mapa

---

**Desenvolvido por: Antigravity AI**  
**Data: 05/01/2026**
