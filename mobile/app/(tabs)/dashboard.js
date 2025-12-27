
import React, { useEffect, useState, useRef } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, StatusBar, RefreshControl, Linking } from 'react-native';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';
import { RefreshCw, Plus, Signal, Server, MapPin, LogOut, Settings, Navigation, Wifi } from 'lucide-react-native';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export default function TechDashboard() {
    const router = useRouter();
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [towers, setTowers] = useState([]);
    const [location, setLocation] = useState(null);
    const [errorMsg, setErrorMsg] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);
    const [isSendingLocation, setIsSendingLocation] = useState(false);

    const isMounted = useRef(true);
    const retryTimeout = useRef(null);

    const locationSubscription = useRef(null);
    const lastSentLocation = useRef(null);

    useEffect(() => {
        isMounted.current = true;

        startLocationTracking();

        return () => {
            isMounted.current = false;
            if (locationSubscription.current) {
                locationSubscription.current.remove();
            }
            if (retryTimeout.current) {
                clearTimeout(retryTimeout.current);
            }
        };
    }, []);

    const startLocationTracking = async () => {
        try {
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (!isMounted.current) return;

            if (status !== 'granted') {
                setErrorMsg('Permissão de localização negada.');
                return;
            }

            const initialLocation = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
            if (isMounted.current) handleLocationUpdate(initialLocation);

            locationSubscription.current = await Location.watchPositionAsync(
                { accuracy: Location.Accuracy.Balanced, timeInterval: 30000, distanceInterval: 50 },
                (newLocation) => {
                    if (isMounted.current) handleLocationUpdate(newLocation);
                }
            );

        } catch (e) {
            if (isMounted.current) setErrorMsg('Erro GPS: ' + e.message);
        }
    };

    const handleLocationUpdate = async (newLocation) => {
        const coords = newLocation.coords;
        setLocation(coords);
        if (shouldSendLocation(coords)) {
            await sendLocationToBackend(coords);
            lastSentLocation.current = coords;
        }
        if (!towers.length || shouldRefreshTowers()) {
            fetchNearbyTowers(coords);
        }
    };

    const shouldSendLocation = (coords) => {
        if (!lastSentLocation.current) return true;
        const distance = getDistanceFromLatLonInMeters(
            lastSentLocation.current.latitude, lastSentLocation.current.longitude,
            coords.latitude, coords.longitude
        );
        return distance > 50;
    };

    const shouldRefreshTowers = () => {
        if (!lastUpdate) return true;
        return (Date.now() - lastUpdate) > (5 * 60 * 1000);
    };

    const getDistanceFromLatLonInMeters = (lat1, lon1, lat2, lon2) => {
        const R = 6371000;
        const dLat = deg2rad(lat2 - lat1);
        const dLon = deg2rad(lon2 - lon1);
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    };

    const deg2rad = (deg) => deg * (Math.PI / 180);

    const sendLocationToBackend = async (coords) => {
        if (!isMounted.current) return;
        setIsSendingLocation(true);
        try {
            await api.post('/mobile/location', {
                latitude: coords.latitude,
                longitude: coords.longitude
            });
            if (isMounted.current) setLastUpdate(Date.now());
        } catch (error) {
            console.log("Falha Location:", error);
            // Retry seguro
            if (isMounted.current) {
                retryTimeout.current = setTimeout(() => sendLocationToBackend(coords), 5000);
            }
        } finally {
            if (isMounted.current) setIsSendingLocation(false);
        }
    };

    const fetchNearbyTowers = async (coords) => {
        if (!isMounted.current) return;
        setLoading(true);
        try {
            const response = await api.post('/mobile/nearby-towers', {
                latitude: coords.latitude,
                longitude: coords.longitude
            });
            if (isMounted.current) setTowers(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            if (isMounted.current) {
                setLoading(false);
                setRefreshing(false);
            }
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        if (location) {
            await sendLocationToBackend(location);
            await fetchNearbyTowers(location);
        } else {
            setRefreshing(false);
        }
    };

    const openMaps = (lat, lon) => {
        const scheme = Platform.OS === 'ios' ? 'maps:' : 'geo:';
        const url = `${scheme}${lat},${lon}?q=${lat},${lon}`;
        Linking.openURL(url);
    };

    const formatLastUpdate = () => {
        if (!lastUpdate) return "Nunca";
        const seconds = Math.floor((Date.now() - lastUpdate) / 1000);
        if (seconds < 60) return "Agora mesmo";
        const minutes = Math.floor(seconds / 60);
        return `${minutes} min atrás`;
    };

    const renderTower = ({ item }) => (
        <View style={styles.card}>
            <View style={styles.cardHeader}>
                <View>
                    <Text style={styles.cardTitle}>{item.name}</Text>
                    <View style={styles.inlineInfo}>
                        <Wifi size={14} color="#64748b" />
                        <Text style={styles.ipText}>{item.ip || "Sem IP"}</Text>
                    </View>
                </View>
                <View style={styles.distanceBadge}>
                    <MapPin size={12} color="#60a5fa" />
                    <Text style={styles.distanceText}>{item.distance_km} km</Text>
                </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.statsContainer}>
                <View style={styles.statItem}>
                    <View style={[styles.iconBg, { backgroundColor: 'rgba(137, 180, 250, 0.1)' }]}>
                        <Server size={18} color="#89b4fa" />
                    </View>
                    <View>
                        <Text style={styles.statLabel}>Equipamentos</Text>
                        <Text style={styles.statValue}>{item.panel_count}</Text>
                    </View>
                </View>

                <View style={styles.statItem}>
                    <View style={[styles.iconBg, { backgroundColor: 'rgba(166, 227, 161, 0.1)' }]}>
                        <Signal size={18} color="#a6e3a1" />
                    </View>
                    <View>
                        <Text style={styles.statLabel}>Clientes</Text>
                        <Text style={styles.statValue}>{item.total_clients}</Text>
                    </View>
                </View>

                <TouchableOpacity
                    style={styles.navButton}
                    onPress={() => item.latitude && openMaps(item.latitude, item.longitude)}
                >
                    <Navigation size={20} color="#f8fafc" />
                </TouchableOpacity>
            </View>
        </View>
    );

    return (
        <View style={styles.container}>
            <StatusBar barStyle="light-content" backgroundColor="#0f172a" />

            {/* Modern Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.greeting}>Olá, <Text style={styles.userName}>{user?.name?.split(' ')[0] || 'Técnico'}</Text></Text>
                    <View style={styles.statusRow}>
                        <View style={[styles.statusDot, { backgroundColor: isSendingLocation ? '#f9e2af' : '#a6e3a1' }]} />
                        <Text style={styles.statusText}>
                            {location ? "GPS Ativo" : "Buscando GPS..."} • {formatLastUpdate()}
                        </Text>
                    </View>
                </View>

                <TouchableOpacity
                    style={styles.settingsBtn}
                    onPress={() => router.push('/settings')}
                >
                    <Settings size={24} color="#94a3b8" />
                </TouchableOpacity>
            </View>

            {/* Lista Principal */}
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
                    contentContainerStyle={styles.listContent}
                    showsVerticalScrollIndicator={false}
                    initialNumToRender={5}
                    maxToRenderPerBatch={5}
                    windowSize={5}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#60a5fa" />
                    }
                    ListHeaderComponent={
                        <Text style={styles.sectionHeader}>Torres Próximas</Text>
                    }
                    ListEmptyComponent={
                        loading ? (
                            <View style={styles.centerLoading}>
                                <ActivityIndicator size="large" color="#60a5fa" />
                                <Text style={styles.loadingText}>Escaneando perímetro...</Text>
                            </View>
                        ) : (
                            <View style={styles.emptyContainer}>
                                <MapPin size={48} color="#334155" />
                                <Text style={styles.emptyText}>Nenhuma torre encontrada num raio próximo.</Text>
                            </View>
                        )
                    }
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#0f172a' },

    header: {
        paddingHorizontal: 24,
        paddingTop: 60,
        paddingBottom: 24,
        backgroundColor: '#0f172a',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#1e293b'
    },
    greeting: { color: '#94a3b8', fontSize: 16 },
    userName: { color: '#f8fafc', fontWeight: 'bold', fontSize: 20 },
    statusRow: { flexDirection: 'row', alignItems: 'center', marginTop: 4 },
    statusDot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
    statusText: { color: '#64748b', fontSize: 12 },

    settingsBtn: {
        width: 44, height: 44, borderRadius: 22,
        backgroundColor: '#1e293b', justifyContent: 'center', alignItems: 'center',
        borderWidth: 1, borderColor: '#334155'
    },

    listContent: { padding: 24, paddingBottom: 100 },
    sectionHeader: { color: '#f8fafc', fontSize: 18, fontWeight: 'bold', marginBottom: 16 },

    card: {
        backgroundColor: '#1e293b',
        borderRadius: 20,
        padding: 20,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: '#334155',
        shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 4
    },
    cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
    cardTitle: { color: '#f8fafc', fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
    inlineInfo: { flexDirection: 'row', alignItems: 'center', gap: 6 },
    ipText: { color: '#64748b', fontSize: 12, fontFamily: 'monospace' },

    distanceBadge: {
        flexDirection: 'row', alignItems: 'center', gap: 4,
        backgroundColor: 'rgba(96, 165, 250, 0.1)', paddingHorizontal: 10, paddingVertical: 6,
        borderRadius: 12, borderWidth: 1, borderColor: 'rgba(96, 165, 250, 0.2)'
    },
    distanceText: { color: '#60a5fa', fontSize: 12, fontWeight: '700' },

    divider: { height: 1, backgroundColor: '#334155', marginVertical: 16 },

    statsContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    statItem: { flexDirection: 'row', alignItems: 'center', gap: 12 },
    iconBg: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
    statLabel: { color: '#64748b', fontSize: 10, textTransform: 'uppercase', fontWeight: 'bold' },
    statValue: { color: '#cbd5e1', fontSize: 14, fontWeight: '600' },

    navButton: {
        width: 40, height: 40, borderRadius: 20,
        backgroundColor: '#3b82f6', justifyContent: 'center', alignItems: 'center',
        shadowColor: '#3b82f6', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.4, elevation: 4
    },

    center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
    centerLoading: { alignItems: 'center', paddingVertical: 40 },
    loadingText: { color: '#64748b', marginTop: 12 },
    emptyContainer: { alignItems: 'center', marginTop: 40, opacity: 0.5 },
    emptyText: { color: '#64748b', marginTop: 16, width: 200, textAlign: 'center' },

    errorText: { color: '#f87171', textAlign: 'center', marginBottom: 20 },
    retryBtn: { backgroundColor: '#334155', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 8 },
    btnText: { color: '#f8fafc', fontWeight: 'bold' }
});
