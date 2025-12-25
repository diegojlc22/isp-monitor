# 📱 Guia de Build do APK - ISP Monitor

## ✅ Otimizações Implementadas

### 🔋 Economia de Bateria
- **GPS Inteligente**: Só atualiza ao mover >50m
- **Intervalo de 30s**: Verifica localização a cada 30s (não fica ativo o tempo todo)
- **Precisão Balanceada**: Equilíbrio entre precisão e consumo
- **Envio Condicional**: Só envia se houver mudança significativa

### ⚡ Responsividade
- **Feedback Visual**: Indicadores de status em tempo real
- **Timestamp**: Mostra quando foi a última atualização
- **Loading States**: Indicadores visuais em todas as ações
- **Retry Automático**: Reenvio silencioso em caso de falha

### 🎯 Confiabilidade
- **Tratamento de Erros**: Try/catch em todas as operações
- **Validações**: Verifica dados antes de usar
- **Cleanup**: Remove listeners ao desmontar

### 🆕 Novas Funcionalidades
- **Tela de Configurações**: Com botão de atualização OTA
- **Informações do App**: Versão, build, perfil do usuário
- **Botão de Logout**: Com confirmação

---

## 🧪 Teste no Expo Go (Desenvolvimento)

1. **Recarregue o app** no celular:
   ```
   Agite o celular → Reload
   ```

2. **Teste as funcionalidades**:
   - ✅ Login funciona
   - ✅ Dashboard mostra torres próximas
   - ✅ Mapa abre com OpenStreetMap
   - ✅ Localização é enviada automaticamente
   - ✅ Botão de atualização manual funciona
   - ✅ Tela de configurações abre

3. **Verifique no admin (PC)**:
   - Abra `http://localhost:8080`
   - Vá em "Mapa em Tempo Real"
   - Você deve ver o marcador azul do técnico

---

## 📦 Gerar APK (Produção)

### Pré-requisitos
1. **Instalar EAS CLI**:
   ```bash
   npm install -g eas-cli
   ```

2. **Fazer login no Expo**:
   ```bash
   eas login
   ```
   (Se não tiver conta, crie em https://expo.dev)

### Gerar o APK

1. **Navegar para a pasta mobile**:
   ```bash
   cd mobile
   ```

2. **Configurar o projeto** (primeira vez):
   ```bash
   eas build:configure
   ```

3. **Gerar o APK**:
   ```bash
   eas build --platform android --profile preview
   ```

4. **Aguardar o build** (10-20 minutos):
   - O build é feito na nuvem do Expo
   - Você receberá um link para download do APK
   - Baixe o arquivo `.apk`

5. **Instalar no celular**:
   - Transfira o APK para o celular
   - Abra o arquivo e instale
   - Pode precisar permitir "Instalar de fontes desconhecidas"

---

## 🔄 Atualizações OTA (Over-The-Air)

Após gerar o APK, você pode fazer atualizações **sem precisar gerar um novo APK**:

1. **Fazer mudanças no código** (ex: corrigir bug, mudar texto)

2. **Publicar atualização**:
   ```bash
   eas update --branch production --message "Correção de bugs"
   ```

3. **No app**: O usuário abre o app → vai em "Configurações" → "Verificar Atualizações" → Atualiza automaticamente!

**Limitações do OTA:**
- ✅ Pode atualizar: JavaScript, assets, estilos
- ❌ NÃO pode atualizar: Dependências nativas, configurações do app.json

---

## 🚀 Publicar na Play Store (Opcional)

Se quiser publicar oficialmente:

1. **Gerar AAB** (Android App Bundle):
   ```bash
   eas build --platform android --profile production
   ```

2. **Criar conta de desenvolvedor** na Play Store ($25 uma vez)

3. **Upload do AAB** no Play Console

4. **Preencher informações** (descrição, screenshots, etc.)

5. **Publicar!**

---

## 📝 Checklist Final

Antes de gerar o APK, verifique:

- [ ] App funciona no Expo Go
- [ ] Localização está sendo enviada
- [ ] Técnico aparece no mapa do admin
- [ ] Todas as telas abrem sem erro
- [ ] Botão de logout funciona
- [ ] Mapa mostra torres corretamente

---

## 🆘 Problemas Comuns

### "Erro ao verificar atualizações"
- Normal no Expo Go (modo DEV)
- Funciona apenas no APK de produção

### "GPS não funciona"
- Verifique se deu permissão de localização
- Teste ao ar livre (GPS precisa de sinal)

### "Não conecta no backend"
- Verifique se o ngrok está rodando
- Confirme a URL no `services/api.js`

---

## 📞 Suporte

Qualquer dúvida, me avise! 🚀
