# 🎨 INTERFACE GRÁFICA - ISP MONITOR LAUNCHER

**Versão:** 2.3  
**Tipo:** GUI moderna e intuitiva  
**Funcionalidades:** Iniciar, Parar, Reiniciar, Abrir Dashboard

---

## 🚀 COMO USAR

### Iniciar a Interface:

**Opção 1: Duplo clique**
```
LAUNCHER.bat
```

**Opção 2: Linha de comando**
```bash
python launcher.py
```

---

## 🎯 FUNCIONALIDADES

### ▶ INICIAR SISTEMA
- Inicia o ISP Monitor
- Abre em nova janela de terminal
- Verifica se iniciou corretamente
- Mostra mensagem de sucesso

### ⏹ PARAR SISTEMA
- Para o sistema gracefully
- Mata o processo na porta 8080
- Atualiza status automaticamente
- Confirma quando parado

### 🔄 REINICIAR SISTEMA
- Para o sistema atual
- Aguarda 2 segundos
- Inicia novamente
- Pede confirmação antes

### 🌐 ABRIR DASHBOARD
- Abre http://localhost:8080 no navegador
- Funciona mesmo se sistema não estiver rodando
- Atalho rápido para acessar

### 🔍 VERIFICAR STATUS
- Verifica se porta 8080 está em uso
- Mostra PID do processo
- Atualiza informações
- Habilita/desabilita botões

---

## 📊 INTERFACE

### Status do Sistema:
- **● RODANDO** (verde) - Sistema ativo
- **● PARADO** (vermelho) - Sistema inativo
- **● VERIFICANDO** (amarelo) - Checando status
- **● ERRO** (vermelho) - Problema detectado

### Informações Mostradas:
- Porta em uso (8080)
- PID do processo
- URL de acesso
- Mensagens de erro (se houver)

---

## 🎨 DESIGN

### Cores Modernas:
- **Background:** Escuro (#1e1e2e)
- **Texto:** Claro (#cdd6f4)
- **Accent:** Azul (#89b4fa)
- **Sucesso:** Verde (#a6e3a1)
- **Erro:** Vermelho (#f38ba8)
- **Aviso:** Amarelo (#f9e2af)

### Botões:
- **INICIAR** - Verde (sucesso)
- **PARAR** - Vermelho (erro)
- **REINICIAR** - Amarelo (aviso)
- **DASHBOARD** - Azul (accent)
- **VERIFICAR** - Cinza (neutro)

---

## ⚙️ REQUISITOS

### Dependências Python:
- `tkinter` (incluído no Python)
- `psutil` (já instalado)
- `subprocess` (incluído no Python)

### Sistema:
- Windows 10/11
- Python 3.11+
- Virtual environment (.venv)

---

## 🔧 TROUBLESHOOTING

### Interface não abre:
```bash
# Verificar se psutil está instalado
.venv\Scripts\pip install psutil

# Tentar novamente
python launcher.py
```

### Botões não funcionam:
- Verificar se `iniciar_postgres.bat` existe
- Verificar permissões de execução
- Executar como Administrador se necessário

### Status não atualiza:
- Clicar em "VERIFICAR STATUS"
- Aguardar alguns segundos
- Verificar se porta 8080 está livre

---

## 📝 ATALHOS

| Ação | Atalho |
|------|--------|
| Iniciar | Botão verde |
| Parar | Botão vermelho |
| Reiniciar | Botão amarelo |
| Dashboard | Botão azul |
| Verificar | Botão cinza |

---

## 🎉 VANTAGENS

✅ **Fácil de usar** - Interface intuitiva  
✅ **Visual moderno** - Design profissional  
✅ **Feedback visual** - Status em tempo real  
✅ **Seguro** - Confirmações antes de ações críticas  
✅ **Rápido** - Ações com um clique  
✅ **Informativo** - Mostra PID e porta  

---

## 📸 PREVIEW

```
┌─────────────────────────────────────────┐
│         🌐 ISP Monitor                  │
│                                         │
│  Status do Sistema:                     │
│  ● RODANDO                              │
│  Porta: 8080 | PID: 6360               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  ▶ INICIAR SISTEMA              │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  ⏹ PARAR SISTEMA                │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  🔄 REINICIAR SISTEMA           │   │
│  └─────────────────────────────────┘   │
│  ────────────────────────────────────  │
│  ┌─────────────────────────────────┐   │
│  │  🌐 ABRIR DASHBOARD             │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  🔍 VERIFICAR STATUS            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  v2.3 Ultra Otimizado | -50% CPU       │
└─────────────────────────────────────────┘
```

---

## 🚀 USO RECOMENDADO

### Desenvolvimento:
1. Abrir `LAUNCHER.bat`
2. Clicar em "INICIAR SISTEMA"
3. Trabalhar...
4. Clicar em "PARAR SISTEMA" quando terminar

### Produção:
1. Abrir `LAUNCHER.bat`
2. Clicar em "INICIAR SISTEMA"
3. Minimizar interface
4. Deixar rodando 24/7

---

**Criado:** 25/12/2024  
**Versão:** 2.3  
**Status:** ✅ Funcionando perfeitamente
