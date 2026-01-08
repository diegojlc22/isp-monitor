# Relatório Técnico de Análise e Otimização - ISP Monitor (v3.0)

**Data:** 26/12/2025  
**Autor:** Antigravity AI Agent  
**Status:** Aguardando Aprovação

---

## 1. Visão Geral
O sistema ISP Monitor encontra-se em um estágio maduro de desenvolvimento (v3.0), utilizando tecnologias modernas (FastAPI, React, AsyncPG). A arquitetura de separação entre API e Coletor (Worker) é robusta e previne travamentos da interface.

Entretanto, identificamos oportunidades de limpeza de código (débito técnico), otimização de banco de dados e melhoria na experiência de atualização.

---

## 2. Código Morto e Limpeza (Cleanup)

Os seguintes arquivos foram identificados como temporários, obsoletos ou de debug e devem ser removidos para manter a higiene do repositório:

| Arquivo | Motivo da Remoção | Ação Recomendada |
| :--- | :--- | :--- |
| `DEBUG_LAUNCHER.bat` | Script criado apenas para diagnóstico de falha no startup. | **Excluir** |
| `CHECK_DB.bat` | Ferramenta pontual de correção de senha do banco. | **Mover para `scripts/tools` ou Excluir** |
| `check_db.py` | Script Python auxiliar do batch acima. | **Mover para `scripts/tools` ou Excluir** |
| `.setup-state.json` | Arquivo de estado interno do instalador (setup.ps1). | **Manter (GitIgnored)**, mas pode ser limpo em clean install. |
| `iniciar_postgres.bat` (Linhas comentadas) | Definições hardcoded de `DATABASE_URL` foram comentadas. | **Remover linhas comentadas** definitivamente. |

---

## 3. Análise de Performance (Backend & Coletor)

### 3.1. Monitoramento SNMP (`snmp_monitor.py`)
*   **Diagnóstico:** O código utiliza `asyncio.Semaphore(100)` para paralelizar consultas. Isso é excelente. Também implementa "Smart Logging" (linhas 153-191), evitando gravar no banco se a variação de tráfego for < 10%. Isso economiza GBs de disco a longo prazo.
*   **Oportunidade:** As atualizações no banco são feitas iterativamente (`session.add(eq_obj)` dentro de um loop).
*   **Impacto:** Em cenários com >500 dispositivos, o `session.commit()` final pode demorar devido ao *overhead* do ORM rastreando centenas de objetos.
*   **Sugestão:** Converter para **Bulk Update** usando SQLAlchemy Core (`update(Equipment).where(...).values(...)`) para performance 10x superior em escalas grandes.

### 3.2. Coletor (`collector.py`)
*   **Diagnóstico:** Utiliza `asyncio.gather` corretamente.
*   **Oportunidade:** O Loop de manutenção diária (`maintenance_loop`) dorme por 86400 segundos fixos. Se o serviço for reiniciado, o timer reseta e a manutenção roda na hora errada.
*   **Sugestão:** Agendar a limpeza para um horário fixo (ex: 03:00 AM) usando `apscheduler` (já listado em requirements) em vez de `sleep` simples.

### 3.3. Banco de Dados
*   **Diagnóstico:** Driver `asyncpg` configurado corretamente. Otimizações de pool aplicadas.
*   **Oportunidade:** As tabelas de logs (`PingLog`, `TrafficLog`) crescem indefinitamente se o `cleanup_job` falhar.
*   **Sugestão:** Implementar **Particionamento de Tabelas** no PostgreSQL por mês (ex: `traffic_log_2025_12`), facilitando o descarte (DROP TABLE) de dados antigos sem travar o banco com `DELETE FROM` massivo.

---

## 4. Análise de Frontend

### 4.1. Cache e Atualizações
*   **Problema Resolvido:** O navegador cacheava arquivos antigos (`RequestsPage` desatualizada).
*   **Solução Aplicada:** Implementado "Smart Build System" no Launcher.
*   **Sugestão Adicional:** Configurar o arquivo `vite.config.ts` para gerar nomes de arquivos com hash único a cada build (já é padrão, mas pode ser tunado) e configurar o servidor Uvicorn para enviar headers `Cache-Control: no-cache` para o arquivo `index.html`.

### 4.2. Renderização de Mapas
*   **Oportunidade:** Se houver milhares de equipamentos, renderizar todos os marcadores no Leaflet trava o navegador.
*   **Sugestão:** Implementar **Clusterização de Marcadores** (MarkerCluster) no mapa. Agrupar pontos próximos em um único ícone com contador.

---

## 5. Plano de Ação Recomendado

1.  **Imediato (Limpeza):**
    *   Executar script de remoção dos arquivos listados na seção 2.
    
2.  **Curto Prazo (Robustez):**
    *   Migrar updates do SNMP Monitor para Bulk Updates.
    *   Configurar `apscheduler` para tarefas cronometradas reais.

3.  **Médio Prazo (Escalabilidade):**
    *   Implementar Particionamento de Tabelas no Postgres.
    *   Implementar WebSockets para substituir polling no Frontend (reduz carga de rede em 80%).

---

**Aprovação:** Aguardo seu OK para executar a **Fase 1 (Limpeza)** imediatamente e arquivar este relatório.
