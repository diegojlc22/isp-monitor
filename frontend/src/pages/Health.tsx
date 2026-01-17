import { useState, useEffect } from 'react';
import { getSystemHealth } from '../services/api';
import { Activity, Server, Database, ShieldAlert, Cpu, HardDrive, CheckCircle2, XCircle, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import clsx from 'clsx';

export function Health() {
    const [health, setHealth] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showAlerts, setShowAlerts] = useState(true);

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

    const cleanAlertMessage = (msg: string) => {
        // Remove markdown bolding and extra symbols for a cleaner UI table display
        return msg
            .replace(/\*(.*?)\*/g, '$1') // Remove *bold*
            .replace(/📡|🌐|🕒|📍|📟|⚠️|🛑|🔔|📍|🔋/g, '') // Remove redundant icons (we have our own in the table)
            .split('\n')[0] // Take only the first line/title
            .trim();
    };

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto animate-in fade-in duration-500">
            {/* Real-time Status Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Coletor Principal"
                    icon={Server}
                    status={health?.collector?.status}
                    value={health?.collector?.status === 'online' ? "ATIVO" : "INATIVO"}
                    subtext={health?.collector?.last_seen ? `Visto: ${new Date(health.collector.last_seen).toLocaleTimeString()}` : "Desconectado"}
                    colorClass="text-sky-500 bg-sky-500"
                />
                <StatCard
                    title="Monitor SNMP"
                    icon={Activity}
                    status={health?.snmp?.status === 'active' ? 'ok' : 'offline'}
                    value={`${health?.snmp?.online} / ${health?.snmp?.total}`}
                    subtext="Dispositivos Online"
                    colorClass="text-indigo-500 bg-indigo-500"
                />
                <StatCard
                    title="Banco de Dados"
                    icon={Database}
                    status={health?.database?.status}
                    value={`${health?.database?.latency_ms} ms`}
                    subtext="Latência de Query"
                    colorClass="text-amber-500 bg-amber-500"
                />
                <StatCard
                    title="Backup & Segurança"
                    icon={ShieldAlert}
                    status={health?.backup?.last_run ? 'ok' : 'offline'}
                    value={health?.backup?.last_run ? "PROTEGIDO" : "PENDENTE"}
                    subtext={health?.backup?.last_run ? `Último: ${new Date(health.backup.last_run).toLocaleDateString()} ${new Date(health.backup.last_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : "Backup automático pendente"}
                    colorClass="text-emerald-500 bg-emerald-500"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Resources Panel */}
                <div className="lg:col-span-4 space-y-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden h-full">
                        <div className="absolute top-0 right-0 p-4 opacity-5">
                            <Cpu size={120} />
                        </div>

                        <h3 className="text-lg font-bold text-white mb-6">Recursos do Servidor</h3>

                        <div className="space-y-8">
                            <div className="space-y-3">
                                <div className="flex justify-between items-end">
                                    <span className="flex items-center gap-2 text-slate-400 text-sm font-medium">
                                        <Cpu size={18} className="text-sky-500" /> CPU App
                                    </span>
                                    <span className="text-white font-bold">{health?.resources?.cpu_percent}%</span>
                                </div>
                                <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                                    <div
                                        className={clsx("h-full transition-all duration-1000 ease-out", health?.resources?.cpu_percent > 80 ? "bg-rose-500" : "bg-sky-500")}
                                        style={{ width: `${Math.min(health?.resources?.cpu_percent, 100)}%` }}
                                    />
                                </div>
                            </div>

                            <div className="space-y-3">
                                <div className="flex justify-between items-end">
                                    <span className="flex items-center gap-2 text-slate-400 text-sm font-medium">
                                        <HardDrive size={18} className="text-indigo-500" /> RAM App
                                    </span>
                                    <span className="text-white font-bold">{health?.resources?.ram_percent}%</span>
                                </div>
                                <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                                    <div
                                        className={clsx("h-full transition-all duration-1000 ease-out", health?.resources?.ram_percent > 90 ? "bg-rose-500" : "bg-indigo-500")}
                                        style={{ width: `${health?.resources?.ram_percent}%` }}
                                    />
                                </div>
                                <div className="flex justify-between text-[10px] text-slate-500 font-medium px-1">
                                    <span>Uso: {health?.resources?.ram_used_gb} GB</span>
                                    <span>Total: {health?.resources?.ram_total_gb} GB</span>
                                </div>
                            </div>

                            <div className="pt-6 border-t border-slate-800/50">
                                <div className="flex items-center gap-4 bg-emerald-500/5 border border-emerald-500/10 p-4 rounded-xl">
                                    <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-500">
                                        <ShieldAlert size={20} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex justify-between items-center mb-0.5">
                                            <h5 className="text-sm font-bold text-white leading-none">Cortex AI Firewall</h5>
                                            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                        </div>
                                        <p className="text-xs text-slate-500">Núcleo de monitoramento protegido.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Recent Alerts List */}
                <div className="lg:col-span-8 space-y-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-xl h-full flex flex-col">
                        <div className="p-5 border-b border-slate-800 flex justify-between items-center">
                            <h3 className="text-lg font-bold text-white flex items-center gap-3">
                                <ShieldAlert className="text-amber-500" size={20} /> Eventos Recentes de Infraestrutura
                            </h3>
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-1.5 bg-slate-800/50 px-2 py-1 rounded text-[10px] text-slate-400 border border-slate-700">
                                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Live Monitoring
                                </div>
                                <button
                                    onClick={() => setShowAlerts(!showAlerts)}
                                    className="p-1.5 text-slate-400 hover:text-white transition-colors hover:bg-slate-800 rounded-lg"
                                    title={showAlerts ? "Esconder" : "Mostrar"}
                                >
                                    {showAlerts ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-auto max-h-[480px]">
                            {showAlerts ? (
                                <table className="w-full text-left border-collapse">
                                    <thead className="sticky top-0 bg-slate-900 text-slate-500 text-[10px] font-bold uppercase tracking-wider border-b border-slate-800 z-10">
                                        <tr>
                                            <th className="px-6 py-4">🕒 Timestamp</th>
                                            <th className="px-6 py-4">📡 Dispositivo</th>
                                            <th className="px-6 py-4">💬 Mensagem</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800/50">
                                        {health?.alerts && health.alerts.length > 0 ? (
                                            health.alerts.map((alert: any) => (
                                                <tr key={alert.id} className="hover:bg-slate-800/20 transition-colors group">
                                                    <td className="px-6 py-5 text-xs text-slate-500 whitespace-nowrap">
                                                        <span className="group-hover:text-slate-300">
                                                            {new Date(alert.timestamp).toLocaleDateString()}
                                                        </span>
                                                        <br />
                                                        <span className="text-slate-600 group-hover:text-slate-400 font-medium">
                                                            {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-1.5 h-10 rounded-full bg-slate-800 group-hover:bg-blue-500 transition-all duration-300"></div>
                                                            <div className="flex flex-col">
                                                                <span className="text-sm font-bold text-slate-100 group-hover:text-white">{alert.device_name}</span>
                                                                <span className="text-[10px] text-slate-500 font-mono">{alert.device_ip}</span>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <div className="flex items-center gap-3">
                                                            {alert.message.toLowerCase().includes('concluí') || alert.message.toLowerCase().includes('restabelecida') || alert.message.toLowerCase().includes('up') ? (
                                                                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                                                                    <CheckCircle2 size={16} />
                                                                </div>
                                                            ) : alert.message.toLowerCase().includes('falha') || alert.message.toLowerCase().includes('down') ? (
                                                                <div className="p-2 rounded-lg bg-rose-500/10 text-rose-500">
                                                                    <XCircle size={16} />
                                                                </div>
                                                            ) : (
                                                                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
                                                                    <AlertTriangle size={16} />
                                                                </div>
                                                            )}
                                                            <span className="text-sm text-slate-300 font-medium group-hover:text-slate-100 transition-colors">
                                                                {cleanAlertMessage(alert.message)}
                                                            </span>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={3} className="px-6 py-20 text-center">
                                                    <div className="flex flex-col items-center gap-3 text-slate-600">
                                                        <Activity size={32} className="opacity-20" />
                                                        <span className="text-sm">Nenhum evento registrado recentemente.</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="flex flex-col items-center justify-center p-20 text-slate-500 gap-4 opacity-50">
                                    <EyeOff size={48} strokeWidth={1} />
                                    <p className="text-sm italic">Oculto por privacidade. Clique no ícone para mostrar.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
            {/* Footer / Version */}
            <div className="flex justify-between items-center text-[10px] text-slate-600 font-mono pt-4 border-t border-slate-800/50">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/50 animate-pulse" />
                    <span>SISTEMA OPERACIONAL • NÚCLEO V{health?.version || '4.2.0-TURBO'}</span>
                </div>
                <span>ISP MONITOR © 2026 • TODOS OS DIREITOS RESERVADOS</span>
            </div>
        </div>
    );
}
