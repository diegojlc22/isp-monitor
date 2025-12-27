import React, { useEffect, useState, useCallback, useRef, useMemo, memo } from 'react';
import { getEquipments, createEquipment, updateEquipment, deleteEquipment, getTowers, getLatencyHistory, rebootEquipment, exportEquipmentsCSV, importEquipmentsCSV } from '../services/api'; // removed unused getLatencyConfig
import { Plus, Trash2, Search, Server, MonitorPlay, CheckSquare, Square, Edit2, Activity, Power, Wifi, Info, Download, Upload } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import clsx from 'clsx';

// @ts-ignore
import * as ReactWindow from 'react-window';
// @ts-ignore
import { AutoSizer } from 'react-virtualized-auto-sizer';
import { useDebounce } from 'use-debounce';

// Fix para compatibilidade de build Vite/Rollup com CJS e TS
const List = (ReactWindow as any).FixedSizeList || (ReactWindow as any).default?.FixedSizeList;
const areEqual = (ReactWindow as any).areEqual || (ReactWindow as any).default?.areEqual;

// Fallback se areEqual ainda falhar (Implementação manual simples)
const safeAreEqual = areEqual || ((prev: any, next: any) => {
    return prev.index === next.index && prev.style === next.style && prev.data === next.data;
});

// --- Interfaces ---
interface Tower { id: number; name: string; }
interface Equipment {
    id: number; name: string; ip: string; tower_id: number | null; parent_id: number | null;
    is_online: boolean; brand: string; equipment_type: string; signal_dbm?: number;
    ccq?: number; connected_clients?: number; ssh_user?: string; ssh_port?: number;
    snmp_community?: string; snmp_version?: number; snmp_port?: number; snmp_interface_index?: number;
    is_mikrotik?: boolean; mikrotik_interface?: string; api_port?: number;
}
interface FormData {
    name: string; ip: string; tower_id: string; parent_id: string; ssh_user: string; ssh_password: string;
    ssh_port: number; snmp_community: string; snmp_version: number; snmp_port: number; snmp_interface_index: number;
    brand: string; equipment_type: string; is_mikrotik: boolean; mikrotik_interface: string; api_port: number;
}

const INITIAL_FORM_STATE: FormData = {
    name: '', ip: '', tower_id: '', parent_id: '', ssh_user: 'admin', ssh_password: '', ssh_port: 22,
    snmp_community: 'public', snmp_version: 1, snmp_port: 161, snmp_interface_index: 1, brand: 'generic',
    equipment_type: 'station', is_mikrotik: false, mikrotik_interface: '', api_port: 8728
};

// --- Custom Hooks ---
function usePoll(callback: () => void, intervalMs: number) {
    useEffect(() => {
        callback();
        const interval = setInterval(() => {
            if (!document.hidden) {
                callback();
            }
        }, intervalMs);
        return () => clearInterval(interval);
    }, [callback, intervalMs]);
}

// --- Componentes Otimizados ---

const EquipmentRow = memo(({ index, style, data }: any) => {
    const { equipments, towers, onAction, onReboot, onDelete, onHistory, onEdit } = data;
    const eq = equipments[index];
    const tower = towers.find((t: Tower) => t.id === eq.tower_id);

    return (
        <div style={style} className={clsx("flex items-center text-sm border-b border-slate-800 transition-colors hover:bg-slate-800/50 group", index % 2 === 0 ? "bg-transparent" : "bg-slate-900/30")}>
            {/* Status */}
            <div className="w-16 flex justify-center shrink-0">
                <div
                    className={clsx("w-3 h-3 rounded-full transition-all duration-500", eq.is_online ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] scale-110" : "bg-rose-500 opacity-80")}
                    title={eq.is_online ? "Online" : "Offline"}
                />
            </div>

            {/* Nome & Torre */}
            <div className="flex-1 px-4 min-w-0">
                <div className="font-medium text-white flex items-center gap-2 truncate">
                    {eq.brand === 'mikrotik' ? <Activity size={16} className="text-blue-400 shrink-0" /> :
                        eq.brand === 'ubiquiti' ? <Wifi size={16} className="text-sky-400 shrink-0" /> :
                            eq.brand === 'intelbras' ? <Wifi size={16} className="text-green-400 shrink-0" /> :
                                <Server size={16} className="text-slate-500 shrink-0" />}
                    <span className="truncate" title={eq.name}>{eq.name}</span>
                </div>
                {tower && <div className="text-xs text-slate-500 ml-6 truncate">📍 {tower.name}</div>}
            </div>

            {/* IP */}
            <div className="w-32 px-4 font-mono text-slate-300 text-xs hidden sm:block shrink-0">
                {eq.ip}
            </div>

            {/* Ações */}
            <div className="w-48 px-4 flex justify-end gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                {(eq.signal_dbm || eq.connected_clients !== undefined) && (
                    <button onClick={() => onAction(eq)} className="text-slate-400 hover:text-sky-400 p-1.5 rounded hover:bg-slate-700" title="Info">
                        <Info size={16} />
                    </button>
                )}
                <button onClick={() => onReboot(eq)} className="text-slate-400 hover:text-orange-500 p-1.5 rounded hover:bg-slate-700" title="Reiniciar">
                    <Power size={16} />
                </button>
                <button onClick={() => onHistory(eq)} className="text-slate-400 hover:text-amber-400 p-1.5 rounded hover:bg-slate-700" title="Histórico">
                    <Activity size={16} />
                </button>
                <button onClick={() => onEdit(eq)} className="text-slate-400 hover:text-blue-400 p-1.5 rounded hover:bg-slate-700" title="Editar">
                    <Edit2 size={16} />
                </button>
                <button onClick={() => onDelete(eq.id)} className="text-slate-400 hover:text-rose-500 p-1.5 rounded hover:bg-slate-700" title="Remover">
                    <Trash2 size={16} />
                </button>
            </div>
        </div>
    );
}, safeAreEqual);


