# 🔄 COMO APLICAR AS ALTERAÇÕES

## ✅ **Build do Frontend Concluído!**

O frontend foi recompilado com sucesso. Agora você precisa **reiniciar o sistema** para ver as mudanças.

---

## 🚀 **PASSOS PARA REINICIAR:**

### **Opção 1: Usando o Launcher (Recomendado)**

1. **Feche** o navegador (se estiver aberto)
2. **Feche** o launcher atual (se estiver rodando)
3. **Execute** novamente: `launcher.pyw` ou `iniciar_sistema.bat`
4. **Aguarde** o sistema iniciar
5. **Abra** o navegador e acesse o painel
6. **Vá em Equipamentos** e veja a nova coluna "Status Wireless"!

---

### **Opção 2: Reiniciar Manualmente**

Se estiver rodando manualmente:

1. **Pare** o backend (Ctrl+C no terminal do Uvicorn)
2. **Inicie** novamente:
   ```bash
   cd c:\diegolima\isp-monitor
   .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
3. **Abra** o navegador em `http://localhost:8000`
4. **Vá em Equipamentos**

---

## 🔍 **O QUE VOCÊ VERÁ:**

Após reiniciar, na página de **Equipamentos**, você verá:

```
┌────────────────────────────────────────────────────────────────┐
│ ● │ Nome              │ IP            │ Status Wireless      │ Ações │
├────────────────────────────────────────────────────────────────┤
│ 🟢│ Transmissor Torre │ 192.168.47.35 │ 📶 Signal: -54 dBm  │ ...   │
│   │                   │               │ 📊 CCQ: 94%         │       │
│   │                   │               │ 👥 Clientes: 4      │       │
└────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ **IMPORTANTE:**

- ✅ O build do frontend já foi feito
- ✅ Os arquivos estão em `frontend/dist/`
- ⚠️ **Você PRECISA reiniciar** o sistema para ver as mudanças
- ⚠️ **Limpe o cache** do navegador se não aparecer (Ctrl+Shift+R)

---

## 🧪 **VERIFICAÇÃO:**

Após reiniciar, verifique:

1. ✅ Coluna "Status Wireless" aparece na tabela
2. ✅ Mostra Signal, CCQ e Clientes para equipamentos Ubiquiti
3. ✅ Número de clientes em **verde e negrito**
4. ✅ Dados atualizam a cada 60 segundos

---

## 📊 **ARQUIVOS ATUALIZADOS:**

```
✅ frontend/dist/assets/Equipments-DHi7PrDW.js (23.34 kB)
✅ frontend/dist/assets/index-RCKb34gq.js (287.35 kB)
✅ frontend/dist/index.html (0.47 kB)
```

---

## 🎯 **PRÓXIMOS PASSOS:**

1. **Reinicie** o sistema (launcher ou manualmente)
2. **Abra** o navegador
3. **Vá em Equipamentos**
4. **Veja** a nova coluna "Status Wireless"
5. **Confirme** que mostra os clientes conectados!

---

**Tudo pronto! Basta reiniciar!** 🚀
