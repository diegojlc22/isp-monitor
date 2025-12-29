import { Wrench, Smartphone } from 'lucide-react';

export function MobileApp() {
    return (
        <div className="flex flex-col items-center justify-center p-12 text-center h-[calc(100vh-100px)]">
            <div className="bg-slate-800/50 p-6 rounded-full mb-6 relative">
                <Smartphone className="w-16 h-16 text-slate-500" />
                <div className="absolute -bottom-2 -right-2 bg-yellow-500 text-black p-2 rounded-full shadow-lg">
                    <Wrench className="w-6 h-6 animate-pulse" />
                </div>
            </div>

            <h1 className="text-3xl font-bold text-white mb-2">Módulo em Manutenção</h1>
            <p className="text-slate-400 max-w-md mx-auto mb-8">
                Estamos aprimorando a integração do App Mobile via Web.
                <br />
                Por enquanto, utilize o botão <strong>"Mobile"</strong> diretamente no <strong>Launcher (Janela Azul)</strong> para iniciar o aplicativo.
            </p>

            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 max-w-sm w-full mx-auto">
                <h3 className="text-slate-300 font-semibold mb-2 text-sm uppercase tracking-wider">Status</h3>
                <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-500">Integração Web</span>
                    <span className="text-yellow-500 font-bold bg-yellow-500/10 px-2 py-1 rounded">EM BREVE</span>
                </div>
                <div className="flex justify-between items-center text-sm mt-2">
                    <span className="text-slate-500">Launcher (Desktop)</span>
                    <span className="text-green-500 font-bold bg-green-500/10 px-2 py-1 rounded">ATIVO</span>
                </div>
            </div>
        </div>
    );
}
