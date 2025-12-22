import { useState, useEffect } from 'react';
import { api, getTelegramConfig, updateTelegramConfig } from '../services/api';
import { Bell, RefreshCw, Save } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface Alert {
    id: number;
    device_type: string;
    device_name: string;
    device_ip: string;
    message: string;
    timestamp: string;
}

export function Alerts() {
    const { user } = useAuth();
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);

    // Telegram Config State
    const [config, setConfig] = useState({ bot_token: '', chat_id: '' });
    const [configLoading, setConfigLoading] = useState(false);
    const [msg, setMsg] = useState('');

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const response = await api.get('/alerts/');
            setAlerts(response.data);
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 30000); // Auto-refresh every 30s

        // Load Telegram Config if Admin
        if (user?.role === 'admin') {
            getTelegramConfig().then(setConfig).catch(console.error);
        }

        return () => clearInterval(interval);
    }, [user]);

    async function handleSaveConfig(e: React.FormEvent) {
        e.preventDefault();
        setConfigLoading(true);
        try {
            await updateTelegramConfig(config);
            setMsg('Configuração do Telegram salva com sucesso!');
            setTimeout(() => setMsg(''), 3000);
        } catch (e) {
            setMsg('Erro ao salvar configuração.');
        } finally {
            setConfigLoading(false);
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Bell className="w-8 h-8 text-yellow-500" /> Alertas
                    </h1>
                    <p className="text-slate-400">Histórico de eventos e configurações de notificação</p>
                </div>
                <button
                    onClick={fetchAlerts}
                    className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                >
                    <RefreshCw className={`w-5 h-5 text-slate-300 ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {/* Telegram Configuration Section (Admin Only) */}
            {user?.role === 'admin' && (
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden mb-8">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Bell className="text-blue-500" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Configuração do Telegram</h3>
                            <p className="text-sm text-slate-400">Configure o bot para receber alertas instantâneos.</p>
                        </div>
                    </div>

                    <form onSubmit={handleSaveConfig} className="p-6 space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Bot Token</label>
                                <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                    value={config.bot_token} onChange={e => setConfig({ ...config, bot_token: e.target.value })} placeholder="123456789:ABCDefGHI..." />
                                <p className="mt-1 text-xs text-slate-500">Token fornecido pelo @BotFather.</p>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Chat ID</label>
                                <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                    value={config.chat_id} onChange={e => setConfig({ ...config, chat_id: e.target.value })} placeholder="-100..." />
                                <p className="mt-1 text-xs text-slate-500">ID do grupo/usuário para receber alertas.</p>
                            </div>
                        </div>

                        {msg && (
                            <div className={`p-3 rounded-lg text-sm ${msg.includes('Erro') ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                                {msg}
                            </div>
                        )}

                        <div className="flex justify-end">
                            <button type="submit" disabled={configLoading} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                                <Save size={18} />
                                {configLoading ? 'Salvando...' : 'Salvar Configuração'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="p-4 border-b border-slate-800">
                    <h3 className="text-lg font-semibold text-white">Histórico de Alertas</h3>
                </div>
                <table className="w-full text-left text-sm text-slate-400">
                    <thead className="bg-slate-950 text-slate-200 uppercase font-medium">
                        <tr>
                            <th className="px-6 py-4">Data/Hora</th>
                            <th className="px-6 py-4">Dispositivo</th>
                            <th className="px-6 py-4">IP</th>
                            <th className="px-6 py-4">Mensagem</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {loading && alerts.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                                    Carregando alertas...
                                </td>
                            </tr>
                        ) : alerts.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                                    Nenhum alerta registrado.
                                </td>
                            </tr>
                        ) : (
                            alerts.map((alert) => (
                                <tr key={alert.id} className="hover:bg-slate-800/50 transition-colors">
                                    <td className="px-6 py-4 font-mono text-slate-500">
                                        {new Date(alert.timestamp).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 font-medium text-white">
                                        {alert.device_name}
                                        <span className="ml-2 text-xs text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded uppercase">
                                            {alert.device_type}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 font-mono">{alert.device_ip}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            {alert.message.includes('🔴') || alert.message.includes('offline') || alert.message.includes('down') ? (
                                                <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"></span>
                                            ) : (
                                                <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                                            )}
                                            <span className={alert.message.includes('🔴') || alert.message.includes('down') ? 'text-red-400' : 'text-green-400'}>
                                                {alert.message}
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
