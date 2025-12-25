# ✅ GUIA RÁPIDO - TESTAR SPRINT 1

**Tempo estimado:** 2-3 minutos

---

## 🚀 PASSO 1: Reiniciar Sistema

```bash
# Fechar sistema atual (se estiver rodando)
# Pressione Ctrl+C no terminal

# Iniciar novamente
iniciar_postgres.bat
```

**O que observar:**
- ✅ Sistema inicia sem erros
- ✅ Mensagem: "Iniciando ISP Monitor com POSTGRESQL"
- ✅ Sem erros de import ou sintaxe

---

## 🔍 PASSO 2: Verificar Dashboard

1. Abrir navegador: http://localhost:8080
2. Fazer login
3. Observar tempo de carregamento

**Esperado:**
- ✅ Dashboard carrega em <1s (antes: ~2-3s)
- ✅ Lista de equipamentos rápida
- ✅ Alertas aparecem instantaneamente

---

## 📊 PASSO 3: Testar Endpoints (Opcional)

Abrir outro terminal:

```bash
# Testar latency history (com paginação)
curl "http://localhost:8080/api/equipments/1/latency-history?hours=2&limit=100"

# Deve retornar JSON com:
# - "data": [...]
# - "count": número
# - "hours": 2
# - "limit": 100
# - "truncated": true/false
```

---

## ✅ VALIDAÇÃO RÁPIDA

- [ ] Sistema rodando sem erros
- [ ] Dashboard carrega rápido
- [ ] Sem erros no console do navegador
- [ ] CPU estável (~40-50%)

**Se tudo OK:** Sprint 1 validado! ✅

**Se houver erro:** Verificar logs e reportar

---

**Próximo:** Sprint 2 (intervalo dinâmico + concorrência adaptativa)
