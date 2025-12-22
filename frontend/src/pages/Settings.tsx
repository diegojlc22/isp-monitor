import { useEffect, useState } from 'react';
import { getSystemName, updateSystemName, getLatencyConfig, updateLatencyConfig, getDatabaseConfig, updateDatabaseConfig } from '../services/api';
import { Save, Smartphone, Settings as SettingsIcon, Activity, Database } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Settings() {
    const { user, refreshSystemName } = useAuth();
    // const [config, setConfig] = useState({ bot_token: '', chat_id: '' }); // REMOVED
    const [sysName, setSysName] = useState('');
    const [thresholds, setThresholds] = useState({ good: 50, critical: 200 });
    const [dbConfig, setDbConfig] = useState({ db_type: 'sqlite', postgres_url: '' });
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    useEffect(() => {
        // getTelegramConfig().then(setConfig).catch(console.error); // REMOVED
        getSystemName().then(res => setSysName(res.name)).catch(console.error);
        getLatencyConfig().then(setThresholds).catch(console.error);
        getDatabaseConfig().then(setDbConfig).catch(console.error);
    }, []);

    async function handleSave(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        try {
            // await updateTelegramConfig(config); // REMOVED
            await updateSystemName(sysName);
            await updateLatencyConfig(thresholds);
            // Don't just auto-save DB config, it's sensitive.
            // We'll let the DB section have its own "Save & Migrate logic" if needed
            // But for now, user requested straightforward UI, so maybe save everything together
            // Or better: check if DB changed

            await refreshSystemName();
            setMsg('Configurações salvas com sucesso!');
            setTimeout(() => setMsg(''), 3000);
        } catch (e) {
            setMsg('Erro ao salvar.');
        } finally {
            setLoading(false);
        }
    }

    async function handleSaveDb() {
        if (!confirm("Isso irá salvar a configuração de banco e pode exigir reinicialização do backend. Continuar?")) return;
        try {
            await updateDatabaseConfig(dbConfig);
            alert("Configuração de banco salva! Reinicie o backend manualmente para aplicar.");
        } catch (e) {
            alert("Erro ao salvar config de banco.");
        }
    }

    async function handleMigrate() {
        if (!dbConfig.postgres_url || !dbConfig.postgres_url.startsWith('postgresql')) {
            alert("URL do Postgres inválida.");
            return;
        }

        if (!confirm("Isso irá migrar TODOS os dados do banco atual (SQLite) para o PostgreSQL configurado. Dados existentes no destino podem ser sobrescritos. Continuar?")) return;

        try {
            setLoading(true);
            const { migrateData } = await import('../services/api');
            const res = await migrateData(dbConfig.postgres_url);
            alert(res.message || "Migração concluída!");
        } catch (e: any) {
            console.error(e);
            alert("Erro na migração: " + (e.response?.data?.error || e.message));
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
            <h2 className="text-2xl font-bold mb-6 text-white">Configurações</h2>

            <div className="space-y-6">
                <form onSubmit={handleSave} className="space-y-6">
                    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <SettingsIcon className="text-slate-200" size={24} />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white">Geral</h3>
                                <p className="text-sm text-slate-400">Configurações globais do sistema.</p>
                            </div>
                        </div>
                        <div className="p-6">
                            <label className="block text-sm font-medium text-slate-400 mb-1">Nome do Sistema</label>
                            <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                value={sysName} onChange={e => setSysName(e.target.value)} />
                        </div>
                    </div>

                    {/* Database Config Section */}
                    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                            <div className="p-2 bg-indigo-500/10 rounded-lg">
                                <Database className="text-indigo-500" size={24} />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white">Banco de Dados</h3>
                                <p className="text-sm text-slate-400">Gerencie onde seus dados são armazenados.</p>
                            </div>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="flex gap-4 p-4 bg-slate-950 rounded-lg border border-slate-800">
                                <div className="flex items-center gap-2">
                                    <input type="radio" name="dbtype" id="sqlite" checked={dbConfig.db_type === 'sqlite'}
                                        onChange={() => setDbConfig({ ...dbConfig, db_type: 'sqlite' })} />
                                    <label htmlFor="sqlite" className="text-white font-medium cursor-pointer">SQLite (Padrão)</label>
                                </div>
                                <div className="flex items-center gap-2">
                                    <input type="radio" name="dbtype" id="postgres" checked={dbConfig.db_type === 'postgresql'}
                                        onChange={() => setDbConfig({ ...dbConfig, db_type: 'postgresql' })} />
                                    <label htmlFor="postgres" className="text-white font-medium cursor-pointer">PostgreSQL (Recomendado)</label>
                                </div>
                            </div>

                            {dbConfig.db_type === 'postgresql' && (
                                <div className="animate-fade-in">
                                    <label className="block text-sm font-medium text-slate-400 mb-1">URL de Conexão (Postgres)</label>
                                    <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono text-sm"
                                        placeholder="postgresql+asyncpg://user:pass@localhost:5432/dbname"
                                        value={dbConfig.postgres_url}
                                        onChange={e => setDbConfig({ ...dbConfig, postgres_url: e.target.value })}
                                    />
                                    <p className="text-xs text-slate-500 mt-2">
                                        Certifique-se que o banco existe e as credenciais estão corretas. O backend precisará ser reiniciado.
                                    </p>
                                </div>
                            )}

                            <div className="flex justify-end pt-2 gap-3 items-center">
                                {dbConfig.db_type === 'postgresql' && dbConfig.postgres_url.length > 10 && (
                                    <button type="button" onClick={handleMigrate} className="text-sm bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded transition-colors border border-slate-600">
                                        Copiar Dados (SQLite → Postgres)
                                    </button>
                                )}
                                <button type="button" onClick={handleSaveDb} className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded transition-colors">
                                    Salvar Config Banco
                                </button>
                            </div>
                        </div>
                    </div>



                    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                            <div className="p-2 bg-amber-500/10 rounded-lg">
                                <Activity className="text-amber-500" size={24} />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white">Latência (Ping)</h3>
                                <p className="text-sm text-slate-400">Limiares para classificação de latência nos gráficos.</p>
                            </div>
                        </div>

                        <div className="p-6 grid grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Limiar Bom (ms)</label>
                                <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-green-400 font-bold focus:border-green-500 focus:outline-none"
                                    value={thresholds.good} onChange={e => setThresholds({ ...thresholds, good: parseInt(e.target.value) })} />
                                <p className="mt-1 text-xs text-slate-500">Abaixo disso é Verde.</p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Limiar Crítico (ms)</label>
                                <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-rose-400 font-bold focus:border-rose-500 focus:outline-none"
                                    value={thresholds.critical} onChange={e => setThresholds({ ...thresholds, critical: parseInt(e.target.value) })} />
                                <p className="mt-1 text-xs text-slate-500">Acima disso é Vermelho.</p>
                            </div>
                        </div>
                    </div>

                    {msg && (
                        <div className={`p-3 rounded-lg text-sm ${msg.includes('Erro') ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                            {msg}
                        </div>
                    )}

                    <div className="flex justify-end">
                        <button type="submit" disabled={loading} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            <Save size={18} />
                            {loading ? 'Salvando...' : 'Salvar Tudo'}
                        </button>
                    </div>
                </form>

                <div className="mt-8 bg-slate-900 rounded-xl border border-slate-800 p-6 opacity-75">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-slate-800 rounded-lg">
                            <Smartphone className="text-slate-400" size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">App Técnico (Em Breve)</h3>
                            <p className="text-sm text-slate-400">Acesso via API para aplicativo móvel.</p>
                        </div>
                    </div>
                    <p className="text-sm text-slate-500">
                        A API já está preparada para integração. A chave de API poderá ser gerada aqui futuramente.
                    </p>
                </div>
            </div>
        </div>
    )
}
