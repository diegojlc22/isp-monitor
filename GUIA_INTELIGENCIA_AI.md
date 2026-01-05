# 🤖 Guia Completo - Inteligência de Rede (AI)

## 📋 Como Funciona

O sistema possui **análises automáticas** que rodam em segundo plano para equipamentos prioritários:

### 1. 🔒 **Auditoria de Segurança**
**Arquivo:** `backend/app/services/security_audit.py`

**O que verifica:**
- ✅ Senhas padrão (ubnt/ubnt, admin/admin, etc.)
- ✅ Portas abertas perigosas (SSH 22, Telnet 23, HTTP 80)
- ✅ SNMP com community "public"
- ✅ Firmware desatualizado

**Recomendações geradas:**
- 🔐 Trocar senhas padrão
- 🚪 Fechar portas desnecessárias
- 🔒 Alterar SNMP community
- ⬆️ Atualizar firmware

---

### 2. 📊 **Planejamento de Capacidade**
**Arquivo:** `backend/app/services/capacity_planning.py`

**O que analisa:**
- ✅ Tráfego médio das últimas 24h
- ✅ Picos de utilização
- ✅ Tendência de crescimento (30 dias)
- ✅ Comparação com limites configurados

**Recomendações geradas:**
- 📈 Upgrade de link (quando >80% de uso)
- ⚖️ Balanceamento de carga
- 🔄 Redistribuição de clientes
- 📊 Monitoramento mais frequente

---

## 🧪 Como Testar (Passo a Passo)

### **Passo 1: Adicionar Equipamentos Prioritários**

**IMPORTANTE:** Não existe mais checkbox na página de Equipamentos!

**Forma correta:**
1. Acesse a aba **"Prioritários"** no menu lateral
2. Clique no botão **"+ Adicionar Prioritário"**
3. Selecione os equipamentos da lista
4. Clique em **"Selecionar"**

---

### **Passo 2: Configurar Limites de Tráfego**

1. Na aba **"Prioritários"**, localize o equipamento
2. Clique no ícone **⚙️** (Settings) ao lado do nome
3. Configure:
   - **Limite Download:** Ex: 60 Mbps
   - **Limite Upload:** Ex: 30 Mbps
4. Clique em **"Salvar"**

---

### **Passo 3: Aguardar Análise Automática**

As análises rodam automaticamente:
- **Auditoria de Segurança:** A cada 24 horas
- **Planejamento de Capacidade:** A cada 6 horas

**OU** você pode forçar a execução manualmente via API:

```bash
# Via curl (Windows PowerShell)
curl http://localhost:8080/api/insights/analyze -H "Authorization: Bearer SEU_TOKEN"
```

---

### **Passo 4: Visualizar Resultados**

1. Acesse a página **"Inteligência"** no menu
2. Você verá cards com as análises:
   - 🔒 **Segurança** (vermelho)
   - 📊 **Capacidade** (azul)
3. Cada card mostra:
   - Equipamento afetado
   - Problema detectado
   - Recomendação de ação
4. Após resolver, clique em **"Arquivar"**

---

## 📊 Exemplo de Insights Gerados

### **Segurança:**
```
🔒 Vulnerabilidade Detectada
Equipamento: TORRE-CENTRO
IP: 192.168.1.1

Problema: Porta SSH (22) aberta publicamente
Severidade: ALTA

Recomendação:
- Fechar porta SSH para internet
- Usar VPN para acesso remoto
- Configurar firewall
```

### **Capacidade:**
```
📊 Link Próximo da Saturação
Equipamento: LINK-PRINCIPAL
IP: 192.168.1.10

Problema: Tráfego médio em 85% da capacidade
Tendência: Crescimento de 15% ao mês

Recomendação:
- Upgrade de link de 100Mbps para 200Mbps
- Considerar balanceamento de carga
- Monitorar horários de pico (18h-22h)
```

---

## 🎯 Dashboard de Insights

No **Dashboard principal**, você verá:
- Card **"IA Insights"** com contador de análises pendentes
- Cor **âmbar** quando há insights não resolvidos
- Clique no card para ir direto para a página de Inteligência

---

## 🔧 Configurações Avançadas

### **Ajustar Frequência de Análise**
Edite os arquivos:
- `backend/app/services/security_audit.py` (linha ~200)
- `backend/app/services/capacity_planning.py` (linha ~240)

### **Personalizar Critérios**
- **Threshold de capacidade:** Linha 70-80 em `capacity_planning.py`
- **Portas perigosas:** Linha 60-70 em `security_audit.py`
- **Credenciais padrão:** Linha 16-23 em `security_audit.py`

---

## ❓ Troubleshooting

### **Não aparecem insights:**
1. Verifique se há equipamentos marcados como prioritários
2. Confirme que os equipamentos estão online
3. Verifique se há dados de tráfego (última coleta SNMP)
4. Cheque os logs: `logs/backend.log`

### **Insights duplicados:**
- O sistema evita duplicatas automaticamente
- Se aparecerem, arquive os antigos

### **Como resetar insights:**
```sql
-- Via PostgreSQL
DELETE FROM insights WHERE is_dismissed = true;
```

---

## 📈 Próximos Passos

Após configurar a Inteligência:
1. Configure alertas no Telegram/WhatsApp
2. Defina limites de tráfego para todos prioritários
3. Revise insights semanalmente
4. Arquive insights resolvidos

---

**Dúvidas?** Verifique os logs em `logs/backend.log` ou acesse a documentação completa no README.md
