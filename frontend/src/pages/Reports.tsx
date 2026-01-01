import React, { useState } from 'react';
import { CloudDownload, FileText, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';

const Reports: React.FC = () => {
    const [period, setPeriod] = useState("30");
    const [loading, setLoading] = useState(false);

    const handleDownload = async () => {
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

    return (
        <div className="p-6 space-y-6">
            <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-6">Relatórios Gerenciais</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                {/* CARD SLA */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-all border border-gray-200 dark:border-gray-700">
                    <div className="p-6 pb-2">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Disponibilidade (SLA)</h3>
                            <FileText className="h-6 w-6 text-blue-500" />
                        </div>
                    </div>
                    <div className="p-6 pt-0">
                        <p className="text-gray-500 dark:text-gray-400 mb-4 text-sm">
                            Gera um arquivo PDF contendo o resumo de disponibilidade (uptime) e latência média de todos os equipamentos monitorados.
                        </p>

                        <div className="space-y-4">
                            <div className="flex flex-col space-y-1.5">
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Período</span>
                                <select
                                    value={period}
                                    onChange={(e) => setPeriod(e.target.value)}
                                    className="flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-transparent px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-100 dark:focus:ring-blue-400 dark:focus:ring-offset-gray-900"
                                >
                                    <option value="7">Últimos 7 dias</option>
                                    <option value="15">Últimos 15 dias</option>
                                    <option value="30">Últimos 30 dias</option>
                                    <option value="90">Últimos 3 Meses</option>
                                </select>
                            </div>

                            <button
                                className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 dark:ring-offset-slate-950 dark:focus-visible:ring-slate-300 bg-blue-600 text-slate-50 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 h-10 px-4 py-2 w-full"
                                onClick={handleDownload}
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Gerando PDF...
                                    </>
                                ) : (
                                    <>
                                        <CloudDownload className="mr-2 h-4 w-4" />
                                        Baixar PDF
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Placeholder para Futuros Relatórios */}
                <div className="bg-white dark:bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 p-6 opacity-60 flex flex-col justify-center">
                    <div className="mb-2">
                        <h3 className="text-xl font-semibold text-gray-400">Incidentes (Em Breve)</h3>
                    </div>
                    <div>
                        <p className="text-gray-400 text-sm">
                            Relatório detalhado de quedas e alertas disparados.
                        </p>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Reports;
