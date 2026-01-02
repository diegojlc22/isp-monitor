import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Plus, X, Activity, ArrowDownUp, Wifi, Users, Heart } from 'lucide-react';
import { getEquipments, getLatencyHistory, getTrafficHistory, getLiveStatus } from '../services/api'; // NEW import
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// --- Tipos ---
interface WidgetItem {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
    type: 'latency' | 'traffic' | 'signal' | 'clients' | 'health';
    equipmentId: number;
    title: string;
    interfaceIndex?: number;
}

interface WidgetProps {
    item: WidgetItem;
    onRemove: (id: string) => void;
    liveData?: any; // NEW Prop from Parent
}

// --- Componente de Gráfico Individual ---
// Refatorado para usar cache history + atualizações live do pai
const ChartWidget = React.memo(({ item, onRemove, liveData }: WidgetProps) => {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // 1. Initial Load of History (Once on mount)
    useEffect(() => {
        let isMounted = true;
        const fetchHistory = async () => {
            try {
                if (item.type === 'signal' || item.type === 'clients' || item.type === 'health') {
                    // Sinal e Client histórico não tem API específica, usa Equipamento status
                    // Vamos simular histórico ou iniciar com vazio
                    // Para simplificar, iniciamos o array apenas com o liveData atual se disponível
                    setLoading(false);
                } else {
                    let res;
                    if (item.type === 'latency') {
                        res = await getLatencyHistory(item.equipmentId, '1h');
                    } else {
                        res = await getTrafficHistory(item.equipmentId, '1h');
                    }

                    if (isMounted && res.data) {
                        const formatted = res.data.map((d: any) => ({
                            ...d,
                            time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        }));
                        // Sort by time just in case
                        setData(formatted);
                    }
                    setLoading(false);
                }
            } catch (err) {
                if (isMounted) setLoading(false);
            }
        };
        fetchHistory();
        return () => { isMounted = false; };
    }, [item.equipmentId, item.type]); // Only on Mount or Type Change

    // 2. Watch for Live Updates from Parent
    useEffect(() => {
        if (!liveData) return;

        // liveData contains { traffic: {in, out}, signal: {dbm, ccq}, clients, latency, timestamp }
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        let newPoint: any = {
            time: timeStr,
            cpu: liveData.health?.cpu_usage || 0,
            ram: liveData.health?.memory_usage || 0,
            disk: liveData.health?.disk_usage || 0,
            temp: liveData.health?.temperature || 0,
            volt: liveData.health?.voltage || 0
        };
        let hasData = false;

        if (item.type === 'traffic') {
            newPoint.in_mbps = liveData.traffic.in;
            newPoint.out_mbps = liveData.traffic.out;
            hasData = true;
        } else if (item.type === 'latency') {
            newPoint.latency = liveData.latency;
            hasData = true;
        } else if (item.type === 'signal') {
            newPoint.signal = liveData.signal.dbm;
            hasData = true;
        } else if (item.type === 'clients') {
            newPoint.clients = liveData.clients || 0;
            hasData = true;
        } else if (item.type === 'health') {
            hasData = true;
        }

        if (hasData) {
            setData(prev => {
                // Prevent duplicate timestamps if polling is fast
                const last = prev[prev.length - 1];
                if (last && last.time === timeStr) return prev;

                // Append and slice to keep e.g. 50 points
                return [...prev, newPoint].slice(-50);
            });
        }

    }, [liveData, item.type]);


    const getIcon = () => {
        if (item.type === 'latency') return <Activity size={14} className="text-emerald-400" />;
        if (item.type === 'traffic') return <ArrowDownUp size={14} className="text-blue-400" />;
        if (item.type === 'clients') return <Users size={14} className="text-purple-400" />;
        if (item.type === 'health') return <Heart size={14} className="text-rose-400" />;
        return <Wifi size={14} className="text-yellow-400" />;
    };

    const Gauge = ({ value, label, unit, color, max = 100 }: any) => {
        const radius = 22;
        const circumference = 2 * Math.PI * radius;
        const percentage = Math.min(100, Math.max(0, (value / max) * 100));
        const offset = circumference - (percentage / 100) * circumference;

        return (
            <div className="flex flex-col items-center justify-center flex-1 min-w-0">
                <div className="relative w-12 h-12 sm:w-16 sm:h-16">
                    <svg className="w-full h-full transform -rotate-90">
                        <circle
                            cx="50%"
                            cy="50%"
                            r={radius}
                            stroke="#0f172a"
                            strokeWidth="5"
                            fill="transparent"
                        />
                        <circle
                            cx="50%"
                            cy="50%"
                            r={radius}
                            stroke={color}
                            strokeWidth="5"
                            fill="transparent"
                            strokeDasharray={circumference}
                            strokeDashoffset={offset}
                            strokeLinecap="round"
                            className="transition-all duration-1000 ease-in-out"
                            style={{ filter: `drop-shadow(0 0 2px ${color})` }}
                        />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-[10px] sm:text-xs font-black text-white leading-none">
                            {Math.round(value)}
                        </span>
                        <span className="text-[8px] sm:text-[10px] font-bold text-slate-500 -mt-0.5">{unit}</span>
                    </div>
                </div>
                <span className="text-[9px] sm:text-[10px] uppercase font-black text-slate-300 mt-2 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-700/50">
                    {label}
                </span>
            </div>
        );
    };

    // --- Componente de Gráfico Individual ---
    const latest = data[data.length - 1] || {};

    return (
        <div className="h-full flex flex-col bg-slate-800 rounded-lg shadow-lg border border-slate-700 overflow-hidden">
            <div className="flex justify-between items-center px-3 py-2 bg-slate-900/50 border-b border-slate-700 cursor-move draggable-handle">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    {getIcon()}
                    <span className="truncate max-w-[150px]" title={item.title}>{item.title}</span>
                </div>
                <button onMouseDown={(e) => e.stopPropagation()} onClick={() => onRemove(item.i)} className="text-slate-500 hover:text-rose-500 transition-colors">
                    <X size={14} />
                </button>
            </div>

            <div className="flex-1 min-h-0 p-2 relative">
                {loading && data.length === 0 ? (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-xs">Carregando...</div>
                ) : item.type === 'health' ? (
                    <div className="h-full flex items-center justify-between px-1 gap-1">
                        <Gauge value={latest.cpu || 0} label="CPU" unit="%" color="#ef4444" />
                        <Gauge value={latest.ram || 0} label="RAM" unit="%" color="#3b82f6" />
                        <Gauge value={latest.disk || 0} label="Disk" unit="%" color="#10b981" />
                        <Gauge value={latest.temp || 0} label="Temp" unit="°" color="#f97316" />
                        <Gauge value={latest.volt || 0} label="Volt" unit="V" color="#06b6d4" max={30} />
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        {item.type === 'signal' ? (
                            <AreaChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
                                <XAxis dataKey="time" hide />
                                <YAxis stroke="#64748b" fontSize={10} width={25} domain={['auto', 'auto']} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f1f5f9', fontSize: '12px' }}
                                    itemStyle={{ padding: 0 }}
                                />
                                <Area type="monotone" dataKey="signal" stroke="#facc15" fill="#facc15" fillOpacity={0.1} strokeWidth={2} isAnimationActive={false} />
                            </AreaChart>
                        ) : item.type === 'clients' ? (
                            <AreaChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
                                <XAxis dataKey="time" hide />
                                <YAxis stroke="#64748b" fontSize={10} width={25} allowDecimals={false} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f1f5f9' }} />
                                <Area type="monotone" dataKey="clients" stroke="#c084fc" fill="#c084fc" fillOpacity={0.1} strokeWidth={2} isAnimationActive={false} />
                            </AreaChart>
                        ) : item.type === 'latency' ? (
                            <AreaChart data={data}>
                                <defs>
                                    <linearGradient id={`gradLatency-${item.i}`} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
                                <XAxis dataKey="time" hide />
                                <YAxis stroke="#64748b" fontSize={10} width={25} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f1f5f9' }}
                                    formatter={(value: any) => [Math.round(value), 'Latência']}
                                />
                                <Area type="monotone" dataKey="latency" stroke="#10b981" fill={`url(#gradLatency-${item.i})`} strokeWidth={2} isAnimationActive={false} />
                            </AreaChart>
                        ) : (
                            <AreaChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
                                <XAxis dataKey="time" hide />
                                <YAxis stroke="#64748b" fontSize={10} width={25} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f1f5f9' }} />
                                <Area type="monotone" dataKey="in_mbps" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} strokeWidth={2} name="Down" isAnimationActive={false} />
                                <Area type="monotone" dataKey="out_mbps" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} strokeWidth={2} name="Up" isAnimationActive={false} />
                            </AreaChart>
                        )}
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
});

// --- Página Principal ---
export function LiveMonitor() {
    // 1. Start with empty layout
    const [layout, setLayout] = useState<WidgetItem[]>([]);

    // ... states ...
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [equipments, setEquipments] = useState<any[]>([]);
    const [liveData, setLiveData] = useState<Record<number, any>>({});

    // Form state
    const [selectedEq, setSelectedEq] = useState('');
    const [selectedType, setSelectedType] = useState<'latency' | 'traffic' | 'signal' | 'clients' | 'health'>('traffic');
    const [selectedInterface, setSelectedInterface] = useState<number>(1);
    const [interfaceList, setInterfaceList] = useState<{ index: number; name: string }[]>([]);
    const [isLoadingInterfaces, setIsLoadingInterfaces] = useState(false);

    // Initial Data Load
    useEffect(() => {
        getEquipments().then(setEquipments);

        // Load Layout from Server
        import('../services/api').then(api => {
            api.getDashboardLayout()
                .then(serverLayout => {
                    if (serverLayout && Array.isArray(serverLayout) && serverLayout.length > 0) {
                        setLayout(serverLayout);
                    } else {
                        // Fallback to LocalStorage if Server is empty (Migration)
                        const local = localStorage.getItem('dashboard_layout');
                        if (local) {
                            try {
                                const parsed = JSON.parse(local);
                                if (parsed.length > 0) {
                                    setLayout(parsed);
                                    // Sync to server immediately
                                    api.saveDashboardLayout(parsed);
                                }
                            } catch (e) { }
                        }
                    }
                })
                .catch(err => console.error("Error loading layout", err));
        });
    }, []);

    // NEW: Centralized Safe Poller
    useEffect(() => {
        if (layout.length === 0) return;

        const ids = layout.map(w => w.equipmentId);
        const uniqueIds = Array.from(new Set(ids));

        if (uniqueIds.length === 0) return;

        let isMounted = true;
        let timeoutId: any = null;

        const fetchLive = async () => {
            try {
                const data = await getLiveStatus(uniqueIds);
                if (isMounted) {
                    setLiveData(data);
                }
            } catch (err) {
                console.error("Live poll error", err);
            } finally {
                if (isMounted) {
                    // Schedule next poll ONLY after current one finishes
                    timeoutId = setTimeout(fetchLive, 3000);
                }
            }
        };

        fetchLive(); // Start loop

        return () => {
            isMounted = false;
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [layout]); // Restart poll when layout (devices) changes

    // Load interfaces when equipment and type=traffic change
    useEffect(() => {
        if (selectedEq && selectedType === 'traffic') {
            const eq = equipments.find(e => e.id.toString() === selectedEq);
            if (eq && ['mikrotik', 'ubiquiti', 'mimosa', 'intelbras'].includes(eq.brand)) {
                setIsLoadingInterfaces(true);
                import('../services/api').then(api => {
                    api.scanInterfaces(eq.ip, eq.snmp_community, eq.snmp_port)
                        .then(list => {
                            setInterfaceList(list);
                            if (list.length > 0) {
                                // Default to current or first
                                const current = list.find((l: any) => l.index === eq.snmp_interface_index);
                                setSelectedInterface(current ? current.index : list[0].index);
                            }
                        })
                        .catch(err => {
                            console.error("Erro ao carregar interfaces", err);
                            setInterfaceList([]);
                        })
                        .finally(() => setIsLoadingInterfaces(false));
                });
            } else {
                setInterfaceList([]);
            }
        } else {
            setInterfaceList([]);
        }
    }, [selectedEq, selectedType, equipments]);

    // Persistent Save
    const saveLayout = (newLayout: WidgetItem[]) => {
        setLayout(newLayout);
        // Save to Local (Backup)
        localStorage.setItem('dashboard_layout', JSON.stringify(newLayout));
        // Save to Server (Primary)
        import('../services/api').then(api => api.saveDashboardLayout(newLayout));
    };

    const addWidget = () => {
        if (!selectedEq) return;
        const eq = equipments.find(e => e.id.toString() === selectedEq);
        if (!eq) return;

        const newItem: WidgetItem = {
            i: `widget-${Date.now()}`,
            x: 0,
            y: Infinity,
            w: 4,
            h: 3,
            type: selectedType,
            equipmentId: eq.id,
            interfaceIndex: selectedType === 'traffic' ? selectedInterface : undefined,
            title: `${eq.name} - ${selectedType === 'traffic' ? (interfaceList.find(i => i.index === selectedInterface)?.name || 'Tráfego') : selectedType === 'signal' ? 'Sinal' : selectedType === 'clients' ? 'Clientes' : selectedType === 'health' ? 'Saúde (CPU/T/V)' : 'Latência'}`
        };

        const newLayout = [...layout, newItem];
        saveLayout(newLayout);
        setIsModalOpen(false);
        setSelectedEq('');
    };

    const removeWidget = (i: string) => {
        const newLayout = layout.filter(item => item.i !== i);
        saveLayout(newLayout);
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Monitoramento Ao Vivo</h1>
                    <p className="text-slate-400">Arraste e organize seus gráficos em tempo real</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                >
                    <Plus size={18} />
                    Adicionar Gráfico
                </button>
            </div>

            {/* Grid Area - Simple CSS Grid Implementation (Stable) */}
            {layout.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 border-2 border-dashed border-slate-800 rounded-xl bg-slate-900/50 text-slate-500">
                    <Activity size={48} className="mb-4 opacity-50" />
                    <p className="text-lg">Seu dashboard está vazio.</p>
                    <p className="text-sm">Clique em "Adicionar Gráfico" para começar.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {layout.map(item => (
                        <div key={item.i} className="h-64 relative group">
                            <ChartWidget item={item} onRemove={removeWidget} liveData={liveData[item.equipmentId]} />
                        </div>
                    ))}
                </div>
            )}

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-white">Novo Gráfico</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Equipamento</label>
                                <select
                                    value={selectedEq}
                                    onChange={e => setSelectedEq(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 outline-none"
                                >
                                    <option value="">Selecione...</option>
                                    {equipments.map(eq => (
                                        <option key={eq.id} value={eq.id}>{eq.name} ({eq.ip})</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Tipo de Dados</label>
                                <div className="grid grid-cols-3 gap-2">
                                    <button
                                        onClick={() => setSelectedType('traffic')}
                                        className={`px-4 py-2 rounded-lg border flex items-center justify-center gap-2 transition-colors ${selectedType === 'traffic' ? 'bg-blue-600/20 border-blue-500 text-blue-400' : 'bg-slate-950 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                                    >
                                        <ArrowDownUp size={16} /> Tráfego
                                    </button>
                                    <button
                                        onClick={() => setSelectedType('latency')}
                                        className={`px-4 py-2 rounded-lg border flex items-center justify-center gap-2 transition-colors ${selectedType === 'latency' ? 'bg-emerald-600/20 border-emerald-500 text-emerald-400' : 'bg-slate-950 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                                    >
                                        <Activity size={16} /> Latência
                                    </button>

                                    {equipments.find(e => e.id.toString() === selectedEq)?.equipment_type === 'transmitter' && (
                                        <button
                                            onClick={() => setSelectedType('clients')}
                                            className={`px-4 py-2 rounded-lg border flex items-center justify-center gap-2 transition-colors ${selectedType === 'clients' ? 'bg-purple-600/20 border-purple-500 text-purple-400' : 'bg-slate-950 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                                        >
                                            <Users size={16} /> Clientes
                                        </button>
                                    )}

                                    {equipments.find(e => e.id.toString() === selectedEq)?.equipment_type === 'station' && (
                                        <button
                                            onClick={() => setSelectedType('signal')}
                                            className={`px-4 py-2 rounded-lg border flex items-center justify-center gap-2 transition-colors ${selectedType === 'signal' ? 'bg-yellow-600/20 border-yellow-500 text-yellow-400' : 'bg-slate-950 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                                        >
                                            <Wifi size={16} /> Sinal
                                        </button>
                                    )}

                                    {equipments.find(e => e.id.toString() === selectedEq)?.brand === 'mikrotik' && (
                                        <button
                                            onClick={() => setSelectedType('health')}
                                            className={`px-4 py-2 rounded-lg border flex items-center justify-center gap-2 transition-colors ${selectedType === 'health' ? 'bg-rose-600/20 border-rose-500 text-rose-400' : 'bg-slate-950 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                                        >
                                            <Heart size={16} /> Saúde
                                        </button>
                                    )}
                                </div>
                            </div>

                            {selectedType === 'traffic' && interfaceList.length > 0 && (
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Porta/Interface</label>
                                    <div className="flex gap-2">
                                        <select
                                            value={selectedInterface}
                                            onChange={e => setSelectedInterface(parseInt(e.target.value))}
                                            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 outline-none"
                                        >
                                            {interfaceList.map(iface => (
                                                <option key={iface.index} value={iface.index}>{iface.name}</option>
                                            ))}
                                        </select>
                                        <button
                                            onClick={async () => {
                                                const eq = equipments.find(e => e.id.toString() === selectedEq);
                                                if (eq) {
                                                    const btn = document.getElementById('btn-detect-traffic');
                                                    if (btn) btn.innerText = '...';
                                                    try {
                                                        const { detectBestInterface } = await import('../services/api');
                                                        // Se tiver community específica usa, senão manda undefined pro backend usar a Global
                                                        const comm = eq.snmp_community || undefined;
                                                        const best = await detectBestInterface(eq.ip, comm, eq.snmp_port);
                                                        if (best && best.index) {
                                                            setSelectedInterface(best.index);
                                                            toast.success(`Detectado: ${best.name} (${best.current_mbps} Mbps)`);
                                                        } else {
                                                            toast.error("Nenhum tráfego relevante detectado no momento.");
                                                        }
                                                    } catch (e) {
                                                        console.error(e);
                                                        toast.error("Erro ao detectar tráfego.");
                                                    } finally {
                                                        if (btn) btn.innerText = 'Auto';
                                                    }
                                                }
                                            }}
                                            id="btn-detect-traffic"
                                            className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                                            title="Detectar porta com maior consumo agora"
                                        >
                                            Auto
                                        </button>
                                    </div>
                                </div>
                            )}

                            {selectedType === 'traffic' && isLoadingInterfaces && (
                                <div className="text-xs text-blue-400 animate-pulse">
                                    Buscando interfaces disponíveis...
                                </div>
                            )}

                            <button
                                onClick={addWidget}
                                disabled={!selectedEq}
                                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg mt-4 transition-colors"
                            >
                                Adicionar ao Dashboard
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
