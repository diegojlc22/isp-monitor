
import React, { createContext, useState, useContext, useEffect } from 'react';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

const AuthContext = createContext({});

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [initializing, setInitializing] = useState(true);

    // Restaurar sessão ao iniciar
    useEffect(() => {
        loadStoredAuth();
    }, []);

    const loadStoredAuth = async () => {
        try {
            const token = await AsyncStorage.getItem('@auth_token');
            const userData = await AsyncStorage.getItem('@auth_user');

            if (token && userData) {
                api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
                setUser(JSON.parse(userData));
            }
        } catch (error) {
            console.error('Erro ao carregar autenticação:', error);
        } finally {
            setInitializing(false);
        }
    };

    const signIn = async (email, password) => {
        setLoading(true);
        try {
            const response = await api.post('/auth/login', { email, password });
            const { access_token, user: userData } = response.data;

            // Salvar token e usuário
            await AsyncStorage.setItem('@auth_token', access_token);
            await AsyncStorage.setItem('@auth_user', JSON.stringify(userData));

            // Configurar header
            api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

            setUser(userData);
            router.replace('/(tabs)/dashboard');
        } catch (error) {
            console.error("Login error", error);
            alert("Email ou senha inválidos.");
        } finally {
            setLoading(false);
        }
    };

    const signOut = async () => {
        await AsyncStorage.removeItem('@auth_token');
        await AsyncStorage.removeItem('@auth_user');
        delete api.defaults.headers.common['Authorization'];
        setUser(null);
        router.replace('/login');
    };

    // Não renderizar até carregar auth
    if (initializing) {
        return null;
    }

    return (
        <AuthContext.Provider value={{ user, signIn, signOut, loading }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
