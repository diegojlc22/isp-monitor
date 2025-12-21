import { LayoutDashboard, Map, Radio, Server, Settings, Users, LogOut, User } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import { useAuth } from '../context/AuthContext';

export function Sidebar() {
    const { user, systemName, logout } = useAuth();

    // Initial of user name
    const initial = user?.name ? user.name[0].toUpperCase() : 'U';

    return (
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen text-slate-300 flex-shrink-0">
            <div className="p-6 flex items-center gap-3">
                <div className="bg-blue-600 p-2 rounded-lg">
                    <Radio className="text-white w-6 h-6" />
                </div>
                <span className="font-bold text-white text-lg truncate" title={systemName}>{systemName}</span>
            </div>

            <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
                <NavLink to="/" className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-colors", isActive ? "bg-blue-600 text-white" : "hover:bg-slate-800")}>
                    <LayoutDashboard className="w-5 h-5" /> <span className="font-medium">Dashboard</span>
                </NavLink>
                <NavLink to="/map" className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-colors", isActive ? "bg-blue-600 text-white" : "hover:bg-slate-800")}>
                    <Map className="w-5 h-5" /> <span className="font-medium">Mapa</span>
                </NavLink>
                <NavLink to="/towers" className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-colors", isActive ? "bg-blue-600 text-white" : "hover:bg-slate-800")}>
                    <Radio className="w-5 h-5" /> <span className="font-medium">Torres</span>
                </NavLink>
                <NavLink to="/equipments" className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-colors", isActive ? "bg-blue-600 text-white" : "hover:bg-slate-800")}>
                    <Server className="w-5 h-5" /> <span className="font-medium">Equipamentos</span>
                </NavLink>

                {user?.role === 'admin' && (
                    <>
                        <div className="my-2 border-t border-slate-800 mx-4" />
                        <div className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 mt-4">Administração</div>
                        <NavLink to="/users" className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-colors", isActive ? "bg-blue-600 text-white" : "hover:bg-slate-800")}>
                            <Users className="w-5 h-5" /> <span className="font-medium">Usuários</span>
                        </NavLink>
                        <NavLink to="/settings" className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-colors", isActive ? "bg-blue-600 text-white" : "hover:bg-slate-800")}>
                            <Settings className="w-5 h-5" /> <span className="font-medium">Configurações</span>
                        </NavLink>
                    </>
                )}
            </nav>

            <div className="p-4 border-t border-slate-800 bg-slate-900/50">
                <div className="flex items-center gap-3 px-2 mb-3">
                    <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center border border-slate-600 shadow-lg shadow-blue-500/20">
                        <span className="text-white font-bold text-lg">{initial}</span>
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <p className="text-sm font-medium text-white truncate" title={user?.name}>{user?.name}</p>
                        <p className="text-xs text-slate-500 truncate" title={user?.role}>{user?.role === 'admin' ? 'Administrador' : 'Técnico'}</p>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                    <NavLink to="/profile" className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 rounded-lg text-xs font-medium transition-colors">
                        <User size={14} /> Perfil
                    </NavLink>
                    <button onClick={logout} className="flex items-center justify-center gap-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 py-2 rounded-lg text-xs font-medium transition-colors">
                        <LogOut size={14} /> Sair
                    </button>
                </div>
            </div>
        </aside>
    );
}
