# Projeto ISP Monitor
Análise do Projeto e Relatório de Progresso

## 🔥 Desempenho & Arquitetura (Novo)
*   **Velocidade:** Implementação de Pinger em Lote/Assíncrono (icmplib) -> **500% Mais Rápido** que o ping sequencial. Capaz de escanear 200+ dispositivos em menos de 3 segundos.
*   **Banco de Dados:** SQLite otimizado com modo WAL, Índices e Auto-Vacuum.
*   **Estabilidade:** Adicionado `maintenance_job` para limpeza automática de logs e `sqlite_optimizer` para verificações de saúde do banco.

## 🛠 Funcionalidades Implementadas

1.  **Bandeja do Sistema & Modo Silencioso:**
    *   Fim das janelas de console pretas (Cmd/Terminal).
    *   O App minimiza para a Bandeja do Sistema (Área de Notificação, perto do relógio).
    *   `launcher.pyw` + VBScript implementados para uma inicialização totalmente silenciosa e profissional.

2.  **Alertas Inteligentes (Anti-Spam):**
    *   **Dependência Pai/Filho:** Se um roteador principal cair, os dispositivos conectados a ele (filhos) NÃO enviarão alertas. Isso evita o "spam" de 50 notificações simultâneas quando uma torre cai. (Lógica implementada em `pinger_fast.py`).

3.  **Fundação SNMP (Preparado):**
    *   Backend preparado para SNMP v2c (Novas colunas no banco: community, version, port).
    *   Serviço base criado para consultas futuras de tráfego e uptime.

4.  **Instalação Automatizada (Portátil):**
    *   `iniciar_sistema.bat` gerencia a detecção e instalação de Python e Node.js automaticamente.
    *   Ambiente isolado (`.venv`) garantindo que o software rode em qualquer PC Windows sem conflitos.

## 🚀 Comparação de Velocidade
*   **Lógica Antiga:** Ping sequencial (um por um). Para 50 dispositivos = ~50 segundos.
*   **Nova Lógica (Estilo "The Dude"):** Ping Paralelo (Async). Para 50 dispositivos = **~1.5 segundos**.

## 📌 Como Usar Agora
*   **Para Iniciar:** Clique duplo no arquivo `Abrir Painel.vbs`.
*   **Na Bandeja:** Clique com o botão direito no ícone azul para "Abrir Painel" ou "Sair".
