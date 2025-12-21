import { createContext, useContext, useEffect, useState } from 'react';
import { login as loginApi, getMe, getSystemName } from '../services/api';

interface User {
    id: number;
    name: string;
    email: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    systemName: string;
    login: (e: string, p: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    refreshUser: () => Promise<void>;
    refreshSystemName: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as any);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [systemName, setSystemName] = useState('ISP Monitor');
    const [loading, setLoading] = useState(true);

    async function refreshSystemName() {
        try {
            const res = await getSystemName();
            if (res.name) setSystemName(res.name);
            document.title = res.name || 'ISP Monitor';
        } catch (e) { console.error(e); }
    }

    async function loadUser() {
        if (!token) {
            setLoading(false);
            return;
        }
        try {
            const u = await getMe();
            setUser(u);
        } catch (e) {
            console.error("Auth check failed", e);
            logout();
        } finally {
            setLoading(false);
        }
    }

    async function refreshUser() {
        await loadUser();
    }

    useEffect(() => {
        refreshSystemName();
        loadUser();
    }, []);

    async function login(email: string, pass: string) {
        const res = await loginApi({ email, password: pass });
        localStorage.setItem('token', res.access_token);
        setToken(res.access_token);
        setUser(res.user);
    }

    function logout() {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    }

    if (loading) return <div className="h-screen flex items-center justify-center bg-slate-950 text-white">Carregando...</div>;

    return (
        <AuthContext.Provider value={{ user, token, systemName, login, logout, isAuthenticated: !!user, refreshUser, refreshSystemName }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
