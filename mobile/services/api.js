import Constants from 'expo-constants';
import axios from 'axios';

// 🤖 Lógica Inteligente de IP
// Pega o IP da máquina que está rodando o Expo (seu PC) automaticamente
const getBaseUrl = () => {
    try {
        const debuggerHost = Constants.expoConfig?.hostUri;
        const localhost = debuggerHost?.split(":")[0];

        if (localhost) {
            return `http://${localhost}:8080/api`;
        }
    } catch (e) {
        console.log("Erro ao detectar IP:", e);
    }
    // Fallback Genérico (Emuladores)
    return 'http://localhost:8080/api';
};

const API_URL = getBaseUrl();

console.log(`[MOBILE] Conectando API em: ${API_URL}`);

const api = axios.create({
    baseURL: API_URL,
    timeout: 10000,
    headers: {
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'ISP-Monitor-Mobile',
        'Content-Type': 'application/json'
    }
});

export default api;
