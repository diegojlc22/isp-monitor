
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, TouchableOpacity, Alert, StatusBar, Image } from 'react-native';
import MapView, { Marker, Callout } from 'react-native-maps';
import * as Location from 'expo-location';
import { RefreshCw, MapPin, Server, Signal, RadioTower } from 'lucide-react-native';
import api from '../../services/api';

export default function MapScreen() {
    const [towers, setTowers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [region, setRegion] = useState(null);
    const [mapType, setMapType] = useState('standard');

    const mapRef = React.useRef(null);
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
            console.log('Fetching towers for:', lat, lon);
            const response = await api.post('/mobile/nearby-towers', {
                latitude: lat,
                longitude: lon
            });
            console.log('Towers response:', response.data?.length);
            if (isMounted.current) setTowers(response.data);
        } catch (error) {
            console.error('Fetch Towers Error:', error);
            if (error.response) {
                console.error('Data:', error.response.data);
                console.error('Status:', error.response.status);
            }
        } finally {
            if (isMounted.current) setLoading(false);
        }
    };

    const toggleMapType = () => {
        setMapType(current => current === 'standard' ? 'hybrid' : 'standard');
    };

    // Zoom automático para mostrar todas as torres e o usuário
    useEffect(() => {
        if (towers.length > 0 && mapRef.current) {
            const coords = towers.map(t => ({
                latitude: parseFloat(t.latitude),
                longitude: parseFloat(t.longitude)
            }));

            // Adiciona a localização do usuário (se houver)
            if (region) {
                coords.push({ latitude: region.latitude, longitude: region.longitude });
            }

            // Pequeno delay para garantir que o mapa carregou
            setTimeout(() => {
                mapRef.current?.fitToCoordinates(coords, {
                    edgePadding: { top: 50, right: 50, bottom: 50, left: 50 },
                    animated: true,
                });
            }, 1000);
        }
    }, [towers, region]);

    return (
        <View style={styles.container}>
            <StatusBar barStyle={mapType === 'hybrid' ? 'light-content' : 'dark-content'} translucent backgroundColor="transparent" />

            {region ? (
                <MapView
                    ref={mapRef}
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
                                tracksViewChanges={true}
                            >
                                <View
                                    collapsable={false}
                                    style={{
                                        width: 120,
                                        height: 120,
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        backgroundColor: 'rgba(255, 255, 255, 0.001)' // Magic hack for Android
                                    }}
                                >
                                    {/* Circle */}
                                    <View style={{
                                        backgroundColor: '#10b981',
                                        width: 48,
                                        height: 48,
                                        borderRadius: 24,
                                        borderWidth: 2,
                                        borderColor: 'white',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        marginBottom: 4,
                                        elevation: 5 // Try elevation on inner only
                                    }}>
                                        <RadioTower size={24} color="white" />
                                    </View>

                                    {/* Label */}
                                    <View style={{
                                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                        borderRadius: 4,
                                        paddingHorizontal: 8,
                                        paddingVertical: 4,
                                    }}>
                                        <Text style={{
                                            color: '#cbd5e1',
                                            fontSize: 10,
                                            fontWeight: 'bold',
                                            textAlign: 'center'
                                        }}>
                                            {tower.name}
                                        </Text>
                                    </View>
                                </View>
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
    markerWrapper: {
        alignItems: 'center',
        justifyContent: 'center',
    },
    markerContainer: {
        alignItems: 'center',
        justifyContent: 'center',
        width: 40,
        height: 50,
        zIndex: 2,
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
    shadowLabel: {
        backgroundColor: 'rgba(15, 23, 42, 0.8)',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 8,
        marginTop: 4,
        zIndex: 1,
    },
    labelText: {
        color: '#f8fafc',
        fontSize: 10,
        fontWeight: 'bold',
        textAlign: 'center',
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
