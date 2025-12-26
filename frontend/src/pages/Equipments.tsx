import { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { getEquipments, createEquipment, updateEquipment, deleteEquipment, getTowers, getLatencyHistory, getLatencyConfig, rebootEquipment, exportEquipmentsCSV, importEquipmentsCSV } from '../services/api';
import { Plus, Trash2, Search, Server, MonitorPlay, Save, CheckSquare, Square, Edit2, Activity, Power, Wifi, Info, Download, Upload } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import clsx from 'clsx';

// --- Interfaces ---
interface Tower {
    id: number;
    name: string;
}

interface Equipment {
    id: number;
    name: string;
    ip: string;
    tower_id: number | null;
    parent_id: number | null;
    is_online: boolean;
    brand: string;
    equipment_type: string;
    signal_dbm?: number;
    ccq?: number;
    connected_clients?: number;
    ssh_user?: string;
    ssh_port?: number;
    snmp_community?: string;
    snmp_version?: number;
    snmp_port?: number;
    snmp_interface_index?: number;
    is_mikrotik?: boolean;
    mikrotik_interface?: string;
    api_port?: number;
}

interface FormData {
    name: string;
    ip: string;
    tower_id: string;
    parent_id: string;
    ssh_user: string;
    ssh_password: string;
    ssh_port: number;
    snmp_community: string;
    snmp_version: number;
    snmp_port: number;
    snmp_interface_index: number;
    brand: string;
    equipment_type: string;
    is_mikrotik: boolean;
    mikrotik_interface: string;
    api_port: number;
}

const INITIAL_FORM_STATE: FormData = {
    name: '',
    ip: '',
    tower_id: '',
    parent_id: '',
    ssh_user: 'admin',
    ssh_password: '',
    ssh_port: 22,
    snmp_community: 'public',
    snmp_version: 1,
    snmp_port: 161,
    snmp_interface_index: 1,
    brand: 'generic',
    equipment_type: 'station',
    is_mikrotik: false,
    mikrotik_interface: '',
    api_port: 8728
};

export function Equipments() {
    // --- State ---
    const [equipments, setEquipments] = useState<Equipment[]>([]);
    const [towers, setTowers] = useState<Tower[]>([]);
    const [showModal, setShowModal] = useState(false);
    const [editingEquipment, setEditingEquipment] = useState<Equipment | null>(null);
    const [formData, setFormData] = useState<FormData>(INITIAL_FORM_STATE);
    const [filterText, setFilterText] = useState('');
    const [filterStatus, setFilterStatus] = useState<'all' | 'online' | 'offline'>('all');
    const [filterTower, setFilterTower] = useState<string>('all');
    const [filterType, setFilterType] = useState<string>('all');

    // Scanner States
    const [showScanner, setShowScanner] = useState(false);
    const [scanRange, setScanRange] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [scannedIps, setScannedIps] = useState<string[]>([]);
    const [selectedIps, setSelectedIps] = useState<string[]>([]);
    const [ipNames, setIpNames] = useState<Record<string, string>>({});
    const [progress, setProgress] = useState(0);
    const eventSourceRef = useRef<EventSource | null>(null);

    // History State
    const [historyData, setHistoryData] = useState<any[]>([]);
    const [historyConfig, setHistoryConfig] = useState({ good: 50, critical: 200 });
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [selectedEqHistory, setSelectedEqHistory] = useState<Equipment | null>(null);
    const [historyPeriod, setHistoryPeriod] = useState('24h');

    // Wireless Info Modal
    const [showWirelessModal, setShowWirelessModal] = useState(false);
    const [selectedWirelessEq, setSelectedWirelessEq] = useState<Equipment | null>(null);

    // --- Actions ---
    const load = useCallback(async () => {
        try {
            const [eqs, tws] = await Promise.all([getEquipments(), getTowers()]);
            setEquipments(eqs);
            setTowers(tws);
        } catch (e) { console.error('Error loading data:', e); }
    }, []);

    useEffect(() => {
        load();
        const interval = setInterval(load, 15000);
        return () => clearInterval(interval);
    }, [load]);

    // Cleanup EventSource on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    const filteredEquipments = useMemo(() => {
        let result = equipments;

        // Text filter
        if (filterText) {
            const lower = filterText.toLowerCase();
            result = result.filter(eq =>
                eq.name.toLowerCase().includes(lower) ||
                eq.ip.includes(lower)
            );
        }

        // Status filter
        if (filterStatus !== 'all') {
            result = result.filter(eq =>
                filterStatus === 'online' ? eq.is_online : !eq.is_online
            );
        }

        // Tower filter
        if (filterTower !== 'all') {
            result = result.filter(eq =>
                eq.tower_id === parseInt(filterTower)
            );
        }

        // Type filter
        if (filterType !== 'all') {
            result = result.filter(eq => eq.equipment_type === filterType);
        }

        return result;
    }, [equipments, filterText, filterStatus, filterTower, filterType]);

    async function handleShowHistory(eq: Equipment) {
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
        try {
            const data = await getLatencyHistory(id, period);
            setHistoryData(data.map((d: any) => ({
                ...d,
                timeStr: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            })));
        } catch (e) {
            console.error('Error loading history:', e);
        }
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        try {
            const payload: any = {
                ...formData,
                tower_id: formData.tower_id ? parseInt(formData.tower_id) : null,
                parent_id: formData.parent_id ? parseInt(formData.parent_id) : null,
                ssh_port: Number(formData.ssh_port),
                snmp_version: Number(formData.snmp_version),
                snmp_port: Number(formData.snmp_port),
                snmp_interface_index: Number(formData.snmp_interface_index),
                api_port: Number(formData.api_port)
            };

            // Remove empty password if not provided
            if (!formData.ssh_password) {
                delete payload.ssh_password;
            }

            if (editingEquipment) {
                await updateEquipment(editingEquipment.id, payload);
            } else {
                await createEquipment(payload);
            }

            setShowModal(false);
            setEditingEquipment(null);
            setFormData(INITIAL_FORM_STATE);
            load();
        } catch (error) {
            console.error(error);
            alert('Erro ao salvar equipamento.');
        }
    }

    async function handleReboot(eq: Equipment) {
        if (!confirm(`Tem certeza que deseja REINICIAR o equipamento ${eq.name}? Isso pode causar queda temporária.`)) return;

        try {
            await rebootEquipment(eq.id);
            alert("Comando de reboot enviado com sucesso!");
        } catch (e: any) {
            alert("Erro ao enviar comando: " + (e.response?.data?.detail || e.message));
        }
    }

    function handleEdit(eq: Equipment) {
        setEditingEquipment(eq);
        setFormData({
            name: eq.name,
            ip: eq.ip,
            tower_id: eq.tower_id ? String(eq.tower_id) : '',
            parent_id: eq.parent_id ? String(eq.parent_id) : '',
            ssh_user: eq.ssh_user || 'admin',
            ssh_password: '',
            ssh_port: eq.ssh_port || 22,
            snmp_community: eq.snmp_community || 'public',
            snmp_version: eq.snmp_version || 1,
            snmp_port: eq.snmp_port || 161,
            snmp_interface_index: eq.snmp_interface_index || 1,
            brand: eq.brand || 'generic',
            equipment_type: eq.equipment_type || 'station',
            is_mikrotik: eq.is_mikrotik || false,
            mikrotik_interface: eq.mikrotik_interface || '',
            api_port: eq.api_port || 8728
        });
        setShowModal(true);
    }

    function openNewModal() {
        setEditingEquipment(null);
        setFormData(INITIAL_FORM_STATE);
        setShowModal(true);
    }

    // --- Scanner Logic ---
    async function handleScan() {
        if (isScanning) {
            // Stop scanning
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
            setIsScanning(false);
            return;
        }

        setIsScanning(true);
        setScannedIps([]);
        setSelectedIps([]);
        setIpNames({});
        setProgress(0);

        try {
            const evtSource = new EventSource(`/api/equipments/scan/stream/?ip_range=${encodeURIComponent(scanRange)}`);
            eventSourceRef.current = evtSource;

            evtSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                setProgress(data.progress || 0);

                if (data.is_online) {
                    setScannedIps(prev => {
                        if (prev.includes(data.ip)) return prev;
                        return [...prev, data.ip];
                    });
                }
            };

            evtSource.addEventListener("done", () => {
                evtSource.close();
                eventSourceRef.current = null;
                setIsScanning(false);
            });

            evtSource.onerror = () => {
                if (evtSource.readyState !== EventSource.CLOSED) {
                    evtSource.close();
                    eventSourceRef.current = null;
                    setIsScanning(false);
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

        const results = {
            success: [] as string[],
            failed: [] as { ip: string, reason: string }[]
        };

        for (const ip of selectedIps) {
            try {
                const name = ipNames[ip] || `Dispositivo ${ip}`;
                await createEquipment({
                    name: name,
                    ip: ip,
                    tower_id: null,
                    ssh_user: 'admin',
                    ssh_port: 22
                });
                results.success.push(ip);
            } catch (e: any) {
                const errorMsg = e.response?.data?.detail || e.message || 'Erro desconhecido';
                results.failed.push({ ip, reason: errorMsg });
            }
        }

        let message = '';
        if (results.success.length > 0) message += `✅ ${results.success.length} dispositivo(s) adicionado(s)!\n`;
        if (results.failed.length > 0) {
            message += `\n❌ ${results.failed.length} falhou(ram):\n` + results.failed.map(f => `• ${f.ip}: ${f.reason}`).join('\n');
        }

        alert(message);

        if (results.success.length > 0) {
            setShowScanner(false);
            load();
        }
    }

    function toggleIpSelection(ip: string) {
        setSelectedIps(prev => prev.includes(ip) ? prev.filter(i => i !== ip) : [...prev, ip]);
    }

    async function handleDelete(id: number) {
        if (confirm('Tem certeza?')) {
            try {
                await deleteEquipment(id);
                load();
            } catch (e) { console.error(e); }
        }
    }

    async function handleExportCSV() {
        try {
            const blob = await exportEquipmentsCSV();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `equipments_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            console.error(e);
            alert('Erro ao exportar CSV');
        }
    }

    async function handleImportCSV(event: React.ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            const result = await importEquipmentsCSV(file);
            let message = `✅ Importação concluída!\n\n`;
            message += `• ${result.imported} equipamento(s) importado(s)\n`;
            if (result.skipped > 0) message += `• ${result.skipped} ignorado(s) (já existem)\n`;
            if (result.failed > 0) message += `• ${result.failed} falhou(ram)\n`;

            if (result.details.failed.length > 0) {
                message += `\nErros:\n` + result.details.failed.slice(0, 5).map((f: any) =>
                    `• ${f.row?.ip || 'N/A'}: ${f.reason}`
                ).join('\n');
                if (result.details.failed.length > 5) {
                    message += `\n... e mais ${result.details.failed.length - 5} erros`;
                }
            }

            alert(message);
            if (result.imported > 0) load();
        } catch (e: any) {
            console.error(e);
            alert('Erro ao importar CSV: ' + (e.response?.data?.detail || e.message));
        }

        // Reset input
        event.target.value = '';
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Equipamentos</h2>
                <div className="flex gap-2">
                    <button onClick={() => setShowScanner(true)} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors shadow-lg shadow-emerald-900/20">
                        <MonitorPlay size={20} />
                        Scan Rede
                    </button>

                    {/* Export CSV */}
                    <button onClick={handleExportCSV} className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors shadow-lg shadow-purple-900/20">
                        <Download size={20} />
                        Exportar CSV
                    </button>

                    {/* Import CSV */}
                    <label className="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors shadow-lg shadow-orange-900/20 cursor-pointer">
                        <Upload size={20} />
                        Importar CSV
                        <input type="file" accept=".csv" onChange={handleImportCSV} className="hidden" />
                    </label>

                    <button onClick={openNewModal} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors shadow-lg shadow-blue-900/20">
                        <Plus size={20} />
                        Novo Equipamento
                    </button>
                </div>
            </div>

            <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-xl">
                <div className="p-4 border-b border-slate-800">
                    <div className="flex flex-wrap gap-3">
                        {/* Search Input */}
                        <div className="relative flex-1 min-w-[250px]">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                            <input
                                type="text"
                                placeholder="Buscar por nome ou IP..."
                                className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                                value={filterText}
                                onChange={e => setFilterText(e.target.value)}
                            />
                        </div>

                        {/* Status Filter */}
                        <select
                            value={filterStatus}
                            onChange={e => setFilterStatus(e.target.value as 'all' | 'online' | 'offline')}
                            className="bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                        >
                            <option value="all">📊 Todos os Status</option>
                            <option value="online">🟢 Online</option>
                            <option value="offline">🔴 Offline</option>
                        </select>

                        {/* Tower Filter */}
                        <select
                            value={filterTower}
                            onChange={e => setFilterTower(e.target.value)}
                            className="bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                        >
                            <option value="all">📍 Todas as Torres</option>
                            {towers.map(t => (
                                <option key={t.id} value={t.id}>{t.name}</option>
                            ))}
                        </select>

                        {/* Type Filter */}
                        <select
                            value={filterType}
                            onChange={e => setFilterType(e.target.value)}
                            className="bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                        >
                            <option value="all">🔧 Todos os Tipos</option>
                            <option value="station">📡 Station (CPE)</option>
                            <option value="transmitter">📶 Transmitter (AP)</option>
                        </select>

                        {/* Clear Filters Button */}
                        {(filterText || filterStatus !== 'all' || filterTower !== 'all' || filterType !== 'all') && (
                            <button
                                onClick={() => {
                                    setFilterText('');
                                    setFilterStatus('all');
                                    setFilterTower('all');
                                    setFilterType('all');
                                }}
                                className="px-4 py-2 text-sm text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors border border-slate-700"
                            >
                                Limpar Filtros
                            </button>
                        )}
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-slate-400">
                        <thead className="bg-slate-950 text-slate-200 uppercase font-medium">
                            <tr>
                                <th className="px-4 py-4 w-12 text-center">Status</th>
                                <th className="px-4 py-4">Nome</th>
                                <th className="px-4 py-4">IP</th>
                                <th className="px-4 py-4 text-right">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {filteredEquipments.length === 0 && (
                                <tr><td colSpan={4} className="px-6 py-8 text-center text-slate-500">Nenhum equipamento encontrado.</td></tr>
                            )}
                            {filteredEquipments.map(eq => {
                                const tower = towers.find(t => t.id === eq.tower_id);
                                return (
                                    <tr key={eq.id} className="hover:bg-slate-800/50 transition-colors group">
                                        <td className="px-4 py-4">
                                            <div className={clsx("w-3 h-3 rounded-full mx-auto transition-all duration-500", eq.is_online ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] scale-110" : "bg-rose-500 opacity-80")} title={eq.is_online ? "Online" : "Offline"} />
                                        </td>
                                        <td className="px-4 py-4">
                                            <div className="font-medium text-white flex items-center gap-2">
                                                {eq.brand === 'mikrotik' ? <Activity size={16} className="text-blue-400" /> :
                                                    eq.brand === 'ubiquiti' ? <Wifi size={16} className="text-sky-400" /> :
                                                        eq.brand === 'intelbras' ? <Wifi size={16} className="text-green-400" /> :
                                                            <Server size={16} className="text-slate-500" />}
                                                {eq.name}
                                            </div>
                                            {tower && <div className="text-xs text-slate-500 ml-6 flex items-center gap-1">📍 {tower.name}</div>}
                                        </td>
                                        <td className="px-4 py-4 font-mono text-slate-300 text-xs">{eq.ip}</td>
                                        <td className="px-4 py-4 text-right">
                                            <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                {(eq.signal_dbm || eq.ccq || (eq.connected_clients !== undefined && eq.connected_clients !== null)) && (
                                                    <button onClick={() => { setSelectedWirelessEq(eq); setShowWirelessModal(true); }} className="text-slate-400 hover:text-sky-400 p-2 rounded hover:bg-slate-800 transition-colors" title="Informações Wireless">
                                                        <Info size={16} />
                                                    </button>
                                                )}
                                                <button onClick={() => handleReboot(eq)} className="text-slate-400 hover:text-orange-500 p-2 rounded hover:bg-slate-800 transition-colors" title="Reiniciar">
                                                    <Power size={16} />
                                                </button>
                                                <button onClick={() => handleShowHistory(eq)} className="text-slate-400 hover:text-amber-400 p-2 rounded hover:bg-slate-800 transition-colors" title="Histórico">
                                                    <Activity size={16} />
                                                </button>
                                                <button onClick={() => handleEdit(eq)} className="text-slate-400 hover:text-blue-400 p-2 rounded hover:bg-slate-800 transition-colors" title="Editar">
                                                    <Edit2 size={16} />
                                                </button>
                                                <button onClick={() => handleDelete(eq.id)} className="text-slate-400 hover:text-rose-500 p-2 rounded hover:bg-slate-800 transition-colors" title="Remover">
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal de Criação Manual */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg shadow-2xl p-6 max-h-[90vh] overflow-y-auto custom-scrollbar animate-in zoom-in-95 duration-200">
                        <h3 className="text-xl font-bold text-white mb-6 border-b border-slate-800 pb-2">{editingEquipment ? 'Editar Equipamento' : 'Novo Equipamento'}</h3>
                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Nome</label>
                                    <input required type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none transition-colors"
                                        value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Endereço IP</label>
                                    <input required type="text" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono transition-colors"
                                        value={formData.ip} onChange={e => setFormData({ ...formData, ip: e.target.value })} />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Fabricante</label>
                                    <select className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                        value={formData.brand} onChange={e => setFormData({ ...formData, brand: e.target.value })}>
                                        <option value="generic">Genérico</option>
                                        <option value="mikrotik">Mikrotik</option>
                                        <option value="ubiquiti">Ubiquiti</option>
                                        <option value="intelbras">Intelbras</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Torre</label>
                                    <select className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                        value={formData.tower_id} onChange={e => setFormData({ ...formData, tower_id: e.target.value })}>
                                        <option value="">Nenhuma</option>
                                        {towers.map(t => (
                                            <option key={t.id} value={t.id}>{t.name}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Tipo de Equipamento</label>
                                    <select className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                        value={formData.equipment_type} onChange={e => setFormData({ ...formData, equipment_type: e.target.value })}>
                                        <option value="station">📡 Station (CPE/Cliente)</option>
                                        <option value="transmitter">📶 Transmitter (AP/Transmissor)</option>
                                    </select>
                                    <p className="text-xs text-slate-500 mt-1">Define quais dados serão coletados via SNMP</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">Dependência (Pai)</label>
                                    <select className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                                        value={formData.parent_id} onChange={e => setFormData({ ...formData, parent_id: e.target.value })}>
                                        <option value="">Nenhuma (Independente)</option>
                                        {equipments
                                            .filter(eq => !editingEquipment || eq.id !== editingEquipment.id)
                                            .map(eq => (
                                                <option key={eq.id} value={eq.id}>{eq.name} ({eq.ip})</option>
                                            ))}
                                    </select>
                                    <p className="text-xs text-orange-500/80 mt-1">Silencia alerta se Pai cair</p>
                                </div>
                            </div>

                            <div className="bg-slate-950/50 p-4 rounded-lg border border-slate-800/50">
                                <h4 className="text-sm font-bold text-slate-300 mb-3 uppercase flex items-center gap-2">
                                    <Activity size={14} className="text-blue-500" />
                                    Configuração SNMP
                                </h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="col-span-2">
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Comunidade (Community)</label>
                                        <input type="text" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none transition-colors"
                                            value={formData.snmp_community} onChange={e => setFormData({ ...formData, snmp_community: e.target.value })} />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 col-span-2">
                                        <div>
                                            <label className="block text-xs font-medium text-slate-500 mb-1">Versão SNMP</label>
                                            <select className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                                                value={formData.snmp_version} onChange={e => setFormData({ ...formData, snmp_version: Number(e.target.value) })}>
                                                <option value={1}>v1</option>
                                                <option value={2}>v2c</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-slate-500 mb-1">Porta SNMP</label>
                                            <input type="number" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                                                value={formData.snmp_port} onChange={e => setFormData({ ...formData, snmp_port: Number(e.target.value) })} />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-xs font-medium text-slate-500 mb-1">Index Interface (OID) <span className="text-slate-600">(Padrão: 1)</span></label>
                                            <input type="number" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                                                placeholder="Ex: 1"
                                                value={formData.snmp_interface_index} onChange={e => setFormData({ ...formData, snmp_interface_index: Number(e.target.value) })} />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-slate-950/50 p-4 rounded-lg border border-slate-800/50">
                                <h4 className="text-sm font-bold text-slate-300 mb-3 uppercase flex items-center gap-2">
                                    <Server size={14} className="text-orange-500" />
                                    Acesso SSH (Reboot)
                                </h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Usuário</label>
                                        <input type="text" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none transition-colors"
                                            value={formData.ssh_user} onChange={e => setFormData({ ...formData, ssh_user: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Porta</label>
                                        <input type="number" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                                            value={formData.ssh_port} onChange={e => setFormData({ ...formData, ssh_port: Number(e.target.value) })} />
                                    </div>
                                    <div className="col-span-2">
                                        <label className="block text-xs font-medium text-slate-500 mb-1">Senha {editingEquipment && '(Deixe em branco para manter)'}</label>
                                        <input type="password" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none transition-colors"
                                            value={formData.ssh_password} onChange={e => setFormData({ ...formData, ssh_password: e.target.value })} />
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-2">
                                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-slate-400 hover:text-white transition-colors">Cancelar</button>
                                <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-blue-900/40">
                                    {editingEquipment ? 'Salvar Alterações' : 'Criar Equipamento'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal de Scanner */}
            {showScanner && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
                        <div className="p-6 border-b border-slate-800 bg-slate-950 rounded-t-xl">
                            <h3 className="text-xl font-bold text-white mb-2">Network Scanner</h3>
                            <p className="text-slate-400 text-sm">Escaneie uma faixa de IP para encontrar dispositivos ativos.</p>
                        </div>

                        <div className="p-6 space-y-4 overflow-y-auto flex-1 custom-scrollbar">
                            <div className="flex gap-4 items-end">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-slate-400 mb-1">IP de Referência ou Faixa</label>
                                    <input
                                        type="text"
                                        placeholder="Ex: 192.168.0.1 (Detectamos automaticamente)"
                                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none font-mono transition-colors"
                                        value={scanRange}
                                        onChange={e => setScanRange(e.target.value)}
                                    />
                                </div>
                                <button
                                    onClick={handleScan}
                                    disabled={!isScanning && !scanRange}
                                    className={clsx(
                                        "px-6 py-2 rounded-lg font-medium flex items-center gap-2 h-[42px] transition-all",
                                        isScanning
                                            ? "bg-rose-600 hover:bg-rose-700 text-white"
                                            : "bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                                    )}
                                >
                                    {isScanning ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            Parar
                                        </>
                                    ) : (
                                        <>
                                            <MonitorPlay size={18} />
                                            Iniciar
                                        </>
                                    )}
                                </button>
                            </div>

                            {isScanning && (
                                <div className="w-full bg-slate-800 rounded-full h-2.5 mb-4 overflow-hidden">
                                    <div className="bg-emerald-500 h-2.5 rounded-full transition-all duration-300 ease-out" style={{ width: `${progress}%` }}></div>
                                    <p className="text-xs text-right text-slate-400 mt-1">{progress}% Concluído</p>
                                </div>
                            )}

                            {scannedIps.length > 0 && (
                                <div className="space-y-2 mt-6 animate-in slide-in-from-bottom-2 duration-300">
                                    <div className="flex items-center justify-between text-sm text-slate-400 px-2 mb-2">
                                        <span>{scannedIps.length} Dispositivos Encontrados</span>
                                        <div className="flex items-center gap-3">
                                            <span>{selectedIps.length} Selecionados</span>
                                            <button
                                                onClick={() => {
                                                    if (selectedIps.length === scannedIps.length) {
                                                        setSelectedIps([]);
                                                    } else {
                                                        setSelectedIps([...scannedIps]);
                                                    }
                                                }}
                                                className="text-blue-400 hover:text-blue-300 font-medium transition-colors flex items-center gap-1.5 px-3 py-1 rounded-md hover:bg-blue-500/10 border border-blue-500/20"
                                            >
                                                {selectedIps.length === scannedIps.length ? (
                                                    <>
                                                        <Square size={14} />
                                                        Desmarcar Todos
                                                    </>
                                                ) : (
                                                    <>
                                                        <CheckSquare size={14} />
                                                        Marcar Todos
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                    <div className="bg-slate-950 rounded-lg border border-slate-800 divide-y divide-slate-800 max-h-[400px] overflow-y-auto custom-scrollbar">
                                        {scannedIps.map(ip => (
                                            <div key={ip} className={clsx("flex items-center gap-4 p-3 transition-colors duration-200", selectedIps.includes(ip) ? "bg-blue-900/20" : "hover:bg-slate-900")}>
                                                <button onClick={() => toggleIpSelection(ip)} className="text-slate-400 hover:text-white transition-colors">
                                                    {selectedIps.includes(ip) ? <CheckSquare className="text-blue-500" /> : <Square />}
                                                </button>
                                                <div className="font-mono text-slate-300 w-32">{ip}</div>
                                                <input
                                                    type="text"
                                                    placeholder="Nome do dispositivo"
                                                    className="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-1 text-sm text-white focus:border-blue-500 focus:outline-none transition-colors"
                                                    value={ipNames[ip] || ''}
                                                    onChange={e => setIpNames({ ...ipNames, [ip]: e.target.value })}
                                                />
                                                <div className="text-emerald-500 text-xs font-bold px-2 py-1 bg-emerald-500/10 rounded border border-emerald-500/20">ONLINE</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {!isScanning && scannedIps.length === 0 && (
                                <div className="text-center py-12 text-slate-500 border border-dashed border-slate-800 rounded-lg">
                                    <MonitorPlay size={48} className="mx-auto text-slate-700 mb-3" />
                                    <p>Nenhum dispositivo encontrado ainda.</p>
                                    <p className="text-xs mt-1">Insira um IP e clique em Iniciar para começar.</p>
                                </div>
                            )}
                        </div>

                        <div className="p-6 border-t border-slate-800 flex justify-end gap-3 bg-slate-950 rounded-b-xl">
                            <button onClick={() => setShowScanner(false)} className="px-4 py-2 text-slate-400 hover:text-white transition-colors">Fechar</button>
                            <button
                                onClick={saveScanned}
                                disabled={selectedIps.length === 0}
                                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors shadow-lg shadow-blue-900/40"
                            >
                                <Save size={18} />
                                Salvar Selecionados ({selectedIps.length})
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Histórico */}
            {showHistoryModal && selectedEqHistory && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-5xl shadow-2xl flex flex-col h-[80vh] animate-in zoom-in-95 duration-200">
                        <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-950 rounded-t-xl">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Activity className="text-amber-500" />
                                    Histórico de Latência: {selectedEqHistory.name}
                                </h3>
                                <p className="text-sm text-slate-400 font-mono mt-1 opacity-80">{selectedEqHistory.ip}</p>
                            </div>
                            <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800">
                                {['1h', '6h', '24h', '7d'].map(period => (
                                    <button
                                        key={period}
                                        onClick={() => loadHistory(selectedEqHistory.id, period)}
                                        className={clsx(
                                            "px-4 py-1.5 rounded-md text-sm transition-all font-medium",
                                            historyPeriod === period ? "bg-slate-800 text-white shadow-sm" : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                                        )}
                                    >
                                        {period.toUpperCase()}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="flex-1 p-6 min-h-0 bg-slate-900/50">
                            {historyData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={historyData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                                        <defs>
                                            <linearGradient id="splitColor" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4} />
                                                <stop offset="100%" stopColor="#10b981" stopOpacity={0.1} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <XAxis dataKey="timeStr" stroke="#475569" tick={{ fontSize: 12 }} minTickGap={50} />
                                        <YAxis stroke="#475569" tick={{ fontSize: 12 }} label={{ value: 'ms', angle: -90, position: 'insideLeft', fill: '#475569' }} />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                            itemStyle={{ color: '#cbd5e1' }}
                                        />
                                        <ReferenceLine y={historyConfig.critical} stroke="#fb7185" strokeDasharray="3 3" label={{ value: 'CRÍTICO', fill: '#fb7185', fontSize: 10, position: 'right' }} />
                                        <ReferenceLine y={historyConfig.good} stroke="#4ade80" strokeDasharray="3 3" label={{ value: 'BOM', fill: '#4ade80', fontSize: 10, position: 'right' }} />
                                        <Area type="monotone" dataKey="latency" stroke="#3b82f6" fill="url(#splitColor)" strokeWidth={2} activeDot={{ r: 6, fill: '#60a5fa' }} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-3">
                                    <Activity size={48} className="opacity-20" />
                                    <p>Sem dados de histórico para este período.</p>
                                </div>
                            )}
                        </div>

                        <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-950 rounded-b-xl">
                            <button onClick={() => setShowHistoryModal(false)} className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors border border-slate-700">Fechar</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Informações Wireless */}
            {showWirelessModal && selectedWirelessEq && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-md shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="p-6 border-b border-slate-800 bg-slate-950 rounded-t-xl">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <Wifi className="text-sky-400" />
                                Informações Wireless
                            </h3>
                            <p className="text-sm text-slate-400 mt-1 font-medium">{selectedWirelessEq.name}</p>
                            <p className="text-xs text-slate-500 font-mono flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                {selectedWirelessEq.ip}
                            </p>
                        </div>

                        <div className="p-6 space-y-4">
                            {selectedWirelessEq.equipment_type === 'transmitter' && (
                                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-5 flex items-center justify-between group hover:bg-emerald-500/20 transition-colors">
                                    <div>
                                        <p className="text-xs text-emerald-400/80 uppercase font-bold tracking-wider mb-1">Clientes Conectados</p>
                                        <p className="text-4xl font-bold text-emerald-400">{selectedWirelessEq.connected_clients || 0}</p>
                                    </div>
                                    <Server size={32} className="text-emerald-500/50 group-hover:text-emerald-400 transition-colors" />
                                </div>
                            )}

                            {selectedWirelessEq.equipment_type === 'station' && (
                                <>
                                    {selectedWirelessEq.signal_dbm !== undefined && (
                                        <div className={clsx(
                                            "border rounded-lg p-4 transition-all hover:scale-[1.02]",
                                            selectedWirelessEq.signal_dbm >= -60 ? "bg-emerald-500/10 border-emerald-500/30" :
                                                selectedWirelessEq.signal_dbm >= -70 ? "bg-yellow-500/10 border-yellow-500/30" :
                                                    "bg-rose-500/10 border-rose-500/30"
                                        )}>
                                            <div className="flex items-center gap-4">
                                                <div className={clsx("p-3 rounded-full",
                                                    selectedWirelessEq.signal_dbm >= -60 ? "bg-emerald-500/20" :
                                                        selectedWirelessEq.signal_dbm >= -70 ? "bg-yellow-500/20" : "bg-rose-500/20"
                                                )}>
                                                    <Wifi size={24} className={clsx(
                                                        selectedWirelessEq.signal_dbm >= -60 ? "text-emerald-400" :
                                                            selectedWirelessEq.signal_dbm >= -70 ? "text-yellow-400" :
                                                                "text-rose-400"
                                                    )} />
                                                </div>
                                                <div>
                                                    <p className="text-xs uppercase font-bold opacity-70 mb-0.5">Sinal (dBm)</p>
                                                    <p className={clsx("text-2xl font-bold font-mono tracking-tight",
                                                        selectedWirelessEq.signal_dbm >= -60 ? "text-emerald-400" :
                                                            selectedWirelessEq.signal_dbm >= -70 ? "text-yellow-400" : "text-rose-400"
                                                    )}>
                                                        {selectedWirelessEq.signal_dbm}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {selectedWirelessEq.ccq !== undefined && (
                                        <div className={clsx(
                                            "border rounded-lg p-4 transition-all hover:scale-[1.02]",
                                            (selectedWirelessEq.ccq || 0) >= 80 ? "bg-blue-500/10 border-blue-500/30" :
                                                (selectedWirelessEq.ccq || 0) >= 60 ? "bg-yellow-500/10 border-yellow-500/30" :
                                                    "bg-rose-500/10 border-rose-500/30"
                                        )}>
                                            <div className="flex items-center gap-4">
                                                <div className={clsx("p-3 rounded-full",
                                                    (selectedWirelessEq.ccq || 0) >= 80 ? "bg-blue-500/20" :
                                                        (selectedWirelessEq.ccq || 0) >= 60 ? "bg-yellow-500/20" : "bg-rose-500/20"
                                                )}>
                                                    <Activity size={24} className={clsx(
                                                        (selectedWirelessEq.ccq || 0) >= 80 ? "text-blue-400" :
                                                            (selectedWirelessEq.ccq || 0) >= 60 ? "text-yellow-400" :
                                                                "text-rose-400"
                                                    )} />
                                                </div>
                                                <div>
                                                    <p className="text-xs uppercase font-bold opacity-70 mb-0.5">CCQ (Qualidade)</p>
                                                    <p className={clsx("text-2xl font-bold font-mono tracking-tight",
                                                        (selectedWirelessEq.ccq || 0) >= 80 ? "text-blue-400" :
                                                            (selectedWirelessEq.ccq || 0) >= 60 ? "text-yellow-400" : "text-rose-400"
                                                    )}>
                                                        {selectedWirelessEq.ccq}%
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-900 rounded-b-xl">
                            <button onClick={() => setShowWirelessModal(false)} className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors border border-slate-700">
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
