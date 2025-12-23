import { useState, useEffect } from 'react';
import { getTelegramConfig, updateTelegramConfig } from '../services/api';
import { Database, Save } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Backup() {
    const { user } = useAuth();

    // Config State
    const [config, setConfig] = useState({ bot_token: '', chat_id: '', backup_chat_id: '', template_down: '', template_up: '' });
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    useEffect(() => {
        if (user?.role === 'admin') {
            getTelegramConfig().then(setConfig).catch(console.error);
        }
    }, [user]);

    async function handleSave(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        try {
            await updateTelegramConfig(config);
            setMsg('Configuração de Backup salva com sucesso!');
            setTimeout(() => setMsg(''), 3000);
        } catch (e) {
            setMsg('Erro ao salvar configuração.');
        } finally {
            setLoading(false);
        }
    }

    if (user?.role !== 'admin') {
        return (
            <div className="p-8 text-center text-slate-500">
                Acesso restrito a administradores.
            </div>
        );
    }

    return (
        <div className="max-w-2xl">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-2">
                <Database className="w-8 h-8 text-emerald-500" /> Backup
            </h1>
            <p className="text-slate-400 mb-8">Gestão de arquivos de segurança e backups automáticos.</p>

            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                    <div className="p-2 bg-emerald-500/10 rounded-lg">
                        <Database className="text-emerald-500" size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">Backups Automáticos</h3>
                        <p className="text-sm text-slate-400">Configure um canal exclusivo para seus arquivos de segurança.</p>
                    </div>
                </div>

                <form onSubmit={handleSave} className="p-6 space-y-6">
                    <div className="p-6 border-l-4 border-emerald-500/20 bg-emerald-500/5 rounded-r-lg">
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-emerald-400 mb-1">Chat ID de Backups (Exclusivo)</label>
                            <input type="text" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-emerald-500 focus:outline-none font-mono"
                                value={config.backup_chat_id || ''} onChange={e => setConfig({ ...config, backup_chat_id: e.target.value })}
                                placeholder="Ex: -100987654321..."
                            />
                            <p className="text-xs text-slate-400 mt-2">
                                O sistema enviará o arquivo <b>monitor.db.zip</b> diariamente (00:00) para este grupo.
                                <br />
                                Obs: Utiliza o mesmo Bot Token configurado na aba de Alertas (Telegram).
                            </p>
                        </div>
                    </div>

                    {msg && (
                        <div className={`p-3 rounded-lg text-sm ${msg.includes('Erro') ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                            {msg}
                        </div>
                    )}

                    <div className="flex justify-end">
                        <button type="submit" disabled={loading} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            <Save size={18} />
                            {loading ? 'Salvando...' : 'Salvar Configuração'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
