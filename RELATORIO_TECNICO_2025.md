# Relatório Técnico: ISP Monitor (Dezembro 2025)

## 1. Visão Geral
Este documento detalha a análise de performance, limpeza de código e simulações de carga realizadas no projeto ISP Monitor. O objetivo foi garantir estabilidade para operações em escala média a grande.

---

## 2. Fase 1: Limpeza e Organização
**Ações Realizadas:**
- **Remoção de Arquivos Mortos:** `debug_startup.py` e scripts de teste antigos foram removidos.
- **Organização de Documentação:** Todos os arquivos `.md` (exceto README) e exemplos JSON foram movidos para a pasta `docs/` para limpar a raiz do projeto.
- **Validação de Código:** Confirmada a separação correta entre `auth_utils` (lógica pura) e `dependencies` (FastAPI).
- **SNMP:** Validada a modularização entre `snmp.py` (Tráfego) e `wireless_snmp.py` (Sinal/CCQ). O orquestrador `snmp_monitor.py` integra ambos corretamente.

---

## 3. Fase 2: Simulação de Carga (Stress Testing Teórico)

Considerando a arquitetura atual:
- **Backend:** FastAPI + Uvicorn (AsyncIO)
- **Database:** SQLite (WAL Mode + aiosqlite)
- **Monitoramento:** ICMPLib (Raw Sockets) + PySNMP (UDP)

### Cenário A: Pequena Escala (Situação Atual)
*   **Carga:** 100 Equipamentos.
*   **Intervalos:** Ping 30s, SNMP 60s.
*   **Comportamento:** O sistema opera em "idle" (ocioso) na maior parte do tempo.
*   **Gargalo:** Nenhum.
*   **Uso de Disco:** ~100 writes/min. Irrisório.

### Cenário B: Média Escala (Expansão)
*   **Carga:** 500 Equipamentos.
*   **Intervalos:** Ping 30s, SNMP 60s.
*   **Análise SNMP:** 
    - Antes (Semáforo=20): 25 batches sequenciais. ~25-30s para completar o ciclo. Seguro.
    - Agora (Semáforo=100): 5 batches. ~5s para completar. **Muito performático.**
*   **Análise BD:** Leitura de gráficos pesados (ex: "Últimas 24h" para 500 devices) pode causar leve "lag" na UI, mas não trava o monitoramento (graças ao WAL mode).
*   **Conclusão:** Sistema estável e pronto para este cenário.

### Cenário C: Limite / Estresse
*   **Carga:** 2.000 Equipamentos.
*   **Intervalos:** Ping 10s (Agressivo), SNMP 60s.
*   **Ponto de Falha (Ping):** O Windows pode limitar o número de raw sockets abertos ou descartar pacotes ICMP se a fila encher. Isso geraria "Falsos Positivos" (Offline).
*   **Ponto de Falha (BD):** 2.000 pings a cada 10s = 200 inserts/seg. SQLite aguenta, mas o arquivo `.wal` crescerá rápido (Checkpointing frequente necessário).
*   **Limitação da UI:** Renderizar 2.000 linhas na tabela "Status" vai travar o navegador do cliente (DOM excessivo), não o servidor.

**Limite Recomendado Atual:** Até **800-1000** dispositivos com hardware padrão (i5/16GB). Acima disso, recomenda-se migrar para PostgreSQL e otimizar Frontend (virtualização de lista).

---

## 4. Fase 3: Ajustes e Otimizações
Com base na simulação, aplicamos as seguintes melhorias imediatas:

1.  **Aumento de Concorrência SNMP:**
    - O limite de conexões simultâneas (Semáforo) foi aumentado de **20 para 100**.
    - **Resultado:** Coleta de dados SNMP até 5x mais rápida, liberando tempo de CPU para outras tarefas.

2.  **Limpeza de Interface:**
    - Reduzimos o histórico de logs na tela "Agente" para 20 itens, melhorando a responsividade.

3.  **Correção de Migrações:**
    - Colunas críticas (`is_mikrotik`, `brand`, etc.) foram garantidas no banco de dados via script de migração.

---

## 5. Próximos Passos (Futuro)
Se o projeto ultrapassar 1.000 dispositivos:
1.  **Frontend:** Implementar "Virtual Scroll" na Tabela de Equipamentos (React Window) para não renderizar 1000 linhas de uma vez.
2.  **Database:** Migrar de SQLite para **PostgreSQL** (TimescaleDB seria ideal para logs).
3.  **Batch Insert:** Modificar o Pinger para inserir logs em lotes (ex: a cada 100 resultados) em vez de 1 por 1.
