import { useEffect, useState } from 'react';
import { getEquipments, createEquipment, updateEquipment, deleteEquipment, getTowers, getLatencyHistory, getLatencyConfig, rebootEquipment } from '../services/api';
import { Plus, Trash2, Search, Server, MonitorPlay, Save, CheckSquare, Square, Edit2, Activity, Power } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import clsx from 'clsx';

export function Equipments() {
    const [equipments, setEquipments] = useState<any[]>([]);
    const [towers, setTowers] = useState<any[]>([]);
    const [showModal, setShowModal] = useState(false);
    const [editingEquipment, setEditingEquipment] = useState<any | null>(null);

    // Scanner States
    const [showScanner, setShowScanner] = useState(false);
    const [scanRange, setScanRange] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [scannedIps, setScannedIps] = useState<any[]>([]);
    const [selectedIps, setSelectedIps] = useState<string[]>([]);
    const [ipNames, setIpNames] = useState<Record<string, string>>({});
    const [progress, setProgress] = useState(0);

    // History State
    const [historyData, setHistoryData] = useState<any[]>([]);
    const [historyConfig, setHistoryConfig] = useState({ good: 50, critical: 200 });
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [selectedEqHistory, setSelectedEqHistory] = useState<any>(null);
    const [historyPeriod, setHistoryPeriod] = useState('24h');

    const [formData, setFormData] = useState({
        name: '',
        ip: '',
        tower_id: '',
        ssh_user: 'admin',
        ssh_password: '',
        ssh_port: 22
    });

    async function load() {
        try {
            const [eqs, tws] = await Promise.all([getEquipments(), getTowers()]);
            setEquipments(eqs);
            setTowers(tws);
        } catch (e) { console.error(e); }
    }

    useEffect(() => {
        load();
        const interval = setInterval(load, 15000);
        return () => clearInterval(interval);
    }, []);

    async function handleShowHistory(eq: any) {
        setSelectedEqHistory(eq);
        try {
            const config = await getLatencyConfig();
            setHistoryConfig(config);
            await loadHistory(eq.id, '24h');
            setShowHistoryModal(true);
        } catch (e) {
            console.error(e);
            alert('Erro ao carregar histórico.');
        }
    }

    async function loadHistory(id: number, period: string) {
        setHistoryPeriod(period);
        const data = await getLatencyHistory(id, period);
        // Format timestamp for easier reading
        setHistoryData(data.map((d: any) => ({
            ...d,
            timeStr: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        })));
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        try {
            const payload: any = {
                name: formData.name,
                ip: formData.ip,
                tower_id: formData.tower_id ? parseInt(formData.tower_id) : null,
                ssh_user: formData.ssh_user,
                ssh_port: Number(formData.ssh_port)
            };

            // Only send password if provided (for updates)
            if (formData.ssh_password) {
                payload.ssh_password = formData.ssh_password;
            }

            if (editingEquipment) {
                await updateEquipment(editingEquipment.id, payload);
            } else {
                await createEquipment(payload);
            }

            setShowModal(false);
            setEditingEquipment(null);
            resetFormState();
            load();
        } catch (error) {
            alert('Erro ao salvar equipamento.');
        }
    }

    async function handleReboot(eq: any) {
        if (!confirm(`Tem certeza que deseja REINICIAR o equipamento ${eq.name}? Isso pode causar queda temporária.`)) return;

        try {
            await rebootEquipment(eq.id);
            alert("Comando de reboot enviado com sucesso!");
        } catch (e: any) {
            alert("Erro ao enviar comando: " + (e.response?.data?.detail || e.message));
        }
    }

    function handleEdit(eq: any) {
        setEditingEquipment(eq);
        setFormData({
            name: eq.name,
            ip: eq.ip,
            tower_id: eq.tower_id ? String(eq.tower_id) : '',
            ssh_user: eq.ssh_user || 'admin',
            ssh_password: '', // Password is never returned for security
            ssh_port: eq.ssh_port || 22
        });
        setShowModal(true);
    }

    function resetFormState() {
        setFormData({
            name: '',
            ip: '',
            tower_id: '',
            ssh_user: 'admin',
            ssh_password: '',
            ssh_port: 22
        });
    }

    function openNewModal() {
        setEditingEquipment(null);
        resetFormState();
        setShowModal(true);
    }

    async function handleScan() {
        setIsScanning(true);
        setScannedIps([]);
        setSelectedIps([]);
        setIpNames({});
        setProgress(0);

        try {
            const evtSource = new EventSource(`http://localhost:8000/equipments/scan/stream/?ip_range=${encodeURIComponent(scanRange)}`);

            evtSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                setProgress(data.progress);

                if (data.is_online) {
                    setScannedIps(prev => [...prev, data.ip]);
                }
            };

            evtSource.addEventListener("done", () => {
                evtSource.close();
                setIsScanning(false);
            });

            evtSource.onerror = (err) => {
                // Check readyState to differentiate between actual errors and normal close
                if (evtSource.readyState !== EventSource.CLOSED) {
                    evtSource.close();
                    setIsScanning(false);
                    // Only alert if we haven't made any progress, implying a connection failure
                    if (progress === 0) alert('Erro ao conectar ao scanner.');
                }
            };

        } catch (e) {
            alert('Erro ao iniciar scan.');
            setIsScanning(false);
        }
    }

    async function saveScanned() {
        if (selectedIps.length === 0) return;

        try {
            for (const ip of selectedIps) {
                const name = ipNames[ip] || `Dispositivo ${ip}`;
                await createEquipment({
                    name: name,
                    ip: ip,
                    tower_id: null
                });
            }
            alert(`${selectedIps.length} dispositivos adicionados!`);
            setShowScanner(false);
            load();
        } catch (e) {
            alert('Erro ao salvar alguns dispositivos.');
        }
    }

    function toggleIpSelection(ip: string) {
        if (selectedIps.includes(ip)) {
            setSelectedIps(selectedIps.filter(i => i !== ip));
        } else {
            setSelectedIps([...selectedIps, ip]);
        }
    }

    async function handleDelete(id: number) {
        if (confirm('Tem certeza?')) {
            await deleteEquipment(id);
            load();
        }
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Equipamentos</h2>
                <div className="flex gap-2">
                    <button onClick={() => setShowScanner(true)} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors">
                        <MonitorPlay size={20} />
                        Scan Rede
                    </button>
                    <button onClick={openNewModal} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                        <Plus size={20} />
                        Novo Equipamento
                    </button>
                </div>
            </div>

            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="p-4 border-b border-slate-800 flex gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                        <input type="text" placeholder="Buscar equipamentos..." className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
                    </div>
                </div>

                <table className="w-full text-left text-sm text-slate-400">
                    <thead className="bg-slate-950 text-slate-200 uppercase font-medium">
                        <tr>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4">Nome</th>
                            <th className="px-6 py-4">IP</th>
                            <th className="px-6 py-4">Torre Associada</th>
                            <th className="px-6 py-4 text-right">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {equipments.length === 0 && (
                            <tr><td colSpan={5} className="px-6 py-8 text-center">Nenhum equipamento cadastrado.</td></tr>
                        )}
                        {equipments.map(eq => {
                            const tower = towers.find(t => t.id === eq.tower_id);
                            return (
                                <tr key={eq.id} className="hover:bg-slate-800/50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <div className={clsx("w-2.5 h-2.5 rounded-full animate-pulse", eq.is_online ? "bg-emerald-500" : "bg-rose-500")} />
                                            <span className={eq.is_online ? "text-emerald-400" : "text-rose-400"}>
                                                {eq.is_online ? "Online" : "Offline"}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 font-medium text-white flex items-center gap-2">
                                        <Server size={16} className="text-slate-500" />
                                        {eq.name}
                                    </td>
                                    <td className="px-6 py-4 font-mono text-slate-300">{eq.ip}</td>
                                    <td className="px-6 py-4">
                                        {tower ? <span className="text-blue-400">{tower.name}</span> : <span className="text-slate-600">-</span>}
                                    </td>
                                    <td className="px-6 py-4 text-right flex justify-end gap-2">
                                        <button onClick={() => handleReboot(eq)} className="text-slate-500 hover:text-orange-500 p-2" title="Reiniciar Equipamento (SSH)">
                                            <Power size={18} />
                                        </button>
                                        <button onClick={() => handleShowHistory(eq)} className="text-slate-500 hover:text-amber-400 p-2" title="Histórico de Latência">
                                            <Activity size={18} />
                                        </button>
                                        <button onClick={() => handleEdit(eq)} className="text-slate-500 hover:text-blue-400 p-2">
                                            <Edit2 size={18} />
                                        </button>
                                        <button onClick={() => handleDelete(eq.id)} className="text-slate-500 hover:text-rose-500 p-2">
                                            <Trash2 size={18} />
                                        </button>
                                    </td>
                                </tr>
                            )
                        })}
                    </tbody>
                </table>
            </div>

            {/* Modal de Criação Manual */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg shadow-2xl p-6">
                        <h3 className="text-xl font-bold text-white mb-4">{editingEquipment ? 'Editar Equipamento' : 'Novo Equipamento'}</h3>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Nome</label>
                                    <input required type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                        value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">IP</label>
                                    <input required type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                        value={formData.ip} onChange={e => setFormData({ ...formData, ip: e.target.value })} />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Associar à Torre (Opcional)</label>
                                <select className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                    value={formData.tower_id} onChange={e => setFormData({ ...formData, tower_id: e.target.value })}>
                                    <option value="">Nenhuma</option>
                                    {towers.map(t => (
                                        <option key={t.id} value={t.id}>{t.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                                <h4 className="text-sm font-bold text-slate-300 mb-3 uppercase flex items-center gap-2">
                                    <Server size={14} className="text-orange-500" />
                                    Acesso SSH (Para Reboot)
                                </h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Usuário</label>
                                        <input type="text" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none"
                                            value={formData.ssh_user} onChange={e => setFormData({ ...formData, ssh_user: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Porta</label>
                                        <input type="number" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none"
                                            value={formData.ssh_port} onChange={e => setFormData({ ...formData, ssh_port: Number(e.target.value) })} />
                                    </div>
                                    <div className="col-span-2">
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Senha {editingEquipment && '(Deixe em branco para não alterar)'}</label>
                                        <input type="password" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none"
                                            value={formData.ssh_password} onChange={e => setFormData({ ...formData, ssh_password: e.target.value })} />
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-slate-300 hover:text-white">Cancelar</button>
                                <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium">
                                    {editingEquipment ? 'Salvar Alterações' : 'Salvar Equipamento'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal de Scanner */}
            {showScanner && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh]">
                        <div className="p-6 border-b border-slate-800">
                            <h3 className="text-xl font-bold text-white mb-2">Network Scanner</h3>
                            <p className="text-slate-400 text-sm">Escaneie uma faixa de IP para encontrar dispositivos ativos.</p>
                        </div>

                        <div className="p-6 space-y-4 overflow-y-auto flex-1 custom-scrollbar">
                            <div className="flex gap-4 items-end">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-slate-400 mb-1">IP de Referência ou Faixa</label>
                                    <input
                                        type="text"
                                        placeholder="Ex: 192.168.0.1 (Detectamos a faixa /24 automaticamente)"
                                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono"
                                        value={scanRange}
                                        onChange={e => setScanRange(e.target.value)}
                                    />
                                </div>
                                <button
                                    onClick={handleScan}
                                    disabled={isScanning || !scanRange}
                                    className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 h-[42px]"
                                >
                                    {isScanning ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            Parar
                                        </>
                                    ) : (
                                        <>
                                            <MonitorPlay size={18} />
                                            Iniciar Scan
                                        </>
                                    )}
                                </button>
                            </div>

                            {/* Progress Bar */}
                            {isScanning && (
                                <div className="w-full bg-slate-800 rounded-full h-2.5 mb-4">
                                    <div className="bg-emerald-500 h-2.5 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
                                    <p className="text-xs text-right text-slate-400 mt-1">{progress}% Concluído</p>
                                </div>
                            )}

                            {scannedIps.length > 0 && (
                                <div className="space-y-2 mt-6">
                                    <div className="flex items-center justify-between text-sm text-slate-400 px-2 mb-2">
                                        <span>{scannedIps.length} Dispositivos Encontrados</span>
                                        <span>{selectedIps.length} Selecionados</span>
                                    </div>
                                    <div className="bg-slate-950 rounded-lg border border-slate-800 divide-y divide-slate-800">
                                        {scannedIps.map(ip => (
                                            <div key={ip} className={clsx("flex items-center gap-4 p-3 transition-colors", selectedIps.includes(ip) ? "bg-blue-500/10" : "hover:bg-slate-900")}>
                                                <button onClick={() => toggleIpSelection(ip)} className="text-slate-400 hover:text-white">
                                                    {selectedIps.includes(ip) ?
                                                        <CheckSquare className="text-blue-500" /> :
                                                        <Square />
                                                    }
                                                </button>
                                                <div className="font-mono text-slate-300 w-32">{ip}</div>
                                                <input
                                                    type="text"
                                                    placeholder="Nome do dispositivo"
                                                    className="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
                                                    value={ipNames[ip] || ''}
                                                    onChange={e => setIpNames({ ...ipNames, [ip]: e.target.value })}
                                                />
                                                <div className="text-emerald-500 text-xs font-bold px-2 py-1 bg-emerald-500/10 rounded">ONLINE</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {!isScanning && scannedIps.length === 0 && scanRange && (
                                <div className="text-center py-8 text-slate-500">
                                    Nenhum dispositivo encontrado ou scan ainda não iniciado.
                                </div>
                            )}
                        </div>

                        <div className="p-6 border-t border-slate-800 flex justify-end gap-3 bg-slate-900 rounded-b-xl">
                            <button onClick={() => setShowScanner(false)} className="px-4 py-2 text-slate-300 hover:text-white">Fechar</button>
                            <button
                                onClick={saveScanned}
                                disabled={selectedIps.length === 0}
                                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2"
                            >
                                <Save size={18} />
                                Salvar Selecionados ({selectedIps.length})
                            </button>
                        </div>
                    </div>
                </div>
            )}
            {/* Modal de Histórico de Latência */}
            {showHistoryModal && selectedEqHistory && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-4xl shadow-2xl flex flex-col h-[80vh]">
                        <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-950 rounded-t-xl">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Activity className="text-amber-500" />
                                    Histórico de Latência: {selectedEqHistory.name}
                                </h3>
                                <p className="text-sm text-slate-400 font-mono mt-1">{selectedEqHistory.ip}</p>
                            </div>
                            <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800">
                                <button onClick={() => loadHistory(selectedEqHistory.id, '24h')} className={clsx("px-3 py-1 rounded text-sm transition-colors", historyPeriod === '24h' ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white")}>24h</button>
                                <button onClick={() => loadHistory(selectedEqHistory.id, '7d')} className={clsx("px-3 py-1 rounded text-sm transition-colors", historyPeriod === '7d' ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white")}>7 Dias</button>
                            </div>
                        </div>

                        <div className="flex-1 p-6 min-h-0">
                            {historyData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={historyData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                        <defs>
                                            <linearGradient id="splitColor" x1="0" y1="0" x2="0" y2="1">
                                                {(() => {
                                                    const dataMax = Math.max(...historyData.map((d: any) => d.latency));
                                                    const max = Math.max(dataMax, historyConfig.critical * 1.1);
                                                    const critOff = (max - historyConfig.critical) / max;
                                                    const goodOff = (max - historyConfig.good) / max;
                                                    return (
                                                        <>
                                                            <stop offset={critOff} stopColor="#fb7185" stopOpacity={0.8} />
                                                            <stop offset={critOff} stopColor="#facc15" stopOpacity={0.8} />
                                                            <stop offset={goodOff} stopColor="#facc15" stopOpacity={0.8} />
                                                            <stop offset={goodOff} stopColor="#4ade80" stopOpacity={0.8} />
                                                            <stop offset={1} stopColor="#4ade80" stopOpacity={0.8} />
                                                        </>
                                                    );
                                                })()}
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                        <XAxis dataKey="timeStr" stroke="#64748b" tick={{ fontSize: 12 }} minTickGap={30} />
                                        <YAxis stroke="#64748b" tick={{ fontSize: 12 }} label={{ value: 'ms', angle: -90, position: 'insideLeft', fill: '#64748b' }} />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                                            labelStyle={{ color: '#94a3b8' }}
                                        />
                                        <ReferenceLine y={historyConfig.critical} label={{ value: 'Crítico', fill: '#fb7185', fontSize: 10 }} stroke="#fb7185" strokeDasharray="3 3" />
                                        <ReferenceLine y={historyConfig.good} label={{ value: 'Bom', fill: '#4ade80', fontSize: 10 }} stroke="#4ade80" strokeDasharray="3 3" />
                                        <Area type="monotone" dataKey="latency" stroke="url(#splitColor)" fill="url(#splitColor)" strokeWidth={2} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-full flex items-center justify-center text-slate-500">
                                    Sem dados de histórico para este período.
                                </div>
                            )}
                        </div>

                        <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-900 rounded-b-xl">
                            <button onClick={() => setShowHistoryModal(false)} className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors">Fechar</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
