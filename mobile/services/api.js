
import axios from 'axios';

// ⚠️ IMPORTANTE: 
// Endereço Permanente (Ngrok Static Domain)
const API_URL = 'https://uniconoclastic-addedly-yareli.ngrok-free.dev/api';

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
