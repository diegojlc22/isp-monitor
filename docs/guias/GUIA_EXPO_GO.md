# 📱 Guia: Usar e Compartilhar App via Expo Go

## ✅ Sistema 100% Funcional no Expo Go!

O app ISP Monitor está completamente operacional via Expo Go. Este guia mostra como usar e compartilhar com sua equipe.

---

## 🚀 Como Iniciar o App

### **No PC:**

1. **Abra o PowerShell** na pasta do projeto
2. **Execute:**
   ```bash
   cd mobile
   npx expo start
   ```
3. **Aguarde** aparecer o QR code

### **No Celular:**

1. **Instale o Expo Go:**
   - Android: https://play.google.com/store/apps/details?id=host.exp.exponent
   - iOS: https://apps.apple.com/app/expo-go/id982107779

2. **Abra o Expo Go**
3. **Escaneie o QR code** que apareceu no PC
4. **Aguarde** o app carregar (~10-30 segundos)
5. **Pronto!** Faça login e use normalmente

---

## 👥 Como Compartilhar com Outros Técnicos

### **Método 1: QR Code (Mesma Rede Wi-Fi)**

**Vantagens:**
- ✅ Mais rápido
- ✅ Não precisa de internet

**Como fazer:**
1. Técnico e você na **mesma rede Wi-Fi**
2. Mostre o QR code para ele escanear
3. Pronto!

---

### **Método 2: Link Expo (Qualquer Lugar)**

**Vantagens:**
- ✅ Funciona de qualquer lugar
- ✅ Pode enviar por WhatsApp/Email

**Como fazer:**

1. **Publique o app:**
   ```bash
   cd mobile
   npx expo publish
   ```

2. **Copie o link** que aparece (exemplo):
   ```
   exp://exp.host/@diegojlc22/isp-monitor
   ```

3. **Envie para o técnico** via WhatsApp/Email

4. **Técnico abre o link** no celular
   - Android: Abre automaticamente no Expo Go
   - iOS: Copia o link e cola no Expo Go

---

### **Método 3: Tunnel (Sem Mesma Rede)**

**Vantagens:**
- ✅ QR code funciona de qualquer lugar
- ✅ Não precisa publicar

**Como fazer:**

1. **Inicie com tunnel:**
   ```bash
   cd mobile
   npx expo start --tunnel
   ```

2. **Aguarde** o QR code aparecer
3. **Mostre para o técnico** escanear
4. **Funciona de qualquer lugar!**

---

## 🔐 Credenciais de Acesso

**Para os técnicos testarem:**

**Admin (você):**
- Email: `diegojlc22@gmail.com`
- Senha: `110812`

**Criar conta para técnico:**
1. Acesse o Admin Panel: `http://localhost:8080`
2. Vá em "Usuários"
3. Clique em "Adicionar Usuário"
4. Preencha:
   - Nome: Nome do técnico
   - Email: email@exemplo.com
   - Senha: senha123
   - Função: Técnico
5. Envie as credenciais para o técnico

---

## 📊 Funcionalidades do App

### **Dashboard**
- 🗼 Torres próximas (raio de 50km)
- 📍 Distância até cada torre
- 📡 Quantidade de painéis e clientes
- 🔄 Atualização automática

### **Mapa**
- 🗺️ Visualizar torres no mapa
- 📍 Sua localização em tempo real
- 🔄 Botão de atualização manual

### **Rastreamento Automático**
- ✅ Envia localização a cada 60s
- ✅ Só envia se mover >50m (economia de bateria)
- ✅ Aparece no mapa do admin em tempo real

### **Adicionar Torre**
- ➕ Solicitar nova torre
- 📝 Preencher dados
- 📤 Enviar para aprovação

### **Configurações**
- 👤 Ver perfil
- 🚪 Fazer logout

---

## 🔋 Dicas de Uso

### **Economia de Bateria:**
- ✅ O app já está otimizado
- ✅ GPS só ativa quando necessário
- ✅ Envio condicional de localização

### **Melhor Performance:**
- ✅ Use Wi-Fi quando possível
- ✅ Mantenha o Expo Go atualizado
- ✅ Feche outros apps pesados

### **Se o App Travar:**
1. Agite o celular
2. Clique em "Reload"
3. Ou feche e abra novamente

---

## 🌐 Acessar de Qualquer Lugar

**URL Pública (Ngrok):**
```
https://uniconoclastic-addedly-yareli.ngrok-free.dev
```

**Admin Panel:**
- Acesse de qualquer navegador
- Faça login
- Veja técnicos no mapa em tempo real

**⚠️ Importante:** O ngrok precisa estar rodando no PC!

---

## 🔧 Solução de Problemas

### **"Não consegue conectar"**
- ✅ Verifique se está na mesma rede Wi-Fi
- ✅ Tente o método "Tunnel"
- ✅ Ou publique com `expo publish`

### **"App não carrega"**
- ✅ Verifique sua internet
- ✅ Reinicie o Expo Go
- ✅ Limpe o cache: Agite → "Clear cache"

### **"Localização não funciona"**
- ✅ Dê permissão de localização ao Expo Go
- ✅ Ative o GPS do celular
- ✅ Teste ao ar livre

### **"Não aparece no mapa do admin"**
- ✅ Aguarde 30s (atualização automática)
- ✅ Pressione F5 no navegador
- ✅ Verifique se está logado no app

---

## 📝 Comandos Úteis

### **Iniciar o app:**
```bash
cd mobile
npx expo start
```

### **Publicar atualização:**
```bash
cd mobile
npx expo publish
```

### **Limpar cache:**
```bash
cd mobile
npx expo start --clear
```

### **Modo tunnel:**
```bash
cd mobile
npx expo start --tunnel
```

---

## 🎯 Próximos Passos

### **Quando quiser gerar APK:**
1. Aguarde Expo SDK 55 (Janeiro/2026)
2. Execute: `eas build --platform android`
3. Baixe o APK
4. Distribua para os técnicos

### **Melhorias Futuras:**
- 📊 Histórico de localização
- 🔔 Notificações push
- 📸 Fotos de torres
- 📝 Relatórios de visita

---

## 📞 Suporte

**Problemas? Dúvidas?**
- 📧 Email: diegojlc22@gmail.com
- 📱 WhatsApp: Envie o link do app
- 🐛 Reporte bugs: Descreva o problema

---

## 🎉 Resumo

**O que você tem:**
- ✅ App mobile 100% funcional
- ✅ Rastreamento GPS otimizado
- ✅ Admin panel em tempo real
- ✅ Fácil de compartilhar

**Como usar:**
1. Inicie: `npx expo start`
2. Escaneie QR code
3. Use normalmente!

**Como compartilhar:**
1. Publique: `npx expo publish`
2. Envie o link
3. Técnico abre no Expo Go!

---

**Aproveite o sistema! Está tudo funcionando perfeitamente!** 🚀
