import React, { useState, useEffect } from 'react';
import { CloudDownload, FileText, Loader2, AlertTriangle, RefreshCw, Clock, Activity } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import clsx from 'clsx';

const Reports: React.FC = () => {
    const [period, setPeriod] = useState("30");
    const [loading, setLoading] = useState(false);
    const [incidentsPeriod, setIncidentsPeriod] = useState("30");
    const [incidentsLoading, setIncidentsLoading] = useState(false);
    const [recentIncidents, setRecentIncidents] = useState<any[]>([]);
    const [loadingList, setLoadingList] = useState(true);
    const [showIncidents, setShowIncidents] = useState(true);

    useEffect(() => {
        loadRecentIncidents();
    }, []);

    const loadRecentIncidents = async () => {
        try {
            setLoadingList(true);
            const response = await api.get('/reports/incidents/recent?limit=10');
            setRecentIncidents(response.data);
        } catch (e) {
            console.error("Erro ao carregar incidentes", e);
        } finally {
            setLoadingList(false);
        }
    };

    const handleSlaDownload = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/reports/sla/pdf?days=${period}`, {
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;

            const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
            link.setAttribute('download', `SLA_Report_${period}d_isp_${date}.pdf`);

            document.body.appendChild(link);
            link.click();
            link.remove();

            toast.success("Relatório gerado com sucesso!");
        } catch (error) {
            console.error("Erro no download:", error);
            toast.error("Erro ao gerar relatório.");
        } finally {
            setLoading(false);
        }
    };

    const handleIncidentsDownload = async () => {
        setIncidentsLoading(true);
        try {
            const response = await api.get(`/reports/incidents/pdf?days=${incidentsPeriod}`, {
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;

            const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
            link.setAttribute('download', `Relatorio_Incidentes_${incidentsPeriod}d_${date}.pdf`);

            document.body.appendChild(link);
            link.click();
            link.remove();

            toast.success("Relatório de incidentes gerado com sucesso!");
        } catch (error) {
            console.error("Erro no download de incidentes:", error);
            toast.error("Erro ao gerar relatório de incidentes.");
        } finally {
            setIncidentsLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">Relatórios Gerenciais</h2>
            </div>

            {/* Cards de Download */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* CARD SLA */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden hover:border-blue-500/50 transition-all group">
                    <div className="p-6 border-b border-slate-800 bg-gradient-to-r from-blue-500/10 to-transparent">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                                <FileText className="h-6 w-6 text-blue-400" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">Disponibilidade (SLA)</h3>
                                <p className="text-sm text-slate-400">Uptime e latência média</p>
                            </div>
                        </div>
                    </div>

                    <div className="p-6 space-y-4">
                        <p className="text-sm text-slate-400">
                            Gera um arquivo PDF contendo o resumo de disponibilidade (uptime) e latência média de todos os equipamentos monitorados.
                        </p>

                        <div className="space-y-3">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    <Clock className="inline h-4 w-4 mr-1" />
                                    Período
                                </label>
                                <select
                                    value={period}
                                    onChange={(e) => setPeriod(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                                >
                                    <option value="7">Últimos 7 dias</option>
                                    <option value="15">Últimos 15 dias</option>
                                    <option value="30">Últimos 30 dias</option>
                                    <option value="90">Últimos 3 Meses</option>
                                </select>
                            </div>

                            <button
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40"
                                onClick={handleSlaDownload}
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Gerando PDF...
                                    </>
                                ) : (
                                    <>
                                        <CloudDownload className="h-4 w-4" />
                                        Baixar PDF SLA
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>

                {/* CARD INCIDENTES */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden hover:border-red-500/50 transition-all group">
                    <div className="p-6 border-b border-slate-800 bg-gradient-to-r from-red-500/10 to-transparent">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-red-500/20 rounded-lg group-hover:bg-red-500/30 transition-colors">
                                <AlertTriangle className="h-6 w-6 text-red-400" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">Incidentes e Quedas</h3>
                                <p className="text-sm text-slate-400">Histórico de alertas</p>
                            </div>
                        </div>
                    </div>

                    <div className="p-6 space-y-4">
                        <p className="text-sm text-slate-400">
                            Gera um PDF detalhado com o histórico de quedas e alertas disparados pelo sistema.
                        </p>

                        <div className="space-y-3">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    <Clock className="inline h-4 w-4 mr-1" />
                                    Período
                                </label>
                                <select
                                    value={incidentsPeriod}
                                    onChange={(e) => setIncidentsPeriod(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all"
                                >
                                    <option value="7">Últimos 7 dias</option>
                                    <option value="15">Últimos 15 dias</option>
                                    <option value="30">Últimos 30 dias</option>
                                    <option value="90">Últimos 3 Meses</option>
                                </select>
                            </div>

                            <button
                                className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-500/20 hover:shadow-red-500/40"
                                onClick={handleIncidentsDownload}
                                disabled={incidentsLoading}
                            >
                                {incidentsLoading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Gerando PDF...
                                    </>
                                ) : (
                                    <>
                                        <CloudDownload className="h-4 w-4" />
                                        Baixar PDF Incidentes
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Lista de Incidentes Recentes */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-gradient-to-r from-amber-500/10 to-transparent">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-amber-500/20 rounded-lg">
                            <Activity className="text-amber-400" size={20} />
                        </div>
                        <h3 className="font-bold text-white text-lg">Últimos 10 Incidentes</h3>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={loadRecentIncidents}
                            className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-all"
                            disabled={loadingList}
                        >
                            <RefreshCw className={clsx("h-4 w-4", loadingList && "animate-spin")} />
                            <span className="hidden sm:inline">Atualizar</span>
                        </button>
                        <button
                            onClick={() => setShowIncidents(!showIncidents)}
                            className="text-sm text-slate-400 hover:text-white flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-all"
                        >
                            {showIncidents ? (
                                <>
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                    <span className="hidden sm:inline">Ocultar</span>
                                </>
                            ) : (
                                <>
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                    <span className="hidden sm:inline">Mostrar</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {showIncidents && (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-950/50 border-b border-slate-800">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                        Data/Hora
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                        Dispositivo
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                        Evento
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {loadingList ? (
                                    <tr>
                                        <td colSpan={3} className="px-6 py-12 text-center">
                                            <Loader2 className="mx-auto h-8 w-8 animate-spin text-slate-600 mb-3" />
                                            <p className="text-slate-500 text-sm">Carregando incidentes...</p>
                                        </td>
                                    </tr>
                                ) : recentIncidents.length === 0 ? (
                                    <tr>
                                        <td colSpan={3} className="px-6 py-12 text-center">
                                            <Activity className="mx-auto h-12 w-12 text-slate-700 mb-3" />
                                            <p className="text-slate-500 text-sm">Nenhum incidente registrado recentemente.</p>
                                        </td>
                                    </tr>
                                ) : (
                                    recentIncidents.map((inc, i) => (
                                        <tr key={i} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <Clock className="h-4 w-4 text-slate-500" />
                                                    <span className="text-sm text-slate-400 font-mono">
                                                        {new Date(inc.timestamp).toLocaleString('pt-BR', {
                                                            day: '2-digit',
                                                            month: '2-digit',
                                                            year: 'numeric',
                                                            hour: '2-digit',
                                                            minute: '2-digit'
                                                        })}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="font-semibold text-white">
                                                    {inc.device_name}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={clsx(
                                                    "inline-flex items-center px-3 py-1 rounded-full text-xs font-bold",
                                                    inc.message.includes("ONLINE") || inc.message.includes("🟢") || inc.message.includes("voltou")
                                                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                                        : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                                )}>
                                                    {inc.message.includes("ONLINE") || inc.message.includes("🟢") || inc.message.includes("voltou") ? (
                                                        <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full mr-2 animate-pulse"></span>
                                                    ) : (
                                                        <span className="w-1.5 h-1.5 bg-rose-400 rounded-full mr-2 animate-pulse"></span>
                                                    )}
                                                    {inc.message}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Reports;
