import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
    BrainCircuit, ShieldCheck, TrendingUp, CheckCircle2,
    RefreshCw, Power, Activity, Zap, Info
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';

interface Insight {
    type: 'security' | 'capacity' | 'performance' | 'system' | 'error';
    severity: 'info' | 'warning' | 'critical';
    title: string;
    description: string;
    recommendation?: string | null;
    timestamp: string;
    equipment_name?: string | null;
}

interface CortexConfig {
    enabled: boolean;
    last_run: string | null;
    insights: Insight[];
}

const Intelligence: React.FC = () => {
    const [config, setConfig] = useState<CortexConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [filter, setFilter] = useState<'all' | 'security' | 'capacity' | 'performance'>('all');

    const fetchCortexData = async () => {
        try {
            setLoading(true);
            const response = await api.get('/cortex/insights');
            setConfig(response.data);
        } catch (err) {
            console.error(err);
            toast.error("Erro ao conectar com CORTEX AI.");
        } finally {
            setLoading(false);
        }
    };

    const toggleCortex = async () => {
        if (!config) return;
        const newState = !config.enabled;
        try {
            // Optimistic update
            setConfig({ ...config, enabled: newState });
            await api.post(`/cortex/config?enabled=${newState}`);
            toast.success(newState ? "CORTEX Ativado" : "CORTEX Desativado");
        } catch (err) {
            toast.error("Falha ao alterar estado do CORTEX.");
            setConfig({ ...config, enabled: !newState }); // Rollback
        }
    };

    const forceAnalysis = async () => {
        if (!config?.enabled) {
            toast.error("Ative o CORTEX antes de rodar uma análise.");
            return;
        }
        try {
            setAnalyzing(true);
            const res = await api.post('/cortex/force-run');
            toast.success(`Análise Completa! ${res.data.insights_count} insights gerados.`);
            fetchCortexData(); // Reload results
        } catch (err) {
            toast.error("Erro ao executar análise manual.");
        } finally {
            setAnalyzing(false);
        }
    };

    useEffect(() => {
        fetchCortexData();
    }, []);

    const filteredInsights = config?.insights.filter(i => {
        if (filter === 'all') return true;
        return i.type === filter;
    }) || [];

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header Section */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-32 bg-purple-600/10 blur-[100px] rounded-full pointer-events-none" />

                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className={clsx(
                                "p-3 rounded-xl transition-all",
                                config?.enabled ? "bg-purple-600/20 text-purple-400 shadow-lg shadow-purple-500/10" : "bg-slate-800 text-slate-500"
                            )}>
                                <BrainCircuit size={32} strokeWidth={1.5} />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-white tracking-tight">
                                    CORTEX <span className="text-purple-500">AI</span>
                                </h1>
                                <div className="flex items-center gap-2">
                                    <div className={clsx("w-2 h-2 rounded-full animate-pulse", config?.enabled ? "bg-green-500" : "bg-slate-600")} />
                                    <span className="text-xs font-medium text-slate-400 uppercase tracking-widest">
                                        {config?.enabled ? "Operacional" : "Offline / Standby"}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <p className="text-slate-400 max-w-lg text-sm leading-relaxed mt-2">
                            Sistema de Inteligência Operacional de Nível 3. Monitoramento proativo de segurança,
                            capacidade e performance da infraestrutura.
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={forceAnalysis}
                            disabled={analyzing || !config?.enabled}
                            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <RefreshCw size={16} className={clsx(analyzing && "animate-spin")} />
                            {analyzing ? "Analisando..." : "Rodar Análise"}
                        </button>

                        <button
                            onClick={toggleCortex}
                            className={clsx(
                                "flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-bold transition-all shadow-lg",
                                config?.enabled
                                    ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:shadow-purple-500/25 hover:scale-105"
                                    : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
                            )}
                        >
                            <Power size={18} />
                            {config?.enabled ? "ATIVADO" : "DESATIVADO"}
                        </button>
                    </div>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2 border-b border-slate-800 pb-1">
                {[
                    { id: 'all', label: 'Visão Geral', icon: Activity },
                    { id: 'security', label: 'Segurança', icon: ShieldCheck },
                    { id: 'capacity', label: 'Capacidade', icon: TrendingUp },
                    { id: 'performance', label: 'Performance', icon: Zap },
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setFilter(tab.id as any)}
                        className={clsx(
                            "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-lg transition-all relative top-[1px]",
                            filter === tab.id
                                ? "bg-slate-900 border-x border-t border-slate-800 text-purple-400"
                                : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
                        )}
                    >
                        <tab.icon size={16} />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Insights Grid */}
            {loading ? (
                <div className="flex flex-col items-center justify-center py-32 opacity-50">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-500 mb-4"></div>
                    <p className="text-slate-400 text-sm animate-pulse">Sincronizando com Núcleo Neural...</p>
                </div>
            ) : filteredInsights.length === 0 ? (
                <div className="text-center py-20 bg-slate-900/20 border border-slate-800 border-dashed rounded-xl">
                    <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-500">
                        <CheckCircle2 size={32} />
                    </div>
                    <h3 className="text-white font-medium">Nenhum insight crítico detectado</h3>
                    <p className="text-slate-500 text-sm mt-1 max-w-sm mx-auto">
                        Seus sistemas de {filter === 'all' ? 'rede' : filter} parecem estar operando dentro dos parâmetros normais.
                    </p>
                    <button onClick={forceAnalysis} className="mt-4 text-purple-400 text-sm hover:underline">
                        Forçar nova verificação
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filteredInsights.map((insight, idx) => (
                        <div
                            key={idx}
                            className={clsx(
                                "flex flex-col bg-slate-900 border rounded-xl overflow-hidden transition-all hover:scale-[1.01]",
                                insight.severity === 'critical' ? "border-rose-500/40 shadow-rose-900/10 shadow-lg" :
                                    insight.severity === 'warning' ? "border-amber-500/40" : "border-slate-800"
                            )}
                        >
                            {/* Header Stripe */}
                            <div className={clsx(
                                "h-1 w-full",
                                insight.severity === 'critical' ? "bg-rose-500" :
                                    insight.severity === 'warning' ? "bg-amber-500" : "bg-blue-500"
                            )} />

                            <div className="p-6 flex-1 flex flex-col">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
                                        <span className={clsx(
                                            "px-2 py-0.5 rounded text-[10px]",
                                            insight.type === 'security' ? "bg-rose-500/10 text-rose-400" :
                                                insight.type === 'capacity' ? "bg-blue-500/10 text-blue-400" :
                                                    "bg-amber-500/10 text-amber-400"
                                        )}>
                                            {insight.type}
                                        </span>
                                        <span>•</span>
                                        <span>{new Date(insight.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                    <Info
                                        size={16}
                                        className={clsx(
                                            insight.severity === 'critical' ? "text-rose-500" :
                                                insight.severity === 'warning' ? "text-amber-500" : "text-blue-500"
                                        )}
                                    />
                                </div>

                                <h3 className="text-lg font-bold text-white mb-2 leading-tight">
                                    {insight.title}
                                </h3>

                                <p className="text-slate-400 text-sm mb-6 flex-1">
                                    {insight.description}
                                </p>

                                {insight.recommendation && (
                                    <div className="mt-auto pt-4 border-t border-slate-800">
                                        <div className="flex items-center gap-2 mb-1 text-xs font-bold text-purple-400 uppercase">
                                            <BrainCircuit size={14} /> Recomendação Cortex
                                        </div>
                                        <p className="text-slate-300 text-sm italic bg-slate-800/50 p-3 rounded-lg border border-slate-800/50">
                                            "{insight.recommendation}"
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Intelligence;
