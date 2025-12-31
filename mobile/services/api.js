
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
                // Timeout um pouco maior e log detalhado
                console.log(`[MOBILE] 📡 Tentando: ${localUrl}...`);
                await axios.get(localUrl.replace('/api', '') + '/api/health', { timeout: 3000 });
                api.defaults.baseURL = localUrl;
                console.log("[MOBILE] ✅ SUCESSO! Conectado via Rede Local.");
                return { success: true, mode: 'local', url: localUrl };
            } catch (err) {
                console.log(`[MOBILE] ❌ Local FALHOU: ${err.message || 'Timeout'}`);
            }
        }
    } catch (e) {
        console.error("Erro config API:", e);
    }

    // Fallback garantido (Remoto)
    api.defaults.baseURL = REMOTE_URL;
    console.log("[MOBILE] 🌍 Usando Acesso Externo (Ngrok)");

    // Tenta "aprender" o IP local novo vindo do servidor via Ngrok
    const syncLocalIp = async () => {
        try {
            const config = await api.get('/mobile/config');
            if (config.data?.local_ips?.length > 0) {
                // Pega o primeiro IP que não seja 169.254 (APIPA) se possível
                const bestIp = config.data.local_ips.find(ip => !ip.startsWith('169.254')) || config.data.local_ips[0];
                console.log(`[MOBILE] 🔄 Sincronizando IP local do servidor: ${bestIp}`);
                await AsyncStorage.setItem('settings_local_ip', bestIp);
            }
        } catch (err) {
            console.log("[MOBILE] ❌ Falha ao sincronizar IP local via Ngrok");
        }
    };
    syncLocalIp();

    return { success: true, mode: 'remote', url: REMOTE_URL };
};

// Inicializa na carga
reloadApiConfig();

export default api;

