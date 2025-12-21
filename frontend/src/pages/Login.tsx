import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Activity } from 'lucide-react';

export function Login() {
    const { login, systemName } = useAuth();
    const navigate = useNavigate();
    const [authData, setAuthData] = useState({ email: '', password: '' });
    const [error, setError] = useState('');

    const [isLoading, setIsLoading] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            console.log("Attempting login with:", authData.email);
            await login(authData.email, authData.password);
            console.log("Login successful, navigating...");
            navigate('/');
        } catch (e: any) {
            console.error("Login failed:", e);
            const msg = e.response?.data?.detail || 'Erro ao conectar ao servidor. Verifique se o backend está rodando.';
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
                <div className="flex flex-col items-center mb-8">
                    <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-blue-900/20">
                        <Activity className="text-white" size={24} />
                    </div>
                    <h1 className="text-2xl font-bold text-white text-center">{systemName}</h1>
                    <p className="text-slate-400">Entre para acessar o sistema</p>
                </div>

                {error && (
                    <div className="bg-rose-500/10 border border-rose-500/50 text-rose-500 px-4 py-3 rounded-lg mb-6 text-sm text-center">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Email</label>
                        <input
                            type="email"
                            required
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none transition-colors"
                            value={authData.email}
                            onChange={e => setAuthData({ ...authData, email: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Senha</label>
                        <input
                            type="password"
                            required
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none transition-colors"
                            value={authData.password}
                            onChange={e => setAuthData({ ...authData, password: e.target.value })}
                        />
                    </div>
                    <button type="submit" disabled={isLoading} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors mt-2 flex justify-center items-center gap-2">
                        {isLoading ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Entrando...
                            </>
                        ) : 'Entrar'}
                    </button>
                </form>
            </div>
        </div>
    );
}
