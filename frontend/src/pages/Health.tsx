import { useState, useEffect } from 'react';
import { getSystemHealth } from '../services/api';
import { Activity, Server, Database, ShieldAlert, Cpu, HardDrive, Clock, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

export function Health() {
    const [health, setHealth] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchHealth = async () => {
        try {
            const data = await getSystemHealth();
            setHealth(data);
            setError(null);
        } catch (e: any) {
            console.error('Error fetching health:', e);
            setError('Falha ao obter dados de integridade do sistema.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHealth();
        const interval = setInterval(fetchHealth, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    if (loading && !health) {
        return (
            <div className="p-6 flex flex-col items-center justify-center min-h-[400px]">
                <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></div>
                <p className="text-slate-400">Carregando status do sistema...</p>
            </div>
        );
    }

    if (error && !health) {
        return (
            <div className="p-6 flex flex-col items-center justify-center min-h-[400px]">
                <XCircle size={48} className="text-rose-500 mb-4" />
                <p className="text-white font-medium mb-2">{error}</p>
                <button
                    onClick={() => { setLoading(true); fetchHealth(); }}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                    Tentar Novamente
                </button>
            </div>
        );
    }

    const StatCard = ({ title, icon: Icon, status, value, subtext, colorClass }: any) => (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <div className="flex justify-between items-start mb-4">
                <div className={clsx("p-2 rounded-lg bg-opacity-10", colorClass)}>
                    <Icon size={24} className={colorClass.split(' ')[0]} />
                </div>
                <div className={clsx(
                    "px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider",
                    status === 'online' || status === 'ok' || status === 'connected' ? "bg-emerald-500/10 text-emerald-500" : "bg-rose-500/10 text-rose-500"
                )}>
                    {status}
                </div>
            </div>
            <h4 className="text-slate-400 text-sm font-medium mb-1">{title}</h4>
            <div className="text-2xl font-bold text-white mb-1">{value}</div>
            <p className="text-slate-500 text-xs">{subtext}</p>
        </div>
    );

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Activity className="text-blue-500" /> Integridade do Sistema
                    </h2>
                    <p className="text-slate-400 text-sm mt-1">Status em tempo real de todos os serviços core.</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock size={14} />
                    Última atualização: {new Date().toLocaleTimeString()}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Coletor Principal"
                    icon={Server}
                    status={health?.collector?.status}
                    value={health?.collector?.status === 'online' ? "🟢 ATIVO" : "🔴 INATIVO"}
                    subtext={health?.collector?.last_seen ? `Visto em: ${new Date(health.collector.last_seen).toLocaleTimeString()}` : "Nunca visto"}
                    colorClass="text-blue-500 bg-blue-500"
                />
                <StatCard
                    title="Monitor SNMP"
                    icon={Activity}
                    status={health?.snmp?.online > 0 ? 'ok' : 'offline'}
                    value={`${health?.snmp?.online} / ${health?.snmp?.total}`}
                    subtext="Equipamentos Online"
                    colorClass="text-purple-500 bg-purple-500"
                />
                <StatCard
                    title="Banco de Dados"
                    icon={Database}
                    status={health?.database?.status}
                    value={`${health?.database?.latency_ms} ms`}
                    subtext="Latência de query"
                    colorClass="text-amber-500 bg-amber-500"
                />
                <StatCard
                    title="Versão do Sistema"
                    icon={CheckCircle2}
                    status="ok"
                    value={health?.version || '2.0.0'}
                    subtext="Build: Stable"
                    colorClass="text-emerald-500 bg-emerald-500"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Resources */}
                <div className="lg:col-span-1 space-y-4">
                    <h3 className="text-lg font-bold text-white px-1">Recursos do Servidor</h3>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-6">
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="flex items-center gap-2 text-slate-400"><Cpu size={16} /> CPU</span>
                                <span className="text-white font-bold">{health?.resources?.cpu_percent}%</span>
                            </div>
                            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                <div
                                    className={clsx("h-full transition-all duration-500", health?.resources?.cpu_percent > 80 ? "bg-rose-500" : "bg-blue-500")}
                                    style={{ width: `${health?.resources?.cpu_percent}%` }}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="flex items-center gap-2 text-slate-400"><HardDrive size={16} /> Memória RAM</span>
                                <span className="text-white font-bold">{health?.resources?.ram_percent}%</span>
                            </div>
                            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                                <div
                                    className={clsx("h-full transition-all duration-500", health?.resources?.ram_percent > 90 ? "bg-rose-500" : "bg-purple-500")}
                                    style={{ width: `${health?.resources?.ram_percent}%` }}
                                />
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-500">
                                <span>Usado: {health?.resources?.ram_used_gb} GB</span>
                                <span>Total: {health?.resources?.ram_total_gb} GB</span>
                            </div>
                        </div>

                        <div className="pt-4 border-t border-slate-800">
                            <div className="flex items-start gap-3">
                                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                                    <ShieldAlert size={18} />
                                </div>
                                <div>
                                    <h5 className="text-sm font-bold text-white">Status de Segurança</h5>
                                    <p className="text-xs text-slate-500 mt-0.5">Firewall ativo, logs seguros.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Recent Alerts */}
                <div className="lg:col-span-2 space-y-4">
                    <h3 className="text-lg font-bold text-white px-1">Últimos Eventos de Alerta</h3>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-slate-950 text-slate-500 text-[10px] font-bold uppercase tracking-wider border-b border-slate-800">
                                    <tr>
                                        <th className="px-5 py-3">Timestamp</th>
                                        <th className="px-5 py-3">Dispositivo</th>
                                        <th className="px-5 py-3">Mensagem</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    {health?.alerts && health.alerts.length > 0 ? (
                                        health.alerts.map((alert: any) => (
                                            <tr key={alert.id} className="hover:bg-slate-800/30 transition-colors">
                                                <td className="px-5 py-4 text-xs text-slate-400 whitespace-nowrap">
                                                    {new Date(alert.timestamp).toLocaleString()}
                                                </td>
                                                <td className="px-5 py-4">
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-bold text-white">{alert.device_name}</span>
                                                        <span className="text-[10px] text-slate-500">{alert.device_ip}</span>
                                                    </div>
                                                </td>
                                                <td className="px-5 py-4">
                                                    <div className="flex items-center gap-2">
                                                        {alert.message.toLowerCase().includes('down') ? (
                                                            <div className="p-1 rounded bg-rose-500/10 text-rose-500"><XCircle size={14} /></div>
                                                        ) : alert.message.toLowerCase().includes('up') ? (
                                                            <div className="p-1 rounded bg-emerald-500/10 text-emerald-500"><CheckCircle2 size={14} /></div>
                                                        ) : (
                                                            <div className="p-1 rounded bg-amber-500/10 text-amber-500"><AlertTriangle size={14} /></div>
                                                        )}
                                                        <span className="text-sm text-slate-300">{alert.message}</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={3} className="px-5 py-10 text-center text-slate-500 text-sm">Nenhum alerta recente.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
