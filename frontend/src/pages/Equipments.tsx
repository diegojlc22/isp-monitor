import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getEquipments, createEquipment, createEquipmentsBatch, updateEquipment, deleteEquipment, deleteEquipmentsBatch, getTowers, getLatencyHistory, rebootEquipment, testEquipment, exportEquipmentsCSV, importEquipmentsCSV, getNetworkDefaults, detectEquipmentBrand, getWirelessStatus, scanInterfaces, autoDetectAll } from '../services/api';
import { useScanner } from '../contexts/ScannerContext';

import { Plus, Trash2, Search, Server, MonitorPlay, CheckSquare, Square, Edit2, Activity, Power, Wifi, Download, Upload, Users, Zap, Minus } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import clsx from 'clsx';
import toast from 'react-hot-toast';


// @ts-ignore
import { useDebounce } from 'use-debounce';
import { MetricCard } from '../components/MetricCard';

// --- Interfaces ---
interface Tower { id: number; name: string; }
interface Equipment {
    id: number; name: string; ip: string; tower_id: number | null; parent_id: number | null;
    is_online: boolean; brand: string; equipment_type: string; signal_dbm?: number;
    ccq?: number; connected_clients?: number; ssh_user?: string; ssh_port?: number;
    snmp_community?: string; snmp_version?: number; snmp_port?: number; snmp_interface_index?: number;
    snmp_traffic_interface_index?: number;
    is_mikrotik?: boolean; mikrotik_interface?: string; api_port?: number;
}
interface FormData {
    name: string; ip: string; tower_id: string; parent_id: string; ssh_user: string; ssh_password: string;
    ssh_port: number; snmp_community: string; snmp_version: number; snmp_port: number; snmp_interface_index: number;
    snmp_traffic_interface_index: number | null;
    brand: string; equipment_type: string; is_mikrotik: boolean; mikrotik_interface: string; api_port: number;
}

const INITIAL_FORM_STATE: FormData = {
    name: '', ip: '', tower_id: '', parent_id: '', ssh_user: 'admin', ssh_password: '', ssh_port: 22,
    snmp_community: 'public', snmp_version: 1, snmp_port: 161, snmp_interface_index: 1, snmp_traffic_interface_index: null, brand: 'generic',
    equipment_type: 'station', is_mikrotik: false, mikrotik_interface: '', api_port: 8728
};

// --- Custom Hooks ---
function usePoll(callback: () => Promise<void> | void, intervalMs: number) {
    useEffect(() => {
        // Initial call
        const initial = async () => {
            try { await callback(); } catch (e) { /* Silent */ }
        };
        initial();

        const interval = setInterval(async () => {
            if (!document.hidden) {
                try { await callback(); } catch (e) { /* Silent */ }
            }
        }, intervalMs);
        return () => clearInterval(interval);
    }, [callback, intervalMs]);
}

// --- Componentes Otimizados ---

