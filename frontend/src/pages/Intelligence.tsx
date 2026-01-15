import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
    BrainCircuit, ShieldCheck, TrendingUp, CheckCircle2,
    RefreshCw, Power, Activity, Zap, Info, Wifi
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';

interface Insight {
    type: 'security' | 'capacity' | 'performance' | 'system' | 'error' | 'signal';
    severity: 'info' | 'warning' | 'critical';
    title: string;
    description: string;
    recommendation?: string | null;
    timestamp: string;
    equipment_name?: string | null;
    equipment_id?: number | null;
    learning_key?: string | null;
    learning_value?: any;
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
    const [filter, setFilter] = useState<'all' | 'security' | 'capacity' | 'performance' | 'signal'>('all');
    const [pendingSignals, setPendingSignals] = useState<any[]>([]);
    const [signalThreshold, setSignalThreshold] = useState<number>(-70);
    const [savingThreshold, setSavingThreshold] = useState(false);

    const fetchCortexData = async () => {
        try {
            setLoading(true);
            const [insightsRes, signalsRes, settingsRes] = await Promise.all([
                api.get('/cortex/insights'),
                api.get('/cortex/signal-pending'),
                api.get('/cortex/signal-settings')
            ]);

            setConfig(insightsRes.data);
            setPendingSignals(signalsRes.data);
            setSignalThreshold(settingsRes.data.threshold);
        } catch (err) {
            console.error(err);
            toast.error("Erro ao sincronizar com CORTEX AI.");
        } finally {
            setLoading(false);
        }
    };

    const updateThreshold = async (val: number) => {
        try {
            setSavingThreshold(true);
            await api.post(`/cortex/signal-settings?threshold=${val}`);
            setSignalThreshold(val);
            toast.success(`Limite de monitoramento ajustado para ${val}dBm`);
        } catch (err) {
            toast.error("Erro ao salvar configuração.");
        } finally {
            setSavingThreshold(false);
        }
    };

    const handleSignalConfirmation = async (id: number, normal: boolean) => {
        try {
            toast.loading(normal ? "Ensinando IA..." : "Registrando...", { id: 'sig-conf' });
            await api.post(`/cortex/signal-confirm/${id}?normal=${normal}`);
            toast.success(normal ? "Cortex aprendeu o novo padrão!" : "Alerta mantido.", { id: 'sig-conf' });
            // Refresh list
            const signalsRes = await api.get('/cortex/signal-pending');
            setPendingSignals(signalsRes.data);
        } catch (err) {
            toast.error("Erro ao processar confirmação.", { id: 'sig-conf' });
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

    const handleLearn = async (insight: Insight) => {
        if (!insight.equipment_id || !insight.learning_key) return;

        try {
            toast.loading("IA Estudando comportamento...", { id: 'learn' });
            const val = insight.learning_value !== undefined ? insight.learning_value : true;
            await api.post(`/cortex/teach/${insight.equipment_id}?parameter=${insight.learning_key}&value=${val}`);
            toast.success("Cortex aprendeu! Esse comportamento será ignorado.", { id: 'learn' });

            // Remover localmente para feedback imediato
            if (config) {
                setConfig({
                    ...config,
                    insights: config.insights.filter(item => item !== insight)
                });
            }
        } catch (err) {
            toast.error("Erro ao ensinar IA.");
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
                    { id: 'signal', label: 'Sinal (RF)', icon: Wifi },
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
            ) : filter === 'signal' ? (
                <div className="space-y-6">
                    {/* Signal Logic Header */}
                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                            <div className="flex-1">
                                <h3 className="text-white font-bold flex items-center gap-2 mb-1">
                                    <Wifi size={18} className="text-purple-400" />
                                    Monitoramento de Sinal Adaptativo
                                </h3>
                                <p className="text-sm text-slate-400 max-w-xl">
                                    Defina abaixo a partir de qual nível de sinal o Cortex deve considerar uma "anomalia".
                                    A IA aprenderá com suas respostas para ignorar rádios que possuem sinais altos por natureza.
                                </p>
                            </div>

                            <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg flex items-center gap-4 min-w-[300px]">
                                <div className="flex-1">
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-xs font-bold text-slate-500 uppercase">Monitorar acima de:</label>
                                        {savingThreshold && <RefreshCw size={12} className="animate-spin text-purple-400" />}
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="range"
                                            min="-90"
                                            max="-50"
                                            step="1"
                                            value={signalThreshold}
                                            onChange={(e) => updateThreshold(parseInt(e.target.value))}
                                            className="flex-1 accent-purple-500"
                                        />
                                        <span className="text-lg font-mono font-bold text-purple-400 w-12 text-right">{signalThreshold}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Pending Confirmations */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {pendingSignals.length === 0 ? (
                            <div className="col-span-full py-12 text-center bg-slate-900/10 border border-slate-800 border-dashed rounded-xl">
                                <CheckCircle2 className="mx-auto text-slate-600 mb-2" size={32} />
                                <p className="text-slate-500 text-sm">Nenhum sinal suspeito aguardando confirmação no momento.</p>
                            </div>
                        ) : pendingSignals.map(sig => (
                            <div key={sig.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between gap-4 group hover:border-purple-500/30 transition-all">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-white font-bold">{sig.name}</span>
                                        <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded uppercase font-mono">{sig.brand}</span>
                                    </div>
                                    <p className="text-sm text-slate-400 italic">
                                        Sinal atual: <span className="text-rose-400 font-bold">{sig.signal}dBm</span>. Isso é normal?
                                    </p>
                                </div>

                                <div className="flex gap-2">
                                    <button
                                        onClick={() => handleSignalConfirmation(sig.id, true)}
                                        className="px-4 py-2 bg-purple-600/10 hover:bg-purple-600 text-purple-400 hover:text-white rounded-lg text-sm font-bold border border-purple-600/20 transition-all"
                                    >
                                        Sim (Ignorar)
                                    </button>
                                    <button
                                        onClick={() => handleSignalConfirmation(sig.id, false)}
                                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-lg text-sm font-medium border border-slate-700 transition-all"
                                    >
                                        Não
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
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
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase">
                                                <BrainCircuit size={14} /> Recomendação Cortex
                                            </div>
                                            {insight.equipment_id && insight.learning_key && (
                                                <button
                                                    onClick={() => handleLearn(insight)}
                                                    className="text-[10px] font-bold bg-purple-600/10 hover:bg-purple-600 text-purple-400 hover:text-white px-2 py-1 rounded transition-all border border-purple-600/20"
                                                >
                                                    🎓 Aprender
                                                </button>
                                            )}
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
