# 📱 Guia Completo - APK para Técnicos

## 🎯 Objetivo

Criar um aplicativo Android para técnicos de campo visualizarem e gerenciarem equipamentos em tempo real.

---

## 📋 Funcionalidades do APK

### 1. **Autenticação**
- Login com email e senha
- Token JWT para autenticação
- Perfil de usuário (admin/técnico)

### 2. **Dashboard**
- Estatísticas em tempo real
- Torres online/offline
- Equipamentos online/offline
- Alertas recentes

### 3. **Lista de Equipamentos**
- Ver todos equipamentos
- Filtrar por status (online/offline)
- Filtrar por torre
- Buscar por nome/IP

### 4. **Detalhes do Equipamento**
- Nome, IP, Status
- Última verificação
- Latência atual
- Histórico de latência (gráfico)
- Torre associada

### 5. **Ações**
- **Reboot remoto** (SSH)
- Ver localização no mapa
- Ver histórico de eventos

### 6. **Mapa**
- Ver torres no mapa
- Ver equipamentos por torre
- Filtrar por status
- Navegação GPS até o local

### 7. **Notificações Push** (Futuro)
- Alertas de equipamentos offline
- Alertas de latência alta

---

## 🔌 API Backend

### Base URL
```
http://SEU_SERVIDOR:8000
```

### Autenticação
Todas as requisições (exceto login) precisam do header:
```
Authorization: Bearer {TOKEN}
```

---

## 📡 Endpoints da API

### 1. **Autenticação**

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "tecnico@empresa.com",
  "password": "senha123"
}
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "João Técnico",
    "email": "tecnico@empresa.com",
    "role": "tecnico"
  }
}
```

#### Perfil do Usuário
```http
GET /auth/me
Authorization: Bearer {TOKEN}
```

**Resposta:**
```json
{
  "id": 1,
  "name": "João Técnico",
  "email": "tecnico@empresa.com",
  "role": "tecnico"
}
```

---

### 2. **Torres**

#### Listar Torres
```http
GET /towers/
Authorization: Bearer {TOKEN}
```

**Resposta:**
```json
[
  {
    "id": 1,
    "name": "Torre Centro",
    "ip": "192.168.1.1",
    "latitude": -23.550520,
    "longitude": -46.633308,
    "observations": "Torre principal",
    "is_online": true,
    "last_checked": "2024-12-21T17:30:00Z"
  }
]
```

#### Detalhes de uma Torre
```http
GET /towers/{tower_id}
Authorization: Bearer {TOKEN}
```

---

### 3. **Equipamentos**

#### Listar Equipamentos
```http
GET /equipments/
Authorization: Bearer {TOKEN}
```

**Resposta:**
```json
[
  {
    "id": 1,
    "name": "AP Setor A",
    "ip": "192.168.1.10",
    "tower_id": 1,
    "is_online": true,
    "last_checked": "2024-12-21T17:30:00Z",
    "last_latency": 25,
    "ssh_user": "admin",
    "ssh_port": 22
  }
]
```

#### Detalhes de um Equipamento
```http
GET /equipments/{equipment_id}
Authorization: Bearer {TOKEN}
```

#### Histórico de Latência
```http
GET /equipments/{equipment_id}/latency-history?hours=24
Authorization: Bearer {TOKEN}
```

**Resposta:**
```json
[
  {
    "timestamp": "2024-12-21T17:00:00Z",
    "latency_ms": 25,
    "status": "online"
  },
  {
    "timestamp": "2024-12-21T17:05:00Z",
    "latency_ms": 30,
    "status": "online"
  }
]
```

#### Reboot de Equipamento
```http
POST /equipments/{equipment_id}/reboot
Authorization: Bearer {TOKEN}
```

**Resposta:**
```json
{
  "success": true,
  "message": "✅ Reboot command sent successfully"
}
```

---

### 4. **Dashboard**

#### Estatísticas
```http
GET /equipments/
GET /towers/
Authorization: Bearer {TOKEN}
```

Processar no app:
- Total de torres
- Torres online/offline
- Total de equipamentos
- Equipamentos online/offline

---

## 🛠️ Stack Recomendada para APK

### **Opção 1: React Native** (Recomendado)
- ✅ Reutiliza conhecimento de React
- ✅ Desenvolvimento rápido
- ✅ Cross-platform (Android + iOS)
- ✅ Comunidade grande

**Bibliotecas:**
```json
{
  "react-native": "^0.72.0",
  "react-navigation": "^6.0.0",
  "axios": "^1.5.0",
  "react-native-maps": "^1.7.0",
  "react-native-chart-kit": "^6.12.0",
  "@react-native-async-storage/async-storage": "^1.19.0"
}
```

### **Opção 2: Flutter**
- ✅ Performance nativa
- ✅ UI bonita
- ✅ Cross-platform

### **Opção 3: Kotlin (Android Nativo)**
- ✅ Performance máxima
- ⚠️ Apenas Android
- ⚠️ Desenvolvimento mais lento

---

## 📱 Estrutura do APK

```
app/
├── screens/
│   ├── LoginScreen.tsx
│   ├── DashboardScreen.tsx
│   ├── EquipmentsListScreen.tsx
│   ├── EquipmentDetailScreen.tsx
│   ├── MapScreen.tsx
│   └── ProfileScreen.tsx
├── services/
│   ├── api.ts              # Cliente HTTP
│   ├── auth.ts             # Autenticação
│   └── storage.ts          # AsyncStorage
├── components/
│   ├── EquipmentCard.tsx
│   ├── StatusBadge.tsx
│   ├── LatencyChart.tsx
│   └── MapMarker.tsx
├── navigation/
│   └── AppNavigator.tsx
└── utils/
    ├── constants.ts
    └── helpers.ts
