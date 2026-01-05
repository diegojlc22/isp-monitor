import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { BrainCircuit, ShieldCheck, TrendingUp, CheckCircle2, Trash2, Info, HelpCircle } from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';

interface Insight {
    id: number;
    insight_type: 'security' | 'capacity' | 'performance';
    severity: 'info' | 'warning' | 'critical';
    equipment_id: number | null;
    title: string;
    message: string;
    recommendation: string | null;
    timestamp: string;
    is_dismissed: boolean;
    equipment_name: string | null;
}

const Intelligence: React.FC = () => {
    const [insights, setInsights] = useState<Insight[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'security' | 'capacity'>('all');

    const fetchInsights = async () => {
        try {
            setLoading(true);
            const response = await api.get('/insights/');
            setInsights(response.data);
        } catch (err) {
            console.error(err);
            toast.error("Erro ao carregar análises de IA.");
        } finally {
            setLoading(false);
        }
    };

    const dismissInsight = async (id: number) => {
        try {
            await api.post(`/insights/${id}/dismiss`);
            setInsights(prev => prev.filter(i => i.id !== id));
            toast.success("Análise arquivada.");
        } catch (err) {
            toast.error("Erro ao arquivar.");
        }
    };

    useEffect(() => {
        fetchInsights();
    }, []);

    const filteredInsights = insights.filter(i => filter === 'all' || i.insight_type === filter);

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <div className="p-2 bg-purple-600/20 rounded-lg">
                            <BrainCircuit className="text-purple-400" size={28} />
                        </div>
                        Inteligência de Rede
                    </h1>
                    <p className="text-slate-400 mt-1">
                        Análises automáticas de segurança, capacidade e performance.
                    </p>
                </div>

                <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-lg">
                    <button
                        onClick={() => setFilter('all')}
                        className={clsx(
                            "px-4 py-1.5 rounded-md text-sm font-medium transition-all",
                            filter === 'all' ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"
                        )}
                    >
                        Tudo
                    </button>
                    <button
                        onClick={() => setFilter('security')}
                        className={clsx(
                            "px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                            filter === 'security' ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"
                        )}
                    >
                        <ShieldCheck size={14} /> Segurança
                    </button>
                    <button
                        onClick={() => setFilter('capacity')}
                        className={clsx(
                            "px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                            filter === 'capacity' ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"
                        )}
                    >
                        <TrendingUp size={14} /> Capacidade
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="flex flex-col items-center justify-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mb-4"></div>
                    <p className="text-slate-500 animate-pulse">Processando dados e gerando insights...</p>
                </div>
            ) : filteredInsights.length === 0 ? (
                <div className="bg-slate-900/50 border border-slate-800 border-dashed rounded-2xl py-20 text-center">
                    <div className="bg-slate-800/50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <CheckCircle2 className="text-slate-600" size={32} />
                    </div>
                    <h3 className="text-white font-semibold text-lg">Tudo limpo por aqui!</h3>
                    <p className="text-slate-500 max-w-sm mx-auto mt-2">
                        Nenhum problema de segurança ou alerta de capacidade detectado no momento.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredInsights.map(insight => (
                        <div
                            key={insight.id}
                            className={clsx(
                                "group bg-slate-900 border rounded-2xl overflow-hidden transition-all hover:shadow-2xl hover:shadow-purple-500/10 flex flex-col",
                                insight.severity === 'critical' ? "border-rose-500/30" : "border-slate-800 hover:border-slate-700"
                            )}
                        >
                            <div className="p-5 flex-1">
                                <div className="flex items-start justify-between mb-4">
                                    <div className={clsx(
                                        "p-2 rounded-xl",
                                        insight.severity === 'critical' ? "bg-rose-500/10 text-rose-400" :
                                            insight.severity === 'warning' ? "bg-amber-500/10 text-amber-400" :
                                                "bg-blue-500/10 text-blue-400"
                                    )}>
                                        {insight.insight_type === 'security' ? <ShieldCheck size={24} /> : <TrendingUp size={24} />}
                                    </div>
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-800 px-2 py-1 rounded">
                                        {new Date(insight.timestamp).toLocaleDateString()}
                                    </span>
                                </div>

                                <h3 className="text-white font-bold text-lg mb-2 leading-tight">
                                    {insight.title}
                                </h3>

                                {insight.equipment_name && (
                                    <div className="flex items-center gap-1.5 text-xs font-medium text-purple-400 mb-3">
                                        <Info size={12} />
                                        {insight.equipment_name}
                                    </div>
                                )}

                                <p className="text-slate-400 text-sm whitespace-pre-line">
                                    {insight.message}
                                </p>

                                {insight.recommendation && (
                                    <div className="mt-4 p-3 bg-slate-800/50 rounded-xl border border-slate-800">
                                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300 uppercase tracking-wide mb-1">
                                            <HelpCircle size={14} className="text-blue-400" />
                                            Recomendação
                                        </div>
                                        <p className="text-slate-400 text-xs italic">
                                            {insight.recommendation}
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div className="px-5 py-4 bg-slate-950/50 border-t border-slate-800 flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <div className={clsx(
                                        "w-2 h-2 rounded-full",
                                        insight.severity === 'critical' ? "bg-rose-500 animate-pulse" :
                                            insight.severity === 'warning' ? "bg-amber-500" : "bg-blue-500"
                                    )} />
                                    <span className={clsx(
                                        "text-xs font-bold uppercase",
                                        insight.severity === 'critical' ? "text-rose-500" :
                                            insight.severity === 'warning' ? "text-amber-500" : "text-blue-500"
                                    )}>
                                        {insight.severity === 'critical' ? 'Crítico' : insight.severity === 'warning' ? 'Atenção' : 'Info'}
                                    </span>
                                </div>
                                <button
                                    onClick={() => dismissInsight(insight.id)}
                                    className="p-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
                                    title="Arquivar Análise"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Intelligence;
