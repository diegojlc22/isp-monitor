# 📱 Guia: Gerar APK com Android Studio

## ✅ Pré-requisitos
- Windows 10/11
- ~10GB de espaço livre
- Conexão com internet
- Paciência (primeira vez demora ~1-2 horas)

---

## 📥 Passo 1: Baixar Android Studio

1. **Acesse:** https://developer.android.com/studio
2. **Clique em:** "Download Android Studio"
3. **Aceite** os termos e condições
4. **Baixe** o instalador (~1GB)

**Arquivo baixado:** `android-studio-2024.x.x.x-windows.exe`

---

## 🔧 Passo 2: Instalar Android Studio

1. **Execute** o instalador baixado
2. **Clique em:** "Next" → "Next" → "Next"
3. **Escolha** a pasta de instalação (padrão: `C:\Program Files\Android\Android Studio`)
4. **Aguarde** a instalação (~5-10 minutos)
5. **Clique em:** "Finish"

### 2.1 Configuração Inicial

1. **Abra** o Android Studio
2. **Escolha:** "Do not import settings"
3. **Clique em:** "OK"
4. **Aguarde** o download de componentes
5. **Escolha:** "Standard" setup
6. **Escolha** o tema (claro ou escuro)
7. **Clique em:** "Next" → "Finish"

### 2.2 Instalar Android SDK

1. **Aguarde** o download do Android SDK (~2-3GB)
2. **Clique em:** "Finish" quando terminar

---

## ⚙️ Passo 3: Configurar Variáveis de Ambiente

### 3.1 Encontrar o caminho do Android SDK

1. **Abra** o Android Studio
2. **Clique em:** "More Actions" → "SDK Manager"
3. **Copie** o caminho que aparece em "Android SDK Location"
   - Exemplo: `C:\Users\DiegoLima\AppData\Local\Android\Sdk`

### 3.2 Adicionar às Variáveis de Ambiente

1. **Pressione:** `Win + R`
2. **Digite:** `sysdm.cpl` e pressione Enter
3. **Clique em:** "Variáveis de Ambiente"
4. **Em "Variáveis do sistema"**, clique em "Novo"
5. **Adicione:**
   - Nome: `ANDROID_HOME`
   - Valor: `C:\Users\DiegoLima\AppData\Local\Android\Sdk` (o caminho que você copiou)
6. **Clique em:** "OK"

### 3.3 Adicionar ao PATH

1. **Ainda em "Variáveis do sistema"**, selecione "Path"
2. **Clique em:** "Editar"
3. **Clique em:** "Novo"
4. **Adicione:** `%ANDROID_HOME%\platform-tools`
5. **Clique em:** "Novo" novamente
6. **Adicione:** `%ANDROID_HOME%\tools`
7. **Clique em:** "OK" → "OK" → "OK"

### 3.4 Verificar Instalação

1. **Abra** um novo PowerShell (importante: NOVO terminal)
2. **Digite:**
   ```bash
   adb --version
   ```
3. **Deve aparecer:** `Android Debug Bridge version x.x.x`

Se não aparecer, **reinicie o PC** e tente novamente.

---

## 🏗️ Passo 4: Preparar o Projeto

### 4.1 Executar Prebuild

1. **Abra** o PowerShell
2. **Navegue** até a pasta do projeto:
   ```bash
   cd C:\Users\DiegoLima\.gemini\antigravity\scratch\isp_monitor\mobile
   ```
3. **Execute:**
   ```bash
   npx expo prebuild --platform android
   ```
4. **Aguarde** (~2-3 minutos)
5. **Deve criar** a pasta `android/`

### 4.2 Verificar Estrutura

Você deve ter agora:
```
mobile/
├── android/          ← Nova pasta criada
│   ├── app/
│   ├── gradle/
│   └── build.gradle
├── app/
├── assets/
└── package.json
```

---

## 📦 Passo 5: Gerar o APK

### 5.1 Navegar para a pasta Android

```bash
cd android
```

### 5.2 Executar o Build

**Windows PowerShell:**
```bash
.\gradlew assembleRelease
```

**Ou, se der erro:**
```bash
.\gradlew.bat assembleRelease
```

### 5.3 Aguardar o Build

- ⏱️ **Primeira vez:** 10-15 minutos
- ⏱️ **Próximas vezes:** 3-5 minutos

Você verá:
```
> Task :app:assembleRelease
BUILD SUCCESSFUL in 12m 34s
```

---

## 🎉 Passo 6: Localizar o APK

O APK estará em:
```
mobile\android\app\build\outputs\apk\release\app-release.apk
```

**Tamanho esperado:** ~50-80MB

---

## 📲 Passo 7: Instalar no Celular

### Método 1: USB

1. **Conecte** o celular no PC via USB
2. **Ative** "Depuração USB" no celular:
   - Configurações → Sobre o telefone
   - Toque 7x em "Número da versão"
   - Volte → Opções do desenvolvedor
   - Ative "Depuração USB"
3. **Copie** o APK para o celular
4. **Abra** o APK no celular
5. **Permita** "Instalar de fontes desconhecidas"
6. **Instale!**

### Método 2: WhatsApp/Email

1. **Envie** o APK para você mesmo via WhatsApp ou Email
2. **Abra** no celular
3. **Baixe** o arquivo
4. **Instale!**

---

## 🔧 Solução de Problemas

### Erro: "ANDROID_HOME not set"
- Reinicie o PC
- Verifique se adicionou corretamente nas variáveis de ambiente

### Erro: "SDK location not found"
- Abra Android Studio
- Vá em SDK Manager
- Instale Android SDK 33 (API 33)

### Erro: "Gradle build failed"
- Verifique se tem Java instalado: `java -version`
- Se não tiver, Android Studio instala automaticamente
- Tente novamente

### APK não instala no celular
- Verifique se permitiu "Fontes desconhecidas"
- Tente desinstalar versão antiga primeiro
- Verifique se o celular é Android 8.0+

---

## 📝 Comandos Resumidos

```bash
# 1. Prebuild
cd C:\Users\DiegoLima\.gemini\antigravity\scratch\isp_monitor\mobile
npx expo prebuild --platform android

# 2. Build APK
cd android
.\gradlew assembleRelease

# 3. Localizar APK
cd app\build\outputs\apk\release
dir
```

---

## 🎯 Próximas Vezes

Depois da primeira vez, para gerar um novo APK:

```bash
cd mobile\android
.\gradlew clean
.\gradlew assembleRelease
```

Pronto! APK atualizado em ~3-5 minutos.

---

## 🚀 Dicas

- **Primeira vez demora:** É normal, muitos downloads
- **Mantenha Android Studio atualizado:** Ajuda a evitar erros
- **Limpe antes de buildar:** `.\gradlew clean` evita problemas
- **Teste no Expo Go primeiro:** Sempre teste antes de gerar APK

---

## 📞 Suporte

Se tiver algum erro:
1. Copie a mensagem de erro completa
2. Me envie
3. Eu te ajudo a resolver!

**Boa sorte!** 🍀
