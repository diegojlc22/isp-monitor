import { Sidebar } from '../components/Sidebar';
import { Outlet } from 'react-router-dom';

export function DashboardLayout() {
    return (
        <div className="flex w-full h-screen bg-slate-950 text-slate-100 overflow-hidden">
            <Sidebar />
            <main className="flex-1 flex flex-col h-full overflow-hidden relative">
                <div className="flex-1 overflow-auto bg-slate-950 p-6 md:p-8 scrollbar-thin scrollbar-thumb-slate-800">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
