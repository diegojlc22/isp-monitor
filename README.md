# 📡 ISP Monitor (NetAdmin)

> Um sistema moderno, ágil e eficiente para monitoramento de infraestrutura de Provedores de Internet (ISP).

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB)
![License](https://img.shields.io/badge/License-MIT-blue)

## 📖 Sobre o Projeto

O **ISP Monitor** foi desenvolvido para centralizar e simplificar a gestão de redes de provedores. Com uma interface limpa e responsiva, ele permite que administradores e técnicos monitorem o status de torres e equipamentos em tempo real, recebam alertas via Telegram e gerenciem sua infraestrutura com facilidade.

Diferente de sistemas complexos e inchados, o foco aqui é **agilidade**: saber o que caiu, onde caiu e agir rápido.

---

## 🚀 Funcionalidades Principais

### 🗺️ Monitoramento Visual
- **Dashboard em Tempo Real:** Visão geral de quantos dispositivos estão online/offline.
- **Mapa Interativo:** Localização exata das torres com indicadores de status (Verde/Vermelho).

### 🛠️ Gestão de Infraestrutura
- **Cadastro de Torres:** Organize sua rede por locais geográficos (Latitude/Longitude).
- **Gestão de Equipamentos:** Adicione rádios, switchs e roteadores, associando-os às torres.
- **Scanner de Rede:** Ferramenta poderosa que varre faixas de IP (ex: `192.168.0.0/24`), detecta dispositivos ativos e permite cadastrá-los com um clique.

### 🔔 Alertas e Automação
- **Monitoramento Contínuo:** O sistema "pinga" os equipamentos a cada 30 segundos automaticamente.
- **Integração com Telegram:** Receba notificações instantâneas no seu celular quando um equipamento cair ou voltar.

### 🔐 Segurança e Acesso
- **Controle de Acesso:** Sistema de login seguro com níveis de permissão.
- **Perfis:**
  - **Admin:** Acesso total, incluindo configurações do sistema e gestão de usuários.
  - **Técnico:** Acesso para visualização e operação do dia-a-dia.

---

## 🛠️ Tecnologias Utilizadas

### Backend (API)
- **Python 3.12+**
- **FastAPI:** Para uma API extremamente rápida e assíncrona.
- **SQLAlchemy (Async):** ORM moderno para interação com banco de dados.
- **APScheduler:** Para tarefas de monitoramento em segundo plano.
- **Ping3:** Para verificação de conectividade ICMP.

### Frontend
- **React + Vite:** Para uma interface ultra-rápida.
- **TailwindCSS v4:** Design moderno, responsivo e elegante (Dark Mode nativo).
- **Leaflet:** Mapas interativos e leves.
- **Lucide React:** Ícones belíssimos e consistentes.

---

## 💻 Como Rodar o Projeto

### Pré-requisitos
- Node.js atualizado
- Python 3.10 ou superior
- Git

### Passo a Passo

1. **Clone o repositório**
   ```bash
   git clone https://github.com/diegojlc22/isp-monitor.git
   cd isp-monitor
   ```

2. **Backend (Servidor)**
   ```bash
   # Crie e ative o ambiente virtual
   python -m venv venv
   .\venv\Scripts\activate # Windows
   
   # Instale as dependências
   pip install -r backend/requirements.txt
   
   # Inicie o servidor
   python -m uvicorn backend.app.main:app --reload --host 0.0.0.0
   ```
   _O backend rodará em `http://localhost:8000`_.

3. **Frontend (Interface)**
   ```bash
   cd frontend
   npm install
   npm run dev -- --host
   ```
   _Acesse a aplicação em `http://localhost:5173`_.

---

## 📱 Próximos Passos
- [ ] Criação do App Mobile para técnicos de campo.
- [ ] Histórico detalhado de uptime/downtime (SLA).
- [ ] Gráficos de latência.

---

Desenvolvido com 💙 por **Diego Lima**.
