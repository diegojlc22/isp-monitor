import { useState, useEffect, useCallback } from 'react';
import { Plus, X, Activity, ArrowDownUp } from 'lucide-react';
import { getEquipments, getLatencyHistory, getTrafficHistory } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// --- Tipos ---
interface WidgetItem {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
    type: 'latency' | 'traffic';
    equipmentId: number;
    title: string;
}

// --- Componente de Gráfico Individual ---
const ChartWidget = ({ item, onRemove }: { item: WidgetItem, onRemove: (id: string) => void }) => {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            let res;
            if (item.type === 'latency') {
                res = await getLatencyHistory(item.equipmentId, '1h'); // Última hora para "Live"
            } else {
                res = await getTrafficHistory(item.equipmentId, '1h');
            }
            // Formatar data se necessário
            const formatted = res.map((d: any) => ({
                ...d,
                time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }));
            setData(formatted);
        } catch (error) {
            console.error("Erro ao buscar dados do widget", error);
        } finally {
            setLoading(false);
        }
    }, [item.equipmentId, item.type]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Atualiza a cada 5s
        return () => clearInterval(interval);
    }, [fetchData]);

    return (
        <div className="h-full flex flex-col bg-slate-800 rounded-lg shadow-lg border border-slate-700 overflow-hidden">
            <div className="flex justify-between items-center px-3 py-2 bg-slate-900/50 border-b border-slate-700 cursor-move draggable-handle">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    {item.type === 'latency' ? <Activity size={14} className="text-emerald-400" /> : <ArrowDownUp size={14} className="text-blue-400" />}
                    {item.title}
                </div>
                <button onMouseDown={(e) => e.stopPropagation()} onClick={() => onRemove(item.i)} className="text-slate-500 hover:text-rose-500 transition-colors">
                    <X size={14} />
                </button>
            </div>

            <div className="flex-1 min-h-0 p-2">
                {loading && data.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-slate-500 text-sm">Carregando...</div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        {item.type === 'latency' ? (
                            <AreaChart data={data}>
                                <defs>
                                    <linearGradient id={`gradLatency-${item.i}`} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                                <XAxis dataKey="time" hide />
                                <YAxis stroke="#94a3b8" fontSize={10} width={30} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                    itemStyle={{ color: '#10b981' }}
                                    formatter={(value: any) => [`${value}ms`, 'Latência']}
                                />
                                <Area type="monotone" dataKey="latency" stroke="#10b981" fill={`url(#gradLatency-${item.i})`} strokeWidth={2} isAnimationActive={false} />
                            </AreaChart>
                        ) : (
                            <AreaChart data={data}>
                                <defs>
                                    <linearGradient id={`gradIn-${item.i}`} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id={`gradOut-${item.i}`} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                                <XAxis dataKey="time" hide />
                                <YAxis stroke="#94a3b8" fontSize={10} width={30} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                    formatter={(value: any) => [`${value} Mbps`, '']}
                                />
                                <Area type="monotone" dataKey="in" stackId="1" stroke="#3b82f6" fill={`url(#gradIn-${item.i})`} strokeWidth={2} name="Download" isAnimationActive={false} />
                                <Area type="monotone" dataKey="out" stackId="1" stroke="#8b5cf6" fill={`url(#gradOut-${item.i})`} strokeWidth={2} name="Upload" isAnimationActive={false} />
                            </AreaChart>
                        )}
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
};

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
    const [selectedType, setSelectedType] = useState<'latency' | 'traffic'>('traffic');

    useEffect(() => {
        getEquipments().then(setEquipments);
    }, []);



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
            title: `${eq.name} (${selectedType === 'traffic' ? 'Tráfego' : 'Latência'})`
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
                                <div className="grid grid-cols-2 gap-2">
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
                                </div>
                            </div>

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
