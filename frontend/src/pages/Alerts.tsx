import { useState, useEffect } from 'react';
import { getTelegramConfig, updateTelegramConfig } from '../services/api';
import { Bell, Save } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Alerts() {
    const { user } = useAuth();

    // Telegram Config State
    const [config, setConfig] = useState({ bot_token: '', chat_id: '', template_down: '', template_up: '' });
    const [configLoading, setConfigLoading] = useState(false);
    const [msg, setMsg] = useState('');
    const [templateDown, setTemplateDown] = useState('O servico [Service.Name] no dispositivo [Device.Name] passou para o status down - IP=[Device.FirstAddress]');
    const [templateUp, setTemplateUp] = useState('O servico [Service.Name] no dispositivo [Device.Name] passou para o status up - IP=[Device.FirstAddress]');

    useEffect(() => {
        // Load Telegram Config if Admin
        if (user?.role === 'admin') {
            getTelegramConfig().then(res => {
                setConfig(res);
                if (res.template_down) setTemplateDown(res.template_down);
                if (res.template_up) setTemplateUp(res.template_up);
            }).catch(console.error);
        }
    }, [user]);

    async function handleSaveConfig(e: React.FormEvent) {
        e.preventDefault();
        setConfigLoading(true);
        try {
            await updateTelegramConfig({ ...config, template_down: templateDown, template_up: templateUp });
            setMsg('Configuração salva com sucesso!');
            setTimeout(() => setMsg(''), 3000);
        } catch (e) {
            setMsg('Erro ao salvar configuração.');
        } finally {
            setConfigLoading(false);
        }
    }

    async function handleSaveTemplates(e: React.FormEvent) {
        // Alias to same save function for now, or could share logic
        handleSaveConfig(e);
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Bell className="w-8 h-8 text-yellow-500" /> Alertas
                    </h1>
                    <p className="text-slate-400">Configurações de notificações e templates</p>
                </div>
            </div>

            {/* Telegram Configuration Section (Admin Only) */}
            {user?.role === 'admin' && (
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden mb-8">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Bell className="text-blue-500" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Configuração do Telegram</h3>
                            <p className="text-sm text-slate-400">Configure o bot para receber alertas instantâneos.</p>
                        </div>
                    </div>

                    <form onSubmit={handleSaveConfig} className="p-6 space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Bot Token</label>
                                <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                    value={config.bot_token} onChange={e => setConfig({ ...config, bot_token: e.target.value })} placeholder="123456789:ABCDefGHI..." />
                                <p className="mt-1 text-xs text-slate-500">Token fornecido pelo @BotFather.</p>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Chat ID</label>
                                <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                    value={config.chat_id} onChange={e => setConfig({ ...config, chat_id: e.target.value })} placeholder="-100..." />
                                <p className="mt-1 text-xs text-slate-500">ID do grupo/usuário para receber alertas.</p>
                            </div>
                        </div>

                        {msg && (
                            <div className={`p-3 rounded-lg text-sm ${msg.includes('Erro') ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                                {msg}
                            </div>
                        )}

                        <div className="flex justify-end">
                            <button type="submit" disabled={configLoading} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                                <Save size={18} />
                                {configLoading ? 'Salvando...' : 'Salvar Configuração'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="p-4 border-b border-slate-800">
                    <h3 className="text-lg font-semibold text-white">Histórico de Alertas</h3>
                </div>
                <div className="p-6">
                    <p className="text-slate-400 mb-6">Personalize as mensagens enviadas ao Telegram quando o status muda. Use as variáveis: <code>[Device.Name]</code>, <code>[Device.IP]</code>, <code>[Service.Name]</code>, <code>[Device.FirstAddress]</code>.</p>

                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Mensagem de Queda (Dispositivo Caiu)</label>
                            <div className="flex gap-2">
                                <span className="p-2 bg-slate-800 rounded-lg text-red-500 font-bold border border-slate-700">🔴</span>
                                <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                    value={templateDown} onChange={e => setTemplateDown(e.target.value)}
                                    placeholder="O servico [Service.Name] no dispositivo [Device.Name] passou para o status down - IP=[Device.FirstAddress]" />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Mensagem de Retorno (Dispositivo Voltou)</label>
                            <div className="flex gap-2">
                                <span className="p-2 bg-slate-800 rounded-lg text-green-500 font-bold border border-slate-700">🟢</span>
                                <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                    value={templateUp} onChange={e => setTemplateUp(e.target.value)}
                                    placeholder="O servico [Service.Name] no dispositivo [Device.Name] passou para o status up - IP=[Device.FirstAddress]" />
                            </div>
                        </div>

                        <div className="flex justify-end">
                            <button onClick={handleSaveTemplates} disabled={configLoading} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                                <Save size={18} />
                                Salvar Templates
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
