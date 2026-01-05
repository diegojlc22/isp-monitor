import { useEffect, useState } from 'react';
import { getSystemName, updateSystemName, getLatencyConfig, updateLatencyConfig, getNetworkDefaults, updateNetworkDefaults, getMonitoringSchedules, updateMonitoringSchedules } from '../services/api';
import { Save, Smartphone, Settings as SettingsIcon, Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Settings() {
    const { user, refreshSystemName } = useAuth();
    const [sysName, setSysName] = useState('');
    const [thresholds, setThresholds] = useState({ good: 50, critical: 200 });
    const [networkDefaults, setNetworkDefaults] = useState({ ssh_user: '', ssh_password: '', snmp_community: '' });
    const [schedules, setSchedules] = useState({
        ping_interval: 30,
        snmp_interval: 10,
        agent_interval: 300,
        topology_interval: 1800,
        daily_report_hour: 8,
        security_audit_days: 7,
        capacity_planning_days: 7
    });
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    useEffect(() => {
        getSystemName().then(res => setSysName(res.name)).catch(console.error);
        getLatencyConfig().then(setThresholds).catch(console.error);
        getNetworkDefaults().then(setNetworkDefaults).catch(console.error);
        getMonitoringSchedules().then(setSchedules).catch(console.error);
    }, []);

    async function handleSave(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        try {
            await updateSystemName(sysName);
            await updateLatencyConfig(thresholds);
            await updateNetworkDefaults(networkDefaults);
            await updateMonitoringSchedules(schedules);

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
        <div className="max-w-2xl relative">
            <h2 className="text-2xl font-bold mb-6 text-white">Configurações</h2>

            <div className="space-y-6">
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

                    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden mt-6">
                        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <SettingsIcon className="text-purple-400" size={24} />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white">Padrões de Rede</h3>
                                <p className="text-sm text-slate-400">Credenciais que serão pré-preenchidas em novos equipamentos.</p>
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

                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden mt-6">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Activity className="text-blue-400" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Cronogramas de Monitoramento</h3>
                            <p className="text-sm text-slate-400">Intervalos de execução dos serviços automáticos.</p>
                        </div>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Intervalo de Ping (segundos)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={schedules.ping_interval} onChange={e => setSchedules({ ...schedules, ping_interval: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Padrão: 30s (Contínuo)</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Intervalo SNMP (segundos)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={schedules.snmp_interval} onChange={e => setSchedules({ ...schedules, snmp_interval: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Padrão: 10s (Tráfego/Sinal)</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Agente IA (segundos)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={schedules.agent_interval} onChange={e => setSchedules({ ...schedules, agent_interval: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Padrão: 300s (5 minutos)</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Topologia (segundos)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={schedules.topology_interval} onChange={e => setSchedules({ ...schedules, topology_interval: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Padrão: 1800s (30 minutos)</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Relatório Diário (hora)</label>
                            <input type="number" min="0" max="23" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={schedules.daily_report_hour} onChange={e => setSchedules({ ...schedules, daily_report_hour: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Padrão: 8h (Piores sinais)</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Auditoria Segurança (dias)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={schedules.security_audit_days} onChange={e => setSchedules({ ...schedules, security_audit_days: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Padrão: 7 dias (Semanal)</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Análise Capacidade (dias)</label>
                            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={schedules.capacity_planning_days} onChange={e => setSchedules({ ...schedules, capacity_planning_days: parseInt(e.target.value) })} />
                            <p className="mt-1 text-xs text-slate-500">Padrão: 7 dias (Semanal)</p>
                        </div>
                    </div>
                    <div className="p-6 pt-0">
                        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                            <p className="text-sm text-amber-400">
                                ⚠️ <strong>Atenção:</strong> Alterações nos cronogramas exigem reinicialização do Collector para ter efeito.
                            </p>
                        </div>
                    </div>
                </div>

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
                </div>
            </div>
        </div>
    )
}
