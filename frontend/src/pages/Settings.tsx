import { useEffect, useState } from 'react';
import { getSystemName, updateSystemName, getLatencyConfig, updateLatencyConfig, getNetworkDefaults, updateNetworkDefaults, getMonitoringSchedules, updateMonitoringSchedules } from '../services/api';
import { Save, Smartphone, Settings as SettingsIcon, Activity, Clock, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Settings() {
    const { user, refreshSystemName } = useAuth();
    const [sysName, setSysName] = useState('');
    const [thresholds, setThresholds] = useState({ good: 50, critical: 200 });
    const [networkDefaults, setNetworkDefaults] = useState({ ssh_user: '', ssh_password: '', snmp_community: '' });
    const [monitoringSchedules, setMonitoringSchedules] = useState({
        ping_interval: 30,
        ping_timeout: 1,
        ping_down_count: 3,
        snmp_interval: 10,
        agent_interval: 300,
        topology_interval: 1800
    });
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    useEffect(() => {
        getSystemName().then(res => setSysName(res.name)).catch(console.error);
        getLatencyConfig().then(setThresholds).catch(console.error);
        getNetworkDefaults().then(setNetworkDefaults).catch(console.error);
        getMonitoringSchedules().then(setMonitoringSchedules).catch(console.error);
    }, []);

    async function handleSave(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        try {
            await updateSystemName(sysName);
            await updateLatencyConfig(thresholds);
            await updateNetworkDefaults(networkDefaults);
            await updateMonitoringSchedules(monitoringSchedules);

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
        <div className="max-w-4xl pb-20">
            <h2 className="text-2xl font-bold mb-6 text-white">Configurações do Sistema</h2>

            <form onSubmit={handleSave} className="space-y-6">
                {/* GERAL */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-slate-800 rounded-lg">
                            <SettingsIcon className="text-slate-200" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Geral</h3>
                            <p className="text-sm text-slate-400">Identificação básica do servidor.</p>
                        </div>
                    </div>
                    <div className="p-6">
                        <label className="block text-sm font-medium text-slate-400 mb-1">Nome do Sistema</label>
                        <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                            value={sysName} onChange={e => setSysName(e.target.value)} />
                    </div>
                </div>

                {/* MONITORAMENTO (POLLING) */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Clock className="text-blue-500" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Monitoramento (Polling)</h3>
                            <p className="text-sm text-slate-400">Configuração de frequência e sensibilidade das sondagens (Igual ao Dude).</p>
                        </div>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Intervalo de Ping (s)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none text-lg font-mono"
                                value={monitoringSchedules.ping_interval}
                                onChange={e => setMonitoringSchedules({ ...monitoringSchedules, ping_interval: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Probe Interval</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Timeout de Ping (s)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none text-lg font-mono"
                                value={monitoringSchedules.ping_timeout}
                                onChange={e => setMonitoringSchedules({ ...monitoringSchedules, ping_timeout: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Probe Timeout</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Contagem para Queda</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none text-lg font-mono"
                                value={monitoringSchedules.ping_down_count}
                                onChange={e => setMonitoringSchedules({ ...monitoringSchedules, ping_down_count: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Probe Down Count</p>
                        </div>

                        <div className="md:col-span-3 h-px bg-slate-800/50"></div>

                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Intervalo SNMP (s)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none text-lg font-mono"
                                value={monitoringSchedules.snmp_interval}
                                onChange={e => setMonitoringSchedules({ ...monitoringSchedules, snmp_interval: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Coleta de Tráfego e Sinal.</p>
                        </div>
                    </div>
                </div>

                {/* LATENCIA */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-amber-500/10 rounded-lg">
                            <Activity className="text-amber-500" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Cores de Latência</h3>
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

                {/* PADROES DE REDE */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-purple-500/10 rounded-lg">
                            <ShieldCheck className="text-purple-400" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Padrões de Rede</h3>
                            <p className="text-sm text-slate-400">Credenciais pré-preenchidas em novos equipamentos.</p>
                        </div>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">SSH User Padrão</label>
                            <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={networkDefaults.ssh_user} onChange={e => setNetworkDefaults({ ...networkDefaults, ssh_user: e.target.value })} />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">SSH Senha Padrão</label>
                            <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={networkDefaults.ssh_password} onChange={e => setNetworkDefaults({ ...networkDefaults, ssh_password: e.target.value })} />
                        </div>
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-slate-400 mb-1">SNMP Community Global</label>
                            <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={networkDefaults.snmp_community} onChange={e => setNetworkDefaults({ ...networkDefaults, snmp_community: e.target.value })} />
                        </div>
                    </div>
                </div>

                {msg && (
                    <div className={`p-4 rounded-xl text-sm font-medium shadow-lg animate-in fade-in slide-in-from-bottom-2 ${msg.includes('Erro') ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
                        {msg}
                    </div>
                )}

                <div className="flex justify-end pt-4">
                    <button type="submit" disabled={loading} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg hover:shadow-blue-500/20 active:scale-95">
                        <Save size={20} />
                        {loading ? 'Salvando...' : 'Salvar Alterações'}
                    </button>
                </div>
            </form>

            <div className="mt-12 bg-slate-900 rounded-xl border border-slate-800 p-6 opacity-60">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-slate-800 rounded-lg">
                        <Smartphone className="text-slate-400" size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">App Técnico (Integração)</h3>
                        <p className="text-sm text-slate-400">Em desenvolvimento: Acesso via API para aplicativo móvel.</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
