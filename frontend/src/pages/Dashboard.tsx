import { useEffect, useState } from 'react';
import api, { getTowers, getEquipments, getLatencyConfig, getLatencyHistory, getAgentLogs } from '../services/api';
import { Activity, ShieldCheck, AlertTriangle, Radio, Loader2, Globe } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import clsx from 'clsx';

export function Dashboard() {
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ towers: 0, equipments: 0, online: 0, offline: 0, insights: 0, agentSuccess: 100 });
    // Widget State
    const [devices, setDevices] = useState<any[]>([]);
    const [selectedDevice, setSelectedDevice] = useState<any>(null);
    const [historyData, setHistoryData] = useState<any[]>([]);
    const [historyConfig, setHistoryConfig] = useState({ good: 50, critical: 200 });
    const [agentData, setAgentData] = useState<any[]>([]);

    useEffect(() => {
        async function load() {
            try {
                // Don't set loading true on interval updates to avoid flicker
                // Only on mount (initial load)

                const [towers, equips, latConfig, insightData, agentLogs] = await Promise.all([
                    getTowers(),
                    getEquipments(),
                    getLatencyConfig(),
                    api.get('/insights/').then(r => r.data).catch(() => []),
                    getAgentLogs(50).catch(() => [])
                ]);
                const allDevices = [...towers, ...equips];
                const monitoredDevices = allDevices.filter((d: any) => d.ip && d.ip.trim() !== '');

                if (monitoredDevices.length === 0) {
                    setStats({ towers: 0, equipments: 0, online: 0, offline: 0, insights: 0, agentSuccess: 100 });
                } else {
                    const online = monitoredDevices.filter((x: any) => x.is_online).length;
                    const offline = monitoredDevices.length - online;

                    const totalLogs = agentLogs.length;
                    const successLogs = agentLogs.filter((l: any) => l.success).length;
                    const successRate = totalLogs > 0 ? Math.round((successLogs / totalLogs) * 100) : 100;

                    setStats({
                        towers: towers.length,
                        equipments: equips.length,
                        online: online,
                        offline: offline,
                        insights: insightData.length,
                        agentSuccess: successRate
                    });
                }

                setAgentData(agentLogs);

                setDevices(equips);
                setHistoryConfig(latConfig);

                if (equips.length > 0 && !selectedDevice) {
                    setSelectedDevice(equips[0]);
                }

            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        load();
        const interval = setInterval(load, 10000); // Increased interval to reduce load
        return () => clearInterval(interval);
    }, []);

    // Load History when selection changes
    useEffect(() => {
        if (selectedDevice) {
            getLatencyHistory(selectedDevice.id, '24h').then(response => {
                setHistoryData((response.data || []).map((d: any) => ({
                    ...d,
                    timeStr: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                })));
            });
        }
    }, [selectedDevice]);

    return (
        <div>
            <h2 className="text-2xl font-bold mb-6 text-white">Visão Geral da Rede</h2>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-blue-500/50 transition-colors">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Radio size={48} className="text-blue-500" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Total Torres</h3>
                    <p className="text-3xl font-bold text-white mt-2">
                        {loading ? <Loader2 className="animate-spin h-8 w-8 text-blue-500" /> : stats.towers}
                    </p>
                </div>

                <div
                    onClick={() => window.location.href = '/equipments?status=online'}
                    className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-emerald-500/50 transition-colors cursor-pointer"
                >
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Activity size={48} className="text-emerald-500" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Online</h3>
                    <p className="text-3xl font-bold text-emerald-400 mt-2">
                        {loading ? <Loader2 className="animate-spin h-8 w-8 text-emerald-500" /> : stats.online}
                    </p>
                </div>

                <div
                    onClick={() => window.location.href = '/equipments?status=offline'}
                    className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-rose-500/50 transition-colors cursor-pointer"
                >
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <AlertTriangle size={48} className="text-rose-500" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Offline/Crítico</h3>
                    <p className="text-3xl font-bold text-rose-500 mt-2">
                        {loading ? <Loader2 className="animate-spin h-8 w-8 text-rose-500" /> : stats.offline}
                    </p>
                </div>

                <div
                    onClick={() => window.location.href = '/agent'}
                    className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-blue-500/50 transition-colors cursor-pointer"
                >
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Globe size={48} className="text-blue-500" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Agente Sintético</h3>
                    <p className="text-3xl font-bold text-blue-400 mt-2">
                        {loading ? <Loader2 className="animate-spin h-8 w-8 text-blue-500" /> : `${stats.agentSuccess}% OK`}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-1">Disponibilidade de serviços externos</p>
                </div>

                <div
                    onClick={() => window.location.href = '/intelligence'}
                    className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-purple-500/50 transition-colors cursor-pointer"
                >
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <ShieldCheck size={48} className={stats.insights > 0 ? "text-amber-500" : "text-purple-500"} />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">IA Insights</h3>
                    <p className={clsx("text-3xl font-bold mt-2", stats.insights > 0 ? "text-amber-400" : "text-purple-400")}>
                        {loading ? <Loader2 className="animate-spin h-8 w-8 text-purple-500" /> :
                            `${stats.insights} ${stats.insights === 1 ? 'Análise' : 'Análises'}`
                        }
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 h-96 flex flex-col">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold text-white">Disponibilidade e Latência (24h)</h3>
                        <select
                            className="bg-slate-950 border border-slate-700 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2"
                            onChange={(e) => {
                                const dev = devices.find(d => d.id === parseInt(e.target.value));
                                setSelectedDevice(dev);
                            }}
                            value={selectedDevice?.id || ''}
                        >
                            <option value="">Selecione um equipamento</option>
                            {devices.map(d => (
                                <option key={d.id} value={d.id}>{d.name} ({d.ip})</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex-1 min-h-0">
                        {selectedDevice && historyData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={historyData}>
                                    <defs>
                                        <linearGradient id="dashboardSplitColor" x1="0" y1="0" x2="0" y2="1">
                                            {(() => {
                                                const dataMax = Math.max(...historyData.map((d: any) => d.latency));
                                                const max = Math.max(dataMax, historyConfig.critical * 1.1);
                                                const critOff = (max - historyConfig.critical) / max;
                                                const goodOff = (max - historyConfig.good) / max;
                                                return (
                                                    <>
                                                        <stop offset={critOff} stopColor="#fb7185" stopOpacity={0.8} />
                                                        <stop offset={critOff} stopColor="#facc15" stopOpacity={0.8} />
                                                        <stop offset={goodOff} stopColor="#facc15" stopOpacity={0.8} />
                                                        <stop offset={goodOff} stopColor="#4ade80" stopOpacity={0.8} />
                                                        <stop offset={1} stopColor="#4ade80" stopOpacity={0.8} />
                                                    </>
                                                );
                                            })()}
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                    <XAxis dataKey="timeStr" stroke="#64748b" tick={{ fontSize: 10 }} minTickGap={30} />
                                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} label={{ value: 'ms', angle: -90, position: 'insideLeft', fill: '#64748b' }} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc', fontSize: '12px' }}
                                        labelStyle={{ color: '#94a3b8' }}
                                        formatter={(value: any) => [Math.round(value), 'Latência']}
                                    />
                                    <ReferenceLine y={historyConfig.critical} stroke="#fb7185" strokeDasharray="3 3" />
                                    <ReferenceLine y={historyConfig.good} stroke="#4ade80" strokeDasharray="3 3" />
                                    <Area type="monotone" dataKey="latency" stroke="url(#dashboardSplitColor)" fill="url(#dashboardSplitColor)" strokeWidth={2} />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                                {selectedDevice ? 'Sem dados para este período.' : 'Selecione um dispositivo para ver o histórico.'}
                            </div>
                        )}
                    </div>
                </div>

                <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col">
                    <h3 className="text-lg font-semibold text-white mb-4">Provas Sintéticas Recentes</h3>
                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                        <div className="space-y-3">
                            {agentData.slice(0, 10).map((log: any) => (
                                <div key={log.id} className="flex items-center gap-3 p-3 bg-slate-950/50 rounded-lg border border-slate-800/50 group hover:border-slate-700 transition-colors">
                                    <div className={clsx("w-2 h-2 rounded-full", log.success ? "bg-emerald-500" : "bg-red-500 animate-pulse")}></div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-slate-200 truncate">{log.target}</p>
                                        <p className="text-[10px] text-slate-500">{log.test_type.toUpperCase()} • {new Date(log.timestamp).toLocaleTimeString()}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className={clsx("text-sm font-mono font-bold", log.latency_ms > 200 ? "text-amber-400" : "text-emerald-400")}>
                                            {log.latency_ms ? `${Math.round(log.latency_ms)}ms` : '--'}
                                        </p>
                                    </div>
                                </div>
                            ))}
                            {agentData.length === 0 && (
                                <div className="h-full flex items-center justify-center text-slate-500 text-sm py-10">
                                    Sem dados de monitoramento sintético.
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Alertas Recentes</h3>
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded border border-slate-800">
                            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                            <p className="text-sm text-slate-300">Sistema operando normalmente.</p>
                            <span className="ml-auto text-xs text-slate-500">Agora</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
