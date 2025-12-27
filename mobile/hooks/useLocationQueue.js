import { useState, useEffect, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';


const QUEUE_KEY = '@gps_queue';

export function useLocationQueue() {
    const [queueSize, setQueueSize] = useState(0);
    const isProcessing = useRef(false);

    useEffect(() => {
        // Carrega tamanho inicial da fila
        checkQueueSize();

        // Tenta processar fila a cada 30s se houver itens
        const interval = setInterval(() => {
            processQueue();
        }, 30000);

        return () => clearInterval(interval);
    }, []);

    const checkQueueSize = async () => {
        try {
            const queue = await AsyncStorage.getItem(QUEUE_KEY);
            const parsed = queue ? JSON.parse(queue) : [];
            setQueueSize(parsed.length);
        } catch (e) {
            console.log('Erro checkQueueSize', e);
        }
    };

    const addToQueue = async (coords) => {
        try {
            const queue = await AsyncStorage.getItem(QUEUE_KEY);
            const parsed = queue ? JSON.parse(queue) : [];

            const newPoint = {
                latitude: coords.latitude,
                longitude: coords.longitude,
                timestamp: Date.now()
            };

            parsed.push(newPoint);

            // Limite de segurança (últimos 1000 pontos para não estourar memória)
            if (parsed.length > 1000) parsed.shift();

            await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(parsed));
            setQueueSize(parsed.length);
            console.log(`📍 Ponto salvo na fila offline. Total: ${parsed.length}`);
        } catch (e) {
            console.log('Erro addToQueue', e);
        }
    };

    const processQueue = async () => {
        if (isProcessing.current) return;

        try {
            const queue = await AsyncStorage.getItem(QUEUE_KEY);
            if (!queue) return;

            let parsed = JSON.parse(queue);
            if (parsed.length === 0) return;

            isProcessing.current = true;
            console.log(`🔄 Processando fila de ${parsed.length} pontos...`);

            // Pega o lote de até 10 pontos para enviar
            const batch = parsed.slice(0, 50); // Manda de 50 em 50 para ser rápido

            // Aqui idealmente o backend aceitaria Batch (array), mas vamos mandar 1 por 1 ou o último
            // Para não spamar o server, vamos mandar APENAS O ÚLTIMO ponto real instantâneo
            // E os históricos como log se o backend suportasse.
            // Como o backend atual só atualiza a "localização atual", mandar 100 requests velhos é inútil para "onde ele está agora",
            // mas é útil para "histórico de rota".
            // Vamos assumir que queremos apenas garantir que o ULTIMO ponto seja sincronizado se voltarmos online.

            // ESTRATÉGIA OTIMIZADA: Envia o ponto mais recente do lote e remove o lote.
            // Se o backend tiver endpoint de histórico, mudamos isso.

            const lastPoint = batch[batch.length - 1];

            await api.post('/mobile/location', {
                latitude: lastPoint.latitude,
                longitude: lastPoint.longitude,
                // timestamp: lastPoint.timestamp // Backend ignoraria hoje
            });

            // Se deu sucesso, removemos o lote processado
            // (Na prática removemos todo o slice processado, mesmo tendo enviado só o último, 
            // pois o objetivo atual é "Sincronizar Localização Atual")
            parsed = parsed.slice(batch.length);

            await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(parsed));
            setQueueSize(parsed.length);
            console.log(`✅ Lote sincronizado. Restante: ${parsed.length}`);

        } catch (error) {
            if (error.response?.status === 401) {
                // Se for erro de auth, não adianta tentar, limpa fila ou espera login
                console.log('⚠️ Erro 401 no processQueue. Pausando.');
            } else {
                console.log('❌ Falha ao processar fila (sem internet?)');
            }
        } finally {
            isProcessing.current = false;
        }
    };

    const sendLocation = async (coords) => {
        try {
            // Tenta enviar direto
            await api.post('/mobile/location', {
                latitude: coords.latitude,
                longitude: coords.longitude
            });

            // Se funcionou, ótimo. Aproveita e tenta processar fila pendente em background
            if (queueSize > 0) processQueue();

            return true;
        } catch (error) {
            console.log('⚠️ Falha envio online. Salvando na fila.');
            // Se falhou (exceto 401), salva na fila
            if (error.response?.status !== 401) {
                addToQueue(coords);
            }
            return false;
        }
    };

    return {
        sendLocation,
        queueSize
    };
}
