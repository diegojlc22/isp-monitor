
import { useEffect, useState } from 'react';
import { Check, X, MapPin, User, Server } from "lucide-react";

// Definição de tipos simples para evitar erros do TS
interface Request {
    id: number;
    name: string;
    by: string;
    lat: number;
    lon: number;
    editingName?: string; // Campo local para edição
}

const API_Base = "/api";

export default function RequestsPage() {
    const [requests, setRequests] = useState<Request[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRequests();
    }, []);

    const fetchRequests = async () => {
        try {
            const res = await fetch(`${API_Base}/mobile/requests`);
            if (res.ok) {
                const data = await res.json();
                // Inicializa o valor de edição com o nome original
                setRequests(data.map((r: Request) => ({ ...r, editingName: r.name })));
            }
        } catch (error) {
            console.error("Erro ao buscar solicitações", error);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (id: number, finalName: string) => {
        if (!confirm(`Deseja aprovar a torre como "${finalName}"?`)) return;

        try {
            const res = await fetch(`${API_Base}/mobile/requests/${id}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: finalName })
            });

            if (res.ok) {
                alert("Torre Aprovada com sucesso!");
                // Remove da lista local
                setRequests(prev => prev.filter(r => r.id !== id));
            } else {
                throw new Error("Falha na aprovação");
            }
        } catch (error) {
            alert("Erro ao aprovar solicitação.");
        }
    };

    const handleReject = async (id: number, name: string) => {
        if (!confirm(`Tem certeza que deseja REJEITAR a torre ${name}?`)) return;

        try {
            const res = await fetch(`${API_Base}/mobile/requests/${id}/reject`, {
                method: 'POST'
            });

            if (res.ok) {
                alert("Solicitação rejeitada.");
                setRequests(prev => prev.filter(r => r.id !== id));
            } else {
                throw new Error("Falha ao rejeitar");
            }
        } catch (error) {
            alert("Erro ao rejeitar solicitação.");
        }
    };

    if (loading) return <div className="p-8 text-white">Carregando...</div>;

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold text-slate-100 mb-6 flex items-center gap-2">
                <Server className="h-8 w-8 text-blue-400" />
                Solicitações de Cadastro (Mobile)
            </h1>

            {requests.length === 0 ? (
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center text-slate-400">
                    Nenhuma solicitação pendente no momento.
                </div>
            ) : (
                <div className="grid gap-4">
                    {requests.map((req) => (
                        <div key={req.id} className="bg-slate-800 border border-slate-700 text-white rounded-lg shadow-sm">
                            <div className="p-6 flex flex-col md:flex-row justify-between items-center gap-4">

                                <div className="flex-1">
                                    <div className="flex flex-col gap-2">
                                        <label className="text-xs text-slate-500 font-bold uppercase tracking-wider">Nome da Torre</label>
                                        <input
                                            type="text"
                                            className="bg-slate-900 border border-slate-700 text-blue-100 text-lg font-bold p-2 rounded focus:border-blue-500 outline-none"
                                            value={req.editingName}
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                setRequests(prev => prev.map(r => r.id === req.id ? { ...r, editingName: val } : r));
                                            }}
                                        />
                                    </div>
                                    <div className="flex flex-col gap-1 mt-3 text-slate-400 text-sm">
                                        <div className="flex items-center gap-2">
                                            <User size={14} />
                                            <span>Solicitado por: <span className="text-white">{req.by || "Técnico Desconhecido"}</span></span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <MapPin size={14} />
                                            <a
                                                href={`https://www.google.com/maps?q=${req.lat},${req.lon}`}
                                                target="_blank"
                                                rel="noreferrer"
                                                className="font-mono text-xs text-yellow-400 hover:text-yellow-300 hover:underline cursor-pointer flex items-center gap-1"
                                            >
                                                {req.lat.toFixed(6)}, {req.lon.toFixed(6)} (Ver no Mapa ↗)
                                            </a>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex gap-2 items-end">
                                    <button
                                        className="bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 px-3 py-2 h-11 rounded-md flex items-center text-sm font-medium transition-colors"
                                        onClick={() => handleReject(req.id, req.name)}
                                    >
                                        <X className="h-4 w-4 mr-1" /> Rejeitar
                                    </button>
                                    <button
                                        className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 h-11 rounded-md flex items-center text-sm font-medium transition-colors shadow-lg shadow-green-900/20"
                                        onClick={() => handleApprove(req.id, req.editingName || req.name)}
                                    >
                                        <Check className="h-4 w-4 mr-1" /> Aprovar e Salvar
                                    </button>
                                </div>

                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
