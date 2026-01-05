import { MapContainer, TileLayer, Marker, Popup, LayersControl, useMap, Polyline } from 'react-leaflet';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { getTowers, getLinks, createLink, deleteLink, getUsers, getTechLocation, triggerTopologyDiscovery } from '../services/api';
import L from 'leaflet';
import { Search, Network, Eye, EyeOff, Trash2, Plus, RefreshCcw } from 'lucide-react';
import clsx from 'clsx';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

// Fix Leaflet Icons
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: iconRetinaUrl,
    iconUrl: iconUrl,
    shadowUrl: shadowUrl,
});

// Custom Icons for Status
const createTowerIcon = (name: string, isOnline: boolean) => new L.DivIcon({
    className: 'custom-div-icon',
    html: `
        <div style="display: flex; flex-direction: column; align-items: center;">
            <div style="background-color: ${isOnline ? '#22c55e' : '#f43f5e'}; padding: 8px; border-radius: 50%; box-shadow: 0 0 10px rgba(0,0,0,0.5); border: 2px solid white;">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2c0 20 0 20 0 20"></path>
                    <path d="M8 8.5c0 0 2.5-3 8-1.5"></path>
                    <path d="M5 14c0 0 4-4 14-2.5"></path>
                    <path d="M2.5 19.5c0 0 6.5-5.5 19-3.5"></path>
                </svg>
            </div>
            <span style="margin-top: 4px; background-color: rgba(15, 23, 42, 0.8); color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">
                ${name}
            </span>
        </div>
    `,
    iconSize: [40, 60],
    iconAnchor: [20, 60],
    popupAnchor: [0, -60]
});

const createTechIcon = (name: string) => new L.DivIcon({
    className: 'custom-div-icon',
    html: `
        <div style="display: flex; flex-direction: column; align-items: center;">
            <div style="background-color: #3b82f6; padding: 6px; border-radius: 50%; box-shadow: 0 0 10px rgba(0,0,0,0.5); border: 2px solid white; animation: pulse 2s infinite;">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
            </div>
            <span style="margin-top: 4px; background-color: rgba(37, 99, 235, 0.9); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; white-space: nowrap;">
                ${name}
            </span>
        </div>
    `,
    iconSize: [40, 60],
    iconAnchor: [20, 60],
    popupAnchor: [0, -60]
});

// Map Controller to handle Pan/Zoom
function MapController({ center }: { center: [number, number] | null }) {
    const map = useMap();
    useEffect(() => {
        if (center) {
            map.flyTo(center, 14);
        }
    }, [center, map]);
    return null;
}

