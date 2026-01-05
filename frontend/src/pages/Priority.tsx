import { useState, useEffect, useCallback, useMemo } from 'react';
import { getEquipments, updateEquipment } from '../services/api';
import { Zap, Server, Search, Wifi, Trash2, Plus, ArrowRight } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import clsx from 'clsx';
import toast from 'react-hot-toast';

interface Equipment {
    id: number;
    name: string;
    ip: string;
    is_online: boolean;
    is_priority: boolean;
    last_traffic_in?: number;
    last_traffic_out?: number;
    brand?: string;
}

export function Priority() {
    const [equipments, setEquipments] = useState<Equipment[]>([]);
    const [allEquipments, setAllEquipments] = useState<Equipment[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [showAddModal, setShowAddModal] = useState(false);
    const [searchAdd, setSearchAdd] = useState('');

    const load = useCallback(async () => {
        try {
            const data = await getEquipments();
            setAllEquipments(data);
            setEquipments(data.filter((e: Equipment) => e.is_priority));
        } catch (e) {
            toast.error('Erro ao carregar equipamentos.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const handleTogglePriority = async (eq: Equipment) => {
        try {
            await updateEquipment(eq.id, { is_priority: !eq.is_priority });
            toast.success(eq.is_priority ? 'Removido dos prioritários' : 'Adicionado aos prioritários');
            load();
        } catch (e) {
            toast.error('Erro ao atualizar status.');
        }
    };

    const filteredEquipments = useMemo(() => {
        return equipments.filter(e =>
            e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            e.ip.includes(searchTerm)
        );
    }, [equipments, searchTerm]);

    const availableToAdd = useMemo(() => {
        return allEquipments.filter(e =>
            !e.is_priority &&
            (e.name.toLowerCase().includes(searchAdd.toLowerCase()) || e.ip.includes(searchAdd))
        );
    }, [allEquipments, searchAdd]);

    const metrics = useMemo(() => {
        const total = equipments.length;
        const online = equipments.filter(e => e.is_online).length;
        const heavyTraffic = equipments.filter(e => (e.last_traffic_in || 0) > 50).length;
        return { total, online, heavyTraffic };
    }, [equipments]);

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center bg-slate-950">
                <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    return (
        <div className="p-6 h-full flex flex-col bg-slate-950 text-slate-200">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
                        <Zap className="text-yellow-500 fill-yellow-500" size={32} />
                        Monitoramento Prioritário
                    </h1>
                    <p className="text-slate-400 mt-1">Gerencie os equipamentos críticos da sua rede.</p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-bold transition-all shadow-lg shadow-blue-900/20"
                >
                    <Plus size={20} /> Adicionar Prioritário
                </button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <MetricCard
                    title="Equipamentos Críticos"
                    value={metrics.total}
                    icon={Zap}
                    description="Total sob análise prioritária"
                />
                <MetricCard
                    title="Disponibilidade"
                    value={`${metrics.total > 0 ? Math.round((metrics.online / metrics.total) * 100) : 100}%`}
                    status={metrics.online === metrics.total ? 'good' : 'average'}
                    icon={Wifi}
                    description={`${metrics.online} de ${metrics.total} online`}
                />
                <MetricCard
                    title="Tráfego Intenso"
                    value={metrics.heavyTraffic}
                    icon={Server}
                    description="Links com uso acima de 50 Mbps"
                />
            </div>

            <div className="flex-1 bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-col overflow-hidden backdrop-blur-sm">
                <div className="flex gap-4 mb-6 shrink-0">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                        <input
                            type="text"
                            placeholder="Buscar nos prioritários..."
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto min-h-0 custom-scrollbar pr-2">
                    {filteredEquipments.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-500 italic py-20">
                            <Zap size={64} className="mb-4 opacity-10" />
                            <p>Nenhum equipamento cadastrado nesta aba.</p>
                            <button
                                onClick={() => setShowAddModal(true)}
                                className="mt-4 text-blue-400 hover:text-blue-300 font-bold flex items-center gap-1"
                            >
                                Adicionar o primeiro <ArrowRight size={16} />
                            </button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                            {filteredEquipments.map(eq => (
                                <div key={eq.id} className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl flex items-center justify-between group hover:border-blue-500/30 transition-all shadow-sm">
                                    <div className="flex items-center gap-4">
                                        <div className={clsx("w-3 h-3 rounded-full", eq.is_online ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]" : "bg-rose-500")}></div>
                                        <div>
                                            <h4 className="font-bold text-white mb-0.5">{eq.name}</h4>
                                            <p className="text-xs font-mono text-slate-500">{eq.ip}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <div className="text-right hidden sm:block">
                                            <p className="text-[10px] uppercase font-bold text-slate-600 mb-0.5 tracking-wider">Último Tráfego</p>
                                            <p className="text-xs text-blue-400 font-mono">
                                                ↓ {eq.last_traffic_in ? (eq.last_traffic_in).toFixed(1) : 0} Mbps
                                                <span className="text-slate-700 mx-1">/</span>
                                                ↑ {eq.last_traffic_out ? (eq.last_traffic_out).toFixed(1) : 0} Mbps
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => handleTogglePriority(eq)}
                                            className="p-2 text-slate-500 hover:text-rose-500 hover:bg-rose-500/10 rounded-lg transition-all"
                                            title="Remover das prioridades"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Modal de Adição */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg overflow-hidden flex flex-col max-h-[80vh] shadow-2xl animate-in zoom-in-95 fade-in duration-200">
                        <header className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                            <div>
                                <h3 className="text-xl font-bold text-white">Adicionar Prioritário</h3>
                                <p className="text-xs text-slate-500">Selecione equipamentos da rede para análise avançada.</p>
                            </div>
                            <button onClick={() => setShowAddModal(false)} className="text-slate-500 hover:text-white transition-colors">Fechar</button>
                        </header>

                        <div className="p-4 bg-slate-950/50 shrink-0">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" size={16} />
                                <input
                                    type="text"
                                    placeholder="Buscar por nome ou IP..."
                                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500"
                                    value={searchAdd}
                                    onChange={(e) => setSearchAdd(e.target.value)}
                                    autoFocus
                                />
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-2 min-h-0 custom-scrollbar">
                            {availableToAdd.length === 0 ? (
                                <div className="text-center py-10 text-slate-500 text-sm">Nenhum equipamento disponível encontrado.</div>
                            ) : (
                                availableToAdd.map(eq => (
                                    <div key={eq.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 group transition-colors border border-transparent hover:border-slate-700">
                                        <div>
                                            <p className="font-bold text-slate-200 group-hover:text-white transition-colors text-sm">{eq.name}</p>
                                            <p className="text-[10px] font-mono text-slate-500">{eq.ip}</p>
                                        </div>
                                        <button
                                            onClick={() => handleTogglePriority(eq)}
                                            className="bg-slate-800 hover:bg-blue-600 text-slate-400 hover:text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all border border-slate-700 flex items-center gap-2"
                                        >
                                            <Plus size={14} /> Selecionar
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Priority;
