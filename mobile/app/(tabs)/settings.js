
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert, StatusBar } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { LogOut, User, Info, Smartphone } from 'lucide-react-native';
import Constants from 'expo-constants';

export default function SettingsScreen() {
    const { user, signOut } = useAuth();

    const handleLogout = () => {
        Alert.alert(
            "Sair",
            "Tem certeza que deseja sair?",
            [
                { text: "Cancelar", style: "cancel" },
                { text: "Sair", onPress: signOut, style: "destructive" }
            ]
        );
    };

    return (
        <View style={styles.container}>
            <StatusBar barStyle="light-content" backgroundColor="#0f172a" />

            <ScrollView contentContainerStyle={styles.content}>
                {/* User Info */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Perfil</Text>
                    <View style={styles.card}>
                        <View style={styles.row}>
                            <User size={20} color="#60a5fa" />
                            <View style={{ marginLeft: 12 }}>
                                <Text style={styles.label}>Nome</Text>
                                <Text style={styles.value}>{user?.name || 'Técnico'}</Text>
                            </View>
                        </View>
                        <View style={[styles.row, { marginTop: 16 }]}>
                            <User size={20} color="#a6e3a1" />
                            <View style={{ marginLeft: 12 }}>
                                <Text style={styles.label}>Email</Text>
                                <Text style={styles.value}>{user?.email || 'N/A'}</Text>
                            </View>
                        </View>
                        <View style={[styles.row, { marginTop: 16 }]}>
                            <User size={20} color="#f9e2af" />
                            <View style={{ marginLeft: 12 }}>
                                <Text style={styles.label}>Função</Text>
                                <Text style={styles.value}>{user?.role || 'Técnico'}</Text>
                            </View>
                        </View>
                    </View>
                </View>

                {/* App Info */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Informações do App</Text>
                    <View style={styles.card}>
                        <View style={styles.row}>
                            <Smartphone size={20} color="#89b4fa" />
                            <View style={{ marginLeft: 12 }}>
                                <Text style={styles.label}>Versão</Text>
                                <Text style={styles.value}>{Constants.expoConfig?.version || '1.0.0'}</Text>
                            </View>
                        </View>
                        <View style={[styles.row, { marginTop: 16 }]}>
                            <Info size={20} color="#cba6f7" />
                            <View style={{ marginLeft: 12 }}>
                                <Text style={styles.label}>Build</Text>
                                <Text style={styles.value}>
                                    {__DEV__ ? 'Desenvolvimento' : 'Produção'}
                                </Text>
                            </View>
                        </View>
                    </View>
                </View>

                {/* Actions */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Ações</Text>

                    <TouchableOpacity
                        style={[styles.actionBtn, styles.logoutBtn]}
                        onPress={handleLogout}
                    >
                        <LogOut size={20} color="#f87171" />
                        <Text style={[styles.actionText, { color: '#f87171' }]}>Sair</Text>
                    </TouchableOpacity>
                </View>

                {/* Footer */}
                <Text style={styles.footer}>
                    ISP Monitor © 2025{'\n'}
                    Desenvolvido para técnicos de campo
                </Text>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a'
    },
    content: {
        padding: 20,
        paddingTop: 40
    },
    section: {
        marginBottom: 24
    },
    sectionTitle: {
        color: '#94a3b8',
        fontSize: 12,
        fontWeight: '700',
        textTransform: 'uppercase',
        letterSpacing: 1,
        marginBottom: 12
    },
    card: {
        backgroundColor: '#1e293b',
        borderRadius: 16,
        padding: 20,
        borderWidth: 1,
        borderColor: '#334155'
    },
    row: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    label: {
        color: '#64748b',
        fontSize: 12,
        marginBottom: 4
    },
    value: {
        color: '#f8fafc',
        fontSize: 16,
        fontWeight: '600'
    },
    actionBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#1e293b',
        padding: 16,
        borderRadius: 12,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: '#334155'
    },
    actionText: {
        color: '#f8fafc',
        fontSize: 16,
        marginLeft: 12,
        fontWeight: '600'
    },
    logoutBtn: {
        borderColor: 'rgba(248, 113, 113, 0.2)',
        backgroundColor: 'rgba(248, 113, 113, 0.05)'
    },
    footer: {
        color: '#475569',
        fontSize: 12,
        textAlign: 'center',
        marginTop: 40,
        lineHeight: 20
    }
});
