import { useEffect, useState } from 'react';
import { getTelegramConfig, updateTelegramConfig, getSystemName, updateSystemName, getLatencyConfig, updateLatencyConfig } from '../services/api';
import { Save, Bell, Smartphone, Settings as SettingsIcon, Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Settings() {
    const { user, refreshSystemName } = useAuth();
    const [config, setConfig] = useState({ bot_token: '', chat_id: '' });
    const [sysName, setSysName] = useState('');
    const [thresholds, setThresholds] = useState({ good: 50, critical: 200 });
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    useEffect(() => {
        getTelegramConfig().then(setConfig).catch(console.error);
        getSystemName().then(res => setSysName(res.name)).catch(console.error);
        getLatencyConfig().then(setThresholds).catch(console.error);
    }, []);

    async function handleSave(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        try {
            await updateTelegramConfig(config);
            await updateSystemName(sysName);
            await updateLatencyConfig(thresholds);
            await refreshSystemName();
            setMsg('Configurações salvas com sucesso!');
            setTimeout(() => setMsg(''), 3000);
        } catch (e) {
            setMsg('Erro ao salvar.');
        } finally {
            setLoading(false);
        }
    }

    if (user?.role !== 'admin') {
        return (
            <div className="p-8 text-center text-slate-500">
                Acesso restrito a administradores.
            </div>
        );
    }

    return (
        <div className="max-w-2xl">
            <h2 className="text-2xl font-bold mb-6 text-white">Configurações</h2>

            <form onSubmit={handleSave} className="space-y-6">
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-slate-800 rounded-lg">
                            <SettingsIcon className="text-slate-200" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Geral</h3>
                            <p className="text-sm text-slate-400">Configurações globais do sistema.</p>
                        </div>
                    </div>
                    <div className="p-6">
                        <label className="block text-sm font-medium text-slate-400 mb-1">Nome do Sistema</label>
                        <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                            value={sysName} onChange={e => setSysName(e.target.value)} />
                    </div>
                </div>

                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Bell className="text-blue-500" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Integração Telegram</h3>
                            <p className="text-sm text-slate-400">Configure o bot para receber alertas de status.</p>
                        </div>
                    </div>

                    <div className="p-6 space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Bot Token</label>
                            <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                value={config.bot_token} onChange={e => setConfig({ ...config, bot_token: e.target.value })} placeholder="123456789:ABCDefGHI..." />
                            <p className="mt-1 text-xs text-slate-500">O token fornecido pelo @BotFather.</p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Chat ID</label>
                            <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                value={config.chat_id} onChange={e => setConfig({ ...config, chat_id: e.target.value })} placeholder="-100..." />
                            <p className="mt-1 text-xs text-slate-500">O ID do grupo ou usuário para onde enviar alertas.</p>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-amber-500/10 rounded-lg">
                            <Activity className="text-amber-500" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Latência (Ping)</h3>
                            <p className="text-sm text-slate-400">Limiares para classificação de latência nos gráficos.</p>
                        </div>
                    </div>

                    <div className="p-6 grid grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Limiar Bom (ms)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-green-400 font-bold focus:border-green-500 focus:outline-none"
                                value={thresholds.good} onChange={e => setThresholds({ ...thresholds, good: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Abaixo disso é Verde.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Limiar Crítico (ms)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-rose-400 font-bold focus:border-rose-500 focus:outline-none"
                                value={thresholds.critical} onChange={e => setThresholds({ ...thresholds, critical: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Acima disso é Vermelho.</p>
                        </div>
                    </div>
                </div>

                {msg && (
                    <div className={`p-3 rounded-lg text-sm ${msg.includes('Erro') ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                        {msg}
                    </div>
                )}

                <div className="flex justify-end">
                    <button type="submit" disabled={loading} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                        <Save size={18} />
                        {loading ? 'Salvando...' : 'Salvar Tudo'}
                    </button>
                </div>
            </form>

            <div className="mt-8 bg-slate-900 rounded-xl border border-slate-800 p-6 opacity-75">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-slate-800 rounded-lg">
                        <Smartphone className="text-slate-400" size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">App Técnico (Em Breve)</h3>
                        <p className="text-sm text-slate-400">Acesso via API para aplicativo móvel.</p>
                    </div>
                </div>
                <p className="text-sm text-slate-500">
                    A API já está preparada para integração. A chave de API poderá ser gerada aqui futuramente.
                </p>
            </div>
        </div>
    )
}
