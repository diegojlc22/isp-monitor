
import { useState, useEffect, useRef } from 'react';
import { startExpo, stopExpo, getExpoStatus, startNgrok, stopNgrok, getNgrokStatus } from '../services/api';
import { Smartphone, Play, Square, RefreshCw, Terminal, AlertTriangle, Globe } from 'lucide-react';
import QRCode from 'react-qr-code';

export function MobileApp() {
    const [status, setStatus] = useState<{ running: boolean, qr: string | null, logs: string[] }>({
        running: false,
        qr: null,
        logs: []
    });

    // Ngrok State
    const [ngrokStatus, setNgrokStatus] = useState<{ running: boolean, url: string | null }>({
        running: false,
        url: null
    });

    const [loading, setLoading] = useState(false);
    const [ngrokLoading, setNgrokLoading] = useState(false);
    const [error, setError] = useState('');
    const logsEndRef = useRef<HTMLDivElement>(null);

    const fetchStatus = async () => {
        try {
            const data = await getExpoStatus();
            setStatus(data);

            const ngrokData = await getNgrokStatus();
            setNgrokStatus(ngrokData);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 3000); // Poll status every 3s
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        // Auto scroll logs
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [status.logs]);

    const handleStart = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await startExpo();
            if (res.error) setError(res.error);
        } catch (e: any) {
            setError('Erro ao iniciar Expo: ' + (e.response?.data?.detail || e.message));
        } finally {
            setLoading(false);
            fetchStatus(); // Force update
        }
    };

    const handleStop = async () => {
        setLoading(true);
        try {
            await stopExpo();
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
            fetchStatus();
        }
    };

    // Ngrok Handlers
    const handleStartNgrok = async () => {
        setNgrokLoading(true);
        try {
            const res = await startNgrok();
            if (res.error) setError('Ngrok Error: ' + res.error);
        } catch (e: any) {
            setError('Erro ao iniciar Ngrok: ' + e.message);
        } finally {
            setNgrokLoading(false);
            fetchStatus();
        }
    };

    const handleStopNgrok = async () => {
        setNgrokLoading(true);
        try {
            await stopNgrok();
        } catch (e: any) {
            setError('Erro ao parar Ngrok: ' + e.message);
        } finally {
            setNgrokLoading(false);
            fetchStatus();
        }
    };


    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Smartphone className="w-8 h-8 text-purple-500" /> Configuração Mobile (Expo)
                    </h1>
                    <p className="text-slate-400">Gerencie o servidor de desenvolvimento e acesso externo.</p>
                </div>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-center gap-3 text-red-200">
                    <AlertTriangle className="flex-shrink-0" />
                    <span>{error}</span>
                </div>
            )}

            {/* Main Server Control */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        Servidor Expo (Metro Bundler)
                        {status.running && <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">Online</span>}
                    </h3>

                    <div className="flex gap-4">
                        {status.running ? (
                            <button
                                onClick={handleStop}
                                disabled={loading}
                                className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-bold transition-all shadow-lg shadow-red-900/20 disabled:opacity-50 text-sm"
                            >
                                {loading ? <RefreshCw className="animate-spin w-4 h-4" /> : <Square size={16} fill="currentColor" />}
                                Parar Expo
                            </button>
                        ) : (
                            <button
                                onClick={handleStart}
                                disabled={loading}
                                className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold transition-all shadow-lg shadow-purple-900/20 disabled:opacity-50 text-sm"
                            >
                                {loading ? <RefreshCw className="animate-spin w-4 h-4" /> : <Play size={16} fill="currentColor" />}
                                Iniciar Expo
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* External Access (Ngrok) */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                            <Globe size={20} className="text-blue-400" /> Acesso Externo (Ngrok)
                            {ngrokStatus.running && <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">Online</span>}
                        </h3>
                        <p className="text-sm text-slate-400 mt-1">
                            Cria um túnel seguro para acessar a API externamente (necessário para o App funcionar fora da rede local).
                        </p>
                    </div>

                    <div className="flex gap-4">
                        {ngrokStatus.running ? (
                            <button
                                onClick={handleStopNgrok}
                                disabled={ngrokLoading}
                                className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg font-bold transition-all disabled:opacity-50 text-sm"
                            >
                                {ngrokLoading ? <RefreshCw className="animate-spin w-4 h-4" /> : <Square size={16} fill="currentColor" />}
                                Desligar Túnel
                            </button>
                        ) : (
                            <button
                                onClick={handleStartNgrok}
                                disabled={ngrokLoading}
                                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold transition-all shadow-lg shadow-blue-900/20 disabled:opacity-50 text-sm"
                            >
                                {ngrokLoading ? <RefreshCw className="animate-spin w-4 h-4" /> : <Globe size={16} />}
                                Ligar Ngrok
                            </button>
                        )}
                    </div>
                </div>

                {ngrokStatus.running && ngrokStatus.url && (
                    <div className="mt-4 p-3 bg-slate-950 border border-slate-700 rounded-lg flex items-center justify-between animate-in slide-in-from-top-2">
                        <div className="flex items-center gap-3 overflow-hidden">
                            <span className="text-xs font-bold text-slate-500 uppercase">URL Pública:</span>
                            <code className="text-green-400 font-mono text-sm truncate">{ngrokStatus.url}</code>
                        </div>
                        <button
                            onClick={() => navigator.clipboard.writeText(ngrokStatus.url || '')}
                            className="text-xs text-blue-400 hover:text-blue-300 font-medium px-2 py-1 rounded hover:bg-blue-400/10 transition-colors"
                        >
                            Copiar
                        </button>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* QR Code Section */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col items-center justify-center min-h-[400px]">
                    <h3 className="text-lg font-semibold text-white mb-6">Conexão Expo Go</h3>

                    {status.running ? (
                        status.qr ? (
                            <div className="flex flex-col items-center animate-in fade-in duration-500">
                                <div className="p-4 bg-white rounded-xl mb-4">
                                    <QRCode value={status.qr} size={200} />
                                </div>
                                <code className="bg-slate-950 px-3 py-1 rounded text-sm font-mono text-purple-400 mb-2">
                                    {status.qr}
                                </code>
                                <p className="text-slate-400 text-center max-w-xs">
                                    Abra o app <strong>Expo Go</strong> no Android/iOS e escaneie este código.
                                </p>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center text-slate-500">
                                <RefreshCw size={48} className="animate-spin mb-4 text-purple-500" />
                                <p>Gerando QR Code...</p>
                                <p className="text-xs mt-2">Aguardando output do Metro Bundler</p>
                            </div>
                        )
                    ) : (
                        <div className="text-center text-slate-500">
                            <Smartphone size={64} className="mx-auto mb-4 opacity-20" />
                            <p>Servidor parado.</p>
                            <p className="text-sm">Inicie o servidor para ver o QR Code.</p>
                        </div>
                    )}
                </div>

                {/* Logs Section */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 flex flex-col overflow-hidden max-h-[500px]">
                    <div className="p-3 bg-slate-950 border-b border-slate-800 flex items-center gap-2">
                        <Terminal size={16} className="text-slate-400" />
                        <span className="text-sm font-mono text-slate-300">Terminal Output (Metro)</span>
                    </div>
                    <div className="flex-1 overflow-auto p-4 font-mono text-xs space-y-1 bg-[#0d1117]">
                        {status.logs.length === 0 ? (
                            <span className="text-slate-600 block italic">Nenhum log disponível.</span>
                        ) : (
                            status.logs.map((log, i) => (
                                <div key={i} className="break-all whitespace-pre-wrap text-slate-300 border-b border-white/5 pb-0.5 mb-0.5 last:border-0">
                                    {log}
                                </div>
                            ))
                        )}
                        <div ref={logsEndRef} />
                    </div>
                </div>

            </div>
        </div>
    );
}
