import React, { useState, useEffect } from 'react';
import {
    CloudDownload, FileText, Loader2, AlertTriangle, RefreshCw,
    Globe, ArrowDown, Server, CheckCircle, AlertCircle, Activity
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import clsx from 'clsx';

const Reports: React.FC = () => {
    const [period, setPeriod] = useState("7"); // Padrão 7 dias
    const [loadingSLA, setLoadingSLA] = useState(false);
    const [loadingIncidents, setLoadingIncidents] = useState(false);

    // Estados para Estatísticas
    const [incidentsStats, setIncidentsStats] = useState<any>(null);
    const [slaStats, setSlaStats] = useState<any>(null);
    const [loadingStats, setLoadingStats] = useState(true);

    useEffect(() => {
        loadDashboardStats();
    }, [period]);

    const loadDashboardStats = async () => {
        setLoadingStats(true);
        try {
            const [incidentsRes, slaRes] = await Promise.all([
                api.get(`/reports/incidents/stats?days=${period}`),
                api.get(`/reports/sla/stats?days=${period}`)
            ]);
            setIncidentsStats(incidentsRes.data);
            setSlaStats(slaRes.data);
        } catch (error) {
            console.error("Erro ao carregar estatísticas:", error);
            toast.error("Erro ao atualizar dashboard.");
        } finally {
            setLoadingStats(false);
        }
    };

    const handleDownload = async (type: 'sla' | 'incidents') => {
        const isSLA = type === 'sla';
        const setLoading = isSLA ? setLoadingSLA : setLoadingIncidents;
        const endpoint = isSLA ? '/reports/sla/pdf' : '/reports/incidents/pdf';
        const prefix = isSLA ? 'Relatorio_SLA' : 'Relatorio_Executivo';

        setLoading(true);
        try {
            const response = await api.get(`${endpoint}?days=${period}`, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
            link.setAttribute('download', `${prefix}_${period}dias_${date}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            toast.success("Relatório baixado com sucesso!");
        } catch (error) {
            console.error("Erro no download:", error);
            toast.error("Falha ao gerar o arquivo.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Cabeçalho */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                        Monitoramento Executivo
                    </h1>
                    <p className="text-gray-400 mt-1">Análise de performance e estabilidade da rede em tempo real.</p>
                </div>

                <div className="flex items-center gap-2 bg-slate-800/50 p-1 rounded-lg border border-slate-700/50">
                    {['7', '15', '30'].map((d) => (
                        <button
                            key={d}
                            onClick={() => setPeriod(d)}
                            className={clsx(
                                "px-4 py-1.5 rounded-md text-sm font-medium transition-all",
                                period === d
                                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                                    : "text-gray-400 hover:text-white hover:bg-slate-700"
                            )}
                        >
                            {d} dias
                        </button>
                    ))}
                    <button
                        onClick={loadDashboardStats}
                        className="p-1.5 text-gray-400 hover:text-white hover:bg-slate-700 rounded-md ml-1"
                        title="Atualizar Dados"
                    >
                        <RefreshCw size={18} className={clsx(loadingStats && "animate-spin")} />
                    </button>
                </div>
            </div>

            {loadingStats ? (
                <div className="h-96 flex items-center justify-center">
                    <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
                </div>
            ) : (
                <>
                    {/* TOP KPIs */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* SLA GLOBAL DA REDE */}
                        <div className="bg-slate-900/80 backdrop-blur rounded-xl p-6 border border-slate-700/50 relative overflow-hidden group hover:border-emerald-500/30 transition-colors">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <Globe size={80} className="text-emerald-500" />
                            </div>
                            <p className="text-gray-400 text-sm font-medium">SLA Global da Rede</p>
                            <div className="mt-2 flex items-baseline gap-2">
                                <span className={clsx("text-4xl font-bold", (slaStats?.global_uptime || 0) >= 99 ? "text-emerald-400" : "text-amber-400")}>
                                    {slaStats?.global_uptime || "0.00"}%
                                </span>
                            </div>
                            <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
                                <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                                Meta SLA: 99.00%
                            </div>
                        </div>

                        {/* QUEDAS NO PERÍODO */}
                        <div className="bg-slate-900/80 backdrop-blur rounded-xl p-6 border border-slate-700/50 relative overflow-hidden group hover:border-red-500/30 transition-colors">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <ArrowDown size={80} className="text-red-500" />
                            </div>
                            <p className="text-gray-400 text-sm font-medium">Quedas no Período</p>
                            <div className="mt-2 flex items-baseline gap-2">
                                <span className="text-4xl font-bold text-red-400">
                                    {incidentsStats?.total_drops || 0}
                                </span>
                                <span className="text-sm text-gray-500">eventos</span>
                            </div>
                            <div className="mt-2 text-xs text-green-500 flex items-center gap-1">
                                <RefreshCw size={12} />
                                {incidentsStats?.total_recoveries || 0} recuperações automáticas
                            </div>
                        </div>

                        {/* DISPOSITIVOS CRÍTICOS */}
                        <div className={clsx("backdrop-blur rounded-xl p-6 border relative overflow-hidden group transition-all",
                            (slaStats?.critical_devices_count || 0) > 0
                                ? "bg-amber-950/20 border-amber-500/30"
                                : "bg-slate-900/80 border-slate-700/50 hover:border-amber-500/30"
                        )}>
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <AlertTriangle size={80} className="text-amber-500" />
                            </div>
                            <p className="text-gray-400 text-sm font-medium">Dispositivos Críticos</p>
                            <div className="mt-2 flex items-baseline gap-2">
                                <span className="text-4xl font-bold text-amber-400">
                                    {slaStats?.critical_devices_count || 0}
                                </span>
                            </div>
                            <div className="mt-2 text-xs text-amber-500/80">
                                SLA abaixo de 99.0%
                            </div>
                        </div>

                        {/* ATIVOS MONITORADOS */}
                        <div className="bg-slate-900/80 backdrop-blur rounded-xl p-6 border border-slate-700/50 relative overflow-hidden group hover:border-blue-500/30 transition-colors">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <Server size={80} className="text-blue-500" />
                            </div>
                            <p className="text-gray-400 text-sm font-medium">Ativos Monitorados</p>
                            <div className="mt-2 flex items-baseline gap-2">
                                <span className="text-4xl font-bold text-blue-400">
                                    {slaStats?.monitored_devices || 0}
                                </span>
                            </div>
                            <div className="mt-2 text-xs text-blue-500/80">
                                Total de infraestrutura
                            </div>
                        </div>
                    </div>

                    {/* Middle Section */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                        {/* LEFT: AI ANALYSIS */}
                        <div className="lg:col-span-1 bg-gradient-to-br from-slate-900 to-slate-950 rounded-xl p-6 border border-slate-700/50 flex flex-col justify-between relative overflow-hidden group hover:border-purple-500/30 transition-colors">
                            {/* Glow Effect */}
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500"></div>

                            <div>
                                <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
                                    <Activity className="text-purple-400" />
                                    Análise Inteligente de Rede
                                </h3>

                                <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
                                    <div className="flex items-start gap-3">
                                        {(incidentsStats?.total_drops || 0) === 0 ? (
                                            <CheckCircle className="text-emerald-400 shrink-0 mt-1" />
                                        ) : (
                                            <AlertCircle className="text-amber-400 shrink-0 mt-1" />
                                        )}
                                        <p className="text-sm text-gray-300 leading-relaxed"
                                            dangerouslySetInnerHTML={{ __html: incidentsStats?.conclusion || "Analisando dados da rede..." }}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="mt-6 pt-6 border-t border-slate-800">
                                <button
                                    onClick={() => handleDownload('incidents')}
                                    disabled={loadingIncidents}
                                    className="w-full py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-red-900/20 group"
                                >
                                    {loadingIncidents ? <Loader2 className="animate-spin" /> : <FileText className="group-hover:scale-110 transition-transform" />}
                                    Baixar Relatório Executivo
                                </button>
                                <p className="text-center text-xs text-gray-500 mt-2">Inclui ranking de quedas e análise detalhada</p>
                            </div>
                        </div>

                        {/* RIGHT: TOP OFFENDERS TABLE */}
                        <div className="lg:col-span-2 bg-slate-900/80 rounded-xl border border-slate-700/50 overflow-hidden flex flex-col">
                            <div className="p-4 bg-slate-800/50 border-b border-slate-700/50 flex justify-between items-center">
                                <h3 className="font-bold text-white flex items-center gap-2">
                                    <ArrowDown className="text-red-400" size={18} />
                                    Top 5 - Maiores Instabilidades
                                </h3>
                                <span className="text-xs px-2 py-1 bg-slate-700 rounded text-gray-300">
                                    Ranking de Quedas
                                </span>
                            </div>

                            <div className="flex-1 overflow-x-auto">
                                <table className="w-full text-sm text-left">
                                    <thead className="text-xs text-gray-400 uppercase bg-slate-800/30">
                                        <tr>
                                            <th className="px-6 py-3">Dispositivo</th>
                                            <th className="px-6 py-3">Diagnóstico</th>
                                            <th className="px-6 py-3 text-right">Quedas (Offline)</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-700/50">
                                        {incidentsStats?.top_problematic?.length > 0 ? (
                                            incidentsStats.top_problematic.map((device: any, idx: number) => (
                                                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                                                    <td className="px-6 py-4 font-medium text-white">
                                                        {device.name}
                                                        <div className="text-xs text-gray-500 font-normal">{device.ip || 'IP não identificado'}</div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className={clsx(
                                                            "px-2 py-1 rounded text-xs font-bold",
                                                            device.drops > 10 ? "bg-red-500/10 text-red-400" : "bg-amber-500/10 text-amber-400"
                                                        )}>
                                                            {device.drops > 10 ? "CRÍTICO" : "ATENÇÃO"}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <span className="text-red-400 font-bold">{device.drops}</span>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={3} className="px-6 py-12 text-center text-gray-500">
                                                    <CheckCircle size={32} className="mx-auto mb-2 text-emerald-500/50" />
                                                    Nenhum dispositivo com instabilidade relevante no período.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Bottom Action */}
                    <div className="bg-slate-900/50 rounded-xl p-6 border border-slate-800 flex justify-between items-center group hover:border-blue-500/30 transition-colors">
                        <div>
                            <h3 className="font-bold text-white">Documentação de Conformidade (SLA)</h3>
                            <p className="text-gray-400 text-sm">Gere o documento oficial com o cálculo exato de disponibilidade para auditoria.</p>
                        </div>
                        <button
                            onClick={() => handleDownload('sla')}
                            disabled={loadingSLA}
                            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold flex items-center gap-2 transition-all shadow-lg hover:shadow-blue-900/20"
                        >
                            {loadingSLA ? <Loader2 className="animate-spin" /> : <CloudDownload />}
                            Baixar Relatório SLA Completo
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default Reports;
