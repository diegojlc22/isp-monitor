# Relatório Técnico: Implementação de Gestão de Performance via SNMP

## 1. Análise de Valor: De "Uptime" para "Performance"
A implementação do protocolo SNMP (Simple Network Management Protocol) eleva o **ISP Monitor** de uma ferramenta reativa (que avisa quando caiu) para uma plataforma proativa de **Observabilidade**.

*   **Transformação de Dados**: Um monitor baseada em ICMP (Ping) gera dados binários (`0` ou `1`, `Online` ou `Offline`) e Latência (`ms`). O SNMP desbloqueia métricas contínuas e volumétricas:
    *   **Tráfego (bps)**: Capacidade real utilizada pelo cliente.
    *   **Erros (CRC/Discards)**: Qualidade física do link.
    *   **Hardware Vital**: CPU, Memória, Temperatura e Voltagem.
*   **Gestão de SLA**: Permite não apenas garantir que o serviço está "no ar", mas provar que a largura de banda contratada está sendo entregue (Throughput).

## 2. Nível de Melhoria: Monitoramento L3 (Ping) vs. L2/L1 (SNMP)
O ganho de visibilidade é da ordem de **100x** em profundidade diagnóstica.

### Camada 3 (Rede/Ping)
*   **O que vê**: Conectividade IP ponta-a-ponta.
*   **Ponto Cego**: Não sabe *por que* um pacote foi perdido (foi congestionamento? foi erro de CRC? foi CPU alta?).
*   **Limitação**: Um ping pode responder ✅ mesmo que o link esteja com 99% de perda de pacotes ou saturado, mascarando a experiência ruim do cliente.

### Camada 2/L1 (Enlace/Física via SNMP)
*   **O que vê**: O estado das portas físicas (interfaces) e contadores de quadros.
*   **Visibilidade**:
    *   **ifOperStatus**: Identifica se o cabo foi desconectado (Link Down) ou se está negociando.
    *   **ifInErrors / ifOutErrors**: Detecção direta de problemas físicos (cabos ruins, conectores oxidados, interferência eletromagnética). Erros de CRC e Frame são visíveis aqui.
    *   **ifInDiscards**: Indica que o equipamento está recebendo mais tráfego do que seu buffer/CPU consegue processar (gargalo de CPU ou Bufferfloat), mesmo que o link físico esteja perfeito.

## 3. Detecção de Gargalos (Capacity Planning)
A coleta de `ifInOctets` e `ifOutOctets` (especialmente os contadores de 64-bits `HC` implementados) permite calcular a taxa de transferência instantânea (`bps`):

`Throughput = (Octets_Atual - Octets_Anterior) * 8 / (Tempo_Decorrido)`

*   **Previsão de Saturação**: Ao cruzar o throughput atual com a capacidade da interface (`ifHighSpeed`), podemos gerar alertas preventivos.
    *   *Exemplo*: Alertar quando o tráfego médio de 5 minutos exceder 80% da capacidade do link.
*   **Benefício**: O provedor pode oferecer um upgrade de plano ou ampliar o link de backbone *antes* que o cliente abra um chamado reclamando de lentidão no horário de pico.

## 4. Resolução de Problemas (Troubleshooting Avançado)
O SNMP fornece a "assinatura Digital" do problema:

| Sintoma (Usuário) | Visão Ping (L3) | Visão SNMP (Diagnóstico) | Causa Provável |
| :--- | :--- | :--- | :--- |
| **Lentidão** | Latência Alta / Perda | `ifInOctets` no teto (`100Mbps` em porta `100M`) | **Saturação de Link**. Solução: Upgrade. |
| **Quedas Intermitentes** | Timeout Aleatório | `ifInErrors` (CRC) crescendo | **Físico**. Solução: Trocar cabo/conector. |
| **Equipamento Travando** | Timeout Total | CPU Load (`1.3.6.1.2.1.25.3.3.1.2`) em 100% | **Processamento**. Solução: Roteador subdimensionado ou Loop. |
| **Lentidão sem Tráfego** | Latência Alta | `ifInDiscards` crescendo | **Bufferbloat / Qos**. Solução: Ajustar filas/regras. |

## 5. Arquitetura de Dados Recomendada
Para armazenar séries temporais de alta frequência (ex: coleta a cada 10s ou 60s de dezenas de interfaces), bancos relacionais tradicionais (SQL) sofrem com o volume de escrita e queries de agregação.

### Sugestão: Otimização do PostgreSQL Atual
1.  **Metadados (PostgreSQL)**: Armazena o cadastro dos equipamentos, nomes, IPs, communities. (O que o ISP Monitor já faz).
2.  **Séries Temporais (TimescaleDB)**:
    *   **O que é**: Como você **já utiliza PostgreSQL**, o próximo passo ideal é ativar a **extensão TimescaleDB**.
    *   **Benefício**: Transforma a tabela `TrafficLog` (que hoje é uma tabela padrão do Postgres) em uma **Hypertable**. Isso aumenta drasticamente a velocidade de inserção e compressão dos dados históricos, sem precisar trocar de banco de dados.

*Para o estágio atual do projeto*, o modelo relacional padrão do PostgreSQL é robusto. A ativação do **TimescaleDB** será necessária apenas quando o histórico crescer para milhões de linhas (ex: meses de logs detalhados), para manter os gráficos rápidos.

## 6. Roadmap Básico e OIDs Universais
Para resultados rápidos e compatibilidade multi-vendor (Mikrotik, Ubiquiti, Cisco, Linux), foque na **Standard MIB-II (RFC 1213)**.

### Bibliotecas Sugeridas
*   **Python Backend**: `pysnmp` (já em uso, versão Asyncio para performance).
*   **Visualização**: Grafana (plugado no banco) ou Recharts (React, já em uso).

### OIDs Universais (Comece por aqui)
| Métrica | OID / Nome | Descrição |
| :--- | :--- | :--- |
| **Identificação** | `.1.3.6.1.2.1.1.1.0` (sysDescr) | Nome e versão do SO. |
| **Uptime** | `.1.3.6.1.2.1.1.3.0` (sysUpTime) | Tempo ligado (detecta reboots não autorizados). |
| **Lista de Interfaces** | `.1.3.6.1.2.1.2.2.1.2` (ifDescr) | Nomes (ether1, wlan1). Use `walk`. |
| **Tráfego (Entrada)** | `.1.3.6.1.2.1.31.1.1.1.6` (ifHCInOctets) | Contador 64-bit (obrigatório para >100Mbps). |
| **Tráfego (Saída)** | `.1.3.6.1.2.1.31.1.1.1.10` (ifHCOutOctets) | Contador 64-bit. |
| **Status Operacional** | `.1.3.6.1.2.1.2.2.1.8` (ifOperStatus) | 1=Up, 2=Down. |
| **Erros de Entrada** | `.1.3.6.1.2.1.2.2.1.14` (ifInErrors) | Soma de CRCs, frames alinhados incorretamente, etc. |

### Próximos Passos (Action Plan)
1.  **Validar Counters 64-bit**: Confirmar se a nova função `get_snmp_interface_traffic` está lendo as OIDs `HC` (High Capacity) para evitar gráficos serrilhados em portas Gigabit. **(Feito)**.
2.  **Monitoramento de Erros**: Criar serviço para coletar `ifInErrors` e alertar se `delta > 0` (qualquer erro é ruim).
3.  **Visualização Histórica**: Implementar gráficos com "Zoom" no frontend para permitir ver picos de consumo em granularidade fina.
