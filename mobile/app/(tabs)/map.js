
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, TouchableOpacity, Alert, StatusBar } from 'react-native';
import MapView, { Marker, Callout } from 'react-native-maps';
import * as Location from 'expo-location';
import { RefreshCw, MapPin, Server, Signal } from 'lucide-react-native';
import api from '../../services/api';

export default function MapScreen() {
    const [towers, setTowers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [region, setRegion] = useState(null);
    const [mapType, setMapType] = useState('standard');

    // Ref para garantir que não atualizaremos estado em componente desmontado
    const isMounted = React.useRef(true);

    useEffect(() => {
        isMounted.current = true;
        getCurrentLocation();

        return () => {
            isMounted.current = false;
        };
    }, []);

    const getCurrentLocation = async () => {
        if (!isMounted.current) return;
        setLoading(true);
        try {
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert("Erro", "Permissão de localização negada");
                if (isMounted.current) setLoading(false);
                return;
            }

            let location = await Location.getCurrentPositionAsync({});
            const { latitude, longitude } = location.coords;

            if (isMounted.current) {
                setRegion({
                    latitude,
                    longitude,
                    latitudeDelta: 0.05,
                    longitudeDelta: 0.05,
                });

                fetchTowers(latitude, longitude);
            }

        } catch (error) {
            Alert.alert("Erro", "Não foi possível obter localização");
            if (isMounted.current) setLoading(false);
        }
    };

    const fetchTowers = async (lat, lon) => {
        try {
            const response = await api.post('/mobile/nearby-towers', {
                latitude: lat,
                longitude: lon
            });
            if (isMounted.current) setTowers(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            if (isMounted.current) setLoading(false);
        }
    };

    const toggleMapType = () => {
        setMapType(current => current === 'standard' ? 'hybrid' : 'standard');
    };

    return (
        <View style={styles.container}>
            <StatusBar barStyle={mapType === 'hybrid' ? 'light-content' : 'dark-content'} translucent backgroundColor="transparent" />

            {region ? (
                <MapView
                    style={styles.map}
                    initialRegion={region}
                    showsUserLocation={true}
                    showsMyLocationButton={false}
                    loadingEnabled={false}
                    userInterfaceStyle="dark"
                    mapType={mapType}
                >
                    {towers.map((tower) => {
                        if (!tower.latitude || !tower.longitude) return null;

                        return (
                            <Marker
                                key={tower.id}
                                coordinate={{ latitude: parseFloat(tower.latitude), longitude: parseFloat(tower.longitude) }}
                                tracksViewChanges={false} // OTIMIZAÇÃO CRÍTICA PARA CPU
                            >
                                <View style={styles.markerContainer}>
                                    <View style={styles.markerIcon}>
                                        <Server size={20} color="#fff" />
                                    </View>
                                    <View style={styles.markerArrow} />
                                </View>

                                <Callout tooltip>
                                    <View style={styles.calloutContainer}>
                                        <Text style={styles.calloutTitle}>{tower.name}</Text>
                                        <View style={styles.calloutDivider} />

                                        <View style={styles.calloutRow}>
                                            <MapPin size={12} color="#60a5fa" />
                                            <Text style={styles.calloutText}>{tower.distance_km} km</Text>
                                        </View>

                                        <View style={styles.calloutRow}>
                                            <Signal size={12} color="#a6e3a1" />
                                            <Text style={styles.calloutText}>{tower.total_clients} Clientes</Text>
                                        </View>

                                        <View style={styles.calloutRow}>
                                            <Server size={12} color="#89b4fa" />
                                            <Text style={styles.calloutText}>{tower.panel_count} Painéis</Text>
                                        </View>
                                    </View>
                                </Callout>
                            </Marker>
                        );
                    })}
                </MapView>
            ) : (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#60a5fa" />
                    <Text style={styles.loadingText}>Carregando Mapa...</Text>
                </View>
            )}

            {/* Satellite Toggle Button */}
            <TouchableOpacity
                style={[styles.fab, styles.satFab]}
                onPress={toggleMapType}
                activeOpacity={0.8}
            >
                <MapPin color="#fff" size={24} />
            </TouchableOpacity>

            {/* Refresh Button */}
            <TouchableOpacity
                style={styles.fab}
                onPress={getCurrentLocation}
                disabled={loading}
                activeOpacity={0.8}
            >
                {loading ? <ActivityIndicator color="#fff" /> : <RefreshCw color="#fff" size={24} />}
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
    },
    map: {
        width: '100%',
        height: '100%',
    },

    // Custom Marker
    markerContainer: {
        alignItems: 'center',
        justifyContent: 'center',
        width: 40,
        height: 50,
    },
    markerIcon: {
        backgroundColor: '#2563eb',
        width: 36,
        height: 36,
        borderRadius: 18,
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 2,
        borderColor: '#fff',
        shadowColor: "#000", shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.25, elevation: 5
    },
    markerArrow: {
        width: 0,
        height: 0,
        backgroundColor: 'transparent',
        borderStyle: 'solid',
        borderLeftWidth: 6,
        borderRightWidth: 6,
        borderBottomWidth: 0,
        borderTopWidth: 8,
        borderLeftColor: 'transparent',
        borderRightColor: 'transparent',
        borderTopColor: '#2563eb', // Arrow pointing down
        marginTop: -1,
        shadowColor: "#000", shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, elevation: 1
    },

    // Custom Callout
    calloutContainer: {
        backgroundColor: '#1e293b',
        borderRadius: 12,
        padding: 12,
        width: 180,
        borderWidth: 1,
        borderColor: '#334155',
        shadowColor: "#000", shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.3, elevation: 5
    },
    calloutTitle: {
        color: '#f8fafc',
        fontWeight: 'bold',
        fontSize: 14,
        marginBottom: 8,
        textAlign: 'center'
    },
    calloutDivider: {
        height: 1,
        backgroundColor: '#334155',
        marginBottom: 8
    },
    calloutRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
        marginBottom: 4
    },
    calloutText: {
        color: '#cbd5e1',
        fontSize: 12
    },

    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#0f172a'
    },
    loadingText: {
        color: '#94a3b8',
        marginTop: 16,
        fontSize: 16
    },
    fab: {
        position: 'absolute',
        bottom: 24,
        right: 24,
        backgroundColor: '#2563eb',
        width: 56,
        height: 56,
        borderRadius: 28,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 8,
        shadowColor: '#2563eb',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.4,
        shadowRadius: 8,
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.1)'
    },
    satFab: {
        bottom: 96, // Positioned above the refresh button
        backgroundColor: '#475569'
    }
});
