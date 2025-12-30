
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, TouchableOpacity, Alert, StatusBar, Image } from 'react-native';
import MapView, { Marker, Callout } from 'react-native-maps';
import * as Location from 'expo-location';
import { RefreshCw, MapPin, Server, Signal, RadioTower, Send } from 'lucide-react-native';
import api from '../../services/api';

export default function MapScreen() {
    const [towers, setTowers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [region, setRegion] = useState(null);
    const [mapType, setMapType] = useState('standard');

    const mapRef = React.useRef(null);
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
                    latitudeDelta: 0.1,
                    longitudeDelta: 0.1,
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

            if (isMounted.current) {
                setTowers(response.data);
                console.log('✅ Torres setadas:', response.data?.length);
            }
        } catch (error) {
            console.error('Fetch Towers Error:', error);
            Alert.alert("Erro de Conexão", "Não foi possível carregar as torres.");
        } finally {
            if (isMounted.current) setLoading(false);
        }
    };

    const sendLocationUpdate = async () => {
        if (!region) return;
        try {
            await api.post('/mobile/location', {
                latitude: region.latitude,
                longitude: region.longitude
            });
            Alert.alert("Sucesso", "Localização enviada para a central! 📍");
        } catch (e) {
            Alert.alert("Erro", "Falha ao enviar localização.");
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
            if (region) {
                coords.push({ latitude: region.latitude, longitude: region.longitude });
            }
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
                <View style={{ flex: 1 }}>
                    <MapView
                        ref={mapRef}
                        style={styles.map}
                        initialRegion={region}
                        showsUserLocation={true}
                        showsMyLocationButton={false}
                        mapType={mapType}
                    >
                        {console.log('🗺️ Render:', towers.length)}
                        {towers.map((tower) => {
                            const lat = parseFloat(tower.latitude);
                            const lon = parseFloat(tower.longitude);
                            if (isNaN(lat) || !tower.latitude) return null;

                            return (
                                <Marker
                                    key={`tower-${tower.id}`}
                                    coordinate={{ latitude: lat, longitude: lon }}
                                    title={tower.name}
                                >
                                    <View style={{
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        paddingBottom: 10, // Espaço para não cortar a sombra/baixo
                                        paddingHorizontal: 10,
                                    }}>
                                        <View style={{
                                            backgroundColor: '#10b981',
                                            width: 44,
                                            height: 44,
                                            borderRadius: 22,
                                            borderWidth: 2,
                                            borderColor: 'white',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            elevation: 6,
                                            shadowColor: '#000',
                                            shadowOffset: { width: 0, height: 2 },
                                            shadowOpacity: 0.3,
                                            shadowRadius: 3,
                                        }}>
                                            <RadioTower size={24} color="white" />
                                        </View>

                                        <View style={{
                                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                            paddingHorizontal: 8,
                                            paddingVertical: 3,
                                            borderRadius: 6,
                                            marginTop: 4,
                                            borderWidth: 1,
                                            borderColor: 'rgba(255,255,255,0.2)',
                                            minWidth: 60,
                                        }}>
                                            <Text style={{
                                                color: 'white',
                                                fontSize: 11,
                                                fontWeight: 'bold',
                                                textAlign: 'center'
                                            }}>
                                                {tower.name}
                                            </Text>
                                        </View>
                                    </View>
                                    <Callout>
                                        <View style={{ padding: 10, minWidth: 150 }}>
                                            <Text style={{ fontWeight: 'bold' }}>{tower.name}</Text>
                                            <Text>Distância: {tower.distance?.toFixed(2)} km</Text>
                                            <Text style={{ fontSize: 10, color: 'gray' }}>Lat: {lat.toFixed(4)}, Lon: {lon.toFixed(4)}</Text>
                                        </View>
                                    </Callout>
                                </Marker>
                            );
                        })}
                    </MapView>

                    {/* Satellite Toggle Button */}
                    <TouchableOpacity
                        style={[styles.fab, styles.satFab]}
                        onPress={toggleMapType}
                        activeOpacity={0.8}
                    >
                        <MapPin color="#fff" size={24} />
                    </TouchableOpacity>

                    {/* Check-in Button */}
                    <TouchableOpacity
                        style={[styles.fab, { bottom: 168, backgroundColor: '#10b981' }]}
                        onPress={sendLocationUpdate}
                        activeOpacity={0.8}
                    >
                        <Send color="#fff" size={24} />
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
            ) : (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#60a5fa" />
                    <Text style={styles.loadingText}>Carregando Mapa...</Text>
                </View>
            )}
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
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 4,
    },
    satFab: {
        bottom: 96,
        backgroundColor: '#475569'
    }
});
