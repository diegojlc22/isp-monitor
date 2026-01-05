import { useEffect, useState } from 'react';
import { getMonitoringSchedules, updateMonitoringSchedules } from '../services/api';
import { Save, Clock, Activity, Calendar, Shield, TrendingUp, Wifi } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Schedules() {
    const { user } = useAuth();
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
        getMonitoringSchedules().then(setSchedules).catch(console.error);
    }, []);

    async function handleSave(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        try {
            await updateMonitoringSchedules(schedules);
            setMsg('✅ Cronogramas salvos! Reinicie o Collector para aplicar.');
            setTimeout(() => setMsg(''), 5000);
        } catch (e) {
            setMsg('❌ Erro ao salvar configurações.');
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
        <div className="max-w-4xl mx-auto">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                    <Clock className="text-blue-400" size={32} />
                    Cronogramas de Monitoramento
                </h2>
                <p className="text-slate-400 mt-2">
                    Configure os intervalos de execução dos serviços automáticos do sistema.
                </p>
            </div>

            <form onSubmit={handleSave} className="space-y-6">
                {/* Serviços Contínuos */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-emerald-500/10 rounded-lg">
                            <Activity className="text-emerald-400" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Serviços Contínuos</h3>
                            <p className="text-sm text-slate-400">Monitoramento em tempo real</p>
                        </div>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                <Wifi className="inline mr-2" size={16} />
                                Intervalo de Ping
                            </label>
                            <div className="flex items-center gap-3">
                                <input
                                    type="number"
                                    min="5"
                                    max="300"
                                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white text-lg font-bold focus:border-emerald-500 focus:outline-none"
                                    value={schedules.ping_interval}
                                    onChange={e => setSchedules({ ...schedules, ping_interval: parseInt(e.target.value) })}
                                />
                                <span className="text-slate-400 font-medium">segundos</span>
                            </div>
                            <p className="mt-2 text-xs text-slate-500">
                                ⚡ Padrão: 30s | Verifica conectividade de todos os dispositivos
                            </p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                <Activity className="inline mr-2" size={16} />
                                Intervalo SNMP
                            </label>
                            <div className="flex items-center gap-3">
                                <input
                                    type="number"
                                    min="5"
                                    max="300"
                                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white text-lg font-bold focus:border-emerald-500 focus:outline-none"
                                    value={schedules.snmp_interval}
                                    onChange={e => setSchedules({ ...schedules, snmp_interval: parseInt(e.target.value) })}
                                />
                                <span className="text-slate-400 font-medium">segundos</span>
                            </div>
                            <p className="mt-2 text-xs text-slate-500">
                                ⚡ Padrão: 10s | Coleta tráfego, sinal e estatísticas wireless
                            </p>
                        </div>
                    </div>
                </div>

                {/* Serviços Periódicos */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Clock className="text-blue-400" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Serviços Periódicos</h3>
                            <p className="text-sm text-slate-400">Análises e descobertas automáticas</p>
                        </div>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                🤖 Agente Inteligente (IA)
                            </label>
                            <div className="flex items-center gap-3">
                                <input
                                    type="number"
                                    min="60"
                                    max="3600"
                                    step="60"
                                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white text-lg font-bold focus:border-blue-500 focus:outline-none"
                                    value={schedules.agent_interval}
                                    onChange={e => setSchedules({ ...schedules, agent_interval: parseInt(e.target.value) })}
                                />
                                <span className="text-slate-400 font-medium">segundos</span>
                            </div>
                            <p className="mt-2 text-xs text-slate-500">
                                🧠 Padrão: 300s (5 min) | Detecta degradação de rede
                            </p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                🗺️ Descoberta de Topologia
                            </label>
                            <div className="flex items-center gap-3">
                                <input
                                    type="number"
                                    min="300"
                                    max="7200"
                                    step="300"
                                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white text-lg font-bold focus:border-blue-500 focus:outline-none"
                                    value={schedules.topology_interval}
                                    onChange={e => setSchedules({ ...schedules, topology_interval: parseInt(e.target.value) })}
                                />
                                <span className="text-slate-400 font-medium">segundos</span>
                            </div>
                            <p className="mt-2 text-xs text-slate-500">
                                🔍 Padrão: 1800s (30 min) | Mapeia conexões via LLDP/MNDP
                            </p>
                        </div>
                    </div>
                </div>

                {/* Relatórios e Auditorias */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-amber-500/10 rounded-lg">
                            <Calendar className="text-amber-400" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Relatórios e Auditorias</h3>
                            <p className="text-sm text-slate-400">Notificações programadas</p>
                        </div>
                    </div>
                    <div className="p-6 space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-2">
                                    📊 Relatório Diário de Sinal
                                </label>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="number"
                                        min="0"
                                        max="23"
                                        className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white text-lg font-bold focus:border-amber-500 focus:outline-none"
                                        value={schedules.daily_report_hour}
                                        onChange={e => setSchedules({ ...schedules, daily_report_hour: parseInt(e.target.value) })}
                                    />
                                    <span className="text-slate-400 font-medium">:00h</span>
                                </div>
                                <p className="mt-2 text-xs text-slate-500">
                                    📡 Padrão: 8h | Top 10 piores sinais/CCQ
                                </p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
                                    <Shield size={16} />
                                    Auditoria de Segurança
                                </label>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="number"
                                        min="1"
                                        max="30"
                                        className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white text-lg font-bold focus:border-amber-500 focus:outline-none"
                                        value={schedules.security_audit_days}
                                        onChange={e => setSchedules({ ...schedules, security_audit_days: parseInt(e.target.value) })}
                                    />
                                    <span className="text-slate-400 font-medium">dias</span>
                                </div>
                                <p className="mt-2 text-xs text-slate-500">
                                    🔒 Padrão: 7 dias | Senhas padrão, portas inseguras
                                </p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
                                    <TrendingUp size={16} />
                                    Análise de Capacidade
                                </label>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="number"
                                        min="1"
                                        max="30"
                                        className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white text-lg font-bold focus:border-amber-500 focus:outline-none"
                                        value={schedules.capacity_planning_days}
                                        onChange={e => setSchedules({ ...schedules, capacity_planning_days: parseInt(e.target.value) })}
                                    />
                                    <span className="text-slate-400 font-medium">dias</span>
                                </div>
                                <p className="mt-2 text-xs text-slate-500">
                                    📈 Padrão: 7 dias | Previsão de saturação de links
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Mensagem de Feedback */}
                {msg && (
                    <div className={`p-4 rounded-lg text-sm font-medium ${msg.includes('❌')
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                        {msg}
                    </div>
                )}

                {/* Aviso Importante */}
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <div className="text-amber-400 mt-0.5">⚠️</div>
                        <div>
                            <p className="text-sm text-amber-400 font-medium">
                                <strong>Atenção:</strong> Alterações nos cronogramas exigem reinicialização do Collector para ter efeito.
                            </p>
                            <p className="text-xs text-amber-400/70 mt-1">
                                O Doctor (Self-Heal) reiniciará automaticamente o Collector se detectar problemas, ou você pode reiniciar manualmente.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Botão Salvar */}
                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={loading}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20"
                    >
                        <Save size={20} />
                        {loading ? 'Salvando...' : 'Salvar Cronogramas'}
                    </button>
                </div>
            </form>
        </div>
    );
}
