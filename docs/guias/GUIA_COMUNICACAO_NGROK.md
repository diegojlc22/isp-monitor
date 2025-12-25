# 🌐 Guia: Garantir Comunicação Servidor ↔️ App Mobile

## 🎯 Objetivo

Manter o servidor local **sempre acessível** para o app mobile, mesmo sem IP público.

---

## ✅ Solução: Ngrok com Domínio Fixo

### **Por que Ngrok?**

**Problema:**
- 💻 Servidor no seu PC (sem IP público)
- 📱 App precisa acessar de qualquer lugar
- 🌍 Técnicos em diferentes redes (4G, Wi-Fi, etc.)

**Solução:**
```
App Mobile → Ngrok (IP público) → Seu PC
```

**Vantagens:**
- ✅ Funciona de qualquer lugar
- ✅ HTTPS grátis (seguro)
- ✅ URL fixa (não muda)
- ✅ Fácil de configurar

---

## 🔧 Como Funciona

### **1. Ngrok Cria um Túnel**

```
┌─────────────────────────────────────┐
│  🌍 Internet                        │
│                                     │
│  https://uniconoclastic-addedly-   │
│  yareli.ngrok-free.dev             │
│                                     │
│  (IP Público do Ngrok)             │
└──────────────┬──────────────────────┘
               │
               │ Túnel Seguro
               │
┌──────────────▼──────────────────────┐
│  💻 Seu PC (Sem IP Público)         │
│                                     │
│  http://localhost:8080              │
│                                     │
│  Backend + PostgreSQL               │
└─────────────────────────────────────┘
```

### **2. App Se Conecta ao Ngrok**

```javascript
// mobile/services/api.js
const API_URL = 'https://uniconoclastic-addedly-yareli.ngrok-free.dev';

// Todas as requisições vão para o Ngrok
// Ngrok encaminha para localhost:8080
```

---

## 🚀 Configuração Atual (Já Está Pronto!)

### **✅ Você já tem:**

1. **Domínio Fixo Configurado:**
   ```
   https://uniconoclastic-addedly-yareli.ngrok-free.dev
   ```

2. **Ngrok Rodando:**
   ```bash
   .\ngrok.exe http --domain=uniconoclastic-addedly-yareli.ngrok-free.dev 8080
   ```

3. **App Configurado:**
   ```javascript
   // mobile/services/api.js
   const API_URL = 'https://uniconoclastic-addedly-yareli.ngrok-free.dev';
   ```

**Está tudo funcionando!** ✅

---

## 🔒 Como Garantir Comunicação Sempre Ativa

### **Opção 1: Iniciar Automaticamente com Windows**

**Passo 1:** Execute o script (como Administrador):
```powershell
.\scripts\setup\configurar_ngrok_auto.ps1
```

**Passo 2:** Pronto! Ngrok vai iniciar automaticamente quando o Windows ligar.

**Vantagens:**
- ✅ Nunca esquece de iniciar
- ✅ Sempre disponível
- ✅ Roda em background

---

### **Opção 2: Usar o Launcher (Atual)**

**Passo 1:** Duplo clique em `LAUNCHER.bat`

**Passo 2:** Deixe rodando

**Vantagens:**
- ✅ Controle manual
- ✅ Fácil de parar/reiniciar
- ✅ Vê o status em tempo real

---

### **Opção 3: Manter Terminal Aberto**

**Passo 1:** Abra PowerShell

**Passo 2:** Execute:
```bash
cd tools\ngrok
.\ngrok.exe http --domain=uniconoclastic-addedly-yareli.ngrok-free.dev 8080
```

**Passo 3:** Minimize (não feche!)

**Vantagens:**
- ✅ Simples
- ✅ Vê logs em tempo real

---

## 🔍 Verificar se Está Funcionando

### **Método 1: Script de Verificação**

```powershell
.\scripts\setup\verificar_ngrok.ps1
```

