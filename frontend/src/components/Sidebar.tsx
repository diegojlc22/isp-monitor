import { LayoutDashboard, Map, Radio, Server, Settings, Users, LogOut, User, Bell, Menu, X, Activity, Smartphone, FileText, Clock, Zap, BrainCircuit } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { PrefetchNavLink } from './PrefetchNavLink';
import clsx from 'clsx';
import { useAuth } from '../context/AuthContext';
import { useState } from 'react';

export function Sidebar() {
    const { user, systemName, logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);

    // Initial of user name
    const initial = user?.name ? user.name[0].toUpperCase() : 'U';

    const toggle = () => setIsOpen(!isOpen);

    const baseLinkClass = ({ isActive }: { isActive: boolean }) =>
        clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200",
            isActive ? "bg-blue-600 text-white shadow-md shadow-blue-900/20" : "hover:bg-slate-800 text-slate-400 hover:text-white");

    return (
        <>
            {/* Mobile Menu Button */}
            <button onClick={toggle} className="md:hidden fixed top-4 left-4 z-50 p-2 bg-slate-900 border border-slate-700 text-white rounded-lg shadow-lg">
                {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Overlay for Mobile */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/60 z-30 md:hidden backdrop-blur-sm"
                    onClick={() => setIsOpen(false)}
                />
            )}

            <aside className={clsx(
                "fixed md:static top-0 left-0 z-40 h-screen w-64 bg-slate-900 border-r border-slate-800 flex flex-col text-slate-300 flex-shrink-0 transition-transform duration-300 ease-in-out",
                isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
            )}>
                <div className="p-6 flex items-center gap-3 md:pt-6 pt-16">
                    <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-600/20">
                        <Radio className="text-white w-6 h-6" />
                    </div>
                    <span className="font-bold text-white text-lg truncate" title={systemName}>{systemName}</span>
                </div>

                <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto custom-scrollbar">
                    <PrefetchNavLink to="/" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/Dashboard')}>
                        <LayoutDashboard className="w-5 h-5" /> <span className="font-medium">Dashboard</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/live" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/LiveMonitor')}>
                        <Activity className="w-5 h-5" /> <span className="font-medium">Monitor Live</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/health" onClick={() => setIsOpen(false)} className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200", isActive ? "bg-indigo-600 text-white shadow-md shadow-indigo-900/20" : "hover:bg-slate-800 text-slate-400 hover:text-white")} prefetchPage={() => import('../pages/Health')}>
                        <Server className="w-5 h-5" /> <span className="font-medium">Saúde do Sistema</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/map" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/NetMap')}>
                        <Map className="w-5 h-5" /> <span className="font-medium">Mapa</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/towers" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/Towers')}>
                        <Radio className="w-5 h-5" /> <span className="font-medium">Torres</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/equipments" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/Equipments')}>
                        <Server className="w-5 h-5" /> <span className="font-medium">Equipamentos</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/priority" onClick={() => setIsOpen(false)} className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200", isActive ? "bg-yellow-600 text-white shadow-md shadow-yellow-900/20" : "hover:bg-slate-800 text-slate-400 hover:text-white")} prefetchPage={() => import('../pages/Priority')}>
                        <Zap className="w-5 h-5 flex-shrink-0" /> <span className="font-medium">Prioritários</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/alerts" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/Alerts')}>
                        <Bell className="w-5 h-5" /> <span className="font-medium">Alertas</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/agent" onClick={() => setIsOpen(false)} className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200", isActive ? "bg-purple-600 text-white shadow-md shadow-purple-900/20" : "hover:bg-slate-800 text-slate-400 hover:text-white")} prefetchPage={() => import('../pages/Agent')}>
                        <Activity className="w-5 h-5" /> <span className="font-medium">Agente IA</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/intelligence" onClick={() => setIsOpen(false)} className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200", isActive ? "bg-purple-600 text-white shadow-md shadow-purple-900/20" : "hover:bg-slate-800 text-slate-400 hover:text-white")} prefetchPage={() => import('../pages/Intelligence')}>
                        <BrainCircuit className="w-5 h-5" /> <span className="font-medium">Inteligência</span>
                    </PrefetchNavLink>
                    <PrefetchNavLink to="/reports" onClick={() => setIsOpen(false)} className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200", isActive ? "bg-amber-600 text-white shadow-md shadow-amber-900/20" : "hover:bg-slate-800 text-slate-400 hover:text-white")} prefetchPage={() => import('../pages/Reports')}>
                        <FileText className="w-5 h-5" /> <span className="font-medium">Relatórios</span>
                    </PrefetchNavLink>

                    {user?.role === 'admin' && (
                        <>
                            <div className="my-4 border-t border-slate-800 mx-4 opacity-50" />
                            <div className="px-4 text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Administração</div>
                            <PrefetchNavLink to="/users" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/ManageUsers')}>
                                <Users className="w-5 h-5" /> <span className="font-medium">Usuários</span>
                            </PrefetchNavLink>
                            <PrefetchNavLink to="/mobile" onClick={() => setIsOpen(false)} className={({ isActive }) => clsx("flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200", isActive ? "bg-purple-600 text-white shadow-md shadow-purple-900/20" : "hover:bg-slate-800 text-slate-400 hover:text-white")} prefetchPage={() => import('../pages/MobileApp')}>
                                <Smartphone className="w-5 h-5" /> <span className="font-medium">App Mobile (Expo)</span>
                            </PrefetchNavLink>
                            <PrefetchNavLink to="/requests" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/RequestsPage')}>
                                <Smartphone className="w-5 h-5" /> <span className="font-medium">Solicitações (App)</span>
                            </PrefetchNavLink>
                            <PrefetchNavLink to="/settings" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/Settings')}>
                                <Settings className="w-5 h-5" /> <span className="font-medium">Configurações</span>
                            </PrefetchNavLink>
                            <PrefetchNavLink to="/schedules" onClick={() => setIsOpen(false)} className={baseLinkClass} prefetchPage={() => import('../pages/Schedules')}>
                                <Clock className="w-5 h-5" /> <span className="font-medium">Cronogramas</span>
                            </PrefetchNavLink>
                        </>
                    )}
                </nav>

                <div className="p-4 border-t border-slate-800 bg-slate-900/50">
                    <div className="flex items-center gap-3 px-2 mb-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center border border-slate-600 shadow-lg cursor-default select-none">
                            <span className="text-white font-bold text-lg">{initial}</span>
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <p className="text-sm font-medium text-white truncate" title={user?.name}>{user?.name}</p>
                            <p className="text-xs text-slate-500 truncate">{user?.role === 'admin' ? 'Administrador' : 'Técnico'}</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <NavLink to="/profile" onClick={() => setIsOpen(false)} className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 rounded-lg text-xs font-medium transition-colors border border-slate-700/50">
                            <User size={14} /> Perfil
                        </NavLink>
                        <button onClick={logout} className="flex items-center justify-center gap-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 py-2 rounded-lg text-xs font-medium transition-colors border border-rose-500/10">
                            <LogOut size={14} /> Sair
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
}
