import { useEffect, useState } from 'react';
import { getTowers, getEquipments } from '../services/api';
import { Activity, ShieldCheck, AlertTriangle, Radio } from 'lucide-react';

export function Dashboard() {
    const [stats, setStats] = useState({ towers: 0, equipments: 0, online: 0, offline: 0 });

    useEffect(() => {
        async function load() {
            try {
                const [towers, equips] = await Promise.all([getTowers(), getEquipments()]);
                const allDevices = [...towers, ...equips];
                const online = allDevices.filter((x: any) => x.is_online).length;
                const offline = allDevices.length - online;

                setStats({
                    towers: towers.length,
                    equipments: equips.length,
                    online: online,
                    offline: offline
                });
            } catch (e) {
                console.error(e);
            }
        }
        load();
        const interval = setInterval(load, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div>
            <h2 className="text-2xl font-bold mb-6 text-white">Visão Geral da Rede</h2>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-blue-500/50 transition-colors">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Radio size={48} className="text-blue-500" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Total Torres</h3>
                    <p className="text-3xl font-bold text-white mt-2">{stats.towers}</p>
                </div>

                <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-emerald-500/50 transition-colors">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Activity size={48} className="text-emerald-500" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Online</h3>
                    <p className="text-3xl font-bold text-emerald-400 mt-2">{stats.online}</p>
                </div>

                <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-rose-500/50 transition-colors">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <AlertTriangle size={48} className="text-rose-500" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Offline/Crítico</h3>
                    <p className="text-3xl font-bold text-rose-500 mt-2">{stats.offline}</p>
                </div>

                <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm relative overflow-hidden group hover:border-purple-500/50 transition-colors">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <ShieldCheck size={48} className="text-purple-500" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Equipamentos</h3>
                    <p className="text-3xl font-bold text-purple-400 mt-2">{stats.equipments}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 h-64 flex items-center justify-center text-slate-500">
                    <p>Gráfico de Disponibilidade (Em Breve)</p>
                </div>
                <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Alertas Recentes</h3>
                    <div className="space-y-4">
                        {/* Placeholder Logic for alerts */}
                        <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded border border-slate-800">
                            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                            <p className="text-sm text-slate-300">Sistema iniciado com sucesso.</p>
                            <span className="ml-auto text-xs text-slate-500">Agora</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
