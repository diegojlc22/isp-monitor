# ISP Monitor - Launcher v2.4

## 🎯 Novidade: Modo Silencioso

### O que mudou?

Agora quando você executa o `LAUNCHER.bat`, o sistema inicia **completamente em segundo plano**, sem mostrar a janela do CMD do PostgreSQL/Uvicorn.

### Benefícios

✅ **Interface mais limpa** - Apenas o launcher fica visível  
✅ **Menos confusão** - Não há mais múltiplas janelas abertas  
✅ **Mais profissional** - O sistema roda silenciosamente em background  
✅ **Mesma funcionalidade** - Tudo continua funcionando normalmente  

### Como funciona?

O launcher agora usa a flag `CREATE_NO_WINDOW` (0x08000000) do Windows para iniciar o processo do servidor sem criar uma janela de console visível. O processo continua rodando normalmente em segundo plano.

### Mudanças técnicas

1. **launcher.py** e **launcher.pyw**:
   - Alterado de `CREATE_NEW_CONSOLE` para `CREATE_NO_WINDOW`
   - Adicionado redirecionamento de stdout/stderr para DEVNULL
   - Removido botão "Minimizar Console" (não é mais necessário)
   - Atualizado para versão 2.4

2. **Tamanho da janela**:
   - Reduzido de 700px para 650px (após remover botão desnecessário)

### Como usar?

1. Execute `LAUNCHER.bat` normalmente
2. Clique em "▶ INICIAR SISTEMA"
3. Aguarde a confirmação
4. Use o botão "🌐 ABRIR NO NAVEGADOR" para acessar o sistema

**Pronto!** Apenas a interface do launcher ficará visível. O servidor roda silenciosamente em segundo plano.

### Verificando se está rodando

Use o botão "🔍 VERIFICAR STATUS" no launcher para confirmar que o sistema está ativo.

---

**Versão**: 2.4  
**Data**: 25/12/2024  
**Autor**: Diego Lima
