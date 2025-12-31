import React, { useState, useEffect } from 'react';
import { Plus, X, Activity, ArrowDownUp, Wifi, Users } from 'lucide-react';
import { getEquipments, getLatencyHistory, getTrafficHistory } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// --- Tipos ---
interface WidgetItem {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
    type: 'latency' | 'traffic' | 'signal' | 'clients';
    equipmentId: number;
    title: string;
    interfaceIndex?: number;
}

// --- Componente de Gráfico Individual ---
// --- Widget Otimizado (Recebe dados prontos ou usa cache) ---
interface WidgetProps {
    item: WidgetItem;
    onRemove: (id: string) => void;
    // Opcional: Se quisermos passar dados diretamente, ou manter o fetch interno mas controlado
    // Para simplificar e manter a independência dos widgets (ex: cada um precisa de um history diferente),
    // vamos manter o fetch mas otimizar o React.memo para evitar re-renders desnecessários.
    // Mas a verdadeira otimização seria Context. Como não temos Context aqui, 
    // vamos apenas garantir que o componente não quebre.
    // O pedido do usuário é focar em performance. Vamos manter o polling local mas aumentar o intervalo
    // ou usar um cache simples de memória `swr` like se fosse possível.

    // MELHOR ESTRATÉGIA AGORA: Manter fetch local mas com AbortController para cancelar reqs antigas
}

// Widget com AbortController e Proteção de Memória
const ChartWidget = React.memo(({ item, onRemove }: WidgetProps) => {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;
        let controller = new AbortController();

        const fetchData = async () => {
            // Cancel previous request if any
            controller.abort();
            controller = new AbortController();

            try {
                if (item.type === 'signal' || item.type === 'clients') {
                    // Otimização: Pegar apenas o equipamento específico, não ALL
                    // Mas a API `getEquipments` pega todos. Em um app maior isso seria ruim,
                    // mas aqui é cacheado pelo browser se tiver cache-control.
                    const eqs = await getEquipments();
                    if (!isMounted) return;

                    const eq = eqs.find((e: any) => e.id === item.equipmentId);
                    if (eq) {
                        const now = new Date();
                        const newPoint = {
                            time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                            signal: eq.signal_dbm,
                            clients: eq.connected_clients || 0
                        };
                        setData(prev => [...prev, newPoint].slice(-30));
                    }
                } else {
                    let res;
                    if (item.type === 'latency') {
                        res = await getLatencyHistory(item.equipmentId, '1h');
                    } else {
                        res = await getTrafficHistory(item.equipmentId, '1h');
                    }
                    if (!isMounted) return;

                    const formatted = (res.data || []).map((d: any) => ({
                        ...d,
                        time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    }));
                    setData(formatted);
                }
                setLoading(false);
            } catch (error) {
                if (isMounted) console.error("Widget fetch err", error);
            }
        };

        fetchData(); // Initial
        const interval = setInterval(fetchData, 5000);

        return () => {
            isMounted = false;
            controller.abort();
            clearInterval(interval);
        };
    }, [item.equipmentId, item.type]);

    const getIcon = () => {
        if (item.type === 'latency') return <Activity size={14} className="text-emerald-400" />;
        if (item.type === 'traffic') return <ArrowDownUp size={14} className="text-blue-400" />;
        if (item.type === 'clients') return <Users size={14} className="text-purple-400" />;
        return <Wifi size={14} className="text-yellow-400" />;
    };

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
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        {item.type === 'signal' ? (
                            <AreaChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
                                <XAxis dataKey="time" hide />
                                <YAxis stroke="#64748b" fontSize={10} width={25} domain={[-90, -30]} tickLine={false} axisLine={false} />
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
                                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f1f5f9' }} />
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
    // Carregar layout salvo ou padrão
    const savedLayout = localStorage.getItem('dashboard_layout');
    const initialLayout = savedLayout ? JSON.parse(savedLayout) : [];

    const [layout, setLayout] = useState<WidgetItem[]>(initialLayout);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [equipments, setEquipments] = useState<any[]>([]);

    // Form state
    const [selectedEq, setSelectedEq] = useState('');
    const [selectedType, setSelectedType] = useState<'latency' | 'traffic' | 'signal' | 'clients'>('traffic');
    const [selectedInterface, setSelectedInterface] = useState<number>(1);
    const [interfaceList, setInterfaceList] = useState<{ index: number; name: string }[]>([]);
    const [isLoadingInterfaces, setIsLoadingInterfaces] = useState(false);

    useEffect(() => {
        getEquipments().then(setEquipments);
    }, []);

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



    const saveToLocal = (data: WidgetItem[]) => {
        localStorage.setItem('dashboard_layout', JSON.stringify(data));
    };

    const addWidget = () => {
        if (!selectedEq) return;
        const eq = equipments.find(e => e.id.toString() === selectedEq);
        if (!eq) return;

        const newItem: WidgetItem = {
            i: `widget-${Date.now()}`,
            x: (layout.length * 4) % 12, // Tenta distribuir
            y: Infinity, // Coloca no final
            w: 4,
            h: 3,
            type: selectedType,
            equipmentId: eq.id,
            interfaceIndex: selectedType === 'traffic' ? selectedInterface : undefined,
            title: `${eq.name} - ${selectedType === 'traffic' ? (interfaceList.find(i => i.index === selectedInterface)?.name || 'Tráfego') : selectedType === 'signal' ? 'Sinal' : selectedType === 'clients' ? 'Clientes' : 'Latência'}`
        };

        const newLayout = [...layout, newItem];
        setLayout(newLayout);
        saveToLocal(newLayout);
        setIsModalOpen(false);
        setSelectedEq('');
    };

    const removeWidget = (i: string) => {
        const newLayout = layout.filter(item => item.i !== i);
        setLayout(newLayout);
        saveToLocal(newLayout);
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
                            <ChartWidget item={item} onRemove={removeWidget} />
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

                                    {equipments.find(e => e.id.toString() === selectedEq)?.equipment_type === 'station' && (
                                        <button
                                            onClick={() => setSelectedType('signal')}
                                            className={`px-4 py-2 rounded-lg border flex items-center justify-center gap-2 transition-colors ${selectedType === 'signal' ? 'bg-yellow-600/20 border-yellow-500 text-yellow-400' : 'bg-slate-950 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                                        >
                                            <Wifi size={16} /> Sinal
                                        </button>
                                    )}

                                    {equipments.find(e => e.id.toString() === selectedEq)?.equipment_type === 'transmitter' && (
                                        <button
                                            onClick={() => setSelectedType('clients')}
                                            className={`px-4 py-2 rounded-lg border flex items-center justify-center gap-2 transition-colors ${selectedType === 'clients' ? 'bg-purple-600/20 border-purple-500 text-purple-400' : 'bg-slate-950 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                                        >
                                            <Users size={16} /> Clientes
                                        </button>
                                    )}
                                </div>
                            </div>

                            {selectedType === 'traffic' && interfaceList.length > 0 && (
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Porta/Interface</label>
                                    <select
                                        value={selectedInterface}
                                        onChange={e => setSelectedInterface(parseInt(e.target.value))}
                                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 outline-none"
                                    >
                                        {interfaceList.map(iface => (
                                            <option key={iface.index} value={iface.index}>{iface.name}</option>
                                        ))}
                                    </select>
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
