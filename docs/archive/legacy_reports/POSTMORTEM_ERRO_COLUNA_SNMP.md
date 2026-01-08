# Post-Mortem: Erro de Coluna Ausente (UndefinedColumnError) - SNMP

**Data:** 31/12/2025
**Incidente:** Falha ao salvar logs de tráfego SNMP e ao carregar gráficos no Frontend.
**Erro Observado:** `sqlalchemy.exc.ProgrammingError: ... column traffic_logs.interface_index does not exist`.

## 1. O Problema
Durante a implementação da funcionalidade de "Seleção de Interface de Tráfego", adicionamos o campo `interface_index` ao modelo `TrafficLog` no código Python (`models.py`), mas a migração automática (Alembic) ou a atualização do esquema não foi aplicada corretamente no banco de dados de produção local.

Isso gerou um descompasso:
*   **Código:** Tentava ler/escrever na coluna `interface_index`.
*   **Banco de Dados:** A coluna não existia.
*   **Consequência:** O backend retornava erro 500 fatal ao tentar salvar dados de tráfego, travando a coleta.

## 2. A Solução (Hotfix)
Foi criada uma ferramenta de **Auto-Reparo** (`ferramentas/system_repair.py`) que:
1.  Conecta ao banco de dados PostgreSQL.
2.  Verifica se as colunas críticas existem (`snmp_traffic_interface_index` na tabela `equipments` e `interface_index` na tabela `traffic_logs`).
3.  Se não existirem, executa o comando `ALTER TABLE ... ADD COLUMN` automaticamente.

## 3. Prevenção Futura
*   Sempre que houver alterações em `models.py`, deve-se garantir que uma migração SQL correspondente seja executada.
*   A ferramenta `ferramentas/system_repair.py` foi mantida no projeto. Se um erro similar ocorrer no futuro (ex: "column X does not exist"), basta rodar este script para forçar a atualização do banco.

## 4. Scripts Criados
*   `ferramentas/system_repair.py`: Ferramenta definitiva para corrigir schema drift.
*   `scripts/self_heal.py`: Atualizado para reiniciar o serviço do PostgreSQL (versão 17) automaticamente se ele travar.
