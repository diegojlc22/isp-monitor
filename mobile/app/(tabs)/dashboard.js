
import React, { useEffect, useState, useRef } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, StatusBar } from 'react-native';
import { Link, useRouter } from 'expo-router';
import * as Location from 'expo-location';
import { RefreshCw, Plus, Signal, Server, MapPin, LogOut } from 'lucide-react-native';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export default function TechDashboard() {
    const router = useRouter();
    const { signOut, user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [towers, setTowers] = useState([]);
    const [location, setLocation] = useState(null);
    const [errorMsg, setErrorMsg] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);
    const [isSendingLocation, setIsSendingLocation] = useState(false);

    const locationSubscription = useRef(null);
    const lastSentLocation = useRef(null);

    useEffect(() => {
        startLocationTracking();
        return () => {
            // Cleanup ao desmontar
            if (locationSubscription.current) {
                locationSubscription.current.remove();
            }
        };
    }, []);

    const startLocationTracking = async () => {
        try {
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                setErrorMsg('Permissão de localização negada. Ative nas configurações.');
                return;
            }

            // Obter localização inicial
            const initialLocation = await Location.getCurrentPositionAsync({
                accuracy: Location.Accuracy.Balanced // Economia de bateria
            });

            handleLocationUpdate(initialLocation);

            // Monitorar mudanças de localização (GPS inteligente)
            locationSubscription.current = await Location.watchPositionAsync(
                {
                    accuracy: Location.Accuracy.Balanced,
                    timeInterval: 30000, // Verificar a cada 30s
                    distanceInterval: 50 // Só atualizar se mover 50m
                },
                (newLocation) => {
                    handleLocationUpdate(newLocation);
                }
            );

        } catch (e) {
            setErrorMsg('Erro ao obter GPS: ' + e.message);
        }
    };

    const handleLocationUpdate = async (newLocation) => {
        const coords = newLocation.coords;
        setLocation(coords);

        // Verificar se houve mudança significativa
        if (shouldSendLocation(coords)) {
            await sendLocationToBackend(coords);
            lastSentLocation.current = coords;
        }

        // Buscar torres próximas (só na primeira vez ou a cada 5 minutos)
        if (!towers.length || shouldRefreshTowers()) {
            fetchNearbyTowers(coords);
        }
    };

    const shouldSendLocation = (coords) => {
        if (!lastSentLocation.current) return true;

        // Calcular distância desde o último envio
        const distance = getDistanceFromLatLonInMeters(
            lastSentLocation.current.latitude,
            lastSentLocation.current.longitude,
            coords.latitude,
            coords.longitude
        );

        return distance > 50; // Só enviar se moveu mais de 50m
    };

    const shouldRefreshTowers = () => {
        if (!lastUpdate) return true;
        const fiveMinutes = 5 * 60 * 1000;
        return (Date.now() - lastUpdate) > fiveMinutes;
    };

    const getDistanceFromLatLonInMeters = (lat1, lon1, lat2, lon2) => {
        const R = 6371000; // Raio da Terra em metros
        const dLat = deg2rad(lat2 - lat1);
        const dLon = deg2rad(lon2 - lon1);
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    };

    const deg2rad = (deg) => deg * (Math.PI / 180);

    const sendLocationToBackend = async (coords) => {
        setIsSendingLocation(true);
        try {
            await api.post('/mobile/location', {
                latitude: coords.latitude,
                longitude: coords.longitude
            });
            console.log("📍 Localização enviada:", coords.latitude, coords.longitude);
            setLastUpdate(Date.now());
        } catch (error) {
            console.log("Falha ao enviar localização:", error);
            // Retry silencioso após 5s
            setTimeout(() => sendLocationToBackend(coords), 5000);
        } finally {
            setIsSendingLocation(false);
        }
    };

    const fetchNearbyTowers = async (coords) => {
        setLoading(true);
        try {
            const response = await api.post('/mobile/nearby-towers', {
                latitude: coords.latitude,
                longitude: coords.longitude
            });
            setTowers(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleManualRefresh = async () => {
        if (!location) {
            Alert.alert("Aguarde", "Obtendo localização...");
            return;
        }

        setLoading(true);
        await sendLocationToBackend(location);
        await fetchNearbyTowers(location);
        setLoading(false);
        Alert.alert("Sucesso", "Dados atualizados!");
    };

    const renderTower = ({ item }) => (
        <View style={styles.card}>
            <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>{item.name}</Text>
                <View style={styles.badge}>
                    <Text style={styles.badgeText}>{item.distance_km} km</Text>
                </View>
            </View>

            <View style={styles.statsRow}>
                <View style={styles.stat}>
                    <Server size={18} color="#89b4fa" />
                    <Text style={styles.statText}>{item.panel_count} Painéis</Text>
                </View>
                <View style={styles.stat}>
                    <Signal size={18} color="#a6e3a1" />
                    <Text style={styles.statText}>{item.total_clients} Clientes</Text>
                </View>
            </View>

            <Text style={styles.ipText}>IP: {item.ip || "N/A"}</Text>
        </View>
    );

    const formatLastUpdate = () => {
        if (!lastUpdate) return "Nunca";
        const seconds = Math.floor((Date.now() - lastUpdate) / 1000);
        if (seconds < 60) return `${seconds}s atrás`;
        const minutes = Math.floor(seconds / 60);
        return `${minutes}min atrás`;
    };

    return (
        <View style={styles.container}>
            <StatusBar barStyle="light-content" backgroundColor="#0f172a" />

            {/* Header Info */}
            <View style={styles.headerInfo}>
                <View>
                    <Text style={styles.welcome}>Olá, {user?.name || 'Técnico'}</Text>
                    <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }}>
                        <MapPin size={14} color={isSendingLocation ? "#f9e2af" : "#a6e3a1"} />
                        <Text style={styles.coords}>
                            {location ? `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}` : "Obtendo GPS..."}
                        </Text>
                    </View>
                    <Text style={styles.updateText}>Última atualização: {formatLastUpdate()}</Text>
                </View>

                <View style={{ flexDirection: 'row', gap: 16 }}>
                    <TouchableOpacity onPress={handleManualRefresh} disabled={loading}>
                        {loading ? (
                            <ActivityIndicator size={24} color="#60a5fa" />
                        ) : (
                            <RefreshCw size={24} color="#60a5fa" />
                        )}
                    </TouchableOpacity>
                    <TouchableOpacity onPress={signOut}>
                        <LogOut size={24} color="#f87171" />
                    </TouchableOpacity>
                </View>
            </View>

            {/* Conteúdo */}
            {errorMsg ? (
                <View style={styles.center}>
                    <Text style={styles.errorText}>{errorMsg}</Text>
                    <TouchableOpacity style={styles.retryBtn} onPress={startLocationTracking}>
                        <Text style={styles.btnText}>Tentar Novamente</Text>
                    </TouchableOpacity>
                </View>
            ) : (
                <FlatList
                    data={towers}
                    keyExtractor={(item) => item.id.toString()}
                    renderItem={renderTower}
                    contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
                    ListEmptyComponent={
                        loading ? (
                            <View style={styles.center}>
                                <ActivityIndicator size="large" color="#60a5fa" />
                                <Text style={styles.loadingText}>Procurando torres...</Text>
                            </View>
                        ) : (
                            <Text style={styles.emptyText}>Nenhuma torre encontrada num raio próximo.</Text>
                        )
                    }
                />
            )}

            {/* FAB (Botão Flutuante) */}
            <Link href="/add-tower" asChild>
                <TouchableOpacity style={styles.fab}>
                    <Plus size={32} color="#fff" />
                </TouchableOpacity>
            </Link>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#0f172a' },
    center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },

    headerInfo: {
        flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
        padding: 20, paddingTop: 40, backgroundColor: '#1e293b',
        borderBottomWidth: 1, borderBottomColor: '#334155'
    },
    welcome: { color: '#f8fafc', fontSize: 18, fontWeight: 'bold' },
    coords: { color: '#94a3b8', marginLeft: 6, fontFamily: 'monospace', fontSize: 12 },
    updateText: { color: '#64748b', fontSize: 10, marginTop: 2 },

    card: {
        backgroundColor: '#1e293b',
        borderRadius: 16,
        padding: 16,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: '#334155',
        shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.2, elevation: 2
    },
    cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
    cardTitle: { color: '#f8fafc', fontSize: 18, fontWeight: 'bold' },
    badge: { backgroundColor: 'rgba(96, 165, 250, 0.1)', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20, borderWidth: 1, borderColor: 'rgba(96, 165, 250, 0.2)' },
    badgeText: { color: '#60a5fa', fontSize: 12, fontWeight: '700' },

    statsRow: { flexDirection: 'row', gap: 20, marginBottom: 12 },
    stat: { flexDirection: 'row', alignItems: 'center', gap: 6 },
    statText: { color: '#cbd5e1', fontSize: 14 },

    ipText: { color: '#64748b', fontSize: 12, marginTop: 4, fontFamily: 'monospace' },

    loadingText: { color: '#94a3b8', marginTop: 12 },
    errorText: { color: '#f87171', textAlign: 'center', marginBottom: 20 },
    emptyText: { color: '#64748b', textAlign: 'center', marginTop: 40 },

    retryBtn: { backgroundColor: '#334155', padding: 12, borderRadius: 8 },
    btnText: { color: '#f8fafc' },

    fab: {
        position: 'absolute',
        bottom: 24,
        right: 24,
        width: 64,
        height: 64,
        borderRadius: 32,
        backgroundColor: '#2563eb',
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 8,
        shadowColor: '#2563eb',
        shadowOpacity: 0.4,
        shadowOffset: { width: 0, height: 4 }
    }
});
