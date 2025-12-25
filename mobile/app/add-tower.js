
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';
import { Save, MapPin, X } from 'lucide-react-native';
import api from '../services/api';

export default function AddTowerScreen() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [gpsLoading, setGpsLoading] = useState(true);

    const [form, setForm] = useState({
        name: '',
        ip: '',
        latitude: 0,
        longitude: 0,
        requested_by: 'Técnico Android' // Idealmente viria de um Auth Context
    });

    useEffect(() => {
        (async () => {
            try {
                let loc = await Location.getCurrentPositionAsync({});
                setForm(prev => ({
                    ...prev,
                    latitude: loc.coords.latitude,
                    longitude: loc.coords.longitude
                }));
            } catch (e) {
                Alert.alert("Erro GPS", "Não foi possível pegar a localização exata.");
            } finally {
                setGpsLoading(false);
            }
        })();
    }, []);

    const handleSubmit = async () => {
        if (!form.name) return Alert.alert("Erro", "Nome da torre é obrigatório");

        setLoading(true);
        try {
            await api.post('/mobile/tower-request', form);
            Alert.alert("Sucesso", "Solicitação enviada! Aguarde a aprovação do administrador.", [
                { text: "OK", onPress: () => router.back() }
            ]);
        } catch (error) {
            Alert.alert("Erro", "Falha ao enviar solicitação.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <ScrollView contentContainerStyle={{ padding: 20 }}>

                <Text style={styles.label}>Nome da Torre</Text>
                <TextInput
                    style={styles.input}
                    placeholder="Ex: Torre Central"
                    placeholderTextColor="#45475a"
                    value={form.name}
                    onChangeText={t => setForm({ ...form, name: t })}
                />

                <Text style={styles.label}>IP (Opcional)</Text>
                <TextInput
                    style={styles.input}
                    placeholder="Ex: 10.0.0.1"
                    placeholderTextColor="#45475a"
                    keyboardType="numeric"
                    value={form.ip}
                    onChangeText={t => setForm({ ...form, ip: t })}
                />

                <View style={styles.gpsContainer}>
                    <View style={{ flex: 1 }}>
                        <Text style={styles.label}>Localização Atual</Text>
                        {gpsLoading ? (
                            <Text style={styles.gpsText}>Obtendo GPS...</Text>
                        ) : (
                            <Text style={styles.gpsText}>
                                Lat: {form.latitude.toFixed(6)}{"\n"}
                                Lon: {form.longitude.toFixed(6)}
                            </Text>
                        )}
                    </View>
                    <MapPin color="#f9e2af" size={32} />
                </View>

                <TouchableOpacity
                    style={[styles.btn, loading && styles.btnDisabled]}
                    onPress={handleSubmit}
                    disabled={loading}
                >
                    <Save color="#1e1e2e" size={20} />
                    <Text style={styles.btnText}>
                        {loading ? "Enviando..." : "ENVIAR SOLICITAÇÃO"}
                    </Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={styles.btnCancel}
                    onPress={() => router.back()}
                >
                    <Text style={styles.btnCancelText}>Cancelar</Text>
                </TouchableOpacity>

            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#11111b' },
    label: { color: '#a6adc8', marginBottom: 8, fontSize: 14, fontWeight: 'bold' },
    input: {
        backgroundColor: '#1e1e2e',
        color: '#cdd6f4',
        padding: 16,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#313244',
        marginBottom: 20,
        fontSize: 16
    },
    gpsContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#181825',
        padding: 16,
        borderRadius: 8,
        marginTop: 10,
        marginBottom: 30,
        borderWidth: 1,
        borderColor: '#313244'
    },
    gpsText: { color: '#89b4fa', fontFamily: 'monospace', fontSize: 14, lineHeight: 20 },

    btn: {
        backgroundColor: '#a6e3a1',
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 16,
        borderRadius: 8,
        gap: 10,
        marginBottom: 12
    },
    btnDisabled: { opacity: 0.7 },
    btnText: { color: '#1e1e2e', fontWeight: 'bold', fontSize: 16 },

    btnCancel: { padding: 16, alignItems: 'center' },
    btnCancelText: { color: '#f38ba8' }
});
