
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const REMOTE_URL = "https://uniconoclastic-addedly-yareli.ngrok-free.dev/api";

const api = axios.create({
    baseURL: REMOTE_URL,
    timeout: 15000,
    headers: {
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'ISP-Monitor-Mobile',
        'Content-Type': 'application/json'
    }
});

// Função para recarregar configuração de IP Local
export const reloadApiConfig = async () => {
    try {
        const localIp = await AsyncStorage.getItem('settings_local_ip');
        if (localIp) {
            const localUrl = `http://${localIp}:8080/api`;
            console.log(`[MOBILE] Testando IP Local configurado: ${localUrl}`);

            try {
                // Timeout curto para não travar UX
                await axios.get(localUrl.replace('/api', '') + '/docs', { timeout: 1500 });
                api.defaults.baseURL = localUrl;
                console.log("[MOBILE] ✅ Conectado na Rede Local!");
                return { success: true, mode: 'local', url: localUrl };
            } catch (err) {
                console.log("[MOBILE] ⚠️ IP Local inacessível. Mantendo remoto.");
            }
        }
    } catch (e) {
        console.error("Erro config API:", e);
    }

    // Fallback garantido
    api.defaults.baseURL = REMOTE_URL;
    return { success: true, mode: 'remote', url: REMOTE_URL };
};

// Inicializa na carga
reloadApiConfig();

export default api;