**Vai mostrar:**
- ✅ Se Ngrok está rodando
- ✅ Se servidor está acessível
- ✅ Tempo que está rodando

---

### **Método 2: Testar no Navegador**

Abra no navegador:
```
https://uniconoclastic-addedly-yareli.ngrok-free.dev/api/health
```

**Deve aparecer:**
```json
{"status": "ok"}
```

---

### **Método 3: Testar no App**

1. Abra o app no celular
2. Tente fazer login
3. Se funcionar = Ngrok está OK! ✅

---

## ⚠️ Possíveis Problemas e Soluções

### **Problema 1: "Ngrok não está rodando"**

**Solução:**
```bash
# Inicie o Ngrok:
.\tools\ngrok\ngrok.exe http --domain=uniconoclastic-addedly-yareli.ngrok-free.dev 8080
```

---

### **Problema 2: "App não conecta"**

**Verificar:**
1. ✅ Ngrok está rodando?
2. ✅ Backend está rodando?
3. ✅ URL no app está correta?

**Solução:**
```bash
# Reinicie tudo:
.\LAUNCHER.bat
```

---

### **Problema 3: "Conexão lenta"**

**Causa:** Ngrok grátis tem limite de velocidade

**Soluções:**
- ✅ Usar Ngrok pago ($8/mês)
- ✅ Migrar para servidor dedicado
- ✅ Aceitar a velocidade (geralmente OK)

---

### **Problema 4: "Ngrok fechou sozinho"**

**Causa:** PC foi reiniciado ou terminal fechado

**Solução:**
- ✅ Configure inicialização automática (Opção 1)
- ✅ Ou sempre use o Launcher

---

## 📊 Monitoramento em Tempo Real

### **Dashboard do Ngrok:**

Acesse: http://localhost:4040

**Você vai ver:**
- 📊 Requisições em tempo real
- 🔍 Detalhes de cada chamada
- ⏱️ Tempo de resposta
- 📈 Gráficos de uso

---

## 🎯 Checklist de Funcionamento

Antes de distribuir o app, verifique:

- [ ] Ngrok está rodando
- [ ] Backend está rodando
- [ ] PostgreSQL está rodando
- [ ] URL do app está correta
- [ ] Teste no navegador funciona
- [ ] Teste no app funciona

---

## 🚀 Melhorias Futuras

### **Opção 1: Servidor Dedicado (Recomendado para Produção)**

**Vantagens:**
- ✅ Sempre online (24/7)
- ✅ Mais rápido
- ✅ Sem limites
- ✅ IP fixo próprio

**Custo:** ~R$20-50/mês

**Quando migrar:**
- Quando tiver muitos técnicos (>10)
- Quando precisar de 100% uptime
- Quando quiser profissionalizar

---

### **Opção 2: Ngrok Pago**

**Plano Pro:** $8/mês

**Vantagens:**
- ✅ Sem banner
- ✅ Mais conexões simultâneas
- ✅ Múltiplos túneis
- ✅ Suporte

---

## 📝 Resumo

### **Como está agora:**

```
✅ Servidor local (seu PC)
✅ Ngrok com domínio fixo
✅ App configurado para usar Ngrok
✅ Funciona de qualquer lugar
```

### **Para garantir sempre funcionando:**

1. **Opção Automática:**
   - Execute: `.\scripts\setup\configurar_ngrok_auto.ps1`
   - Ngrok inicia com Windows

2. **Opção Manual:**
   - Use: `LAUNCHER.bat`
   - Deixe rodando

3. **Verificar:**
   - Execute: `.\scripts\setup\verificar_ngrok.ps1`
   - Ou teste no navegador

---

## 🎉 Conclusão

**Ngrok é a solução PERFEITA para o seu caso!**

- ✅ Servidor local sem IP público
- ✅ App acessa de qualquer lugar
- ✅ Fácil de configurar
- ✅ Grátis (para começar)
- ✅ Seguro (HTTPS)

**Está tudo configurado e funcionando!** 🚀

---

**Última atualização:** 25/12/2024
