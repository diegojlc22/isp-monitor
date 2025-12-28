# Relatório de Desenvolvimento - ISP Monitor

**Data:** 26/12/2025
**Autoria:** Antigravity (Google Deepmind)

## 📌 Resumo da Sessão

Nesta sessão, focamos em tornar o **ISP Monitor** robusto, auto-gerenciável e com suporte completo a **notificações multi-canal** (WhatsApp + Telegram).

### 🛠️ 1. Infraestrutura e Auto-Reparo (Doctor AI)

Implementamos um sistema de "Self-Healing" para reduzir a necessidade de suporte técnico manual.

*   **Launcher Inteligente (`LAUNCHER.bat`)**:
    *   Agora detecta automaticamente se o Python ou dependências estão faltando.
    *   Executa o `setup.ps1` automaticamente se necessário (Zero Config).
    *   Gerencia processos (API, Frontend, WhatsApp) e verifica status via arquivos (`whatsapp_is_ready.txt`) em vez de portas, evitando falsos negativos.

*   **Doctor AI (`tools/reparo/diagnostico.py`)**:
    *   Script inteligente que analisa logs (`startup.log`, `api.log`) em busca de padrões de erro (Porta Presa, No LID, Missing Module).
    *   Aciona scripts de correção específicos:
        *   `correcao_whatsapp.bat`: Limpa sessões travadas e caches.
        *   `destravar_processos.bat`: Mata processos zumbis (Python/Node).
        *   `instalar_dependencias.bat`: Reinstala libs.
        *   `rebuild_frontend.bat`: Reconstrói a UI se faltar `index.html`.
        *   `turbo_db.py`: Otimiza o PostgreSQL (`postgresql.conf`).

### 📱 2. WhatsApp Gateway 2.0

Reescrevemos partes críticas da integração com WhatsApp (`server.js`):

*   **Correção "No LID"**: Travamos a versão do WhatsApp Web (`2.2407.3`) para evitar bugs recentes de envio.
*   **Validação de Destino**: O sistema agora verifica se o número existe e formata (55DDD9...) antes de enviar.
*   **Detector de Grupos/Contatos**: Suporte nativo a `@g.us` e `@c.us`.
*   **Status API**: Endpoint `/status` informa se está pronto e quem está logado.

### 🔔 3. Notificações Multi-Canal (A Pedido do Usuário)

O sistema de alertas foi expandido para permitir escolha granular de canais via UI.

*   **Frontend (`Alerts.tsx`)**:
    *   Painéis separados para Telegram e WhatsApp.
    *   Checkboxes para ativar/desativar cada canal.
    *   Input para "Destino WhatsApp" (ID de Grupo ou Número).
    *   Botão de **Teste Imediato** que usa o valor digitado no input (sem precisar salvar antes).
    
*   **Backend (`settings.py`, `pinger_fast.py`, `notifier.py`)**:
    *   Nova estrutura de configuração no banco (`parameters` table).
    *   Rotas API para salvar preferências e testar envio.
    *   Motor de monitoramento (`Pinger`) agora lê essas configurações a cada 60s e dispara notificações para os canais ativos.

### 🖥️ 4. Interface (Launcher GUI)

*   **Lista de Grupos Interativa**:
    *   Nova janela `Listar Grupos` no Launcher exibe uma `Treeview`.
    *   Permite copiar ID com duplo clique e testar envio imediatamente.

---

## 🚀 Próximos Passos (Sugestões)

1.  **Monitoramento Mobile**: Criar versão responsiva ou App (já preparado com API).
2.  **Relatórios PDF**: Gerar relatórios de SLA baseados nos logs de Ping.
3.  **Dashboards Grafana**: Integrar o banco PostgreSQL com Grafana para gráficos históricos avançados.

---


### 🐛 Hotfix (26/12 - 13:50)
*   **Correção de Startup**: Corrigido erro `NameError: name 'Optional' is not defined` no backend (`settings.py`) que impedia a inicialização da API Uvicorn. Importação adicionada com sucesso.

### 🎨 UI Update (26/12 - 13:55)
*   **Melhoria em Configurações (Alertas)**: A pedido do usuário, a seção do WhatsApp foi dividida em dois campos claros: "Destino Individual (Número)" e "ID do Grupo", assemelhando-se à estrutura Token/ChatID do Telegram e facilitando o envio para ambos os destinos simultaneamente.

**Status Final:** ✅ Sistema Operacional, Estável e Documentado.
