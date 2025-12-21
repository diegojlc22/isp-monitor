import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { useEffect, useState } from 'react';
import { getTowers } from '../services/api';
import L from 'leaflet';
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

export function NetMap() {
    const [towers, setTowers] = useState<any[]>([]);

    useEffect(() => {
        getTowers().then(setTowers).catch(console.error);
        const interval = setInterval(() => getTowers().then(setTowers), 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="h-full flex flex-col">
            <h2 className="text-2xl font-bold mb-4 text-white">Mapa em Tempo Real</h2>
            <div className="flex-1 rounded-xl overflow-hidden border border-slate-800 relative z-0">
                <MapContainer center={[-19.51, -54.04]} zoom={6} style={{ height: '100%', width: '100%' }}>
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
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
