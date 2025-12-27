
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView, StatusBar, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';
import { Save, MapPin, X, ArrowLeft } from 'lucide-react-native';
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
        requested_by: 'Técnico Android'
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
            <StatusBar barStyle="light-content" backgroundColor="#0f172a" />

            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
                    <ArrowLeft color="#f8fafc" size={24} />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Nova Torre</Text>
            </View>

            <ScrollView contentContainerStyle={styles.content}>

                <View style={styles.card}>
                    <Text style={styles.sectionTitle}>INFORMAÇÕES BÁSICAS</Text>

                    <Text style={styles.label}>Nome da Torre</Text>
                    <TextInput
                        style={styles.input}
                        placeholder="Ex: Torre Central"
                        placeholderTextColor="#64748b"
                        value={form.name}
                        onChangeText={t => setForm({ ...form, name: t })}
                    />

                    <Text style={styles.label}>IP (Opcional)</Text>
                    <TextInput
                        style={styles.input}
                        placeholder="Ex: 10.0.0.1"
                        placeholderTextColor="#64748b"
                        keyboardType="numeric"
                        value={form.ip}
                        onChangeText={t => setForm({ ...form, ip: t })}
                    />
                </View>

                <View style={styles.card}>
                    <Text style={styles.sectionTitle}>LOCALIZAÇÃO</Text>

                    <View style={styles.gpsContainer}>
                        <View style={styles.gpsIconBox}>
                            <MapPin color="#f9e2af" size={24} />
                        </View>
                        <View style={{ flex: 1 }}>
                            <Text style={styles.gpsLabel}>Coordenadas Atuais</Text>
                            {gpsLoading ? (
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                                    <ActivityIndicator size="small" color="#60a5fa" />
                                    <Text style={styles.gpsValue}>Obtendo GPS...</Text>
                                </View>
                            ) : (
                                <Text style={styles.gpsValue}>
                                    {form.latitude.toFixed(6)}, {form.longitude.toFixed(6)}
                                </Text>
                            )}
                        </View>
                    </View>
                    <Text style={styles.hint}>
                        A posição atual do dispositivo será usada para o cadastro.
                    </Text>
                </View>

                <TouchableOpacity
                    style={[styles.btn, loading && styles.btnDisabled]}
                    onPress={handleSubmit}
                    disabled={loading}
                    activeOpacity={0.8}
                >
                    {loading ? (
                        <ActivityIndicator color="#1e293b" />
                    ) : (
                        <>
                            <Save color="#1e293b" size={20} />
                            <Text style={styles.btnText}>ENVIAR SOLICITAÇÃO</Text>
                        </>
                    )}
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
    container: { flex: 1, backgroundColor: '#0f172a' },

    header: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingTop: 50,
        paddingBottom: 20,
        paddingHorizontal: 20,
        backgroundColor: '#0f172a',
        borderBottomWidth: 1,
        borderBottomColor: '#1e293b'
    },
    headerTitle: { color: '#f8fafc', fontSize: 20, fontWeight: 'bold', marginLeft: 16 },
    backBtn: { padding: 4 },

    content: { padding: 20 },

    card: {
        backgroundColor: '#1e293b',
        borderRadius: 16,
        padding: 20,
        borderWidth: 1,
        borderColor: '#334155',
        marginBottom: 24
    },
    sectionTitle: {
        color: '#64748b', fontSize: 12, fontWeight: 'bold', marginBottom: 16,
        letterSpacing: 1
    },

    label: { color: '#cbd5e1', marginBottom: 8, fontSize: 14, fontWeight: '500' },
    input: {
        backgroundColor: '#0f172a',
        color: '#f8fafc',
        padding: 16,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#334155',
        marginBottom: 20,
        fontSize: 16
    },

    gpsContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#0f172a',
        padding: 16,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#334155',
        gap: 16
    },
    gpsIconBox: {
        width: 48, height: 48, borderRadius: 24,
        backgroundColor: 'rgba(249, 226, 175, 0.1)',
        justifyContent: 'center', alignItems: 'center'
    },
    gpsLabel: { color: '#64748b', fontSize: 12, marginBottom: 4 },
    gpsValue: { color: '#f8fafc', fontSize: 16, fontWeight: 'bold', fontFamily: 'monospace' },
    hint: { color: '#64748b', fontSize: 12, marginTop: 12, textAlign: 'center' },

    btn: {
        backgroundColor: '#a6e3a1',
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 18,
        borderRadius: 12,
        gap: 10,
        marginBottom: 16,
        marginTop: 8,
        elevation: 4
    },
    btnDisabled: { opacity: 0.7 },
    btnText: { color: '#1e293b', fontWeight: 'bold', fontSize: 16 },

    btnCancel: { padding: 16, alignItems: 'center' },
    btnCancelText: { color: '#f87171', fontWeight: '500' }
});
