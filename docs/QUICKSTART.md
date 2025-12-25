# 🚀 Como Iniciar o ISP Monitor

## Método Rápido (Recomendado)

### Windows
```bash
python start.py
```

### Linux/Mac
```bash
python3 start.py
```

---

## O que o script faz?

✅ Verifica se Python e Node.js estão instalados  
✅ Abre o **Backend** em uma janela separada (porta 8000)  
✅ Abre o **Frontend** em outra janela separada (porta 5173)  
✅ Mostra os links de acesso

---

## Acessar o Sistema

Após executar `python start.py`, acesse:

- **🌐 Aplicação Web**: http://localhost:5173
- **📡 API Backend**: http://localhost:8000
- **📚 Documentação da API**: http://localhost:8000/docs

---

## Parar os Serviços

Feche as janelas que foram abertas ou pressione `CTRL+C` em cada uma.

---

## Método Manual (Alternativo)

Se preferir iniciar manualmente:

### 1. Backend
```bash
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend (em outro terminal)
```bash
cd frontend
npm run dev -- --host
```

---

## Requisitos

- **Python 3.9+** (com `requests` instalado: `pip install requests`)
- **Node.js 16+**
- Dependências instaladas:
  - Backend: `pip install -r backend/requirements.txt`
  - Frontend: `cd frontend && npm install`
