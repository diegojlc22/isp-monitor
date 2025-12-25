
import { Slot, useRouter, useSegments } from 'expo-router';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { useEffect } from 'react';
import { View, ActivityIndicator, StatusBar } from 'react-native';

const MainLayout = () => {
    const { user, loading } = useAuth();
    const segments = useSegments();
    const router = useRouter();

    useEffect(() => {
        if (loading) return;

        const inTabsGroup = segments[0] === '(tabs)';

        if (!user && inTabsGroup) {
            // Se não logado e tentando acessar tabs, manda pro login
            router.replace('/login');
        } else if (user && segments[0] === 'login') {
            // Se logado e no login, manda pra dashboard
            router.replace('/(tabs)/dashboard');
        }
    }, [user, loading, segments]);

    if (loading) {
        return (
            <View style={{ flex: 1, backgroundColor: '#0f172a', justifyContent: 'center', alignItems: 'center' }}>
                <ActivityIndicator size="large" color="#60a5fa" />
            </View>
        );
    }

    return <Slot />;
}

export default function Root() {
    return (
        <AuthProvider>
            <StatusBar barStyle="light-content" backgroundColor="#0f172a" />
            <MainLayout />
        </AuthProvider>
    );
}
