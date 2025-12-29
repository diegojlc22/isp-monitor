import Constants from 'expo-constants';
import axios from 'axios';

// 🤖 Configuração de Acesso (Forçado para Externo/4G)
// Usamos sempre o túnel Ngrok para garantir que funcione ao sair do Wi-Fi
const API_URL = "https://uniconoclastic-addedly-yareli.ngrok-free.dev/api";

console.log(`[MOBILE] Conectando API em: ${API_URL}`);

const api = axios.create({
    baseURL: API_URL,
    timeout: 15000,
    headers: {
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'ISP-Monitor-Mobile',
        'Content-Type': 'application/json'
    }
});

export default api;
