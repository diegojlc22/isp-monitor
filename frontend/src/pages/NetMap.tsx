import { MapContainer, TileLayer, Marker, Popup, LayersControl, useMap } from 'react-leaflet';
import { useEffect, useState } from 'react';
import { getTowers } from '../services/api';
import L from 'leaflet';
import { Search } from 'lucide-react';
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
    const [searchQuery, setSearchQuery] = useState('');
    const [filteredTowers, setFilteredTowers] = useState<any[]>([]);
    const [selectedPosition, setSelectedPosition] = useState<[number, number] | null>(null);

    useEffect(() => {
        getTowers().then(setTowers).catch(console.error);
        const interval = setInterval(() => getTowers().then(setTowers), 30000);
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

    return (
        <div className="h-full flex flex-col relative">
            <h2 className="text-2xl font-bold mb-4 text-white">Mapa em Tempo Real</h2>

            {/* Search Bar Overlay */}
            <div className="absolute top-4 left-16 z-[1000] w-72">
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
                <MapContainer center={[-19.51, -54.04]} zoom={6} style={{ height: '100%', width: '100%' }}>
                    <LayersControl position="topright">
                        <LayersControl.BaseLayer checked name="OpenStreetMap (Padrão)">
                            <TileLayer
                                attribution='&copy; OpenStreetMap contributors'
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            />
                        </LayersControl.BaseLayer>

                        <LayersControl.BaseLayer name="Satélite (Esri)">
                            <TileLayer
                                attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                            />
                        </LayersControl.BaseLayer>

                        <LayersControl.BaseLayer name="Relevo (OpenTopoMap)">
                            <TileLayer
                                attribution='Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)'
                                url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                            />
                        </LayersControl.BaseLayer>
                    </LayersControl>

                    <MapController center={selectedPosition} />

                    {towers.map(tower => (
                        <Marker
                            key={tower.id}
                            position={[tower.latitude || 0, tower.longitude || 0]}
                            icon={createTowerIcon(tower.name, tower.is_online)}
                        >
                            <Popup>
                                <strong>{tower.name}</strong><br />
                                IP: {tower.ip || 'Sem IP'}<br />
                                Status: {tower.is_online ? "Online" : "Offline"}
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
        </div>
    )
}
