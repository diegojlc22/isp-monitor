import { useEffect, useState } from 'react';
import { getTowers, createTower, deleteTower } from '../services/api';
import { Plus, Trash2, MapPin, Search } from 'lucide-react';


export function Towers() {
    const [towers, setTowers] = useState<any[]>([]);
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({ name: '', ip: '', latitude: 0, longitude: 0, observations: '' });

    async function load() {
        try {
            const data = await getTowers();
            setTowers(data);
        } catch (e) { console.error(e); }
    }

    useEffect(() => {
        load();
        const interval = setInterval(load, 15000); // Live updates
        return () => clearInterval(interval);
    }, []);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        try {
            await createTower(formData);
            setShowModal(false);
            setFormData({ name: '', ip: '', latitude: 0, longitude: 0, observations: '' });
            load();
        } catch (error) {
            alert('Erro ao criar torre. Verifique os dados.');
        }
    }

    async function handleDelete(id: number) {
        if (confirm('Tem certeza?')) {
            await deleteTower(id);
            load();
        }
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Torres</h2>
                <button onClick={() => setShowModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                    <Plus size={20} />
                    Nova Torre
                </button>
            </div>

            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="p-4 border-b border-slate-800 flex gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                        <input type="text" placeholder="Buscar torres..." className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
                    </div>
                </div>

                <table className="w-full text-left text-sm text-slate-400">
                    <thead className="bg-slate-950 text-slate-200 uppercase font-medium">
                        <tr>

                            <th className="px-6 py-4">Nome</th>

                            <th className="px-6 py-4">Localização</th>
                            <th className="px-6 py-4 text-right">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {towers.length === 0 && (
                            <tr><td colSpan={3} className="px-6 py-8 text-center">Nenhuma torre cadastrada.</td></tr>
                        )}
                        {towers.map(tower => (
                            <tr key={tower.id} className="hover:bg-slate-800/50 transition-colors">

                                <td className="px-6 py-4 font-medium text-white">{tower.name}</td>

                                <td className="px-6 py-4">
                                    <span className="flex items-center gap-1 text-xs">
                                        <MapPin size={14} />
                                        {tower.latitude}, {tower.longitude}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button onClick={() => handleDelete(tower.id)} className="text-slate-500 hover:text-rose-500 p-2">
                                        <Trash2 size={18} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg shadow-2xl p-6">
                        <h3 className="text-xl font-bold text-white mb-4">Nova Torre</h3>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Nome</label>
                                <input required type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                    value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Latitude</label>
                                    <input type="number" step="any" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                        value={formData.latitude} onChange={e => setFormData({ ...formData, latitude: parseFloat(e.target.value) })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Longitude</label>
                                    <input type="number" step="any" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                        value={formData.longitude} onChange={e => setFormData({ ...formData, longitude: parseFloat(e.target.value) })} />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Observações</label>
                                <textarea className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                    value={formData.observations} onChange={e => setFormData({ ...formData, observations: e.target.value })} />
                            </div>
                            <div className="flex justify-end gap-3 mt-6">
                                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-slate-300 hover:text-white">Cancelar</button>
                                <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium">Salvar Torre</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
