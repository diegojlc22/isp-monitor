
import React, { useEffect, useState } from 'react';
import {
    getAgentStatus,
    getMonitorTargets,
    createMonitorTarget,
    deleteMonitorTarget,
    triggerAgentTest,
    stopAgentTest,
    clearAgentLogs,
    getAgentLogs,
    getAgentSettings,
    updateAgentSettings,
    updateMonitorTarget
} from '../services/api';
import { Activity, Globe, Play, AlertTriangle, Plus, Trash2, X, Settings, ChevronDown, ChevronUp, RefreshCw, Eraser, Pencil, Check, TrendingUp, ShieldCheck } from 'lucide-react';
import { AreaChart, Area, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import toast from 'react-hot-toast';
import clsx from 'clsx';

interface SyntheticLog {
    id: number;
    test_type: string;
    target: string;
    latency_ms: number | null;
    success: boolean;
    timestamp: string;
}

interface MonitorTarget {
    id: number;
    name: string;
    target: string;
    type: string;
}

const Agent: React.FC = () => {
    const [logs, setLogs] = useState<SyntheticLog[]>([]);
    const [targets, setTargets] = useState<MonitorTarget[]>([]);
    const [loading, setLoading] = useState(false);
    const [showLogs, setShowLogs] = useState(true);

    // Modals
    const [showModal, setShowModal] = useState(false);
    const [showSettingsModal, setShowSettingsModal] = useState(false);

    // Add Target Form
    const [newName, setNewName] = useState('');
    const [newTarget, setNewTarget] = useState('');
    const [newType, setNewType] = useState('http');
    const [newIsPriority, setNewIsPriority] = useState(false);

    // Editing State
    const [editingTargetId, setEditingTargetId] = useState<number | null>(null);
    const [editingName, setEditingName] = useState('');

    // Settings Form
    const [latencyThreshold, setLatencyThreshold] = useState(300);
    const [anomalyCycles, setAnomalyCycles] = useState(2);
    const [checkInterval, setCheckInterval] = useState(300);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [resLogs, resTargets] = await Promise.all([
                getAgentLogs(200), // Increased limit for better charts
                getMonitorTargets()
            ]);
            setLogs(resLogs);
            setTargets(resTargets);
        } catch (err) {
            console.error(err);
            toast.error('Erro ao buscar dados.');
        } finally {
            setLoading(false);
        }
    };

    const fetchSettings = async () => {
        try {
            const res = await getAgentSettings();
            setLatencyThreshold(parseInt(res.agent_latency_threshold || '300'));
            setAnomalyCycles(parseInt(res.agent_anomaly_cycles || '2'));
            setCheckInterval(parseInt(res.agent_check_interval || '300'));
            setShowSettingsModal(true);
        } catch (err) {
            toast.error('Erro ao carregar configurações.');
        }
    };

    const saveSettings = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await updateAgentSettings({
                latency_threshold: latencyThreshold,
                anomaly_cycles: anomalyCycles,
                check_interval: checkInterval
            });
            toast.success('Configurações salvas!');
            setShowSettingsModal(false);
        } catch (err) {
            toast.error('Erro ao salvar configurações.');
        }
    };

    const handleAddTarget = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName || !newTarget) return;

        try {
            await createMonitorTarget({
                name: newName,
                target: newTarget,
                type: newType,
                is_priority: newIsPriority
            });
            toast.success(newIsPriority ? 'Alvo prioritário adicionado! Monitoramento automático ativado.' : 'Alvo adicionado!');
            setShowModal(false);
            setNewName('');
            setNewTarget('');
            setNewIsPriority(false);
            fetchData();
        } catch (err) {
            toast.error('Erro ao adicionar alvo.');
        }
    };

    const startEditing = (target: MonitorTarget) => {
        setEditingTargetId(target.id);
        setEditingName(target.name);
    };

    const saveEdit = async () => {
        if (!editingTargetId || !editingName.trim()) return;
        try {
            await updateMonitorTarget(editingTargetId, { name: editingName });
            toast.success('Nome atualizado!');
            setEditingTargetId(null);
            fetchData();
        } catch (err: any) {
            console.error(err);
            const msg = err.response?.data?.detail || err.message || 'Erro desconhecido';
            toast.error(`Erro ao atualizar: ${msg}`);
        }
    };

    const cancelEdit = () => {
        setEditingTargetId(null);
        setEditingName('');
    };

    const handleDeleteTarget = async (id: number) => {
        if (!confirm('Remover monitoramento deste alvo?')) return;
        try {
            await deleteMonitorTarget(id);
            toast.success('Alvo removido.');
            fetchData();
        } catch (err) {
            toast.error('Erro ao remover.');
        }
    };

    const clearLogs = async () => {
        if (!confirm("Limpar todo o histórico de testes sintéticos?")) return;
        try {
            await clearAgentLogs();
            toast.success("Logs limpos!");
            fetchData();
        } catch (err) {
            toast.error("Erro ao limpar log.");
        }
    };

    const [testing, setTesting] = useState(false);
    const [manualRunning, setManualRunning] = useState(false);

    const checkStatus = async () => {
        try {
            const status = await getAgentStatus();
            setManualRunning(status.manual_loop_running || false);
        } catch (e) { /* ignore */ }
    };

    const triggerTest = async () => {
        setTesting(true);
        try {
            await triggerAgentTest();
            toast.success('Loop de teste contínuo INICIADO.');
            setTesting(false);
            setManualRunning(true);
        } catch (err) {
            toast.error('Erro ao iniciar teste.');
            setTesting(false);
        }
    };

    const stopTest = async () => {
        try {
            await stopAgentTest();
            toast('Sinal de parada enviado.', { icon: '🛑' });
            setManualRunning(false);
        } catch (err) {
            toast.error('Erro ao parar o teste.');
        }
    };

    useEffect(() => {
        fetchData();
        checkStatus();
        const interval = setInterval(() => {
            fetchData();
            checkStatus();
        }, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent flex items-center gap-2">
                        <Activity className="h-8 w-8 text-purple-500" />
                        Agente Inteligente
                    </h1>
                    <p className="text-gray-400">Monitoramento sintético (DNS, Web) e detecção de anomalias.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchSettings}
                        className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors text-slate-400 hover:text-white"
                        title="Configurações do Agente"
                    >
                        <Settings size={20} />
                    </button>
                    <button
                        onClick={() => setShowModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors font-medium text-slate-200"
                    >
                        <Plus size={18} />
                        Novo Alvo
                    </button>
                    {manualRunning ? (
                        <button
                            onClick={stopTest}
                            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium animate-pulse"
                        >
                            <X size={18} />
                            Parar Testes
                        </button>
                    ) : (
                        <button
                            onClick={triggerTest}
                            disabled={testing}
                            className={clsx("flex items-center gap-2 px-4 py-2 rounded-lg transition-colors font-medium", testing ? "bg-purple-800 text-purple-300 cursor-not-allowed" : "bg-purple-600 hover:bg-purple-700 text-white")}
                        >
                            {testing ? <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" /> : <Play size={18} />}
                            {testing ? "Iniciando..." : "Rodar Teste Agora"}
                        </button>
                    )}
                </div>
            </div>

            {/* Alvos Configurados */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {targets.map(t => (
                    <div key={t.id} className="bg-slate-900 border border-slate-800 p-4 rounded-lg flex justify-between items-center group">
                        <div className="flex-1 min-w-0 mr-4">
                            {editingTargetId === t.id ? (
                                <div className="flex items-center gap-2 mb-1">
                                    <input
                                        type="text"
                                        value={editingName}
                                        onChange={e => setEditingName(e.target.value)}
                                        className="bg-slate-800 border border-slate-700 text-white text-sm rounded px-2 py-1 w-full outline-none focus:ring-1 focus:ring-purple-500"
                                        autoFocus
                                        onKeyDown={e => e.key === 'Enter' && saveEdit()}
                                    />
                                    <button onClick={saveEdit} className="text-green-400 hover:text-green-300 p-1"><Check size={16} /></button>
                                    <button onClick={cancelEdit} className="text-slate-500 hover:text-slate-300 p-1"><X size={16} /></button>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2">
                                    <h4 className="font-semibold text-slate-200 group-hover:text-purple-400 transition-colors truncate">{t.name}</h4>
                                    <button
                                        onClick={() => startEditing(t)}
                                        className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-purple-400 transition-all p-1"
                                    >
                                        <Pencil size={12} />
                                    </button>
                                </div>
                            )}
                            <p className="text-xs text-slate-500 font-mono text-ellipsis overflow-hidden w-full max-w-[150px]" title={t.target}>{t.target}</p>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] uppercase bg-slate-800 px-1.5 py-0.5 rounded text-slate-400 border border-slate-700">{t.type}</span>
                                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                            </div>
                        </div>
                        <button onClick={() => handleDeleteTarget(t.id)} className="text-slate-600 hover:text-red-500 transition-colors p-2 hover:bg-slate-800 rounded-full">
                            <Trash2 size={16} />
                        </button>
                    </div>
                ))}
                {targets.length === 0 && (
                    <div className="col-span-4 text-center py-4 text-slate-500 text-sm bg-slate-900/50 rounded-lg border border-slate-800 border-dashed">
                        Nenhum alvo personalizado. Usando padrões.
                    </div>
                )}
            </div>

            {/* Cards de Resumo Modernizados */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg hover:border-blue-500/50 transition-all">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Globe className="text-blue-500" size={20} />
                        </div>
                        <span className="text-[10px] font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded uppercase">Internet Ops</span>
                    </div>
                    <div>
                        <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">Status Web</p>
                        <h3 className="text-2xl font-bold text-white mt-1">Normal</h3>
                        <p className="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
                            <ShieldCheck size={12} className="text-emerald-500" /> Todos os serviços respondendo
                        </p>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg hover:border-purple-500/50 transition-all">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-purple-500/10 rounded-lg">
                            <Activity className="text-purple-500" size={20} />
                        </div>
                        <span className="text-[10px] font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded uppercase">Desempenho</span>
                    </div>
                    <div>
                        <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">Média Latência</p>
                        <h3 className="text-2xl font-bold text-white mt-1">
                            {logs.length > 0 ? Math.round(logs.reduce((acc, l) => acc + (l.latency_ms || 0), 0) / logs.length) : 0}ms
                        </h3>
                        <p className="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
                            <TrendingUp size={12} className="text-purple-500" /> Baseado nos últimos 200 testes
                        </p>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg hover:border-emerald-500/50 transition-all">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-emerald-500/10 rounded-lg">
                            <ShieldCheck className="text-emerald-500" size={20} />
                        </div>
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded uppercase">Disponibilidade</span>
                    </div>
                    <div>
                        <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">Taxa de Sucesso</p>
                        <h3 className="text-2xl font-bold text-white mt-1">
                            {logs.length > 0 ? Math.round((logs.filter(l => l.success).length / logs.length) * 100) : 100}%
                        </h3>
                        <p className="text-[10px] text-slate-400 mt-1 flex items-center gap-1 tracking-tight">
                            Controle sintético contínuo
                        </p>
                    </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg hover:border-amber-500/50 transition-all">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-amber-500/10 rounded-lg">
                            <AlertTriangle className="text-amber-500" size={20} />
                        </div>
                        <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded uppercase">Alertas AI</span>
                    </div>
                    <div>
                        <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">Anomalias Hoje</p>
                        <h3 className="text-2xl font-bold text-white mt-1">
                            {logs.filter(l => l.timestamp.includes(new Date().toISOString().split('T')[0]) && !l.success).length}
                        </h3>
                        <p className="text-[10px] text-slate-400 mt-1">Detectadas pelo motor CORTEX</p>
                    </div>
                </div>
            </div>

            {/* Visualização de Latência por Alvo */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {targets.map(target => {
                    const targetLogs = logs.filter(l => l.target === target.target).slice(0, 30).reverse();
                    return (
                        <div key={target.id} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
                            <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/30">
                                <div>
                                    <h4 className="text-sm font-bold text-slate-200">{target.name}</h4>
                                    <p className="text-[10px] text-slate-500 font-mono">{target.target}</p>
                                </div>
                                <div className="text-right">
                                    <span className="text-xl font-black text-white font-mono">
                                        {targetLogs.length > 0 ? Math.round(targetLogs[targetLogs.length - 1].latency_ms || 0) : 0}ms
                                    </span>
                                </div>
                            </div>
                            <div className="h-40 w-full p-2 bg-slate-950/20">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={targetLogs}>
                                        <defs>
                                            <linearGradient id={`colorLat-${target.id}`} x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', fontSize: '12px' }}
                                            itemStyle={{ color: '#8b5cf6' }}
                                            labelStyle={{ display: 'none' }}
                                        />
                                        <Area
                                            type="monotone"
                                            dataKey="latency_ms"
                                            stroke="#8b5cf6"
                                            strokeWidth={2}
                                            fillOpacity={1}
                                            fill={`url(#colorLat-${target.id})`}
                                            animationDuration={1500}
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Histórico de Testes */}
            <div className="card bg-gray-800 border border-gray-700/50 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-gray-700/50 flex justify-between items-center bg-gray-800/50">
                    <div className="flex items-center gap-3">
                        <h2 className="font-bold flex items-center gap-2">
                            Histórico de Testes Sintéticos
                        </h2>
                        {manualRunning && (
                            <span className="flex items-center gap-1.5 px-2 py-0.5 bg-green-500/10 text-green-400 text-[10px] font-bold uppercase tracking-wider rounded border border-green-500/20">
                                <div className="w-1 h-1 rounded-full bg-green-400 animate-ping"></div>
                                Live Monitoring
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={clearLogs}
                            className="p-2 hover:bg-red-500/10 text-gray-500 hover:text-red-400 transition-colors rounded-lg"
                            title="Limpar Logs"
                        >
                            <Eraser size={18} />
                        </button>
                        <button
                            onClick={fetchData}
                            disabled={loading}
                            className="p-2 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors rounded-lg"
                        >
                            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                        </button>
                        <button
                            onClick={() => setShowLogs(!showLogs)}
                            className="p-2 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors rounded-lg"
                        >
                            {showLogs ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>
                    </div>
                </div>

                {showLogs && (
                    <div className="overflow-x-auto max-h-[400px] overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse">
                            <thead className="text-xs uppercase text-gray-500 bg-gray-900/30 sticky top-0">
                                <tr>
                                    <th className="px-6 py-3 font-semibold">Horário</th>
                                    <th className="px-6 py-3 font-semibold">Tipo</th>
                                    <th className="px-6 py-3 font-semibold">Alvo</th>
                                    <th className="px-6 py-3 font-semibold">Latência</th>
                                    <th className="px-6 py-3 font-semibold">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700/30">
                                {logs.map((log) => (
                                    <tr key={log.id} className="hover:bg-gray-700/20 transition-colors group">
                                        <td className="px-6 py-4 text-sm text-gray-400 font-mono">
                                            {new Date(log.timestamp).toLocaleTimeString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-[10px] uppercase bg-gray-900 px-2 py-0.5 rounded border border-gray-700 font-bold text-gray-400">
                                                {log.test_type}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm font-medium text-gray-200">{log.target}</td>
                                        <td className="px-6 py-4">
                                            {log.latency_ms ? (
                                                <span className={clsx(
                                                    "font-mono text-sm font-bold",
                                                    log.latency_ms > 200 ? "text-amber-400" : "text-green-400"
                                                )}>
                                                    {Math.round(log.latency_ms)}ms
                                                </span>
                                            ) : (
                                                <span className="text-gray-600">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            {log.success ? (
                                                <span className="inline-flex items-center gap-1 text-green-400 text-xs font-bold">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-green-400"></div>
                                                    SUCESSO
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 text-red-500 text-xs font-bold">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></div>
                                                    FALHA
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                                {logs.length === 0 && !loading && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-10 text-center text-gray-500">
                                            Nenhum log encontrado.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Modal Novo Alvo */}
            {showModal && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
                        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Plus size={20} className="text-purple-500" />
                                Adicionar Novo Alvo
                            </h3>
                            <button onClick={() => setShowModal(false)} className="text-slate-500 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleAddTarget} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Nome do Local</label>
                                <input
                                    type="text"
                                    value={newName}
                                    onChange={e => setNewName(e.target.value)}
                                    placeholder="Ex: Google DNS, Switch Central"
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white outline-none focus:ring-2 focus:ring-purple-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">IP ou URL</label>
                                <input
                                    type="text"
                                    value={newTarget}
                                    onChange={e => setNewTarget(e.target.value)}
                                    placeholder="8.8.8.8 ou google.com"
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white outline-none focus:ring-2 focus:ring-purple-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Tipo de Teste</label>
                                <select
                                    value={newType}
                                    onChange={e => setNewType(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white outline-none focus:ring-2 focus:ring-purple-500"
                                >
                                    <option value="http">Web/HTTP (Porta 80/443)</option>
                                    <option value="icmp">Ping/ICMP</option>
                                    <option value="dns">DNS Resolution</option>
                                </select>
                            </div>
                            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={newIsPriority}
                                        onChange={e => setNewIsPriority(e.target.checked)}
                                        className="w-5 h-5 rounded border-amber-500 bg-slate-950 text-amber-500 focus:ring-amber-500 focus:ring-offset-slate-900"
                                    />
                                    <div>
                                        <span className="text-amber-400 font-bold flex items-center gap-2">
                                            ⭐ Monitoramento Prioritário
                                        </span>
                                        <p className="text-xs text-amber-400/70 mt-0.5">
                                            Ativa monitoramento automático contínuo (a cada 5 minutos)
                                        </p>
                                    </div>
                                </label>
                            </div>
                            <div className="pt-2">
                                <button
                                    type="submit"
                                    className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-bold transition-all shadow-lg shadow-purple-900/20"
                                >
                                    Cadastrar Alvo
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal Configurações Agente */}
            {showSettingsModal && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
                        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Settings size={20} className="text-purple-500" />
                                Configurações do Agente AI
                            </h3>
                            <button onClick={() => setShowSettingsModal(false)} className="text-slate-500 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={saveSettings} className="p-6 space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Limite de Latência (Anomalia)
                                    <span className="block text-xs text-slate-500 font-normal">Sinalizar como problema acima de:</span>
                                </label>
                                <div className="flex items-center gap-4">
                                    <input
                                        type="range" min="50" max="2000" step="50"
                                        value={latencyThreshold}
                                        onChange={e => setLatencyThreshold(parseInt(e.target.value))}
                                        className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                    />
                                    <span className="bg-slate-800 px-3 py-1 rounded text-sm text-white font-mono min-w-[70px] text-center">{latencyThreshold}ms</span>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Sensibilidade (Ciclos de Anomalia)
                                    <span className="block text-xs text-slate-500 font-normal">Quantas vezes seguidas deve falhar antes de alertar?</span>
                                </label>
                                <div className="flex items-center gap-4">
                                    <input
                                        type="range" min="1" max="10" step="1"
                                        value={anomalyCycles}
                                        onChange={e => setAnomalyCycles(parseInt(e.target.value))}
                                        className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                    />
                                    <span className="bg-slate-800 px-3 py-1 rounded text-sm text-white font-mono min-w-[70px] text-center">{anomalyCycles}x</span>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Intervalo de Verificação
                                    <span className="block text-xs text-slate-500 font-normal">Tempo entre cada teste automático.</span>
                                </label>
                                <select
                                    value={checkInterval}
                                    onChange={e => setCheckInterval(parseInt(e.target.value))}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white outline-none focus:ring-2 focus:ring-purple-500"
                                >
                                    <option value="60">1 Minuto (Agressivo)</option>
                                    <option value="300">5 Minutos (Padrão)</option>
                                    <option value="600">10 Minutos (Leve)</option>
                                    <option value="1800">30 Minutos</option>
                                </select>
                            </div>

                            <div className="pt-2 flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setShowSettingsModal(false)}
                                    className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg font-medium transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold transition-colors shadow-lg shadow-purple-900/20"
                                >
                                    Salvar Configurações
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

        </div>
    );
};
export default Agent;
