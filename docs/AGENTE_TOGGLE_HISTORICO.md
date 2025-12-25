# Agente IA - Botão para Ocultar Histórico

## 🎯 Nova Funcionalidade

Adicionado um **botão toggle** ao lado do título "Últimos Testes Sintéticos" na página do Agente IA.

## ✨ Como funciona

- **Ícone de seta para cima** (ChevronUp): Indica que o histórico está visível. Clique para ocultar.
- **Ícone de seta para baixo** (ChevronDown): Indica que o histórico está oculto. Clique para mostrar.

## 🎨 Design

- Botão com hover suave (muda de cinza para branco)
- Ícone animado que muda conforme o estado
- Tooltip informativo ao passar o mouse
- Integrado de forma limpa ao lado do título

## 📝 Mudanças técnicas

1. **Novo estado**: `showLogs` (padrão: `true`)
2. **Novos ícones**: `ChevronDown` e `ChevronUp` do lucide-react
3. **Renderização condicional**: A tabela só é renderizada quando `showLogs === true`

## 🚀 Benefícios

✅ **Economia de espaço** - Oculte o histórico quando não precisar dele  
✅ **Interface mais limpa** - Foco nos cards de resumo quando necessário  
✅ **UX melhorada** - Controle total sobre o que visualizar  
✅ **Performance** - Menos elementos renderizados quando oculto  

---

**Versão**: 1.0  
**Data**: 25/12/2024  
**Arquivo**: `frontend/src/pages/Agent.tsx`
