import { useState, useEffect } from 'react';
import { getTelegramConfig, updateTelegramConfig, testTelegramMessage, testWhatsappMessage, getWhatsappGroups, getWhatsappStatus } from '../services/api';
import { Bell, Save, MessageCircle, Send, Search, Copy, Check, X, RefreshCw, AlertTriangle } from 'lucide-react';
import QRCode from 'react-qr-code';
import { useAuth } from '../context/AuthContext';

export function Alerts() {
    const { user } = useAuth();

    // Config State (Unified)
    const [config, setConfig] = useState({
        bot_token: '',
        chat_id: '',
        template_down: '',
        template_up: '',
        telegram_enabled: true,
        whatsapp_enabled: false,
        whatsapp_target: '',
        whatsapp_target_group: ''
    });
    const [configLoading, setConfigLoading] = useState(false);
    const [msg, setMsg] = useState('');

    // Templates
    const [templateDown, setTemplateDown] = useState('🔴 [Device.Name] caiu! IP=[Device.IP]');
    const [templateUp, setTemplateUp] = useState('🟢 [Device.Name] voltou! IP=[Device.IP]');

    // Group Modal State
    const [showGroupModal, setShowGroupModal] = useState(false);
    const [groups, setGroups] = useState<any[]>([]);
    const [groupFilter, setGroupFilter] = useState('');
    const [loadingGroups, setLoadingGroups] = useState(false);

    // WhatsApp Status State
    const [whatsappStatus, setWhatsappStatus] = useState<{ ready: boolean, qr: string | null }>({ ready: false, qr: null });
    const [showQrModal, setShowQrModal] = useState(false);
    const [qrError, setQrError] = useState('');

    const checkWhatsappStatus = async () => {
        try {
            setQrError('');
            const data = await getWhatsappStatus();
            if (!data.error) {
                setWhatsappStatus(data);
            } else {
                setQrError("Erro no Gateway: " + data.error);
            }
        } catch (e) {
            console.error("Erro ao checar status zap", e);
            setQrError("Erro de conexão com a API. Verifique se o servidor está rodando.");
        }
    };

    useEffect(() => {
        if (showQrModal) {
            checkWhatsappStatus();
            const interval = setInterval(checkWhatsappStatus, 3000); // Poll a cada 3s com modal aberto
            return () => clearInterval(interval);
        } else {
            // Checa uma vez ao carregar a página
            checkWhatsappStatus();
        }
    }, [showQrModal]);

    useEffect(() => {
        if (user?.role === 'admin') {
            getTelegramConfig().then(res => {
                setConfig({
                    ...res,
                    telegram_enabled: res.telegram_enabled !== false,
                    whatsapp_enabled: res.whatsapp_enabled === true,
                    whatsapp_target: res.whatsapp_target || '',
                    whatsapp_target_group: res.whatsapp_target_group || ''
                });
                if (res.template_down) setTemplateDown(res.template_down);
                if (res.template_up) setTemplateUp(res.template_up);
            }).catch(console.error);
        }
    }, [user]);

    const loadGroups = async () => {
        setLoadingGroups(true);
        try {
            const data = await getWhatsappGroups();
            if (Array.isArray(data)) {
                setGroups(data);
            } else {
                alert(data.error || 'Erro ao carregar grupos. Verifique se o ZAP está on.');
            }
        } catch (e) {
            alert('Erro ao carregar grupos.');
        } finally {
            setLoadingGroups(false);
        }
    };

    const openGroupSelector = () => {
        setShowGroupModal(true);
        if (groups.length === 0) loadGroups();
    };

    const selectGroup = (id: string) => {
        setConfig({ ...config, whatsapp_target_group: id });
        setShowGroupModal(false);
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        alert('Copiado!');
    };

    async function handleSaveConfig(e: React.FormEvent) {
        e.preventDefault();
        setConfigLoading(true);
        try {
            await updateTelegramConfig({
                ...config,
                template_down: templateDown,
                template_up: templateUp
            });
            setMsg('Configuração salva com sucesso!');
            setTimeout(() => setMsg(''), 3000);
        } catch (e: any) {
            setMsg('Erro ao salvar configuração.');
        } finally {
            setConfigLoading(false);
        }
    }

    async function handleTestTelegram() {
        setMsg(''); setConfigLoading(true);
        try {
            await testTelegramMessage();
            setMsg('Teste Telegram enviado!');
        } catch (e: any) {
            setMsg('Erro Telegram: ' + (e.response?.data?.error || e.message));
        } finally {
            setConfigLoading(false);
        }
    }

    async function handleTestWhatsapp(targetOverride?: string) {
        setMsg(''); setConfigLoading(true);
        try {
            await testWhatsappMessage(targetOverride || config.whatsapp_target);
            setMsg('Teste WhatsApp enviado com sucesso!');
        } catch (e: any) {
            setMsg('Erro WhatsApp: ' + (e.response?.data?.error || e.message));
        } finally {
            setConfigLoading(false);
        }
    }

    const filteredGroups = groups.filter(g => g.name.toLowerCase().includes(groupFilter.toLowerCase()));

    return (
        <div className="space-y-6 relative">
            {/* Modal de Busca de Grupos */}
            {showGroupModal && (
                <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg flex flex-col max-h-[80vh]">
                        <div className="p-4 border-b border-slate-700 flex justify-between items-center">
                            <h3 className="text-white font-bold text-lg">Selecionar Grupo WhatsApp</h3>
                            <button onClick={() => setShowGroupModal(false)} className="text-slate-400 hover:text-white"><X size={20} /></button>
                        </div>
                        <div className="p-4 border-b border-slate-800">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                                <input
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                    placeholder="Buscar grupo..."
                                    value={groupFilter}
                                    onChange={e => setGroupFilter(e.target.value)}
                                    autoFocus
                                />
                            </div>
                        </div>
                        <div className="flex-1 overflow-y-auto p-2 space-y-1">
                            {loadingGroups ? (
                                <div className="text-center p-8 text-slate-500">Carregando grupos...</div>
                            ) : filteredGroups.length === 0 ? (
                                <div className="text-center p-8 text-slate-500">Nenhum grupo encontrado.</div>
                            ) : (
                                filteredGroups.map(g => (
                                    <div key={g.id} className="flex items-center justify-between p-3 hover:bg-slate-800 rounded-lg group transition-colors">
                                        <div className="min-w-0">
                                            <div className="text-white font-medium truncate">{g.name}</div>
                                            <div className="text-xs text-slate-500 font-mono truncate">{g.id}</div>
                                        </div>
                                        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => copyToClipboard(g.id)} className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-white" title="Copiar ID">
                                                <Copy size={16} />
                                            </button>
                                            <button onClick={() => selectGroup(g.id)} className="p-2 bg-blue-600 hover:bg-blue-700 rounded text-white" title="Selecionar">
                                                <Check size={16} />
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                        <div className="p-3 border-t border-slate-800 bg-slate-950 rounded-b-xl flex justify-between items-center text-xs text-slate-500">
                            <span>{filteredGroups.length} grupos encontrados</span>
                            <button onClick={loadGroups} className="text-blue-400 hover:underline">Recarregar</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Conexão QR Code */}
            {showQrModal && (
                <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl p-6 w-full max-w-sm flex flex-col items-center">
                        <div className="flex justify-between w-full mb-4">
                            <h3 className="text-lg font-bold text-slate-900">Conectar WhatsApp</h3>
                            <button onClick={() => setShowQrModal(false)} className="text-slate-500 hover:text-slate-900"><X /></button>
                        </div>

                        {qrError ? (
                            <div className="text-center py-8">
                                <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-3" />
                                <p className="text-red-600 font-medium mb-1">Falha na Conexão</p>
                                <p className="text-xs text-slate-500 max-w-[200px] mx-auto">{qrError}</p>
                                <button onClick={checkWhatsappStatus} className="mt-4 text-blue-600 hover:underline text-sm">Tentar Novamente</button>
                            </div>
                        ) : whatsappStatus.ready ? (
                            <div className="text-center py-6">
                                <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Check size={32} />
                                </div>
                                <p className="text-green-700 font-semibold text-lg">Sucesso!</p>
                                <p className="text-slate-600">O WhatsApp está conectado.</p>
                                <button onClick={() => setShowQrModal(false)} className="mt-4 bg-slate-900 text-white px-6 py-2 rounded-lg">Fechar</button>
                            </div>
                        ) : whatsappStatus.qr ? (
                            <div className="flex flex-col items-center">
                                <div className="p-2 border-4 border-slate-900 rounded-lg">
                                    <QRCode value={whatsappStatus.qr} size={256} />
                                </div>
                                <p className="text-center text-sm text-slate-600 mt-4 px-4">
                                    Abra o WhatsApp no seu celular &gt; Menu &gt; Aparelhos conectados &gt; Conectar um aparelho
                                </p>
                            </div>
                        ) : (
                            <div className="py-12 flex flex-col items-center text-slate-500">
                                <RefreshCw className="animate-spin mb-2" size={32} />
                                <p>Aguardando QR Code...</p>
                                <p className="text-xs text-slate-400 mt-1">Iniciando sessão do navegador...</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Bell className="w-8 h-8 text-yellow-500" /> Alertas Multicanal
                    </h1>
                    <p className="text-slate-400">Configure para onde enviar os avisos de queda.</p>
                </div>
            </div>

            {user?.role === 'admin' && (
                <form onSubmit={handleSaveConfig} className="space-y-6">

                    {/* Canais */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                        {/* Telegram Panel */}
                        <div className={`rounded-xl border p-6 transition-colors ${config.telegram_enabled ? 'bg-slate-900 border-blue-500/30' : 'bg-slate-900/50 border-slate-800'}`}>
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-500/10 rounded-lg"><Send className="text-blue-500" size={20} /></div>
                                    <h3 className="font-semibold text-white">Telegram</h3>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" checked={config.telegram_enabled}
                                        onChange={e => setConfig({ ...config, telegram_enabled: e.target.checked })} />
                                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                            </div>

                            <div className={`space-y-4 ${!config.telegram_enabled && 'opacity-50 pointer-events-none'}`}>
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1">Bot Token</label>
                                    <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm font-mono"
                                        value={config.bot_token} onChange={e => setConfig({ ...config, bot_token: e.target.value })} placeholder="123456...:ABCD..." />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1">Chat ID</label>
                                    <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm font-mono"
                                        value={config.chat_id} onChange={e => setConfig({ ...config, chat_id: e.target.value })} placeholder="-100..." />
                                </div>
                                <button type="button" onClick={handleTestTelegram} className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                                    <Bell size={12} /> Testar Envio Telegram
                                </button>
                            </div>
                        </div>

                        {/* WhatsApp Panel */}
                        <div className={`rounded-xl border p-6 transition-colors ${config.whatsapp_enabled ? 'bg-slate-900 border-green-500/30' : 'bg-slate-900/50 border-slate-800'}`}>
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-green-500/10 rounded-lg"><MessageCircle className="text-green-500" size={20} /></div>
                                    <div>
                                        <h3 className="font-semibold text-white">WhatsApp</h3>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={`inline-block w-2 h-2 rounded-full ${whatsappStatus.ready ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`}></span>
                                            <span className="text-xs text-slate-400">
                                                {whatsappStatus.ready ? 'Conectado' : 'Desconectado'}
                                            </span>
                                            {!whatsappStatus.ready && (
                                                <button type="button" onClick={() => setShowQrModal(true)} className="text-xs text-blue-400 hover:text-blue-300 underline ml-2">
                                                    Conectar (QR Code)
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" checked={config.whatsapp_enabled}
                                        onChange={e => setConfig({ ...config, whatsapp_enabled: e.target.checked })} />
                                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                                </label>
                            </div>

                            <div className={`space-y-4 ${!config.whatsapp_enabled && 'opacity-50 pointer-events-none'}`}>
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1">Destino Individual (Número)</label>
                                    <div className="flex gap-2">
                                        <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm font-mono"
                                            value={config.whatsapp_target} onChange={e => setConfig({ ...config, whatsapp_target: e.target.value })}
                                            placeholder="551199..." />
                                        <button type="button" onClick={() => handleTestWhatsapp(config.whatsapp_target)}
                                            disabled={!config.whatsapp_target}
                                            className="px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-600 text-xs disabled:opacity-50">
                                            Testar
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1">ID do Grupo</label>
                                    <div className="flex gap-2">
                                        <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm font-mono"
                                            value={(config as any).whatsapp_target_group || ''}
                                            onChange={e => setConfig({ ...config, whatsapp_target_group: e.target.value } as any)}
                                            placeholder="12036...@g.us" />

                                        <button type="button" onClick={openGroupSelector} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded px-3 text-slate-300 transition-colors" title="Buscar Grupo">
                                            <Search size={16} />
                                        </button>

                                        <button type="button" onClick={() => handleTestWhatsapp((config as any).whatsapp_target_group)}
                                            disabled={!(config as any).whatsapp_target_group}
                                            className="px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-600 text-xs disabled:opacity-50">
                                            Testar
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>

                    {/* Feedback e Salvar */}
                    <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 flex items-center justify-between">
                        <div className="text-sm">
                            {msg && <span className={`${msg.includes('Erro') ? 'text-red-400' : 'text-emerald-400'}`}>{msg}</span>}
                        </div>
                        <button type="submit" disabled={configLoading} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-2.5 rounded-lg font-bold transition-all shadow-lg hover:shadow-blue-500/20">
                            <Save size={18} />
                            {configLoading ? 'Salvando...' : 'Salvar Tudo'}
                        </button>
                    </div>
                </form>
            )}

            {/* Templates Section */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="p-4 border-b border-slate-800 bg-slate-900/50">
                    <h3 className="text-base font-semibold text-white">Mensagens Personalizadas</h3>
                </div>
                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Alertar Queda (Down)</label>
                        <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded px-4 py-2 text-white font-mono text-sm border-l-4 border-l-red-500"
                            value={templateDown} onChange={e => setTemplateDown(e.target.value)} />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Alertar Retorno (Up)</label>
                        <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded px-4 py-2 text-white font-mono text-sm border-l-4 border-l-emerald-500"
                            value={templateUp} onChange={e => setTemplateUp(e.target.value)} />
                    </div>
                    <div className="flex justify-end">
                        <button onClick={handleSaveConfig} className="text-sm text-slate-400 hover:text-white underline">Salvar Templates junto com config</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
