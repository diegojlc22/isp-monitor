
import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Activity, Globe, Wifi, Play, AlertTriangle, Plus, Trash2, X, Settings, Send } from 'lucide-react';
import toast from 'react-hot-toast';

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

    // Modals
    const [showModal, setShowModal] = useState(false);
    const [showSettingsModal, setShowSettingsModal] = useState(false);

    // Add Target Form
    const [newName, setNewName] = useState('');
    const [newTarget, setNewTarget] = useState('');
    const [newType, setNewType] = useState('http');

    // Settings Form
    const [latencyThreshold, setLatencyThreshold] = useState(300);
    const [anomalyCycles, setAnomalyCycles] = useState(2);
    const [checkInterval, setCheckInterval] = useState(300);
    const [telegramToken, setTelegramToken] = useState('');
    const [telegramChatId, setTelegramChatId] = useState('');

    const fetchData = async () => {
        setLoading(true);
        try {
            const [resLogs, resTargets] = await Promise.all([
                api.get('/agent/logs'),
                api.get('/agent/targets')
            ]);
            setLogs(resLogs.data);
            setTargets(resTargets.data);
        } catch (err) {
            console.error(err);
            toast.error('Erro ao buscar dados.');
        } finally {
            setLoading(false);
        }
    };

    const fetchSettings = async () => {
        try {
            const res = await api.get('/agent/settings');
            setLatencyThreshold(parseInt(res.data.agent_latency_threshold || '300'));
            setAnomalyCycles(parseInt(res.data.agent_anomaly_cycles || '2'));
            setCheckInterval(parseInt(res.data.agent_check_interval || '300'));
            setTelegramToken(res.data.telegram_token || '');
            setTelegramChatId(res.data.telegram_chat_id || '');
            setShowSettingsModal(true);
        } catch (err) {
            toast.error('Erro ao carregar configurações.');
        }
    };

    const saveSettings = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post('/agent/settings', {
                latency_threshold: latencyThreshold,
                anomaly_cycles: anomalyCycles,
                check_interval: checkInterval,
                telegram_token: telegramToken,
                telegram_chat_id: telegramChatId
            });
            toast.success('Configurações salvas!');
            // Don't close modal immediately so user can test telegram
        } catch (err) {
            toast.error('Erro ao salvar configurações.');
        }
    };

    const testTelegram = async () => {
        // First save current settings to ensure backend has latest token
        try {
            await api.post('/agent/settings', {
                latency_threshold: latencyThreshold,
                anomaly_cycles: anomalyCycles,
                check_interval: checkInterval,
                telegram_token: telegramToken,
                telegram_chat_id: telegramChatId
            });

            const res = await api.post('/agent/telegram-test');
            if (res.data.success) {
                toast.success(res.data.message);
            } else {
                toast.error(res.data.message);
            }
        } catch (err) {
            toast.error('Erro ao testar Telegram.');
        }
    };

    const handleAddTarget = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName || !newTarget) return;

        try {
            await api.post('/agent/targets', { name: newName, target: newTarget, type: newType });
            toast.success('Alvo adicionado!');
            setShowModal(false);
            setNewName('');
            setNewTarget('');
            fetchData();
        } catch (err) {
            toast.error('Erro ao adicionar alvo.');
        }
    };

    const handleDeleteTarget = async (id: number) => {
        if (!confirm('Remover monitoramento deste alvo?')) return;
        try {
            await api.delete(`/agent/targets/${id}`);
            toast.success('Alvo removido.');
            fetchData();
        } catch (err) {
            toast.error('Erro ao remover.');
        }
    };

    const triggerTest = async () => {
        try {
            await api.post('/agent/trigger');
            toast.success('Teste manual solicitado! Atualize em alguns segundos.');
            setTimeout(fetchData, 5000);
        } catch (err) {
            toast.error('Erro ao iniciar teste.');
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
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
                    <button
                        onClick={triggerTest}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors font-medium"
                    >
                        <Play size={18} />
                        Rodar Teste Agora
                    </button>
                </div>
            </div>

            {/* Alvos Configurados */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {targets.map(t => (
                    <div key={t.id} className="bg-slate-900 border border-slate-800 p-4 rounded-lg flex justify-between items-center group">
                        <div>
                            <h4 className="font-semibold text-slate-200 group-hover:text-purple-400 transition-colors">{t.name}</h4>
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

            {/* Cards de Resumo */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card p-6 bg-gray-800 rounded-xl border border-gray-700/50">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <p className="text-gray-400 text-sm">Status Web</p>
                            <h3 className="text-2xl font-bold text-green-400">Normal</h3>
                        </div>
                        <Globe className="text-gray-500" />
                    </div>
                    <div className="text-sm text-gray-500">Média Latência: 45ms</div>
                </div>

                <div className="card p-6 bg-gray-800 rounded-xl border border-gray-700/50">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <p className="text-gray-400 text-sm">Resolução DNS</p>
                            <h3 className="text-2xl font-bold text-green-400">Ótimo</h3>
                        </div>
                        <Wifi className="text-gray-500" />
                    </div>
                    <div className="text-sm text-gray-500">8.8.8.8: 12ms</div>
                </div>

                <div className="card p-6 bg-gray-800 rounded-xl border border-gray-700/50">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <p className="text-gray-400 text-sm">Anomalias (24h)</p>
                            <h3 className="text-2xl font-bold text-gray-200">0</h3>
                        </div>
                        <AlertTriangle className="text-gray-500" />
                    </div>
                    <div className="text-sm text-gray-500">Nenhum desvio detectado</div>
                </div>
            </div>

            {/* Tabela de Logs */}
            <div className="bg-gray-800 rounded-xl border border-gray-700/50 overflow-hidden shadow-lg">
                {loading && logs.length === 0 && (
                    <div className="p-4 text-center text-gray-500">Carregando dados...</div>
                )}
                <div className="px-6 py-4 border-b border-gray-700/50 flex justify-between items-center">
                    <h2 className="font-semibold text-lg">Últimos Testes Sintéticos</h2>
                    <span className="text-xs text-gray-500">Atualizado a cada 30s</span>
                </div>
                <div className="overflow-x-auto max-h-[500px] overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700">
                    <table className="w-full">
                        <thead className="sticky top-0 bg-slate-900 border-b border-gray-700/50 shadow-sm z-10">
                            <tr className="text-left text-sm text-gray-400">
                                <th className="px-6 py-3 font-medium">Hora</th>
                                <th className="px-6 py-3 font-medium">Tipo</th>
                                <th className="px-6 py-3 font-medium">Alvo</th>
                                <th className="px-6 py-3 font-medium">Latência</th>
                                <th className="px-6 py-3 font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700/50 text-sm">
                            {logs.length === 0 && !loading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                                        Nenhum log encontrado. O agente roda a cada 5 minutos.
                                    </td>
                                </tr>
                            ) : (
                                logs.map((log) => (
                                    <tr key={log.id} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-3 text-gray-300 whitespace-nowrap">
                                            {new Date(log.timestamp).toLocaleTimeString()}
                                        </td>
                                        <td className="px-6 py-3">
                                            <span className={`px-2 py-1 rounded text-[10px] font-bold tracking-wide uppercase ${log.test_type === 'dns' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                                                }`}>
                                                {log.test_type}
                                            </span>
                                        </td>
                                        <td className="px-6 py-3 text-gray-300 font-mono text-xs">{log.target}</td>
                                        <td className="px-6 py-3 text-gray-300 font-mono">
                                            {log.latency_ms ? `${log.latency_ms}ms` : '-'}
                                        </td>
                                        <td className="px-6 py-3">
                                            {log.success ? (
                                                <span className="text-green-400 flex items-center gap-1.5 text-xs font-medium">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]" /> OK
                                                </span>
                                            ) : (
                                                <span className="text-red-400 flex items-center gap-1.5 text-xs font-medium">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.5)]" /> FALHA
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal Add Target */}
            {showModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 backdrop-blur-sm p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-white">Novo Alvo de Monitoramento</h3>
                            <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>

                        <form onSubmit={handleAddTarget} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Nome Amigável</label>
                                <input
                                    type="text"
                                    value={newName}
                                    onChange={e => setNewName(e.target.value)}
                                    placeholder="Ex: Servidor Jogo FIFA"
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-purple-500 outline-none"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Tipo</label>
                                <select
                                    value={newType}
                                    onChange={e => setNewType(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-purple-500 outline-none"
                                >
                                    <option value="http">Site WEB (HTTP/HTTPS)</option>
                                    <option value="dns">Servidor DNS (UDP)</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Alvo (IP ou URL)</label>
                                <input
                                    type="text"
                                    value={newTarget}
                                    onChange={e => setNewTarget(e.target.value)}
                                    placeholder={newType === 'http' ? 'https://google.com' : '8.8.4.4'}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-purple-500 outline-none"
                                    required
                                />
                            </div>

                            <div className="pt-4 flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg font-medium transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold transition-colors shadow-lg shadow-purple-900/20"
                                >
                                    Salvar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal Settings */}
            {showSettingsModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 backdrop-blur-sm p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <Settings size={22} className="text-purple-500" />
                                Configurações da IA
                            </h3>
                            <button onClick={() => setShowSettingsModal(false)} className="text-slate-400 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>

                        <form onSubmit={saveSettings} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Limiar de Latência (Spike)
                                    <span className="block text-xs text-slate-500 font-normal">Acima deste valor, o teste é considerado "lento".</span>
                                </label>
                                <div className="flex items-center gap-4">
                                    <input
                                        type="range" min="50" max="1000" step="10"
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

                            <div className="pt-4 border-t border-slate-700/50">
                                <div className="flex justify-between items-center mb-3">
                                    <h4 className="text-white font-semibold">Notificações Telegram</h4>
                                    <button
                                        type="button"
                                        onClick={testTelegram}
                                        className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-2 py-1 rounded flex items-center gap-1 transition-colors"
                                    >
                                        <Send size={12} /> Testar Envio
                                    </button>
                                </div>

                                <div className="space-y-3">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">Bot Token</label>
                                        <input
                                            type="text"
                                            value={telegramToken}
                                            onChange={e => setTelegramToken(e.target.value)}
                                            placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white outline-none focus:ring-2 focus:ring-purple-500 font-mono text-xs"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">Chat ID</label>
                                        <input
                                            type="text"
                                            value={telegramChatId}
                                            onChange={e => setTelegramChatId(e.target.value)}
                                            placeholder="-100123456789"
                                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white outline-none focus:ring-2 focus:ring-purple-500 font-mono text-xs"
                                        />
                                    </div>
                                </div>
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
