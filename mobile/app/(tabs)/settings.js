
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert, StatusBar, TextInput, Modal, Button } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { LogOut, User, Info, Smartphone, ChevronRight, Shield, Bell, Server } from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { reloadApiConfig } from '../../services/api';
import Constants from 'expo-constants';
import { useRouter } from 'expo-router';

export default function SettingsScreen() {
    const { user, signOut } = useAuth();
    const router = useRouter();

    const [ip, setIp] = useState('');
    const [showIpModal, setShowIpModal] = useState(false);

    useEffect(() => {
        AsyncStorage.getItem('settings_local_ip').then(v => setIp(v || ''));
    }, []);

    const handleSaveIp = async () => {
        await AsyncStorage.setItem('settings_local_ip', ip);
        const res = await reloadApiConfig();
        setShowIpModal(false);
        Alert.alert("Rede", res.mode === 'local' ? `Conectado localmente!` : "Salvo. Usando conexão remota no momento (verifique se está no Wi-Fi).");
    };

    const handleLogout = () => {
        Alert.alert(
            "Sair da Conta",
            "Tem certeza que deseja desconectar?",
            [
                { text: "Cancelar", style: "cancel" },
                { text: "Sair", onPress: signOut, style: "destructive" }
            ]
        );
    };

    const SettingItem = ({ icon: Icon, color, label, value, onPress, isAction = false }) => (
        <TouchableOpacity
            style={styles.settingItem}
            onPress={onPress}
            disabled={!onPress}
            activeOpacity={onPress ? 0.7 : 1}
        >
            <View style={[styles.iconContainer, { backgroundColor: `${color}20` }]}>
                <Icon size={20} color={color} />
            </View>
            <View style={styles.settingContent}>
                <Text style={[styles.settingLabel, isAction && { color }]}>{label}</Text>
                {value && <Text style={styles.settingValue}>{value}</Text>}
            </View>
            {onPress && !isAction && <ChevronRight size={16} color="#475569" />}
        </TouchableOpacity>
    );

    return (
        <View style={styles.container}>
            <StatusBar barStyle="light-content" backgroundColor="#0f172a" />

            <View style={styles.header}>
                <Text style={styles.headerTitle}>Configurações</Text>
            </View>

            <ScrollView contentContainerStyle={styles.content}>

                {/* Profile Section */}
                <View style={styles.section}>
                    <Text style={styles.sectionHeader}>PERFIL</Text>
                    <View style={styles.card}>
                        <View style={styles.profileHeader}>
                            <View style={styles.avatar}>
                                <Text style={styles.avatarText}>
                                    {user?.name?.charAt(0).toUpperCase() || 'T'}
                                </Text>
                            </View>
                            <View>
                                <Text style={styles.profileName}>{user?.name || 'Técnico'}</Text>
                                <Text style={styles.profileEmail}>{user?.email || 'email@exemplo.com'}</Text>
                            </View>
                        </View>

                        <View style={styles.divider} />

                        <SettingItem
                            icon={Shield}
                            color="#a6e3a1"
                            label="Função"
                            value={user?.role?.toUpperCase() || 'TÉCNICO'}
                        />
                    </View>
                </View>

                {/* App Settings */}
                <View style={styles.section}>
                    <Text style={styles.sectionHeader}>APLICATIVO</Text>
                    <View style={styles.card}>
                        <SettingItem
                            icon={Bell}
                            color="#f9e2af"
                            label="Notificações"
                            value="Ativado"
                            onPress={() => { }}
                        />
                        <View style={styles.divider} />
                        <SettingItem
                            icon={Smartphone}
                            color="#89b4fa"
                            label="Versão"
                            value={Constants.expoConfig?.version || '1.0.0'}
                        />
                        <View style={styles.divider} />
                        <SettingItem
                            icon={Server}
                            color="#a6e3a1"
                            label="IP Servidor Local"
                            value={ip || 'Automático (Ngrok)'}
                            onPress={() => setShowIpModal(true)}
                        />
                        <View style={styles.divider} />
                        <SettingItem
                            icon={Info}
                            color="#cba6f7"
                            label="Build"
                            value={__DEV__ ? 'Debug' : 'Release'}
                        />
                    </View>
                </View>

                {/* IP Modal */}
                <Modal visible={showIpModal} transparent animationType="fade">
                    <View style={{ flex: 1, justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.7)', padding: 24 }}>
                        <View style={{ backgroundColor: '#1e293b', padding: 24, borderRadius: 16, borderWidth: 1, borderColor: '#334155' }}>
                            <Text style={{ color: 'white', fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>Configurar IP Local</Text>
                            <Text style={{ color: '#94a3b8', marginBottom: 16 }}>Digite o IP do computador onde o servidor está rodando (ex: 192.168.1.10) para acesso rápido via Wi-Fi.</Text>

                            <TextInput
                                value={ip}
                                onChangeText={setIp}
                                placeholder="Ex: 192.168.1.100"
                                placeholderTextColor="#475569"
                                style={{ backgroundColor: '#0f172a', color: 'white', padding: 12, borderRadius: 8, marginBottom: 24, fontSize: 16, borderWidth: 1, borderColor: '#334155' }}
                                keyboardType="numeric"
                            />

                            <View style={{ gap: 12 }}>
                                <Button title="Salvar e Testar" color="#2563eb" onPress={handleSaveIp} />
                                <Button title="Cancelar" color="#ef4444" onPress={() => setShowIpModal(false)} />
                            </View>
                        </View>
                    </View>
                </Modal>

                {/* Actions */}
                <View style={styles.section}>
                    <View style={[styles.card, { borderColor: 'rgba(248, 113, 113, 0.3)' }]}>
                        <SettingItem
                            icon={LogOut}
                            color="#f87171"
                            label="Desconectar"
                            isAction
                            onPress={handleLogout}
                        />
                    </View>
                </View>

                <Text style={styles.footer}>
                    ISP Monitor Mobile{'\n'}
                    ID: {user?.id || '---'}
                </Text>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#0f172a' },

    header: {
        paddingTop: 60,
        paddingBottom: 20,
        paddingHorizontal: 24,
        backgroundColor: '#0f172a',
        borderBottomWidth: 1,
        borderBottomColor: '#1e293b'
    },
    headerTitle: { color: '#f8fafc', fontSize: 24, fontWeight: 'bold' },

    content: { padding: 24 },

    section: { marginBottom: 32 },
    sectionHeader: { color: '#64748b', fontSize: 12, fontWeight: 'bold', marginBottom: 12, marginLeft: 4 },

    card: {
        backgroundColor: '#1e293b',
        borderRadius: 16,
        padding: 4,
        borderWidth: 1,
        borderColor: '#334155'
    },

    profileHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
        gap: 16
    },
    avatar: {
        width: 48, height: 48, borderRadius: 24,
        backgroundColor: '#3b82f6',
        justifyContent: 'center', alignItems: 'center'
    },
    avatarText: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
    profileName: { color: '#f8fafc', fontSize: 18, fontWeight: 'bold' },
    profileEmail: { color: '#94a3b8', fontSize: 14 },

    settingItem: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
        gap: 16
    },
    iconContainer: {
        width: 36, height: 36, borderRadius: 10,
        justifyContent: 'center', alignItems: 'center'
    },
    settingContent: { flex: 1 },
    settingLabel: { color: '#f8fafc', fontSize: 16, fontWeight: '500' },
    settingValue: { color: '#64748b', fontSize: 14, marginTop: 2 },

    divider: { height: 1, backgroundColor: '#334155', marginLeft: 68 }, // Indented divider

    footer: {
        textAlign: 'center', color: '#475569', fontSize: 12,
        lineHeight: 18, marginTop: 20
    }
});