export function Equipments() {
    // --- State ---
    const [equipments, setEquipments] = useState<Equipment[]>([]);
    const [towers, setTowers] = useState<Tower[]>([]);
    const [showModal, setShowModal] = useState(false);
    const [editingEquipment, setEditingEquipment] = useState<Equipment | null>(null);
    const [formData, setFormData] = useState<FormData>(INITIAL_FORM_STATE);

    // Filters & Search
    const [filterText, setFilterText] = useState('');
    const [debouncedFilterText] = useDebounce(filterText, 300);
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

    // History & Modals
    const [historyData, setHistoryData] = useState<any[]>([]);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [selectedEqHistory, setSelectedEqHistory] = useState<Equipment | null>(null);
    const [historyPeriod, setHistoryPeriod] = useState('24h');
    const [showWirelessModal, setShowWirelessModal] = useState(false);
    const [selectedWirelessEq, setSelectedWirelessEq] = useState<Equipment | null>(null);
    const [templates, setTemplates] = useState<Record<string, Partial<FormData>>>({});
    const [showTemplateModal, setShowTemplateModal] = useState(false);
    const [templateName, setTemplateName] = useState('');

    // --- Actions ---
    const load = useCallback(async () => {
        try {
            const [eqs, tws] = await Promise.all([getEquipments(), getTowers()]);
            setEquipments(eqs);
            setTowers(tws);
        } catch (e) { console.error('Error loading data:', e); }
    }, []);

    usePoll(load, 15000);

    // Filter Logic - Memoized
    const filteredEquipments = useMemo(() => {
        let result = equipments;
        if (debouncedFilterText) {
            const lower = debouncedFilterText.toLowerCase();
            result = result.filter(eq => eq.name.toLowerCase().includes(lower) || eq.ip.includes(lower));
        }
        if (filterStatus !== 'all') {
            result = result.filter(eq => filterStatus === 'online' ? eq.is_online : !eq.is_online);
        }
        if (filterTower !== 'all') {
            result = result.filter(eq => eq.tower_id === parseInt(filterTower));
        }
        if (filterType !== 'all') {
            result = result.filter(eq => eq.equipment_type === filterType);
        }
        return result;
    }, [equipments, debouncedFilterText, filterStatus, filterTower, filterType]);

    useEffect(() => {
        const saved = localStorage.getItem('equipment_templates');
        if (saved) { try { setTemplates(JSON.parse(saved)); } catch (e) { } }
    }, []);

    const handleReboot = useCallback(async (eq: Equipment) => {
        if (!confirm(`Reiniciar ${eq.name}?`)) return;
        try { await rebootEquipment(eq.id); alert("Comando enviado!"); } catch (e: any) { alert("Erro: " + (e.response?.data?.detail || e.message)); }
    }, []);

    const handleDelete = useCallback(async (id: number) => {
        if (confirm('Tem certeza?')) { await deleteEquipment(id); load(); }
    }, [load]);

    const handleEdit = useCallback((eq: Equipment) => {
        setEditingEquipment(eq);
        setFormData({
            name: eq.name, ip: eq.ip, tower_id: eq.tower_id ? String(eq.tower_id) : '',
            parent_id: eq.parent_id ? String(eq.parent_id) : '', ssh_user: eq.ssh_user || 'admin',
            ssh_password: '', ssh_port: eq.ssh_port || 22, snmp_community: eq.snmp_community || 'public',
            snmp_version: eq.snmp_version || 1, snmp_port: eq.snmp_port || 161, snmp_interface_index: eq.snmp_interface_index || 1,
            brand: eq.brand || 'generic', equipment_type: eq.equipment_type || 'station', is_mikrotik: eq.is_mikrotik || false,
            mikrotik_interface: eq.mikrotik_interface || '', api_port: eq.api_port || 8728
        });
        setShowModal(true);
    }, []);

    const handleShowHistory = useCallback(async (eq: Equipment) => {
        setSelectedEqHistory(eq);
        try {
            await loadHistory(eq.id, '24h');
            setShowHistoryModal(true);
        } catch (e) { alert('Erro ao carregar histórico.'); }
    }, []);

    const loadHistory = async (id: number, period: string) => {
        setHistoryPeriod(period);
        try {
            const data = await getLatencyHistory(id, period);
            setHistoryData(data.map((d: any) => ({
                ...d, timeStr: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            })));
        } catch (e) { console.error(e); }
    };

    const handleWirelessInfo = useCallback((eq: Equipment) => {
        setSelectedWirelessEq(eq);
        setShowWirelessModal(true);
    }, []);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        try {
            const payload: any = {
                ...formData,
                tower_id: formData.tower_id ? parseInt(formData.tower_id) : null,
                parent_id: formData.parent_id ? parseInt(formData.parent_id) : null,
                ssh_port: Number(formData.ssh_port), snmp_version: Number(formData.snmp_version),
                snmp_port: Number(formData.snmp_port), snmp_interface_index: Number(formData.snmp_interface_index),
                api_port: Number(formData.api_port)
            };
            if (!formData.ssh_password) delete payload.ssh_password;
            editingEquipment ? await updateEquipment(editingEquipment.id, payload) : await createEquipment(payload);
            setShowModal(false); setEditingEquipment(null); setFormData(INITIAL_FORM_STATE); load();
        } catch (error) { alert('Erro ao salvar.'); }
    }

    function saveTemplate() {
        if (!templateName.trim()) return;
        const newHelper = {
            brand: formData.brand, equipment_type: formData.equipment_type, ssh_user: formData.ssh_user,
            ssh_port: formData.ssh_port, snmp_community: formData.snmp_community, snmp_version: formData.snmp_version,
            snmp_port: formData.snmp_port, snmp_interface_index: formData.snmp_interface_index,
            is_mikrotik: formData.is_mikrotik, mikrotik_interface: formData.mikrotik_interface, api_port: formData.api_port
        };
        const newTemplates = { ...templates, [templateName]: newHelper };
        setTemplates(newTemplates);
        localStorage.setItem('equipment_templates', JSON.stringify(newTemplates));
        setShowTemplateModal(false); setTemplateName('');
    }

    async function handleExportCSV() {
        try {
            const blob = await exportEquipmentsCSV();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url;
            a.download = `eq_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
        } catch (e) { alert('Erro ao exportar'); }
    }

    async function handleImportCSV(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0]; if (!file) return;
        try { await importEquipmentsCSV(file); alert('Importado!'); load(); } catch (err: any) { alert("Erro importando: " + err.message); }
        e.target.value = '';
    }

    async function handleScanStart() {
        if (isScanning) { eventSourceRef.current?.close(); setIsScanning(false); return; }
        setIsScanning(true); setScannedIps([]); setProgress(0);
        try {
            const es = new EventSource(`/api/equipments/scan/stream/?ip_range=${encodeURIComponent(scanRange)}`);
            eventSourceRef.current = es;
            es.onmessage = ev => {
                const d = JSON.parse(ev.data); setProgress(d.progress || 0);
                if (d.is_online) setScannedIps(p => p.includes(d.ip) ? p : [...p, d.ip]);
            };
            es.addEventListener("done", () => { es.close(); setIsScanning(false); });
            es.onerror = () => { es.close(); setIsScanning(false); };
        } catch (e) { setIsScanning(false); }
    }
    async function saveScanned() {
        if (!selectedIps.length) return;
        for (const ip of selectedIps) {
            try { await createEquipment({ name: ipNames[ip] || `Dispositivo ${ip}`, ip, ssh_port: 22, ssh_user: 'admin', tower_id: null }); } catch (e) { }
        }
        alert('Salvo!'); setShowScanner(false); load();
    }

    return (
        <div className="h-[calc(100vh-2rem)] flex flex-col">
            <div className="flex justify-between items-center mb-6 shrink-0">
                <h2 className="text-2xl font-bold text-white">Equipamentos <span className="text-sm font-normal text-slate-500 ml-2">({filteredEquipments.length})</span></h2>
                <div className="flex gap-2">
                    <button onClick={() => setShowScanner(true)} className="flex gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg">
                        <MonitorPlay size={18} /> Scan
                    </button>
                    <button onClick={handleExportCSV} className="flex gap-2 bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg">
                        <Download size={18} /> CSV
                    </button>
                    <label className="flex gap-2 bg-orange-600 hover:bg-orange-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg cursor-pointer">
                        <Upload size={18} /> Importar
                        <input type="file" accept=".csv" onChange={handleImportCSV} className="hidden" />
                    </label>
                    <button onClick={() => { setEditingEquipment(null); setFormData(INITIAL_FORM_STATE); setShowModal(true); }} className="flex gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg">
                        <Plus size={18} /> Novo
                    </button>
                </div>
            </div>

            <div className="bg-slate-900 rounded-t-xl border border-slate-800 p-4 shrink-0 flex flex-wrap gap-3">
                <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input type="text" placeholder="Buscar..." className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500" value={filterText} onChange={e => setFilterText(e.target.value)} />
                </div>
                <select value={filterStatus} onChange={e => setFilterStatus(e.target.value as any)} className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none">
                    <option value="all">Status: Todos</option>
                    <option value="online">🟢 Online</option>
                    <option value="offline">🔴 Offline</option>
                </select>
                <select value={filterTower} onChange={e => setFilterTower(e.target.value)} className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none max-w-[200px]">
                    <option value="all">Torres: Todas</option>
                    {towers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
                <select value={filterType} onChange={e => setFilterType(e.target.value)} className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none">
                    <option value="all">Tipos: Todos</option>
                    <option value="station">Station</option>
                    <option value="transmitter">Transmitter</option>
                </select>
            </div>

            <div className="flex-1 bg-slate-900 border-x border-b border-slate-800 rounded-b-xl overflow-hidden flex flex-col shadow-xl">
                <div className="flex bg-slate-950 text-slate-400 uppercase text-xs font-bold py-3 border-b border-slate-800 shrink-0">
                    <div className="w-16 text-center">Status</div>
                    <div className="flex-1 px-4">Nome</div>
                    <div className="w-32 px-4 hidden sm:block">IP</div>
                    <div className="w-48 px-4 text-right">Ações</div>
                </div>

                <div className="flex-1">
                    {filteredEquipments.length === 0 ? (
                        <div className="flex justify-center items-center h-full text-slate-500">Nenhum equipamento encontrado.</div>
                    ) : (
                        // @ts-ignore
                        <AutoSizer>
                            {({ height, width }: any) => (
                                <List
                                    height={height}
                                    width={width}
                                    itemCount={filteredEquipments.length}
                                    itemSize={64}
                                    itemData={{ equipments: filteredEquipments, towers, onAction: handleWirelessInfo, onReboot: handleReboot, onDelete: handleDelete, onHistory: handleShowHistory, onEdit: handleEdit }}
                                >
                                    {EquipmentRow}
                                </List>
                            )}
                        </AutoSizer>
                    )}
                </div>
            </div>

            {showModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
                        <h3 className="text-xl font-bold text-white mb-4">{editingEquipment ? 'Editar' : 'Novo'} Equipamento</h3>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <input className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white" placeholder="Nome" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required />
                            <input className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white" placeholder="IP" value={formData.ip} onChange={e => setFormData({ ...formData, ip: e.target.value })} required />
                            <div className="grid grid-cols-2 gap-2">
                                <select className="bg-slate-950 border border-slate-700 rounded p-2 text-white" value={formData.tower_id} onChange={e => setFormData({ ...formData, tower_id: e.target.value })}>
                                    <option value="">Sem Torre</option>
                                    {towers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                                </select>
                                <select className="bg-slate-950 border border-slate-700 rounded p-2 text-white" value={formData.brand} onChange={e => setFormData({ ...formData, brand: e.target.value })}>
                                    <option value="generic">Genérico</option>
                                    <option value="mikrotik">Mikrotik</option>
                                    <option value="ubiquiti">Ubiquiti</option>
                                </select>
                            </div>
                            <div className="flex justify-end gap-2 mt-4">
                                <button type="button" onClick={() => setShowModal(false)} className="text-slate-400 px-4 py-2">Cancelar</button>
                                <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Salvar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
            {showScanner && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl p-6 h-[80vh] flex flex-col">
                        <h3 className="text-xl font-bold text-white mb-4">Scanner</h3>
                        <div className="flex gap-2 mb-4">
                            <input className="flex-1 bg-slate-950 border border-slate-700 rounded p-2 text-white" placeholder="IP Range (ex: 192.168.1.0/24)" value={scanRange} onChange={e => setScanRange(e.target.value)} />
                            <button onClick={handleScanStart} className="bg-emerald-600 text-white px-4 rounded">{isScanning ? 'Parar' : 'Iniciar'}</button>
                            {progress > 0 && <span className="text-white text-xs self-center ml-2">{progress}%</span>}
                        </div>
                        <div className="flex-1 bg-slate-950 rounded border border-slate-800 p-2 overflow-y-auto">
                            {scannedIps.map(ip => (
                                <div key={ip} className="flex items-center gap-2 p-2 hover:bg-slate-900 cursor-pointer" onClick={() => setSelectedIps(p => p.includes(ip) ? p.filter(i => i !== ip) : [...p, ip])}>
                                    {selectedIps.includes(ip) ? <CheckSquare className="text-blue-500" size={16} /> : <Square className="text-slate-500" size={16} />}
                                    <span className="text-slate-300 font-mono">{ip}</span>
                                    <input className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" placeholder="Nome" value={ipNames[ip] || ''} onClick={e => e.stopPropagation()} onChange={e => setIpNames({ ...ipNames, [ip]: e.target.value })} />
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 flex justify-end gap-2">
                            <button onClick={() => setShowScanner(false)} className="text-slate-400 px-4">Fechar</button>
                            <button onClick={saveScanned} disabled={!selectedIps.length} className="bg-blue-600 text-white px-4 py-2 rounded">Salvar Selecionados</button>
                        </div>
                    </div>
                </div>
            )}
            {showHistoryModal && selectedEqHistory && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-4xl p-6 h-[70vh] flex flex-col">
                        <h3 className="text-white font-bold mb-4">{selectedEqHistory.name} - Histórico ({historyPeriod})</h3>
                        <div className="flex-1 min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={historyData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                    <XAxis dataKey="timeStr" stroke="#666" />
                                    <YAxis stroke="#666" />
                                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                                    <Area type="monotone" dataKey="latency" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                        <button onClick={() => setShowHistoryModal(false)} className="mt-4 bg-slate-800 text-white px-4 py-2 rounded">Fechar</button>
                    </div>
                </div>
            )}
            {showWirelessModal && selectedWirelessEq && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-96">
                        <h3 className="text-white font-bold mb-4">Status Wireless</h3>
                        <div className="space-y-4">
                            <div className="bg-slate-800 p-4 rounded text-center">
                                <div className="text-slate-400 text-xs uppercase">Sinal</div>
                                <div className={clsx("text-3xl font-bold", (selectedWirelessEq.signal_dbm || -100) > -65 ? "text-emerald-400" : "text-yellow-400")}>{selectedWirelessEq.signal_dbm || 'N/A'} dBm</div>
                            </div>
                            <div className="bg-slate-800 p-4 rounded text-center">
                                <div className="text-slate-400 text-xs uppercase">CCQ</div>
                                <div className="text-3xl font-bold text-blue-400">{selectedWirelessEq.ccq || 'N/A'} %</div>
                            </div>
                        </div>
                        <button onClick={() => setShowWirelessModal(false)} className="mt-6 w-full bg-slate-800 hover:bg-slate-700 text-white py-2 rounded">Fechar</button>
                    </div>
                </div>
            )}
            {showTemplateModal && (<div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"><div className="bg-slate-900 border border-slate-700 rounded p-6"><input value={templateName} onChange={e => setTemplateName(e.target.value)} placeholder="Nome do Template" className="bg-slate-950 border border-slate-700 rounded p-2 text-white block mb-4 w-full" /><div className="flex gap-2 justify-end"><button onClick={() => setShowTemplateModal(false)} className="text-slate-400">Cancelar</button><button onClick={saveTemplate} className="bg-purple-600 text-white px-4 py-2 rounded">Salvar</button></div></div></div>)}
        </div>
    );
}

export default Equipments;
