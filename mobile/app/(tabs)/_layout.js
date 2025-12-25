
import { Tabs } from 'expo-router';
import { Home, Map as MapIcon, Settings as SettingsIcon } from 'lucide-react-native';
import { View } from 'react-native';

export default function TabLayout() {
    return (
        <Tabs screenOptions={{
            headerShown: false,
            tabBarStyle: {
                backgroundColor: '#0f172a',
                borderTopColor: '#334155',
                height: 60,
                paddingBottom: 8,
                paddingTop: 8
            },
            tabBarActiveTintColor: '#60a5fa',
            tabBarInactiveTintColor: '#64748b',
        }}>
            <Tabs.Screen
                name="dashboard"
                options={{
                    title: 'Início',
                    tabBarIcon: ({ color }) => <Home size={24} color={color} />,
                }}
            />
            <Tabs.Screen
                name="map"
                options={{
                    title: 'Mapa',
                    tabBarIcon: ({ color }) => <MapIcon size={24} color={color} />,
                }}
            />
            <Tabs.Screen
                name="settings"
                options={{
                    title: 'Config',
                    tabBarIcon: ({ color }) => <SettingsIcon size={24} color={color} />,
                }}
            />
        </Tabs>
    );
}
