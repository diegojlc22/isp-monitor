import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { getEquipments, createEquipment, updateEquipment, deleteEquipment, getTowers, getLatencyHistory, rebootEquipment, exportEquipmentsCSV, importEquipmentsCSV, getNetworkDefaults, detectEquipmentBrand } from '../services/api';


import { Plus, Trash2, Search, Server, MonitorPlay, CheckSquare, Square, Edit2, Activity, Power, Wifi, Download, Upload, Users } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import clsx from 'clsx';

// @ts-ignore
import { useDebounce } from 'use-debounce';

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

const EquipmentRow = ({ index, data }: any) => {
    const { equipments, towers, onAction, onReboot, onDelete, onHistory, onEdit, selectedIds, toggleSelection } = data;
    const eq = equipments[index];
    const tower = towers.find((t: Tower) => t.id === eq.tower_id);
    const isSelected = selectedIds?.includes(eq.id);

    return (
        <div className={clsx("w-full h-16 flex items-center text-sm border-b border-slate-800 transition-colors hover:bg-slate-800/50 group", index % 2 === 0 ? "bg-transparent" : "bg-slate-900/30", isSelected && "bg-blue-900/20")}>
            {/* Selection Checkbox */}
            <div className="w-10 pl-4 flex items-center justify-center shrink-0">
                <div onClick={() => toggleSelection && toggleSelection(eq.id)} className="cursor-pointer">
                    {isSelected ? <CheckSquare size={18} className="text-blue-500" /> : <Square size={18} className="text-slate-600 hover:text-slate-400" />}
                </div>
            </div>

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
                {/* Status Button based on Type */}
                {eq.equipment_type === 'station' && (
                    <button onClick={() => onAction(eq)} className="text-slate-400 hover:text-yellow-400 p-1.5 rounded hover:bg-slate-700" title="Ver Sinal">
                        <Wifi size={16} />
                    </button>
                )}
                {eq.equipment_type === 'transmitter' && (
                    <button onClick={() => onAction(eq)} className="text-slate-400 hover:text-purple-400 p-1.5 rounded hover:bg-slate-700" title="Ver Clientes">
                        <Users size={16} />
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
};

// --- Wireless Monitor Modal Helper Component ---
const WirelessMonitorModal = ({ equipment, onClose }: { equipment: any, onClose: () => void }) => {
    const [data, setData] = useState<any[]>([]);
    const [currentEq, setCurrentEq] = useState(equipment);

    // Derive type from current (live) data source
    const isTransmitter = currentEq.equipment_type === 'transmitter';
    const isStation = currentEq.equipment_type === 'station';

    useEffect(() => {
        let isMounted = true;

        const fetch = async () => {
            try {
                const updatedList = await getEquipments();
                const latest = updatedList.find((e: any) => e.id === equipment.id);

                if (latest && isMounted) {
                    setCurrentEq(latest);

                    const now = new Date();
                    const newPoint = {
                        time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                        signal: latest.signal_dbm,
                        clients: latest.connected_clients || 0
                    };

                    // Only add if we have valid data relevant to the type
                    if ((latest.equipment_type === 'station' && latest.signal_dbm != null) ||
                        (latest.equipment_type === 'transmitter')) {
                        setData(prev => [...prev, newPoint].slice(-60)); // Keep 60 points
                    }
                }
            } catch (err) {
                console.error("Error polling wireless status:", err);
            }
        };

        fetch(); // Initial
        const interval = setInterval(fetch, 2000); // Poll every 2s
        return () => { isMounted = false; clearInterval(interval); };
    }, [equipment.id]); // Removed equipment.equipment_type dependency to rely on fetched data

    const dataKey = isTransmitter ? 'clients' : 'signal';
    const color = isTransmitter ? '#c084fc' : '#facc15';

    // X Icon helper
    const XIcon = ({ size }: { size: number }) => (
        <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
    );

    return (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-lg shadow-2xl">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h3 className="text-white font-bold text-lg">
                            {currentEq.name} <span className="text-slate-500 font-normal text-sm">({isTransmitter ? 'Transmissor' : isStation ? 'Station' : 'Geral'})</span>
                        </h3>
                        <p className="text-slate-400 text-xs uppercase tracking-wide">
                            {isTransmitter ? 'Monitoramento de Clientes' : isStation ? 'Monitoramento de Sinal' : 'Status'}
                        </p>
                    </div>

                    <button onClick={onClose} className="text-slate-400 hover:text-white">
                        <div className="bg-slate-800 hover:bg-slate-700 p-1 rounded-full"><XIcon size={16} /></div>
                    </button>
                </div>

                {/* Big Stats */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                    {isTransmitter ? (
                        <div className="col-span-2 bg-slate-800/50 p-4 rounded border border-slate-700 text-center">
                            <div className="text-slate-400 text-[10px] uppercase font-bold tracking-wider mb-1">Clientes Conectados</div>
                            <div className="text-4xl font-bold text-purple-400">{currentEq.connected_clients || 0}</div>
                        </div>
                    ) : isStation ? (
                        <>
                            <div className="bg-slate-800/50 p-4 rounded border border-slate-700 text-center">
                                <div className="text-slate-400 text-[10px] uppercase font-bold tracking-wider mb-1">Sinal</div>
                                <div className={clsx("text-3xl font-bold", (currentEq.signal_dbm || -100) > -65 ? "text-emerald-400" : "text-yellow-400")}>
                                    {currentEq.signal_dbm ? `${currentEq.signal_dbm} dBm` : 'N/A'}
                                </div>
                            </div>
                            <div className="bg-slate-800/50 p-4 rounded border border-slate-700 text-center">
                                <div className="text-slate-400 text-[10px] uppercase font-bold tracking-wider mb-1">CCQ</div>
                                <div className="text-3xl font-bold text-blue-400">{currentEq.ccq ? `${currentEq.ccq}% ` : 'N/A'}</div>
                            </div>
                        </>
                    ) : (
                        <div className="col-span-2 bg-slate-800/50 p-6 rounded border border-slate-700 text-center text-slate-500 text-sm">
                            Monitoramento wireless não disponível para este tipo de equipamento.
                        </div>
                    )}
                </div>

                {/* Live Chart - Only show if valid type */}
                {(isTransmitter || isStation) && (
                    <div className="h-48 bg-slate-950/50 rounded border border-slate-800/50 p-2">
                        {data.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
                                    <XAxis dataKey="time" hide />
                                    <YAxis
                                        stroke="#64748b"
                                        fontSize={10}
                                        width={30}
                                        domain={isTransmitter ? ['auto', 'auto'] : [-90, -40]}
                                        hide={false}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc', fontSize: '12px' }}
                                        itemStyle={{ color: color }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey={dataKey}
                                        stroke={color}
                                        fill={color}
                                        fillOpacity={0.1}
                                        strokeWidth={2}
                                        isAnimationActive={false}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-slate-600 text-xs">
                                Aguardando dados...
                            </div>
                        )}
                        <div className="mt-2 text-right">
                            <span className="text-[10px] text-slate-500">Atualizado a cada 2s</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export function Equipments() {
    // --- State ---
    const [equipments, setEquipments] = useState<Equipment[]>([]);
    const [towers, setTowers] = useState<Tower[]>([]);
    const [showModal, setShowModal] = useState(false);
    const [editingEquipment, setEditingEquipment] = useState<Equipment | null>(null);
    const [formData, setFormData] = useState<FormData>(INITIAL_FORM_STATE);
    const [networkDefaults, setNetworkDefaults] = useState<any>({});



    // Scanner State
    const [showScanner, setShowScanner] = useState(false);
    const [isScanning, setIsScanning] = useState(false);
    const [scannedDevices, setScannedDevices] = useState<any[]>([]);
    const [progress, setProgress] = useState(0);
    const eventSourceRef = useRef<EventSource | null>(null);
    const [selectedIps, setSelectedIps] = useState<string[]>([]);
    const [ipNames, setIpNames] = useState<{ [key: string]: string }>({});
    const [scanRange, setScanRange] = useState('');

    // Detection Progress
    const [detectionProgress, setDetectionProgress] = useState(0);

    // Configurações do scanner

    // Batch Selection State
    const [selectedIds, setSelectedIds] = useState<number[]>([]);

    // Sorting State
    const [sortConfig, setSortConfig] = useState<{ key: string, direction: 'asc' | 'desc' } | null>(null);

    // Filters & Search
    const [filterText, setFilterText] = useState('');
    const [debouncedFilterText] = useDebounce(filterText, 300);
    const [filterStatus, setFilterStatus] = useState<'all' | 'online' | 'offline'>('all');
    const [filterTower, setFilterTower] = useState<string>('all');
    const [filterType, setFilterType] = useState<string>('all');

    // Load filter from URL
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const status = params.get('status');
        if (status && ['online', 'offline'].includes(status)) {
            setFilterStatus(status as 'online' | 'offline');
        }
    }, []);

    // Filter & Sort Logic - Memoized
    const filteredEquipments = useMemo(() => {
        let result = [...equipments]; // Create a copy to sort safely

        // 1. Filtering
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

        // 2. Sorting
        if (sortConfig) {
            result.sort((a, b) => {
                let aValue: any = a[sortConfig.key as keyof Equipment];
                let bValue: any = b[sortConfig.key as keyof Equipment];

                // Special handling for IP sorting
                if (sortConfig.key === 'ip') {
                    const ipA = a.ip.split('.').map(Number);
                    const ipB = b.ip.split('.').map(Number);
                    for (let i = 0; i < 4; i++) {
                        if (ipA[i] !== ipB[i]) return sortConfig.direction === 'asc' ? ipA[i] - ipB[i] : ipB[i] - ipA[i];
                    }
                    return 0;
                }

                // Generic sorting
                if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
                if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        } else {
            // Default sort: Offline first, then Name
            result.sort((a, b) => {
                if (a.is_online === b.is_online) return a.name.localeCompare(b.name);
                return a.is_online ? 1 : -1;
            });
        }

        return result;
    }, [equipments, debouncedFilterText, filterStatus, filterTower, filterType, sortConfig]);

    const handleSort = (key: string) => {
        setSortConfig(current => {
            if (current && current.key === key) {
                return current.direction === 'asc' ? { key, direction: 'desc' } : null;
            }
            return { key, direction: 'asc' };
        });
    };

    const getSortIcon = (key: string) => {
        if (!sortConfig || sortConfig.key !== key) return <span className="opacity-20 ml-1">⇅</span>;
        return <span className="ml-1 text-blue-400">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>;
    };

    // Selection Logic
    const toggleSelection = useCallback((id: number) => {
        setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
    }, []);

    const toggleSelectAll = () => {
        if (selectedIds.length === filteredEquipments.length && filteredEquipments.length > 0) {
            setSelectedIds([]);
        } else {
            setSelectedIds(filteredEquipments.map(eq => eq.id));
        }
    };

    const handleBatchDelete = async () => {
        if (!confirm(`Tem certeza que deseja EXCLUIR ${selectedIds.length} equipamentos ? `)) return;
        try {
            for (const id of selectedIds) { await deleteEquipment(id); }
            alert('Equipamentos excluídos!'); setSelectedIds([]); load();
        } catch (e) { alert('Erro ao excluir alguns itens.'); }
    };

    const handleBatchReboot = async () => {
        if (!confirm(`Reiniciar ${selectedIds.length} equipamentos ? `)) return;
        try {
            for (const id of selectedIds) { rebootEquipment(id).catch(console.error); }
            alert('Comandos de reboot enviados!'); setSelectedIds([]);
        } catch (e) { alert('Erro ao enviar comandos.'); }
    };



    useEffect(() => {
        getNetworkDefaults().then(setNetworkDefaults).catch(() => { });
    }, []);

    // History & Modals
    const [historyData, setHistoryData] = useState<any[]>([]);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [selectedEqHistory, setSelectedEqHistory] = useState<Equipment | null>(null);
    const [historyPeriod, setHistoryPeriod] = useState('24h');
    const [showWirelessModal, setShowWirelessModal] = useState(false);
    const [selectedWirelessEq, setSelectedWirelessEq] = useState<Equipment | null>(null);
    const [templates, setTemplates] = useState<Record<string, Partial<FormData>>>({});
    const [showTemplateModal, setShowTemplateModal] = useState(false);
    const [isDetecting, setIsDetecting] = useState(false);

    // Auto-detect equipment brand and type
    const handleAutoDetect = async () => {
        if (!formData.ip) {
            alert('Por favor, insira um IP primeiro');
            return;
        }

        setIsDetecting(true);
        try {
            const result = await detectEquipmentBrand(
                formData.ip,
                formData.snmp_community || 'public',
                formData.snmp_port || 161
            );

            setFormData({
                ...formData,
                brand: result.brand,
                equipment_type: result.equipment_type,
                name: result.name || formData.name  // Use detected name if available, otherwise keep current
            });

            const detectedName = result.name ? `\n✅ Nome: ${result.name}` : '';
            alert(`Detectado: \n✅ Marca: ${result.brand.toUpperCase()} \n✅ Tipo: ${result.equipment_type === 'station' ? 'Station (Cliente)' : result.equipment_type === 'transmitter' ? 'Transmitter (AP)' : 'Outro'} ${detectedName}`);
        } catch (error: any) {
            alert(`Erro na detecção: ${error.response?.data?.detail || error.message} `);
        } finally {
            setIsDetecting(false);
        }
    };

    // Batch auto-detect for selected equipments
    const handleBatchAutoDetect = async () => {
        if (selectedIds.length === 0) {
            alert('Selecione pelo menos um equipamento');
            return;
        }

        if (!confirm(`Deseja auto-detectar marca e tipo de ${selectedIds.length} equipamento(s)?`)) {
            return;
        }

        setIsDetecting(true);
        setDetectionProgress(0);
        let successCount = 0;
        let errorCount = 0;

        for (let i = 0; i < selectedIds.length; i++) {
            const id = selectedIds[i];
            const equipment = equipments.find(eq => eq.id === id);
            if (!equipment) continue;

            try {
                const result = await detectEquipmentBrand(
                    equipment.ip,
                    equipment.snmp_community || networkDefaults.snmp_community || 'public',
                    equipment.snmp_port || networkDefaults.snmp_port || 161
                );

                // Update equipment with detected info
                await updateEquipment(id, {
                    ...equipment,
                    brand: result.brand,
                    equipment_type: result.equipment_type,
                    name: result.name || equipment.name,
                    is_mikrotik: result.brand === 'mikrotik'
                });

                successCount++;
            } catch (error) {
                console.error(`Erro ao detectar ${equipment.ip}:`, error);
                errorCount++;
            }

            setDetectionProgress(Math.round(((i + 1) / selectedIds.length) * 100));
        }

        setIsDetecting(false);
        setDetectionProgress(0);
        setSelectedIds([]); // Clear selection
        load(); // Reload data

        alert(`✅ Detecção concluída!\n\nSucesso: ${successCount}\nErros: ${errorCount}`);
    };

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
            const response = await getLatencyHistory(id, period);
            setHistoryData(response.data.map((d: any) => ({
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
        setIsScanning(true); setScannedDevices([]); setProgress(0);
        try {
            const community = networkDefaults.snmp_community || 'public';
            const port = networkDefaults.snmp_port || 161;
            const es = new EventSource(`/api/equipments/scan/stream/?ip_range=${encodeURIComponent(scanRange)}&snmp_community=${encodeURIComponent(community)}&snmp_port=${port}`);
            eventSourceRef.current = es;
            es.onmessage = ev => {
                const d = JSON.parse(ev.data); setProgress(d.progress || 0);
                if (d.is_online) {
                    setScannedDevices(prev => {
                        if (prev.find(p => p.ip === d.ip)) return prev;
                        return [...prev, d]; // Save full object
                    });
                }
            };
            es.addEventListener("done", () => { es.close(); setIsScanning(false); });
            es.onerror = () => { es.close(); setIsScanning(false); };
        } catch (e) { setIsScanning(false); }
    }

    async function saveScanned() {
        if (!selectedIps.length) return;
        let count = 0;
        for (const ip of selectedIps) {
            try {
                const device = scannedDevices.find(d => d.ip === ip);
                await createEquipment({
                    name: ipNames[ip] || `Dispositivo ${ip} `,
                    ip,
                    // Defaults Logic
                    ssh_port: networkDefaults.ssh_port || 22,
                    ssh_user: networkDefaults.ssh_user || 'admin',
                    ssh_password: networkDefaults.ssh_password || '',
                    snmp_community: networkDefaults.snmp_community || 'public',
                    snmp_port: networkDefaults.snmp_port || 161,

                    // Detected Logic
                    brand: device?.brand || 'generic',
                    equipment_type: device?.equipment_type || 'station',
                    is_mikrotik: device?.brand === 'mikrotik',
                    whatsapp_groups: device?.whatsapp_groups || [],

                    tower_id: null
                });
                count++;
            } catch (e) { }
        }
        alert(`Salvo ${count} equipamentos!`); setShowScanner(false); load();
    }

    async function saveAllScanned() {
        if (!scannedDevices.length) return;
        let count = 0;
        for (const device of scannedDevices) {
            try {
                await createEquipment({
                    name: ipNames[device.ip] || `Dispositivo ${device.ip}`,
                    ip: device.ip,
                    // Defaults Logic
                    ssh_port: networkDefaults.ssh_port || 22,
                    ssh_user: networkDefaults.ssh_user || 'admin',
                    ssh_password: networkDefaults.ssh_password || '',
                    snmp_community: networkDefaults.snmp_community || 'public',
                    snmp_port: networkDefaults.snmp_port || 161,

                    // Detected Logic
                    brand: device.brand || 'generic',
                    equipment_type: device.equipment_type || 'station',
                    is_mikrotik: device.brand === 'mikrotik',
                    whatsapp_groups: device.whatsapp_groups || [],

                    tower_id: null
                });
                count++;
            } catch (e) { }
        }
        alert(`Salvo ${count} equipamentos!`); setShowScanner(false); load();
    }

    const handleNewEquipment = async () => {
        setEditingEquipment(null);
        // Defaults are now already in 'networkDefaults' state, but loading freshly just in case
        try {
            const defaults = await getNetworkDefaults(); // Refresh defaults
            setNetworkDefaults(defaults); // Update state too
            setFormData({
                ...INITIAL_FORM_STATE,
                ssh_user: defaults.ssh_user || 'admin',
                ssh_password: defaults.ssh_password || '',
                snmp_community: defaults.snmp_community || 'public'
            });
        } catch (e) {
            setFormData(INITIAL_FORM_STATE);
        }
        setShowModal(true);
    };

    return (
        <div className="h-[calc(100vh-2rem)] flex flex-col relative">


            <div className="flex justify-between items-center mb-6 shrink-0 mt-4">
                <h2 className="text-2xl font-bold text-white">Equipamentos <span className="text-sm font-normal text-slate-500 ml-2">({filteredEquipments.length})</span></h2>
                <div className="flex gap-2">
                    <button onClick={() => setShowScanner(true)} className="flex gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg">
                        <MonitorPlay size={18} /> Scan
                    </button>
                    <button
                        onClick={toggleSelectAll}
                        className="flex gap-2 bg-slate-700 hover:bg-slate-600 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg"
                        title={selectedIds.length === filteredEquipments.length && filteredEquipments.length > 0 ? "Desmarcar Todos" : "Selecionar Todos"}
                    >
                        {selectedIds.length === filteredEquipments.length && filteredEquipments.length > 0 ? (
                            <><CheckSquare size={18} /> Desmarcar Todos</>
                        ) : (
                            <><Square size={18} /> Selecionar Todos</>
                        )}
                    </button>
                    <button
                        onClick={handleBatchAutoDetect}
                        disabled={selectedIds.length === 0 || isDetecting}
                        className="relative overflow-hidden flex gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        title={selectedIds.length === 0 ? "Selecione equipamentos primeiro" : `Auto-detectar ${selectedIds.length} equipamento(s)`}
                    >
                        {isDetecting && (
                            <div
                                className="absolute left-0 top-0 bottom-0 bg-white/20 transition-all duration-300"
                                style={{ width: `${detectionProgress}%` }}
                            />
                        )}
                        <span className="relative flex items-center gap-2">
                            <Search size={18} />
                            {isDetecting ? `Detectando... ${detectionProgress}%` : `Auto-Detectar Marca e Tipo ${selectedIds.length > 0 ? `(${selectedIds.length})` : ''}`}
                        </span>
                    </button>
                    <button
                        onClick={handleBatchReboot}
                        disabled={selectedIds.length === 0}
                        className="flex gap-2 bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        title={selectedIds.length === 0 ? "Selecione equipamentos primeiro" : `Reiniciar ${selectedIds.length} equipamento(s)`}
                    >
                        <Power size={18} /> Reiniciar {selectedIds.length > 0 && `(${selectedIds.length})`}
                    </button>
                    <button
                        onClick={handleBatchDelete}
                        disabled={selectedIds.length === 0}
                        className="flex gap-2 bg-rose-600 hover:bg-rose-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        title={selectedIds.length === 0 ? "Selecione equipamentos primeiro" : `Excluir ${selectedIds.length} equipamento(s)`}
                    >
                        <Trash2 size={18} /> Excluir {selectedIds.length > 0 && `(${selectedIds.length})`}
                    </button>
                    <button onClick={handleExportCSV} className="flex gap-2 bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg">
                        <Download size={18} /> CSV
                    </button>
                    <label className="flex gap-2 bg-orange-600 hover:bg-orange-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg cursor-pointer">
                        <Upload size={18} /> Importar
                        <input type="file" accept=".csv" onChange={handleImportCSV} className="hidden" />
                    </label>
                    <button onClick={handleNewEquipment} className="flex gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-sm transition-colors shadow-lg">
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
                <div className="flex bg-slate-950 text-slate-400 uppercase text-xs font-bold py-3 border-b border-slate-800 shrink-0 select-none">
                    <div className="w-10 pl-4 flex items-center justify-center cursor-pointer" onClick={toggleSelectAll}>
                        {selectedIds.length > 0 && selectedIds.length === filteredEquipments.length ? <CheckSquare size={18} className="text-blue-500" /> : <Square size={18} className="text-slate-600 hover:text-slate-400" />}
                    </div>
                    <div className="w-16 text-center cursor-pointer hover:text-white flex justify-center items-center" onClick={() => handleSort('is_online')}>
                        Status {getSortIcon('is_online')}
                    </div>
                    <div className="flex-1 px-4 cursor-pointer hover:text-white flex items-center" onClick={() => handleSort('name')}>
                        Nome {getSortIcon('name')}
                    </div>
                    <div className="w-32 px-4 hidden sm:flex items-center cursor-pointer hover:text-white" onClick={() => handleSort('ip')}>
                        IP {getSortIcon('ip')}
                    </div>
                    <div className="w-48 px-4 text-right">Ações</div>
                </div>

                <div className="flex-1 bg-slate-950 overflow-y-auto min-h-0">
                    {filteredEquipments.length === 0 ? (
                        <div className="flex justify-center items-center h-full text-slate-500">Nenhum equipamento encontrado.</div>
                    ) : (
                        <div className="w-full">
                            {filteredEquipments.map((eq, index) => (
                                <EquipmentRow
                                    key={eq.id}
                                    index={index}
                                    data={{
                                        equipments: filteredEquipments,
                                        towers,
                                        onAction: handleWirelessInfo,
                                        onReboot: handleReboot,
                                        onDelete: handleDelete,
                                        onHistory: handleShowHistory,
                                        onEdit: handleEdit,
                                        selectedIds,
                                        toggleSelection
                                    }}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {showModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
                        <h3 className="text-xl font-bold text-white mb-4">{editingEquipment ? 'Editar' : 'Novo'} Equipamento</h3>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <input className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white" placeholder="Nome" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required />
                            <div className="space-y-2">
                                <input className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white" placeholder="IP" value={formData.ip} onChange={e => setFormData({ ...formData, ip: e.target.value })} required />
                                <button
                                    type="button"
                                    onClick={handleAutoDetect}
                                    disabled={isDetecting || !formData.ip}
                                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-slate-700 disabled:to-slate-700 text-white px-4 py-2 rounded font-semibold transition-all flex items-center justify-center gap-2"
                                >
                                    {isDetecting ? (
                                        <>
                                            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                            Detectando...
                                        </>
                                    ) : (
                                        <>
                                            <Search size={16} />
                                            🔍 Auto-Detectar Marca e Tipo
                                        </>
                                    )}
                                </button>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <select className="bg-slate-950 border border-slate-700 rounded p-2 text-white" value={formData.tower_id} onChange={e => setFormData({ ...formData, tower_id: e.target.value })}>
                                    <option value="">Sem Torre</option>
                                    {towers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                                </select>
                                <select className="bg-slate-950 border border-slate-700 rounded p-2 text-white" value={formData.brand} onChange={e => setFormData({ ...formData, brand: e.target.value })}>
                                    <option value="generic">Genérico</option>
                                    <option value="ubiquiti">Ubiquiti</option>
                                    <option value="mikrotik">Mikrotik</option>
                                    <option value="mimosa">Mimosa</option>
                                    <option value="intelbras">Intelbras</option>
                                </select>
                            </div>

                            <div className="bg-slate-800/50 p-3 rounded border border-slate-700">
                                <label className="block text-xs text-slate-400 uppercase font-bold mb-2">Tipo de Equipamento</label>
                                <div className="flex gap-4">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input type="radio" name="eqType" checked={formData.equipment_type === 'station'} onChange={() => setFormData({ ...formData, equipment_type: 'station' })} className="accent-blue-500" />
                                        <span className="text-white">Station (Cliente/Ponto)</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input type="radio" name="eqType" checked={formData.equipment_type === 'transmitter'} onChange={() => setFormData({ ...formData, equipment_type: 'transmitter' })} className="accent-purple-500" />
                                        <span className="text-white">Transmissor (AP)</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input type="radio" name="eqType" checked={formData.equipment_type !== 'station' && formData.equipment_type !== 'transmitter'} onChange={() => setFormData({ ...formData, equipment_type: 'other' })} className="accent-slate-500" />
                                        <span className="text-white">Nenhum</span>
                                    </label>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <input className="bg-slate-950 border border-slate-700 rounded p-2 text-white" placeholder="SSH User (admin)" value={formData.ssh_user} onChange={e => setFormData({ ...formData, ssh_user: e.target.value })} />
                                <input className="bg-slate-950 border border-slate-700 rounded p-2 text-white" type="password" placeholder="SSH Password" value={formData.ssh_password} onChange={e => setFormData({ ...formData, ssh_password: e.target.value })} />
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
                            {/* Select All Header */}
                            {scannedDevices.map((device) => (
                                <div key={device.ip} className="flex items-center gap-2 p-2 hover:bg-slate-900 cursor-pointer border-b border-slate-800/50 last:border-0" onClick={() => setSelectedIps(p => p.includes(device.ip) ? p.filter(i => i !== device.ip) : [...p, device.ip])}>
                                    {selectedIps.includes(device.ip) ? <CheckSquare className="text-blue-500 shrink-0" size={16} /> : <Square className="text-slate-500 shrink-0" size={16} />}

                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <span className="text-white font-mono text-sm">{device.ip}</span>
                                            {device.hostname && <span className="text-xs text-slate-500 truncate">({device.hostname})</span>}
                                        </div>
                                        <div className="flex gap-2 text-xs text-slate-500">
                                            <span>{device.vendor}</span>
                                            {device.mac && <span>• {device.mac}</span>}
                                        </div>
                                    </div>

                                    <div className="w-32">
                                        <input
                                            className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                                            placeholder="Nome (Opcional)"
                                            onClick={e => e.stopPropagation()}
                                            value={ipNames[device.ip] || ''}
                                            onChange={e => setIpNames({ ...ipNames, [device.ip]: e.target.value })}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex justify-between items-center mt-4">
                            <span className="text-slate-400 text-sm">{selectedIps.length} selecionados</span>
                            <div className="flex gap-2">
                                <button onClick={() => setShowScanner(false)} className="text-slate-400 px-4 py-2">Cancelar</button>
                                <button
                                    onClick={saveAllScanned}
                                    disabled={scannedDevices.length === 0}
                                    className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded disabled:opacity-50 transition-colors"
                                >
                                    Salvar Todos ({scannedDevices.length})
                                </button>
                                <button
                                    onClick={saveScanned}
                                    disabled={selectedIps.length === 0}
                                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50 transition-colors"
                                >
                                    Salvar Selecionados ({selectedIps.length})
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {
                showHistoryModal && selectedEqHistory && (
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
                )
            }
            {
                showWirelessModal && selectedWirelessEq && (
                    <WirelessMonitorModal equipment={selectedWirelessEq} onClose={() => setShowWirelessModal(false)} />
                )
            }
            {showTemplateModal && (<div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"><div className="bg-slate-900 border border-slate-700 rounded p-6"><input value={templateName} onChange={e => setTemplateName(e.target.value)} placeholder="Nome do Template" className="bg-slate-950 border border-slate-700 rounded p-2 text-white block mb-4 w-full" /><div className="flex gap-2 justify-end"><button onClick={() => setShowTemplateModal(false)} className="text-slate-400">Cancelar</button><button onClick={saveTemplate} className="bg-purple-600 text-white px-4 py-2 rounded">Salvar</button></div></div></div>)}
        </div >
    );
}

export default Equipments;
