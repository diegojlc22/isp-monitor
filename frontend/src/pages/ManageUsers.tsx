
import { useEffect, useState } from 'react';
import { getUsers, createUser, updateUser, deleteUser } from '../services/api';
import { Plus, Trash2, Edit2 } from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../context/AuthContext';

export function ManageUsers() {
    const { user: currentUser } = useAuth();
    const [users, setUsers] = useState<any[]>([]);
    const [showModal, setShowModal] = useState(false);
    const [editingUser, setEditingUser] = useState<any | null>(null);
    const [formData, setFormData] = useState({ name: '', email: '', password: '', role: 'tech' });

    async function load() {
        try {
            const data = await getUsers();
            setUsers(data);
        } catch (e) { alert('Erro ao carregar usuários'); }
    }

    useEffect(() => { load(); }, []);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        try {
            if (editingUser) {
                // Update
                const payload: any = { name: formData.name, email: formData.email, role: formData.role };
                if (formData.password) payload.password = formData.password;

                await updateUser(editingUser.id, payload);
            } else {
                // Create
                await createUser(formData);
            }
            setShowModal(false);
            setEditingUser(null);
            setFormData({ name: '', email: '', password: '', role: 'tech' });
            load();
        } catch (error) {
            alert('Erro ao salvar usuário.');
        }
    }

    function handleEdit(u: any) {
        setEditingUser(u);
        setFormData({ name: u.name, email: u.email, password: '', role: u.role || 'tech' });
        setShowModal(true);
    }

    function resetForm() {
        setEditingUser(null);
        setFormData({ name: '', email: '', password: '', role: 'tech' });
        setShowModal(true);
    }

    async function handleDelete(id: number) {
        if (confirm('Tem certeza?')) {
            await deleteUser(id);
            load();
        }
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Gerenciar Usuários</h2>
                <button onClick={resetForm} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                    <Plus size={20} />
                    Novo Usuário
                </button>
            </div>

            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-left text-sm text-slate-400">
                    <thead className="bg-slate-950 text-slate-200 uppercase font-medium">
                        <tr>
                            <th className="px-6 py-4">Nome</th>
                            <th className="px-6 py-4">Email</th>
                            <th className="px-6 py-4">Função</th>
                            <th className="px-6 py-4 text-right">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {users.map(u => (
                            <tr key={u.id} className="hover:bg-slate-800/50 transition-colors">
                                <td className="px-6 py-4 font-medium text-white">{u.name}</td>
                                <td className="px-6 py-4 font-mono text-slate-300">{u.email}</td>
                                <td className="px-6 py-4">
                                    <span className={clsx("px-2 py-1 rounded text-xs font-bold uppercase", u.role === 'admin' ? "bg-purple-500/10 text-purple-400" : "bg-blue-500/10 text-blue-400")}>
                                        {u.role}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right flex justify-end gap-2">
                                    <button onClick={() => handleEdit(u)} className="text-slate-500 hover:text-blue-400 p-2">
                                        <Edit2 size={18} />
                                    </button>
                                    {u.id !== currentUser?.id && (
                                        <button onClick={() => handleDelete(u.id)} className="text-slate-500 hover:text-rose-500 p-2">
                                            <Trash2 size={18} />
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {showModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-md shadow-2xl p-6">
                        <h3 className="text-xl font-bold text-white mb-4">{editingUser ? 'Editar Usuário' : 'Novo Usuário'}</h3>
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
                                <label className="block text-sm font-medium text-slate-400 mb-1">Senha {editingUser && '(Deixe em branco para manter)'}</label>
                                <input type="password" required={!editingUser} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                    value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Função</label>
                                <select className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                    value={formData.role} onChange={e => setFormData({ ...formData, role: e.target.value })}>
                                    <option value="tech">Técnico</option>
                                    <option value="admin">Administrador</option>
                                </select>
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-slate-300 hover:text-white">Cancelar</button>
                                <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium">Salvar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
