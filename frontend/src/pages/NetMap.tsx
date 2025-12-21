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
const greenIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const redIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
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
                <MapContainer center={[-23.550520, -46.633308]} zoom={10} style={{ height: '100%', width: '100%' }}>
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    {towers.map(tower => (
                        <Marker
                            key={tower.id}
                            position={[tower.latitude || 0, tower.longitude || 0]}
                            icon={tower.is_online ? greenIcon : redIcon}
                        >
                            <Popup>
                                <strong>{tower.name}</strong><br />
                                IP: {tower.ip}<br />
                                Status: {tower.is_online ? "Online" : "Offline"}
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
        </div>
    )
}