const EquipmentRow = ({ index, data }: any) => {
    const { equipments, towers, onAction, onReboot, onTest, onDelete, onHistory, onEdit, selectedIds, toggleSelection } = data;
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
                <button onClick={() => onTest && onTest(eq)} className="text-slate-400 hover:text-green-400 p-1.5 rounded hover:bg-slate-700" title="Testar Ping">
                    <Zap size={16} />
                </button>
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
                // Fetch real-time status via SNMP
                const status = await getWirelessStatus(equipment.id);

                if (status && isMounted) {
                    // Actualiza o estado do equipamento actual com os dados em tempo real
                    setCurrentEq((prev: any) => ({
                        ...prev,
                        signal_dbm: status.signal_dbm,
                        ccq: status.ccq,
                        connected_clients: status.connected_clients
                    }));

                    const now = new Date();
                    const newPoint = {
                        time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                        signal: status.signal_dbm,
                        ccq: status.ccq,
                        clients: status.connected_clients || 0
                    };

                    // Adiciona ao gráfico se tiver dados válidos
                    if (status.signal_dbm !== null || status.connected_clients !== null) {
                        setData(prev => [...prev, newPoint].slice(-60));
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
                        <div className="col-span-2">
                            <MetricCard
                                title="Clientes Conectados"
                                value={currentEq.connected_clients || 0}
                                status="good"
                                description="Total de estações associadas."
                                icon={Users}
                            />
                        </div>
                    ) : isStation ? (
                        <>
                            <MetricCard
                                title="Sinal"
                                value={`${currentEq.signal_dbm || 'N/A'} dBm`}
                                status={(currentEq.signal_dbm || -100) > -65 ? 'good' : 'average'}
                                description="Intensidade do sinal recebido."
                                icon={Wifi}
                            />
                            <MetricCard
                                title="CCQ"
                                value={`${currentEq.ccq || 'N/A'}%`}
                                status={(currentEq.ccq || 0) > 90 ? 'good' : 'average'}
                                description="Qualidade da conexão (Client Connection Quality)."
                                icon={Activity}
                            />
                        </>
                    ) : (
                        <div className="col-span-2 bg-slate-800/50 p-6 rounded border border-slate-700 text-center text-slate-500 text-sm">
                            Monitoramento wireless não disponível para este tipo de equipamento.
                        </div>
                    )}
                </div>

                {/* Live Chart - Only show if valid type */}
                {(isTransmitter || isStation) && (
                    <div className="h-48 bg-slate-950/50 rounded border border-slate-800/50 p-2 relative">
                        {data.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%" debounce={100}>
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
    // Scanner Context
    const { isScanning, progress, scannedDevices, startScan: startContextScan, stopScan, showScannerModal, setShowScannerModal, scanRange: contextScanRange } = useScanner();

    // Local Scanner UI
    const [selectedIps, setSelectedIps] = useState<string[]>([]);
    const [ipNames, setIpNames] = useState<{ [key: string]: string }>({});
    const [scanRangeInput, setScanRangeInput] = useState('');

    // Sync Input with Running Scan and Global Defaults
    useEffect(() => {
        if (isScanning && contextScanRange) setScanRangeInput(contextScanRange);
    }, [isScanning, contextScanRange]);


    const handleScanStart = (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (isScanning) { stopScan(); return; }
        if (!scanRangeInput) return;

        const community = networkDefaults.snmp_community || 'public';
        const port = networkDefaults.snmp_port || 161;
        startContextScan(scanRangeInput, community, port);
    };

    // Detection Progress

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
        if (!confirm(`Tem certeza que deseja EXCLUIR ${selectedIds.length} equipamentos?`)) return;
        try {
            await deleteEquipmentsBatch(selectedIds);
            toast.success('Equipamentos excluídos!');
            setSelectedIds([]);
            load();
        } catch (e: any) {
            toast.error('Erro ao excluir alguns itens: ' + (e.response?.data?.detail || e.message));
        }
    };

    const handleBatchReboot = async () => {
        if (!confirm(`Reiniciar ${selectedIds.length} equipamentos ? `)) return;
        try {
            for (const id of selectedIds) { rebootEquipment(id).catch(console.error); }
            toast.success('Comandos de reboot enviados!'); setSelectedIds([]);
        } catch (e) { toast.error('Erro ao enviar comandos.'); }
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
    const [isDetectingForm, setIsDetectingForm] = useState(false);
    const [isDetectingAll, setIsDetectingAll] = useState(false);
    const [interfaceList, setInterfaceList] = useState<any[]>([]);
    const [isLoadingInterfaces, setIsLoadingInterfaces] = useState(false);

    // Global Tasks from Context
    const { isDetecting, detectionProgress, startDetection, stopDetection } = useScanner();

    // Auto-detect equipment brand and type
    const handleAutoDetect = async () => {
        if (!formData.ip) {
            toast.error('Por favor, insira um IP primeiro');
            return;
        }

        setIsDetectingForm(true);
        try {
            const result = await detectEquipmentBrand(
                formData.ip,
                formData.snmp_community || networkDefaults.snmp_community || 'public',
                formData.snmp_port || networkDefaults.snmp_port || 161
            );

            setFormData({
                ...formData,
                brand: result.brand,
                equipment_type: result.equipment_type,
                name: result.name || formData.name  // Use detected name if available, otherwise keep current
            });

            const detectedName = result.name ? `\n✅ Nome: ${result.name}` : '';
            toast.success(`Detectado: \nMarca: ${result.brand.toUpperCase()} \nTipo: ${result.equipment_type === 'station' ? 'Station (Cliente)' : result.equipment_type === 'transmitter' ? 'Transmitter (AP)' : 'Outro'} ${detectedName}`);
        } catch (error: any) {
            const errorDetail = error.response?.data?.detail;
            const errorMsg = typeof errorDetail === 'object'
                ? JSON.stringify(errorDetail)
                : (errorDetail || error.message);
            toast.error(`Erro na detecção: ${errorMsg}`);
        } finally {
            setIsDetectingForm(false);
        }
    };

    const handleAutoDetectAll = async () => {
        if (!formData.ip) {
            toast.error('Por favor, insira um IP primeiro');
            return;
        }

        setIsDetectingAll(true);
        try {
            const result = await autoDetectAll(
                formData.ip,
                formData.snmp_community || networkDefaults.snmp_community || 'public',
                formData.snmp_port || networkDefaults.snmp_port || 161
            );

            if (result.success) {
                setFormData({
                    ...formData,
                    brand: result.brand || formData.brand,
                    equipment_type: result.equipment_type || formData.equipment_type,
                    snmp_interface_index: result.snmp_interface_index || formData.snmp_interface_index,
                    snmp_traffic_interface_index: result.snmp_traffic_interface_index || formData.snmp_traffic_interface_index
                });

                let msg = 'Detecção completa finalizada com sucesso!';
                if (result.brand) msg += `\n✅ Marca: ${result.brand.toUpperCase()}`;
                if (result.equipment_type) msg += `\n✅ Tipo: ${result.equipment_type}`;
                if (result.snmp_interface_index) msg += `\n✅ Interface Sinal: ${result.snmp_interface_index}`;
                if (result.snmp_traffic_interface_index) msg += `\n✅ Interface Tráfego: ${result.snmp_traffic_interface_index} (${result.traffic_in} Mbps)`;

                if (result.errors && result.errors.length > 0) {
                    msg += `\n\n⚠️ Avisos:\n- ${result.errors.join('\n- ')}`;
                }

                toast.success(msg);
            } else {
                toast.error(`Nenhuma informação detectada. Verifique o IP e SNMP.\nErros: ${result.errors?.join(', ')}`);
            }
        } catch (error: any) {
            const errorDetail = error.response?.data?.detail;
            const errorMsg = typeof errorDetail === 'object'
                ? JSON.stringify(errorDetail)
                : (errorDetail || error.message);
            toast.error(`Erro na detecção completa: ${errorMsg}`);
        } finally {
            setIsDetectingAll(false);
        }
    };

    const handleLoadInterfaces = async () => {
        if (!formData.ip) {
            toast.error('Por favor, insira um IP primeiro');
            return;
        }
        setIsLoadingInterfaces(true);
        try {
            const list = await scanInterfaces(
                formData.ip,
                formData.snmp_community || networkDefaults.snmp_community || 'public',
                formData.snmp_port || networkDefaults.snmp_port || 161
            );
            setInterfaceList(list);
        } catch (error: any) {
            const errorDetail = error.response?.data?.detail;
            const errorMsg = typeof errorDetail === 'object'
                ? JSON.stringify(errorDetail)
                : (errorDetail || error.message);
            toast.error(`Erro ao listar interfaces: ${errorMsg}`);
        } finally {
            setIsLoadingInterfaces(false);
        }
    };

    // Batch auto-detect for selected equipments (delegated to background)
    const handleBatchAutoDetect = async () => {
        if (selectedIds.length === 0) {
            toast.error('Selecione pelo menos um equipamento');
            return;
        }

        if (!confirm(`Deseja auto-detectar marca e tipo de ${selectedIds.length} equipamento(s)?`)) {
            return;
        }

        try {
            await startDetection(selectedIds);
            setSelectedIds([]);
        } catch (e: any) {
            toast.error(e.response?.data?.detail || "Erro ao iniciar detecção.");
        }
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

    usePoll(load, 20000); // Aumentado para 20s para evitar travas com muitos dispositivos

    useEffect(() => {
        const saved = localStorage.getItem('equipment_templates');
        if (saved) { try { setTemplates(JSON.parse(saved)); } catch (e) { } }
    }, []);

    const handleReboot = useCallback(async (eq: Equipment) => {
        if (!confirm(`Reiniciar ${eq.name}?`)) return;
        try { await rebootEquipment(eq.id); toast.success("Comando de reboot enviado!"); } catch (e: any) { toast.error("Erro: " + (e.response?.data?.detail || e.message)); }
    }, []);

    const handleTest = useCallback(async (eq: Equipment) => {
        try {
            toast.loading(`Iniciando teste de ping para ${eq.ip}... Aguarde.`, { id: 'ping-test' });
            const res = await testEquipment(eq.id);
            toast.dismiss('ping-test');
            if (res.is_online) {
                toast.success(`ONLINE - Latência: ${res.latency}ms / Perda: ${res.packet_loss}%`);
            } else {
                toast.error(`OFFLINE - Erro: ${res.error || "Sem resposta"}`);
            }
        } catch (e: any) {
            toast.error("Erro no teste: " + (e.response?.data?.detail || e.message));
        }
    }, []);

    const handleDelete = useCallback(async (id: number) => {
        if (confirm('Tem certeza?')) { await deleteEquipment(id); load(); }
    }, [load]);

    const handleEdit = useCallback((eq: Equipment) => {
        setEditingEquipment(eq);
        setInterfaceList([]); // Reset list on open
        setFormData({
            name: eq.name, ip: eq.ip, tower_id: eq.tower_id ? String(eq.tower_id) : '',
            parent_id: eq.parent_id ? String(eq.parent_id) : '', ssh_user: eq.ssh_user || 'admin',
            ssh_password: '', ssh_port: eq.ssh_port || 22, snmp_community: eq.snmp_community || 'public',
            snmp_version: eq.snmp_version || 1, snmp_port: eq.snmp_port || 161, snmp_interface_index: eq.snmp_interface_index || 1,
            snmp_traffic_interface_index: eq.snmp_traffic_interface_index || null,
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
        } catch (e) { toast.error('Erro ao carregar histórico.'); }
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
        } catch (error: any) {
            toast.error('Erro ao salvar: ' + (error.response?.data?.detail || error.message));
        }
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
        } catch (e) { toast.error('Erro ao exportar'); }
    }

    async function handleImportCSV(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0]; if (!file) return;
        try { await importEquipmentsCSV(file); toast.success('Importado com sucesso!'); load(); } catch (err: any) { toast.error("Erro importando: " + err.message); }
        e.target.value = '';
    }

    async function saveScanned() {
        if (!selectedIps.length) return;

        const payload = selectedIps.map(ip => {
            const device = scannedDevices.find(d => d.ip === ip);
            return {
                name: ipNames[ip] || `Dispositivo ${ip}`,
                ip,
                ssh_port: networkDefaults.ssh_port || 22,
                ssh_user: networkDefaults.ssh_user || 'admin',
                ssh_password: networkDefaults.ssh_password || '',
                snmp_community: networkDefaults.snmp_community || 'public',
                snmp_port: networkDefaults.snmp_port || 161,

                brand: device?.brand || 'generic',
                equipment_type: device?.equipment_type || 'station',
                is_mikrotik: device?.brand === 'mikrotik',
                whatsapp_groups: [],
                tower_id: null
            };
        });

        try {
            const res = await createEquipmentsBatch(payload);
            toast.success(`Salvo: ${res.success} / Ignorados: ${res.failed}`);
            setShowScannerModal(false);
            load();
        } catch (e: any) {
            toast.error("Erro ao salvar lote: " + (e.response?.data?.detail || e.message));
        }
    }

    async function saveAllScanned() {
        if (!scannedDevices.length) return;

        const payload = scannedDevices.map(device => ({
            name: ipNames[device.ip] || `Dispositivo ${device.ip}`,
            ip: device.ip,
            ssh_port: networkDefaults.ssh_port || 22,
            ssh_user: networkDefaults.ssh_user || 'admin',
            ssh_password: networkDefaults.ssh_password || '',
            snmp_community: networkDefaults.snmp_community || 'public',
            snmp_port: networkDefaults.snmp_port || 161,

            brand: device.brand || 'generic',
            equipment_type: device.equipment_type || 'station',
            is_mikrotik: device.brand === 'mikrotik',
            whatsapp_groups: [],
            tower_id: null
        }));

        try {
            const res = await createEquipmentsBatch(payload);
            toast.success(`Salvo: ${res.success} / Ignorados: ${res.failed}`);
            setShowScannerModal(false);
            load();
        } catch (e: any) {
            toast.error("Erro ao salvar lote: " + (e.response?.data?.detail || e.message));
        }
    }

    const handleNewEquipment = async () => {
        setEditingEquipment(null);
        setInterfaceList([]); // Reset list on open
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

    const getMetrics = () => {
        const total = equipments.length;
        if (total === 0) return { total: 0, online: 0, offline: 0, health: 0 };
        const online = equipments.filter(e => e.is_online).length;
        const offline = total - online;
        const health = Math.round((online / total) * 100);
        return { total, online, offline, health };
    };

    const metrics = getMetrics();

    return (

        <div className="flex h-[calc(100vh-2rem)] overflow-hidden gap-6 mt-4">

            {/* --- LEFT MAIN CONTENT --- */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

                {/* 1. Metrics Area */}
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <Activity size={20} className="text-blue-500" /> Métricas em Tempo Real
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 shrink-0">
                    <MetricCard
                        title="Total Dispositivos"
                        value={metrics.total}
                        description="Total de equipamentos cadastrados."
                        icon={Server}
                    />
                    <MetricCard
                        title="Saúde da Rede"
                        value={`${metrics.health}%`}
                        status={metrics.health > 90 ? 'good' : metrics.health > 70 ? 'average' : 'poor'}
                        description={metrics.health > 90 ? "Rede operando em ótima performance." : "Atenção requerida em alguns setores."}
                        icon={Activity}
                    />
                    <MetricCard
                        title="Online Agora"
                        value={metrics.online}
                        status="good"
                        description={`${metrics.online} dispositivos respondendo.`}
                        icon={Wifi}
                        linkText="Ver filtro online"
                        onClick={() => setFilterStatus('online')}
                    />
                    <MetricCard
                        title="Offline (Crítico)"
                        value={metrics.offline}
                        status={metrics.offline === 0 ? 'good' : 'poor'}
                        description={metrics.offline === 0 ? "Nenhum dispositivo offline!" : `${metrics.offline} dispositivos sem resposta.`}
                        icon={Zap}
                        linkText={metrics.offline > 0 ? "Ver falhas" : undefined}
                        onClick={() => setFilterStatus('offline')}
                    />
                </div>

                {/* 2. Tabs / List Header */}
                <div className="flex justify-between items-end border-b border-slate-800 mb-4 px-1">
                    <div className="flex gap-6">
                        <button className="pb-3 text-sm font-medium border-b-2 border-blue-500 text-blue-400">
                            Lista de Equipamentos ({filteredEquipments.length})
                        </button>
                        <button className="pb-3 text-sm font-medium border-b-2 border-transparent text-slate-500 hover:text-slate-300 transition-colors">
                            Mapa de Topologia
                        </button>
                    </div>
                </div>

                {/* 3. The List Content */}
                <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg overflow-hidden flex flex-col shadow-xl relative">
                    {/* List Header */}
                    <div className="flex bg-slate-950/50 text-slate-400 uppercase text-[10px] font-bold py-3 border-b border-slate-800 shrink-0 select-none">
                        <div className="w-10 pl-4 flex items-center justify-center cursor-pointer" onClick={toggleSelectAll}>
                            {selectedIds.length > 0 && selectedIds.length === filteredEquipments.length ? <CheckSquare size={16} className="text-blue-500" /> : <Square size={16} className="text-slate-600 hover:text-slate-400" />}
                        </div>
                        <div className="w-16 text-center cursor-pointer hover:text-white flex justify-center items-center gap-1" onClick={() => handleSort('is_online')}>
                            STATUS {getSortIcon('is_online')}
                        </div>
                        <div className="flex-1 px-4 cursor-pointer hover:text-white flex items-center gap-1" onClick={() => handleSort('name')}>
                            NOME {getSortIcon('name')}
                        </div>
                        <div className="w-32 px-4 hidden sm:flex items-center cursor-pointer hover:text-white gap-1" onClick={() => handleSort('ip')}>
                            IP {getSortIcon('ip')}
                        </div>
                        <div className="w-48 px-4 text-right">AÇÕES</div>
                    </div>

                    {/* Scrollable List */}
                    <div className="flex-1 overflow-y-auto min-h-0 custom-scrollbar">
                        {filteredEquipments.length === 0 ? (
                            <div className="flex flex-col justify-center items-center h-full text-slate-500 italic">
                                <Search size={48} className="mb-4 opacity-20" />
                                Nenhum equipamento encontrado.
                            </div>
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
                                            onTest: handleTest,
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
            </div>

            {/* --- RIGHT SIDEBAR --- */}
            <div className="w-80 shrink-0 flex flex-col gap-6 overflow-y-auto pb-4 pr-1">

                {/* Section 1: Actions */}
                <div className="space-y-3">
                    <h3 className="font-semibold text-slate-300 text-sm">Ações Rápidas</h3>
                    <button onClick={handleNewEquipment} className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-900/20">
                        <Plus size={18} /> Novo Equipamento
                    </button>
                    <button onClick={() => setShowScannerModal(true)} className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 p-3 rounded-lg text-sm font-medium transition-colors border border-slate-700">
                        <MonitorPlay size={18} /> Rede Scanner
                        {isScanning && <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse ml-auto" />}
                    </button>
                    <div className="grid grid-cols-2 gap-2">
                        <button onClick={handleExportCSV} className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 p-2 rounded-lg text-xs font-medium border border-slate-700">
                            <Download size={14} /> Exportar
                        </button>
                        <label className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 p-2 rounded-lg text-xs font-medium border border-slate-700 cursor-pointer">
                            <Upload size={14} /> Importar
                            <input type="file" accept=".csv" onChange={handleImportCSV} className="hidden" />
                        </label>
                    </div>
                </div>

                {/* Section 2: Filters */}
                <div className="space-y-4">
                    <h3 className="font-semibold text-slate-300 text-sm flex items-center justify-between">
                        Filtros de Lista
                        <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400">{filteredEquipments.length}</span>
                    </h3>

                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                        <input
                            type="text"
                            placeholder="Buscar nome ou IP..."
                            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                            value={filterText}
                            onChange={e => setFilterText(e.target.value)}
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs text-slate-500 uppercase font-bold">Status</label>
                        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-blue-500">
                            <option value="all">Mostrar Todos</option>
                            <option value="online">🟢 Apenas Online</option>
                            <option value="offline">🔴 Apenas Offline</option>
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs text-slate-500 uppercase font-bold">Torre</label>
                        <select value={filterTower} onChange={e => setFilterTower(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-blue-500">
                            <option value="all">Todas as Torres</option>
                            {towers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs text-slate-500 uppercase font-bold">Tipo</label>
                        <select value={filterType} onChange={e => setFilterType(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-blue-500">
                            <option value="all">Todos os Tipos</option>
                            <option value="station">Clientes (Station)</option>
                            <option value="transmitter">Torres (AP)</option>
                        </select>
                    </div>
                </div>

                {/* Section 3: Batch Selection (Conditional) */}
                {selectedIds.length > 0 && (
                    <div className="bg-gradient-to-br from-indigo-900/40 to-purple-900/40 border border-indigo-500/30 p-4 rounded-xl space-y-3 animate-in fade-in slide-in-from-right-4">
                        <h3 className="text-indigo-300 text-sm font-bold flex items-center justify-between">
                            {selectedIds.length} Selecionados
                            <button onClick={() => setSelectedIds([])} className="text-[10px] uppercase text-indigo-400 hover:text-white">Limpar</button>
                        </h3>

                        <button
                            onClick={handleBatchAutoDetect}
                            disabled={isDetecting}
                            className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white p-2.5 rounded-lg text-xs font-medium transition-colors shadow-lg"
                        >
                            {isDetecting ? <div className="animate-spin h-3 w-3 border-2 border-white/50 border-t-white rounded-full" /> : <Wifi size={14} />}
                            {isDetecting ? 'Detectando...' : 'Auto-Detectar'}
                        </button>

                        <button
                            onClick={handleBatchReboot}
                            className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-amber-600 hover:text-white text-slate-300 p-2.5 rounded-lg text-xs font-medium transition-colors border border-slate-700 hover:border-amber-500"
                        >
                            <Power size={14} /> Reiniciar em Massa
                        </button>

                        <button
                            onClick={handleBatchDelete}
                            className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-rose-600 hover:text-white text-slate-300 p-2.5 rounded-lg text-xs font-medium transition-colors border border-slate-700 hover:border-rose-500"
                        >
                            <Trash2 size={14} /> Excluir Seleção
                        </button>
                    </div>
                )}

                {/* System Status / Footer */}
                <div className="mt-auto pt-6 border-t border-slate-800">
                    <div className="text-[10px] text-slate-600 uppercase font-bold tracking-wider mb-2">Ambiente</div>
                    <div className="space-y-2">
                        <div className="flex justify-between text-xs text-slate-400">
                            <span>CPU Throttling</span>
                            <span className="text-slate-500">Disabled</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-400">
                            <span>Network (Scanner)</span>
                            <span className="text-emerald-500">Active</span>
                        </div>
                    </div>
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
                                <div className="grid grid-cols-1 gap-2">
                                    <button
                                        type="button"
                                        onClick={handleAutoDetectAll}
                                        disabled={isDetectingAll || !formData.ip}
                                        className="w-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 disabled:from-slate-700 disabled:to-slate-700 text-white px-4 py-3 rounded-lg font-bold transition-all flex items-center justify-center gap-2 shadow-lg hover:scale-[1.02] active:scale-[0.98] border border-white/10"
                                    >
                                        {isDetectingAll ? (
                                            <>
                                                <div className="animate-spin h-5 w-5 border-3 border-white border-t-transparent rounded-full"></div>
                                                <span className="animate-pulse">Analisando Equipamento... (Aguarde)</span>
                                            </>
                                        ) : (
                                            <>
                                                <Zap size={20} className="text-yellow-400 fill-yellow-400" />
                                                <span>� AUTO-DETECTAR TUDO</span>
                                            </>
                                        )}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleAutoDetect}
                                        disabled={isDetectingForm || isDetectingAll || !formData.ip}
                                        className="w-full bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded text-xs font-medium transition-all flex items-center justify-center gap-2 border border-slate-700"
                                    >
                                        {isDetectingForm ? (
                                            <div className="animate-spin h-3 w-3 border-2 border-slate-400 border-t-transparent rounded-full"></div>
                                        ) : (
                                            <Search size={14} />
                                        )}
                                        Detectar apenas Marca e Tipo
                                    </button>
                                </div>
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

                            {['mikrotik', 'ubiquiti', 'mimosa', 'intelbras'].includes(formData.brand) && (
                                <div className="space-y-3">
                                    <div className="bg-slate-800/50 p-3 rounded border border-slate-700 space-y-2">
                                        <div className="flex justify-between items-center">
                                            <label className="text-xs text-slate-400 uppercase font-bold">Interface SFP / Wireless (Sinal)</label>
                                            <button
                                                type="button"
                                                onClick={handleLoadInterfaces}
                                                disabled={isLoadingInterfaces}
                                                className="bg-blue-600 hover:bg-blue-500 text-[10px] uppercase font-bold text-white px-2 py-0.5 rounded transition-colors disabled:opacity-50"
                                            >
                                                {isLoadingInterfaces ? '...' : 'Escanear Interfaces'}
                                            </button>
                                        </div>
                                        <select
                                            className="w-full bg-slate-950 border border-slate-700 rounded p-1.5 text-white text-sm"
                                            value={formData.snmp_interface_index}
                                            onChange={e => setFormData({ ...formData, snmp_interface_index: parseInt(e.target.value) })}
                                        >
                                            <option value={1}>Padrão (1)</option>
                                            {interfaceList.map(iface => (
                                                <option key={iface.index} value={iface.index}>{iface.index}: {iface.name}</option>
                                            ))}
                                            {interfaceList.length === 0 && <option value={formData.snmp_interface_index}>Atual (ID: {formData.snmp_interface_index})</option>}
                                        </select>
                                    </div>

                                    <div className="bg-slate-800/50 p-3 rounded border border-slate-700 space-y-2">
                                        <label className="block text-xs text-slate-400 uppercase font-bold">Interface de Tráfego (Uplink/LAN)</label>
                                        <select
                                            className="w-full bg-slate-950 border border-slate-700 rounded p-1.5 text-white text-sm"
                                            value={formData.snmp_traffic_interface_index || ''}
                                            onChange={e => setFormData({ ...formData, snmp_traffic_interface_index: e.target.value ? parseInt(e.target.value) : null })}
                                        >
                                            <option value="">Mesma da Interface de Sinal</option>
                                            {interfaceList.map(iface => (
                                                <option key={`traffic-${iface.index}`} value={iface.index}>{iface.index}: {iface.name}</option>
                                            ))}
                                            {interfaceList.length === 0 && formData.snmp_traffic_interface_index && (
                                                <option value={formData.snmp_traffic_interface_index}>Atual (ID: {formData.snmp_traffic_interface_index})</option>
                                            )}
                                        </select>
                                        <p className="text-[10px] text-slate-500 italic">Se vazio, usará a mesma interface configurada acima.</p>
                                    </div>
                                </div>
                            )}

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

            {
                showScannerModal && (
                    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                        <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl p-6 h-[80vh] flex flex-col">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-xl font-bold text-white">Scanner de Rede</h3>
                                <button onClick={() => setShowScannerModal(false)} className="text-slate-400 hover:text-white p-1 hover:bg-slate-800 rounded" title="Minimizar (scan continua)">
                                    <Minus size={20} />
                                </button>
                            </div>
                            <div className="flex flex-col gap-2 mb-4">
                                <div className="flex gap-2">
                                    <input className="flex-1 bg-slate-950 border border-slate-700 rounded p-2 text-white" placeholder="Range (ex: 192.168.1.0/24, 10.0.0.50-100, 8.8.8.8)" value={scanRangeInput} onChange={e => setScanRangeInput(e.target.value)} disabled={isScanning} />
                                    <button onClick={handleScanStart} className={clsx("text-white px-6 rounded font-bold shadow-lg transition-all", isScanning ? "bg-red-600 hover:bg-red-500" : "bg-blue-600 hover:bg-blue-500")}>
                                        {isScanning ? 'Parar' : 'Escanear'}
                                    </button>
                                </div>
                                <div className="flex justify-between items-center px-1">
                                    <span className="text-[10px] text-slate-500 uppercase font-bold">Usando credenciais de rede padrão</span>
                                    {progress > 0 && <span className="text-blue-400 text-[10px] font-mono">{progress}%</span>}
                                </div>
                                {progress > 0 && (
                                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                                        <div className="bg-blue-500 h-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
                                    </div>
                                )}
                            </div>
                            <div className="flex-1 bg-slate-950 rounded border border-slate-800 p-2 overflow-y-auto">
                                {/* Select All Header */}
                                {scannedDevices.map((device) => {
                                    const existing = equipments.find(e => e.ip === device.ip);
                                    return (
                                        <div key={device.ip} className={clsx("flex items-center gap-2 p-2 hover:bg-slate-900 cursor-pointer border-b border-slate-800/50 last:border-0", existing && "opacity-60")}
                                            onClick={() => !existing && setSelectedIps(p => p.includes(device.ip) ? p.filter(i => i !== device.ip) : [...p, device.ip])}>

                                            {existing ? <div title="Já cadastrado"><CheckSquare className="text-slate-600 shrink-0" size={16} /></div> :
                                                selectedIps.includes(device.ip) ? <CheckSquare className="text-blue-500 shrink-0" size={16} /> : <Square className="text-slate-500 shrink-0" size={16} />}

                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-white font-mono text-sm">{device.ip}</span>
                                                    {existing ? (
                                                        <span className="text-xs bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700">Existente: {existing.name}</span>
                                                    ) : (
                                                        device.hostname && <span className="text-xs text-slate-500 truncate">({device.hostname})</span>
                                                    )}
                                                </div>
                                                <div className="flex gap-2 text-xs text-slate-500">
                                                    <span>{device.vendor}</span>
                                                    {device.mac && <span>• {device.mac}</span>}
                                                </div>
                                            </div>

                                            <div className="w-32">
                                                {!existing && (
                                                    <input
                                                        className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                                                        placeholder="Nome (Opcional)"
                                                        onClick={e => e.stopPropagation()}
                                                        value={ipNames[device.ip] || ''}
                                                        onChange={e => setIpNames({ ...ipNames, [device.ip]: e.target.value })}
                                                    />
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="flex justify-between items-center mt-4">
                                <span className="text-slate-400 text-sm">{selectedIps.length} selecionados</span>
                                <div className="flex gap-2">
                                    <button onClick={() => setShowScannerModal(false)} className="text-slate-400 px-4 py-2">Cancelar</button>
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

                )
            }

            {
                showHistoryModal && selectedEqHistory && (
                    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                        <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-4xl p-6 h-[70vh] flex flex-col">
                            <h3 className="text-white font-bold mb-4">{selectedEqHistory.name} - Histórico ({historyPeriod})</h3>
                            <div className="flex-1 min-h-0 relative">
                                <ResponsiveContainer width="100%" height="100%" debounce={100}>
                                    <AreaChart data={historyData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                        <XAxis dataKey="timeStr" stroke="#666" />
                                        <YAxis stroke="#666" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                                            formatter={(value: any) => [Math.round(value), 'Latência']}
                                        />
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

            {/* Detecção Progress Table Overlay */}
            {
                isDetecting && (
                    <div className="fixed bottom-6 right-6 z-[60] bg-slate-900 border border-blue-500/30 p-4 rounded-xl shadow-2xl w-80 animate-in fade-in slide-in-from-bottom-4">
                        <div className="flex justify-between items-center mb-3">
                            <h3 className="text-blue-400 font-bold flex items-center gap-2 text-sm">
                                <Zap size={18} className="animate-pulse" /> Detecção em Lote
                            </h3>
                            <button onClick={stopDetection} className="text-slate-500 hover:text-red-400">
                                <Minus size={16} />
                            </button>
                        </div>
                        <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mb-2">
                            <div className="bg-blue-500 h-full transition-all duration-500" style={{ width: `${detectionProgress}%` }}></div>
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                            <span>PROGRESSO {detectionProgress}%</span>
                            <span className="text-blue-400 animate-pulse uppercase">Processando...</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-2 text-center">
                            Você pode navegar livremente. A detecção continuará no servidor.
                        </p>
                    </div>
                )
            }
        </div>
    );
}

export default Equipments;