```

---

## 🔐 Autenticação no APK

### Fluxo:
1. Usuário faz login
2. App recebe token JWT
3. Salva token no AsyncStorage
4. Inclui token em todas requisições
5. Se token expirar, redireciona para login

### Código Exemplo (React Native):

```typescript
// services/api.ts
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://SEU_SERVIDOR:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Interceptor para adicionar token
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratar erros
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expirado, fazer logout
      await AsyncStorage.removeItem('token');
      // Redirecionar para login
    }
    return Promise.reject(error);
  }
);

export default api;
```

```typescript
// services/auth.ts
import api from './api';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const login = async (email: string, password: string) => {
  const response = await api.post('/auth/login', { email, password });
  const { access_token, user } = response.data;
  
  // Salvar token
  await AsyncStorage.setItem('token', access_token);
  await AsyncStorage.setItem('user', JSON.stringify(user));
  
  return { token: access_token, user };
};

export const logout = async () => {
  await AsyncStorage.removeItem('token');
  await AsyncStorage.removeItem('user');
};

export const getUser = async () => {
  const userStr = await AsyncStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};
```

---

## 📊 Telas do APK

### 1. **Login Screen**
- Campo email
- Campo senha
- Botão "Entrar"
- Checkbox "Lembrar-me"

### 2. **Dashboard Screen**
- Cards com estatísticas:
  - Torres Online/Offline
  - Equipamentos Online/Offline
- Lista de alertas recentes
- Botão flutuante "Ver Mapa"

### 3. **Equipments List Screen**
- Lista de equipamentos
- Cada item mostra:
  - Nome
  - IP
  - Status (badge verde/vermelho)
  - Latência
- Filtros:
  - Todos / Online / Offline
  - Por torre
- Busca por nome/IP

### 4. **Equipment Detail Screen**
- Informações:
  - Nome, IP, Status
  - Torre associada
  - Última verificação
  - Latência atual
- Gráfico de latência (24h)
- Botões:
  - 🔄 Reboot
  - 📍 Ver no Mapa
  - 📊 Histórico

### 5. **Map Screen**
- Mapa com marcadores de torres
- Marcadores coloridos por status
- Ao clicar: popup com info
- Botão "Navegar até aqui" (GPS)

---

## 🎨 Design Sugerido

### Cores:
```typescript
const colors = {
  primary: '#3B82F6',      // Azul
  success: '#22C55E',      // Verde (online)
  danger: '#EF4444',       // Vermelho (offline)
  warning: '#F59E0B',      // Amarelo (alerta)
  background: '#F3F4F6',   // Cinza claro
  card: '#FFFFFF',         // Branco
  text: '#1F2937',         // Cinza escuro
};
```

### Componentes:
- **StatusBadge**: Badge verde (online) ou vermelho (offline)
- **EquipmentCard**: Card com info do equipamento
- **LatencyChart**: Gráfico de linha da latência
- **MapMarker**: Marcador customizado no mapa

---

## 🔔 Notificações Push (Futuro)

### Firebase Cloud Messaging (FCM)

1. Técnico instala app
2. App registra token FCM
3. Backend salva token do técnico
4. Quando equipamento fica offline:
   - Backend envia notificação via FCM
   - Técnico recebe alerta no celular

---

## 📦 Exemplo de Tela (React Native)

```typescript
// screens/EquipmentsListScreen.tsx
import React, { useEffect, useState } from 'react';
import { View, FlatList, Text, TouchableOpacity } from 'react-native';
import api from '../services/api';

interface Equipment {
  id: number;
  name: string;
  ip: string;
  is_online: boolean;
  last_latency: number;
}

export default function EquipmentsListScreen({ navigation }) {
  const [equipments, setEquipments] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEquipments();
  }, []);

  const loadEquipments = async () => {
    try {
      const response = await api.get('/equipments/');
      setEquipments(response.data);
    } catch (error) {
      console.error('Erro ao carregar equipamentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderItem = ({ item }: { item: Equipment }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('EquipmentDetail', { id: item.id })}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.name}>{item.name}</Text>
        <View style={[
          styles.badge,
          { backgroundColor: item.is_online ? '#22C55E' : '#EF4444' }
        ]}>
          <Text style={styles.badgeText}>
            {item.is_online ? 'Online' : 'Offline'}
          </Text>
        </View>
      </View>
      <Text style={styles.ip}>{item.ip}</Text>
      {item.is_online && (
        <Text style={styles.latency}>Latência: {item.last_latency}ms</Text>
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={equipments}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        refreshing={loading}
        onRefresh={loadEquipments}
      />
    </View>
  );
}
```

---

## 🚀 Próximos Passos

### 1. **Escolher Stack**
- React Native (recomendado)
- Flutter
- Kotlin nativo

### 2. **Configurar Projeto**
```bash
# React Native
npx react-native init ISPMonitorApp
cd ISPMonitorApp
npm install axios react-navigation react-native-maps
```

### 3. **Implementar Telas**
1. Login
2. Dashboard
3. Lista de Equipamentos
4. Detalhes
5. Mapa

### 4. **Testar**
- Testar em emulador
- Testar em dispositivo real
- Testar com backend real

### 5. **Build e Deploy**
```bash
# Android
cd android
./gradlew assembleRelease

# APK gerado em:
# android/app/build/outputs/apk/release/app-release.apk
```

---

## 📞 Suporte

- **API Docs**: http://SEU_SERVIDOR:8000/docs
- **Backend**: FastAPI (Python)
- **Autenticação**: JWT
- **Formato**: JSON

---

**Pronto para começar o desenvolvimento do APK!** 📱🚀
