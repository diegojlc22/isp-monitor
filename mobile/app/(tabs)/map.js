
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, TouchableOpacity, Alert } from 'react-native';
import MapView, { Marker, Callout } from 'react-native-maps';
import * as Location from 'expo-location';
import { RefreshCw, MapPin } from 'lucide-react-native';
import api from '../../services/api';

export default function MapScreen() {
    const [towers, setTowers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [region, setRegion] = useState(null);

    useEffect(() => {
        getCurrentLocation();
    }, []);

    const getCurrentLocation = async () => {
        setLoading(true);
        try {
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert("Erro", "Permissão de localização negada");
                setLoading(false);
                return;
            }

            let location = await Location.getCurrentPositionAsync({});
            const { latitude, longitude } = location.coords;

            setRegion({
                latitude,
                longitude,
                latitudeDelta: 0.05,
                longitudeDelta: 0.05,
            });

            fetchTowers(latitude, longitude);

        } catch (error) {
            Alert.alert("Erro", "Não foi possível obter localização");
            setLoading(false);
        }
    };

    const fetchTowers = async (lat, lon) => {
        try {
            const response = await api.post('/mobile/nearby-towers', {
                latitude: lat,
                longitude: lon
            });
            setTowers(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            {region ? (
                <MapView
                    style={styles.map}
                    initialRegion={region}
                    showsUserLocation={true}
                    showsMyLocationButton={false}
                    loadingEnabled={true}
                >
                    {towers.map((tower) => {
                        if (!tower.latitude || !tower.longitude) return null;

                        return (
                            <Marker
                                key={tower.id}
                                coordinate={{ latitude: parseFloat(tower.latitude), longitude: parseFloat(tower.longitude) }}
                                title={tower.name}
                                description={`IP: ${tower.ip || 'N/A'}`}
                                pinColor="red"
                            >
                                <Callout>
                                    <View style={styles.callout}>
                                        <Text style={styles.calloutTitle}>{tower.name}</Text>
                                        <Text>Dist: {tower.distance_km}km</Text>
                                        <Text>Painéis: {tower.panel_count}</Text>
                                        <Text>Clientes: {tower.total_clients}</Text>
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

            {/* Floating Refresh Button */}
            <TouchableOpacity
                style={styles.fab}
                onPress={getCurrentLocation}
                disabled={loading}
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
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        color: '#94a3b8',
        marginTop: 10,
    },
    fab: {
        position: 'absolute',
        bottom: 20,
        right: 20,
        backgroundColor: '#2563eb',
        width: 56,
        height: 56,
        borderRadius: 28,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 5,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.3,
        shadowRadius: 3,
    },
    callout: {
        width: 150,
        padding: 5,
    },
    calloutTitle: {
        fontWeight: 'bold',
        marginBottom: 4,
    }
});
