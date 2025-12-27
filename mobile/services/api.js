
import axios from 'axios';

// ⚠️ IMPORTANTE: 
// Endereço Local (Desenvolvimento)
// Substitua pelo IP da sua máquina se mudar
const API_URL = 'http://192.168.0.17:8000/api';

const api = axios.create({
    baseURL: API_URL,
    timeout: 10000,
    headers: {
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'ISP-Monitor-Mobile',
        'Content-Type': 'application/json'
    }
});

// export const setBaseUrl = (ip) => {
//     api.defaults.baseURL = `http://${ip}:8080/api`;
// };

export default api;
