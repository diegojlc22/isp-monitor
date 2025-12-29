import React, { useEffect, useState, useRef } from 'react';
import { Smartphone, RefreshCw, Power, Terminal } from 'lucide-react';
import QRCode from 'react-qr-code';
import { getMobileStatus, startMobile, stopMobile } from '../services/api';
import toast from 'react-hot-toast';

export function MobileApp() {
    const [status, setStatus] = useState({ is_running: false, url: null as string | null, logs: [] as string[] });
    const [loading, setLoading] = useState(false);
    const logsEndRef = useRef<HTMLDivElement>(null);

    const refreshStatus = () => {
        getMobileStatus().then(setStatus).catch(console.error);
    };

    useEffect(() => {
        refreshStatus();
        const interval = setInterval(refreshStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    // Auto-scroll logs
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [status.logs]);

    const handleStart = async () => {
        setLoading(true);
        try {
            await startMobile();
            toast.success("Iniciando Módulo Mobile...");
        } catch (error: any) {
            toast.error("Erro ao iniciar: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
            refreshStatus();
        }
    };

    const handleStop = async () => {
        if (!confirm("Isso vai desconectar o App Mobile. Continuar?")) return;
        setLoading(true);
        try {
            await stopMobile();
            toast.success("Módulo Mobile Parado.");
        } catch (error) {
            toast.error("Erro ao parar.");
        } finally {
            setLoading(false);
            refreshStatus();
        }
    };

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            <header className="flex justify-between items-center bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-purple-500/10 rounded-lg">
                        <Smartphone size={32} className="text-purple-400" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">App Mobile</h1>
                        <p className="text-slate-400">Controle o servidor do aplicativo móvel.</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className={`px-4 py-2 rounded-full font-bold flex items-center gap-2 ${status.is_running ? 'bg-green-500/20 text-green-400' : 'bg-slate-700/50 text-slate-400'}`}>
                        <div className={`w-3 h-3 rounded-full ${status.is_running ? 'bg-green-400 animate-pulse' : 'bg-slate-500'}`} />
                        {status.is_running ? 'ONLINE' : 'OFFLINE'}
                    </div>
                </div>
            </header>

            <div className="grid md:grid-cols-2 gap-6">
                {/* Painel de Controle */}
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg space-y-6">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Power size={20} /> Painel de Controle
                    </h2>

                    <div className="flex flex-col gap-4">
                        {!status.is_running ? (
                            <button
                                onClick={handleStart}
                                disabled={loading}
                                className="w-full py-6 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-bold text-xl transition-all shadow-lg hover:shadow-purple-500/20 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? <RefreshCw className="animate-spin" /> : <Power />}
                                Iniciar Servidor Mobile
                            </button>
                        ) : (
                            <button
                                onClick={handleStop}
                                disabled={loading}
                                className="w-full py-6 bg-red-600 hover:bg-red-500 text-white rounded-xl font-bold text-xl transition-all shadow-lg hover:shadow-red-500/20 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? <RefreshCw className="animate-spin" /> : <Power />}
                                Parar Servidor
                            </button>
                        )}

                        <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700 text-sm text-slate-400 space-y-2">
                            <p className="text-white font-medium">Instruções:</p>
                            <ol className="list-decimal pl-4 space-y-1">
                                <li>Instale o app <strong>Expo Go</strong> no seu celular (Android/iOS).</li>
                                <li>Conecte o celular no <strong>mesmo Wi-Fi</strong> do servidor.</li>
                                <li>Clique em Iniciar e escaneie o QR Code.</li>
                            </ol>
                        </div>
                    </div>

                    {/* QR Code Area */}
                    <div className="mt-6 border-t border-slate-700 pt-6">
                        {status.is_running && status.url ? (
                            <div className="flex flex-col items-center justify-center bg-white p-8 rounded-xl shadow-inner animate-in fade-in zoom-in duration-300">
                                <QRCode value={status.url} size={220} />
                                <div className="mt-4 text-center">
                                    <p className="text-slate-900 font-mono font-bold bg-slate-100 px-3 py-1 rounded border border-slate-200 text-sm select-all cursor-pointer hover:bg-slate-200 transition-colors" onClick={() => { navigator.clipboard.writeText(status.url || ''); toast.success("Link copiado!") }}>
                                        {status.url}
                                    </p>
                                    <p className="mt-2 text-slate-500 text-xs">Scan com Expo Go</p>
                                </div>
                            </div>
                        ) : status.is_running ? (
                            <div className="flex flex-col items-center justify-center h-64 bg-slate-900/50 rounded-xl border border-slate-700 border-dashed animate-pulse">
                                <RefreshCw className="animate-spin text-purple-400 mb-4" size={32} />
                                <p className="text-purple-300">Iniciando Expo...</p>
                                <p className="text-slate-500 text-sm mt-2">Aguardando geração do link...</p>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-64 bg-slate-900/30 rounded-xl border border-slate-800 border-dashed">
                                <Smartphone className="text-slate-700 mb-4" size={48} />
                                <p className="text-slate-500">O servidor está desligado.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Logs Terminal */}
                <div className="bg-[#0c0c0c] p-0 rounded-xl border border-slate-800 shadow-lg flex flex-col h-[600px] overflow-hidden">
                    <div className="bg-slate-900 p-3 border-b border-slate-800 flex justify-between items-center">
                        <h2 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
                            <Terminal size={16} /> Terminal Logs
                        </h2>
                        <span className="text-xs text-slate-600">tail -f expo.log</span>
                    </div>
                    <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1 p-4 text-slate-300 h-full scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
                        {status.logs.length === 0 && <p className="text-slate-600 italic opactiy-50">Esperando output...</p>}
                        {status.logs.map((log, i) => (
                            <div key={i} className="break-all whitespace-pre-wrap hover:bg-white/5 py-0.5 px-1 rounded transition-colors">
                                <span className="text-slate-600 select-none mr-2 w-16 inline-block opacity-50">
                                    {new Date().toLocaleTimeString('pt-BR', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className={log.includes("ERROR") ? "text-red-400" : log.includes("exp://") ? "text-green-400 font-bold" : "text-slate-300"}>
                                    {log}
                                </span>
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                </div>
            </div>
        </div>
    );
}
