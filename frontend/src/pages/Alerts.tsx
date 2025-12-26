import { useState, useEffect } from 'react';
import { getTelegramConfig, updateTelegramConfig, testTelegramMessage, testWhatsappMessage } from '../services/api';
import { Bell, Save, MessageCircle, Send } from 'lucide-react';
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
        whatsapp_target: ''
    });
    const [configLoading, setConfigLoading] = useState(false);
    const [msg, setMsg] = useState('');

    // Templates (UI state separated for big inputs)
    const [templateDown, setTemplateDown] = useState('🔴 [Device.Name] caiu! IP=[Device.IP]');
    const [templateUp, setTemplateUp] = useState('🟢 [Device.Name] voltou! IP=[Device.IP]');

    useEffect(() => {
        if (user?.role === 'admin') {
            getTelegramConfig().then(res => {
                setConfig({
                    ...res,
                    // Garante booleanos e strings
                    telegram_enabled: res.telegram_enabled !== false, // default true se undefined
                    whatsapp_enabled: res.whatsapp_enabled === true,
                    whatsapp_target: res.whatsapp_target || ''
                });
                if (res.template_down) setTemplateDown(res.template_down);
                if (res.template_up) setTemplateUp(res.template_up);
            }).catch(console.error);
        }
    }, [user]);

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

    async function handleTestWhatsapp() {
        setMsg(''); setConfigLoading(true);
        try {
            await testWhatsappMessage();
            setMsg('Teste WhatsApp enviado!');
        } catch (e: any) {
            setMsg('Erro WhatsApp: ' + (e.response?.data?.error || e.message));
        } finally {
            setConfigLoading(false);
        }
    }

    return (
        <div className="space-y-6">
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
                                    <h3 className="font-semibold text-white">WhatsApp</h3>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" checked={config.whatsapp_enabled}
                                        onChange={e => setConfig({ ...config, whatsapp_enabled: e.target.checked })} />
                                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                                </label>
                            </div>

                            <div className={`space-y-4 ${!config.whatsapp_enabled && 'opacity-50 pointer-events-none'}`}>
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 mb-1">Destino (ID ou Número)</label>
                                    <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white text-sm font-mono"
                                        value={config.whatsapp_target} onChange={e => setConfig({ ...config, whatsapp_target: e.target.value })}
                                        placeholder="12036...@g.us ou 551199..." />
                                    <p className="text-[10px] text-slate-500 mt-1">Use a lista de grupos no Launcher para copiar o ID.</p>
                                </div>
                                <button type="button" onClick={handleTestWhatsapp} className="text-xs text-green-400 hover:text-green-300 flex items-center gap-1">
                                    <MessageCircle size={12} /> Testar Envio WhatsApp
                                </button>
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

            {/* Templates Section (Mantido igual mas simplificado visualmente) */}
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
