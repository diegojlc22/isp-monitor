import axios from 'axios';

export const api = axios.create({
    baseURL: '/api',
    timeout: 30000, // Aumentei o timeout também
});

export default api;

api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            // Avoid infinite loops if we are already on login
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

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
export const createEquipmentsBatch = (data: any[]) => api.post('/equipments/batch', data).then(res => res.data);
export const deleteEquipment = (id: number) => api.delete(`/equipments/${id}`).then(res => res.data);
export const deleteEquipmentsBatch = (ids: number[]) => api.post('/equipments/batch/delete', { ids }).then(res => res.data);
export const rebootEquipment = (id: number) => api.post(`/equipments/${id}/reboot`).then(res => res.data);
export const testEquipment = (id: number) => api.post(`/equipments/${id}/test`).then(res => res.data);
export const getWirelessStatus = (id: number) => api.get(`/equipments/${id}/wireless-status`).then(res => res.data);
export const getTechLocation = () => api.get('/mobile/last-location').then(res => res.data);
// Note: scanNetwork uses EventSource in component, so simple POST here might be legacy or unused, but keeping just in case
export const startBatchDetect = (ids: number[], community?: string) => api.post('/equipments/batch-detect', { equipment_ids: ids, community }).then(res => res.data);
export const getBatchDetectStatus = () => api.get('/equipments/batch-detect/status').then(res => res.data);
export const stopBatchDetect = () => api.post('/equipments/batch-detect/stop').then(res => res.data);
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

// Synthetic Agent
export const getAgentLogs = () => api.get('/agent/logs').then(res => res.data);
export const getMonitorTargets = () => api.get('/agent/targets').then(res => res.data);
export const createMonitorTarget = (data: any) => api.post('/agent/targets', data).then(res => res.data);
export const updateMonitorTarget = (id: number, data: any) => api.put(`/agent/targets/${id}`, data).then(res => res.data);
export const deleteMonitorTarget = (id: number) => api.delete(`/agent/targets/${id}`).then(res => res.data);
export const triggerAgentTest = () => api.post('/agent/trigger').then(res => res.data);
export const stopAgentTest = () => api.post('/agent/stop').then(res => res.data);
export const getAgentStatus = () => api.get('/agent/status').then(res => res.data);
export const clearAgentLogs = () => api.delete('/agent/logs').then(res => res.data);
export const getAgentSettings = () => api.get('/agent/settings').then(res => res.data);
export const updateAgentSettings = (data: any) => api.post('/agent/settings', data).then(res => res.data);

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

export const scanInterfaces = (ip: string, community: string = 'public', port: number = 161) =>
    api.get(`/equipments/scan-interfaces`, { params: { ip, community, port } }).then(res => res.data);

export const detectBestInterface = (ip: string, community?: string, port: number = 161) =>
    api.get(`/equipments/scan-best-interface`, { params: { ip, community, port } }).then(res => res.data);

// Auto-detectar interface com tráfego (testa todas as interfaces)
export const detectTrafficInterface = (ip: string, community?: string, port: number = 161) =>
    api.post(`/equipments/detect-traffic-interface`, { ip, community, port }, { timeout: 120000 }).then(res => res.data);

// Auto-configurar interface de tráfego (detecta + atualiza automaticamente)
export const autoConfigureTrafficInterface = (equipmentId: number) =>
    api.post(`/equipments/${equipmentId}/auto-configure-traffic`, {}, { timeout: 120000 }).then(res => res.data);

// Auto-detectar TUDO (Marca, Sinal, Tráfego)
export const autoDetectAll = (ip: string, community?: string, port: number = 161) =>
    api.post(`/equipments/auto-detect-all`, { ip, community, port }, { timeout: 120000 }).then(res => res.data);

export const getWhatsappStatus = () => api.get('/settings/whatsapp/status').then(res => res.data);

// Expo / Mobile
export const getExpoStatus = () => api.get('/expo/status').then(res => res.data);
export const startExpo = () => api.post('/expo/start').then(res => res.data);
export const stopExpo = () => api.post('/expo/stop').then(res => res.data);

// Ngrok / External Access
export const getNgrokStatus = () => api.get('/ngrok/status').then(res => res.data);

// System Health
export const getSystemHealth = () => api.get('/system/health').then(res => res.data);
export const startNgrok = () => api.post('/ngrok/start').then(res => res.data);
export const stopNgrok = () => api.post('/ngrok/stop').then(res => res.data);
export const triggerTopologyDiscovery = () => api.post('/system/topology/discover').then(res => res.data);
// Mobile
export const startMobile = () => api.post('/mobile/start').then(res => res.data);
export const stopMobile = () => api.post('/mobile/stop').then(res => res.data);
export const getMobileStatus = () => api.get('/mobile/status').then(res => res.data);
export const getLiveStatus = (ids: number[]) => api.post('/equipments/live-status', { ids }).then(res => res.data);
export const getDashboardLayout = () => api.get('/settings/dashboard-layout').then(res => res.data);
export const saveDashboardLayout = (layout: any[]) => api.post('/settings/dashboard-layout', { layout }).then(res => res.data);

// Monitoring Schedules
export const getMonitoringSchedules = () => api.get('/settings/monitoring-schedules').then(res => res.data);
export const updateMonitoringSchedules = (data: any) => api.post('/settings/monitoring-schedules', data).then(res => res.data);
