import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { updateMe } from '../services/api';

export function Profile() {
    const { user, refreshUser } = useAuth();
    const [formData, setFormData] = useState({ name: '', email: '', password: '' });

    useEffect(() => {
        if (user) {
            setFormData({ name: user.name, email: user.email, password: '' });
        }
    }, [user]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        try {
            const payload: any = { name: formData.name, email: formData.email };
            if (formData.password) payload.password = formData.password;

            await updateMe(payload);
            await refreshUser();
            setFormData(prev => ({ ...prev, password: '' }));
            alert('Perfil atualizado com sucesso!');
        } catch (e) {
            alert('Erro ao atualizar perfil.');
        }
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Meu Perfil</h2>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-xl">
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Nome</label>
                        <input required type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                            value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Email</label>
                        <input required type="email" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                            value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Nova Senha (deixe em branco para manter)</label>
                        <input type="password" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                            value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} />
                    </div>

                    <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium">Salvar Alterações</button>
                </form>
            </div>
        </div>
    )
}
