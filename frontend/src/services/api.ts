import axios from 'axios';

export const api = axios.create({
    baseURL: '/api',
    timeout: 30000, // Aumentei o timeout também
});

api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const getTowers = () => api.get('/towers/').then(res => res.data);
export const createTower = (data: any) => api.post('/towers/', data).then(res => res.data);
export const deleteTower = (id: number) => api.delete(`/towers/${id}`).then(res => res.data);

export const importTowersCsv = (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/towers/import_csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => res.data);
};

export const getEquipments = () => api.get('/equipments/').then(res => res.data);
export const createEquipment = (data: any) => api.post('/equipments/', data).then(res => res.data);
export const updateEquipment = (id: number, data: any) => api.put(`/equipments/${id}`, data).then(res => res.data);
export const deleteEquipment = (id: number) => api.delete(`/equipments/${id}`).then(res => res.data);
export const rebootEquipment = (id: number) => api.post(`/equipments/${id}/reboot`).then(res => res.data);
// Note: scanNetwork uses EventSource in component, so simple POST here might be legacy or unused, but keeping just in case
export const scanNetwork = (range: string) => api.post('/equipments/scan/', { ip_range: range }).then(res => res.data);

export const getTelegramConfig = () => api.get('/settings/telegram').then(res => res.data);
export const updateTelegramConfig = (data: any) => api.post('/settings/telegram', data).then(res => res.data);

// Auth
export const login = (data: any) => api.post('/auth/login', data).then(res => res.data);
export const getMe = () => api.get('/auth/me').then(res => res.data);
export const updateMe = (data: any) => api.put('/auth/me', data).then(res => res.data);

// Users (Admin)
export const getUsers = () => api.get('/users/').then(res => res.data);
export const createUser = (data: any) => api.post('/users/', data).then(res => res.data);
export const updateUser = (id: number, data: any) => api.put(`/users/${id}`, data).then(res => res.data);
export const deleteUser = (id: number) => api.delete(`/users/${id}`).then(res => res.data);

// System Settings
export const getSystemName = () => api.get('/settings/system-name').then(res => res.data);
export const updateSystemName = (name: string) => api.post('/settings/system-name', { name }).then(res => res.data);

// Latency
export const getLatencyConfig = () => api.get('/settings/latency').then(res => res.data);
export const updateLatencyConfig = (data: any) => api.post('/settings/latency', data).then(res => res.data);
export const getLatencyHistory = (id: number, period: string) => api.get(`/equipments/${id}/latency-history?period=${period}`).then(res => res.data);
export const getTrafficHistory = (id: number, period: string) => api.get(`/equipments/${id}/traffic-history?period=${period}`).then(res => res.data);

// Network Links
export const getLinks = () => api.get('/towers/links').then(res => res.data);
export const createLink = (data: any) => api.post('/towers/links', data).then(res => res.data);
export const deleteLink = (id: number) => api.delete(`/towers/links/${id}`).then(res => res.data);

// Network Defaults
export const getNetworkDefaults = () => api.get('/settings/network-defaults').then(res => res.data);
export const updateNetworkDefaults = (data: any) => api.post('/settings/network-defaults', data).then(res => res.data);

// Database Config
export const getDatabaseConfig = () => api.get('/settings/database').then(res => res.data);
export const updateDatabaseConfig = (data: any) => api.post('/settings/database', data).then(res => res.data);
export const migrateData = (postgres_url: string) => api.post('/settings/migrate-data', { postgres_url }).then(res => res.data);

// Testing
export const testTelegramMessage = () => api.post('/settings/telegram/test-message').then(res => res.data);
export const testWhatsappMessage = (target?: string) => api.post('/settings/whatsapp/test-message', { target }).then(res => res.data);
export const testBackup = () => api.post('/settings/telegram/test-backup').then(res => res.data);
export const getWhatsappGroups = () => api.get('/settings/whatsapp/groups').then(res => res.data);


// CSV Import/Export
export const exportEquipmentsCSV = () => api.get('/equipments/export/csv', { responseType: 'blob' }).then(res => res.data);
export const importEquipmentsCSV = (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/equipments/import/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => res.data);
};

// Auto-detect equipment brand and type
export const detectEquipmentBrand = (ip: string, snmp_community: string = 'public', snmp_port: number = 161) =>
    api.post('/equipments/detect-brand', { ip, snmp_community, snmp_port }, { timeout: 60000 }).then(res => res.data);

export const getWhatsappStatus = () => api.get('/settings/whatsapp/status').then(res => res.data);

// Expo / Mobile
export const getExpoStatus = () => api.get('/expo/status').then(res => res.data);
export const startExpo = () => api.post('/expo/start').then(res => res.data);
export const stopExpo = () => api.post('/expo/stop').then(res => res.data);

// Ngrok / External Access
export const getNgrokStatus = () => api.get('/ngrok/status').then(res => res.data);
export const startNgrok = () => api.post('/ngrok/start').then(res => res.data);
export const stopNgrok = () => api.post('/ngrok/stop').then(res => res.data);
// Mobile
export const startMobile = () => api.post('/mobile/start').then(res => res.data);
export const stopMobile = () => api.post('/mobile/stop').then(res => res.data);
export const getMobileStatus = () => api.get('/mobile/status').then(res => res.data);