export function NetMap() {
    const [towers, setTowers] = useState<any[]>([]);
    const [links, setLinks] = useState<any[]>([]);
    const [techs, setTechs] = useState<any[]>([]); // New state for techs
    const [mobileLocation, setMobileLocation] = useState<any>(null); // Real-time value from /mobile/location
    const [searchQuery, setSearchQuery] = useState('');
    const [filteredTowers, setFilteredTowers] = useState<any[]>([]);
    const [selectedPosition, setSelectedPosition] = useState<[number, number] | null>(null);

    // Topology State
    const [showLinks, setShowLinks] = useState(true);
    const [showLinkModal, setShowLinkModal] = useState(false);
    const [newLinkData, setNewLinkData] = useState({ source: '', target: '' });

    async function loadData() {
        try {
            const [tData, lData, uData] = await Promise.all([getTowers(), getLinks(), getUsers()]);
            setTowers(tData);
            setLinks(lData);
            // Filter users with valid coordinates
            const techsWithLocation = uData.filter((u: any) => u.last_latitude && u.last_longitude);
            console.log('📍 Técnicos com localização:', techsWithLocation);
            setTechs(techsWithLocation);

            // Fetch Live Mobile Location
            const mobLoc = await getTechLocation();
            if (mobLoc && mobLoc.latitude) {
                setMobileLocation(mobLoc);
            }
        } catch (e) { console.error(e); }
    }

    useEffect(() => {
        loadData();
        const interval = setInterval(() => {
            console.log('🔄 Atualizando mapa automaticamente...');
            loadData();
        }, 30000); // 30 segundos
        return () => clearInterval(interval);
    }, []);

    // Filter towers based on search
    useEffect(() => {
        if (searchQuery.trim() === '') {
            setFilteredTowers([]);
        } else {
            const lower = searchQuery.toLowerCase();
            setFilteredTowers(towers.filter(t => t.name.toLowerCase().includes(lower) || t.ip?.includes(lower)));
        }
    }, [searchQuery, towers]);

    const handleSelectTower = (tower: any) => {
        if (tower.latitude && tower.longitude) {
            setSelectedPosition([tower.latitude, tower.longitude]);
            setSearchQuery(''); // Close dropdown
        }
    };

    const handleAddLink = async () => {
        if (!newLinkData.source || !newLinkData.target || newLinkData.source === newLinkData.target) {
            toast.error("Selecione origem e destino diferentes.");
            return;
        }
        try {
            await createLink({
                source_tower_id: parseInt(newLinkData.source),
                target_tower_id: parseInt(newLinkData.target),
                type: 'wireless'
            });
            setNewLinkData({ source: '', target: '' });
            toast.success("Link criado com sucesso!");
            loadData();
        } catch (e) { toast.error("Erro ao criar link"); }
    };

    const handleDeleteLink = async (id: number) => {
        if (confirm("Remover conexão?")) {
            await deleteLink(id);
            loadData();
        }
    };

    const handleDiscovery = async () => {
        if (!confirm("Isso iniciará uma varredura na rede para detectar links entre torres. Continuar?")) return;
        try {
            toast.loading("Iniciando descoberta...");
            await triggerTopologyDiscovery();
            toast.dismiss();
            toast.success("Varredura iniciada! Aguarde alguns minutos e atualize.");
        } catch (e) {
            toast.dismiss();
            toast.error("Erro ao iniciar descoberta.");
        }
    };

    return (
        <div className="h-full flex flex-col relative">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-white">Mapa em Tempo Real</h2>
                <div className="flex gap-2">
                    <button
                        onClick={handleDiscovery}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white p-2 rounded-lg flex items-center gap-2 text-sm"
                        title="Auto Descobrir Topologia"
                    >
                        <RefreshCcw size={18} />
                        <span className="hidden md:inline">Auto Topologia</span>
                    </button>

                    <button
                        onClick={() => setShowLinks(!showLinks)}
                        className="bg-slate-800 hover:bg-slate-700 text-white p-2 rounded-lg flex items-center gap-2 text-sm"
                        title={showLinks ? "Ocultar Linhas" : "Mostrar Linhas"}
                    >
                        {showLinks ? <Eye size={18} /> : <EyeOff size={18} />}
                        <span className="hidden md:inline">{showLinks ? "Ocultar Conexões" : "Mostrar Conexões"}</span>
                    </button>
                    <button
                        onClick={() => setShowLinkModal(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg flex items-center gap-2 text-sm"
                    >
                        <Network size={18} />
                        <span className="hidden md:inline">Gerenciar Links</span>
                    </button>
                </div>
            </div>

            {/* Search Bar Overlay */}
            <div className="absolute top-20 left-1/2 -translate-x-1/2 z-[1000] w-72">
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Buscar torre..."
                        className="w-full bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-blue-500 shadow-xl"
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                    />
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                </div>
                {/* Search Results Dropdown */}
                {filteredTowers.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                        {filteredTowers.map(tower => (
                            <button
                                key={tower.id}
                                onClick={() => handleSelectTower(tower)}
                                className="w-full text-left px-4 py-2 hover:bg-slate-800 text-white border-b border-slate-800 last:border-0 flex justify-between items-center"
                            >
                                <span>{tower.name}</span>
                                <span className={clsx("text-xs px-2 py-0.5 rounded", tower.is_online ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400")}>
                                    {tower.is_online ? 'ON' : 'OFF'}
                                </span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <div className="flex-1 rounded-xl overflow-hidden border border-slate-800 relative z-0">
                <MapContainer center={[-19.51, -54.04]} zoom={12} style={{ height: '100%', width: '100%' }}>
                    <LayersControl position="topright">
                        <LayersControl.BaseLayer checked name="Mapa (Google)">
                            <TileLayer
                                attribution='&copy; Google'
                                url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
                            />
                        </LayersControl.BaseLayer>

                        <LayersControl.BaseLayer name="Satélite Híbrido (Google)">
                            <TileLayer
                                attribution='&copy; Google'
                                url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
                            />
                        </LayersControl.BaseLayer>

                        <LayersControl.BaseLayer name="OpenStreetMap">
                            <TileLayer
                                attribution='&copy; OpenStreetMap contributors'
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            />
                        </LayersControl.BaseLayer>
                    </LayersControl>

                    <MapController center={selectedPosition} />

                    {/* Render Links */}
                    {showLinks && links.map(link => {
                        const source = towers.find(t => t.id === link.source_tower_id);
                        const target = towers.find(t => t.id === link.target_tower_id);
                        if (source && target && source.latitude && target.latitude) {
                            const isLinkDown = !source.is_online || !target.is_online;
                            return (
                                <Polyline
                                    key={link.id}
                                    positions={[
                                        [source.latitude, source.longitude],
                                        [target.latitude, target.longitude]
                                    ]}
                                    pathOptions={{
                                        color: isLinkDown ? '#f43f5e' : (link.type === 'fiber' ? '#3b82f6' : '#22c55e'),
                                        weight: 4,
                                        opacity: 0.7,
                                        dashArray: link.type === 'wireless' ? '10, 10' : undefined
                                    }}
                                >
                                    <Popup>
                                        <div className="p-1">
                                            <div className="font-bold text-slate-900 border-b pb-1 mb-1 flex items-center gap-2">
                                                <Network size={14} className="text-blue-500" />
                                                Enlace {link.type === 'wireless' ? 'Rádio' : 'Fibra'}
                                            </div>
                                            <div className="text-xs space-y-1">
                                                <div className="flex justify-between gap-4">
                                                    <span className="text-slate-500 font-medium">Origem:</span>
                                                    <span className="text-slate-800 font-bold">{source.name}</span>
                                                </div>
                                                <div className="flex justify-between gap-4">
                                                    <span className="text-slate-500 font-medium">Destino:</span>
                                                    <span className="text-slate-800 font-bold">{target.name}</span>
                                                </div>
                                                {(link.source_equipment_name || link.target_equipment_name) && (
                                                    <div className="bg-slate-50 p-1.5 rounded mt-2 border border-slate-200">
                                                        <div className="text-[10px] text-slate-400 uppercase font-bold mb-1">Equipamentos Detectados</div>
                                                        <div className="text-slate-700 font-medium truncate">
                                                            {link.source_equipment_name || '...'} <span className="text-slate-300">↔</span> {link.target_equipment_name || '...'}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </Popup>
                                </Polyline>
                            );
                        }
                        return null;
                    })}

                    {towers
                        .filter(tower => tower.latitude && tower.longitude)
                        .map(tower => (
                            <Marker
                                key={tower.id}
                                position={[tower.latitude, tower.longitude]}
                                icon={createTowerIcon(tower.name, tower.is_online)}
                            >
                                <Popup>
                                    <strong>{tower.name}</strong><br />
                                    IP: {tower.ip || 'Sem IP'}<br />
                                    Status: {tower.is_online ? "Online" : "Offline"}
                                </Popup>
                            </Marker>
                        ))
                    }

                    {/* Tech Markers */}
                    {techs.map(tech => (
                        <Marker
                            key={`tech-${tech.id}`}
                            position={[tech.last_latitude, tech.last_longitude]}
                            icon={createTechIcon(tech.name)}
                            zIndexOffset={100} // Techs on top
                        >
                            <Popup>
                                <strong>Técnico: {tech.name}</strong><br />
                                Atualizado: {tech.last_location_update ? new Date(tech.last_location_update).toLocaleTimeString() : 'Nunca'}
                            </Popup>
                        </Marker>
                    ))}

                    {/* Mobile App Marker */}
                    {mobileLocation && (
                        <Marker
                            key="mobile-live"
                            position={[mobileLocation.latitude, mobileLocation.longitude]}
                            icon={createTechIcon("Técnico (App)")}
                            zIndexOffset={200}
                        >
                            <Popup>
                                <strong>Técnico (App)</strong><br />
                                Última atualização: {mobileLocation.timestamp ? new Date(mobileLocation.timestamp * 1000).toLocaleTimeString() : 'Recente'}
                            </Popup>
                        </Marker>
                    )}
                </MapContainer>
            </div>

            {/* Link Manager Modal */}
            {showLinkModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[2000] flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg shadow-2xl p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <Network className="text-blue-500" />
                                Gerenciar Topologia
                            </h3>
                            <button onClick={() => setShowLinkModal(false)} className="text-slate-400 hover:text-white">✕</button>
                        </div>

                        {/* Create New Link */}
                        <div className="bg-slate-950 p-4 rounded-lg mb-6 border border-slate-800">
                            <h4 className="text-sm font-bold text-slate-300 mb-3 uppercase">Nova Conexão</h4>
                            <div className="flex gap-2 items-end">
                                <div className="flex-1">
                                    <label className="block text-xs text-slate-500 mb-1">Origem</label>
                                    <select
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
                                        value={newLinkData.source}
                                        onChange={e => setNewLinkData({ ...newLinkData, source: e.target.value })}
                                    >
                                        <option value="">Selecione...</option>
                                        {towers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                                    </select>
                                </div>
                                <div className="flex-1">
                                    <label className="block text-xs text-slate-500 mb-1">Destino</label>
                                    <select
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
                                        value={newLinkData.target}
                                        onChange={e => setNewLinkData({ ...newLinkData, target: e.target.value })}
                                    >
                                        <option value="">Selecione...</option>
                                        {towers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                                    </select>
                                </div>
                                <button
                                    onClick={handleAddLink}
                                    className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg flex items-center justify-center"
                                    title="Adicionar"
                                >
                                    <Plus size={20} />
                                </button>
                            </div>
                        </div>

                        {/* Existing Links List */}
                        <div>
                            <h4 className="text-sm font-bold text-slate-300 mb-3 uppercase">Conexões Atuais ({links.length})</h4>
                            <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
                                {links.length === 0 && <p className="text-slate-500 text-sm text-center py-4">Nenhuma conexão criada.</p>}
                                {links.map(link => {
                                    const source = towers.find(t => t.id === link.source_tower_id);
                                    const target = towers.find(t => t.id === link.target_tower_id);
                                    return (
                                        <div key={link.id} className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg border border-slate-800">
                                            <div className="flex items-center gap-3 text-sm text-slate-300">
                                                <span className="font-medium text-white">{source?.name || '?'}</span>
                                                <span className="text-slate-600">→</span>
                                                <span className="font-medium text-white">{target?.name || '?'}</span>
                                            </div>
                                            <button
                                                onClick={() => handleDeleteLink(link.id)}
                                                className="text-slate-500 hover:text-rose-500 p-1"
                                                title="Remover"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
