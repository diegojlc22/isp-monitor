import React, { createContext, useContext, useState, useRef, useCallback, useEffect } from 'react';
import toast from 'react-hot-toast';
import { getBatchDetectStatus, startBatchDetect, stopBatchDetect } from '../services/api';

interface ScannerContextType {
    isScanning: boolean;
    progress: number;
    scannedDevices: any[];
    startScan: (range: string, community: string, port: number) => void;
    stopScan: () => void;
    clearResults: () => void;
    showScannerModal: boolean;
    setShowScannerModal: (show: boolean) => void;
    scanRange: string;
    // Batch Detection
    isDetecting: boolean;
    detectionProgress: number;
    startDetection: (ids: number[], community?: string) => Promise<void>;
    stopDetection: () => Promise<void>;
}

const ScannerContext = createContext<ScannerContextType>({} as any);

export const useScanner = () => useContext(ScannerContext);

export const ScannerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isScanning, setIsScanning] = useState(false);
    const [progress, setProgress] = useState(0);
    const [scannedDevices, setScannedDevices] = useState<any[]>([]);
    const [showScannerModal, setShowScannerModal] = useState(false);
    const [scanRange, setScanRange] = useState('');

    // Batch Detection State
    const [isDetecting, setIsDetecting] = useState(false);
    const [detectionProgress, setDetectionProgress] = useState(0);

    const eventSourceRef = useRef<EventSource | null>(null);

    const startScan = useCallback((range: string, community: string, port: number) => {
        if (isScanning) {
            toast('Varredura já em andamento!', { icon: '🔄' });
            setShowScannerModal(true);
            return;
        }

        setScanRange(range);
        setIsScanning(true);
        setScannedDevices([]);
        setProgress(0);
        setShowScannerModal(true);

        try {
            // Force /api prefix if using Vite proxy is flaky, but usually relative path works.
            // Using relative path to current origin.
            // Note: If using distinct backend url check api.ts base

            const url = `/api/equipments/scan/stream/?ip_range=${encodeURIComponent(range)}&snmp_community=${encodeURIComponent(community)}&snmp_port=${port}`;
            console.log("[SCANNER] Connecting to:", url);

            const es = new EventSource(url);
            eventSourceRef.current = es;

            es.onmessage = (ev) => {
                try {
                    const d = JSON.parse(ev.data);
                    if (d.progress !== undefined) setProgress(d.progress);

                    if (d.is_online) {
                        setScannedDevices(prev => {
                            if (prev.find((p: any) => p.ip === d.ip)) return prev;
                            return [...prev, d];
                        });
                    }
                } catch (e) {
                    console.error("Error parsing SSE:", e);
                }
            };

            es.addEventListener("done", () => {
                es.close();
                setIsScanning(false);
                toast.success("Varredura concluída!");
                eventSourceRef.current = null;
            });

            es.onerror = (e) => {
                console.error("SSE Error:", e);
                es.close();
                setIsScanning(false);
                eventSourceRef.current = null;
                // Don't toast error on manual close or network hiccup implies 'stopped'
                toast.error("Varredura parada (Erro de conexão ou timeout).");
            };
        } catch (e) {
            setIsScanning(false);
            toast.error("Falha ao iniciar serviço de scan.");
        }
    }, [isScanning]);

    const stopScan = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        setIsScanning(false);
        toast('Varredura cancelada.', { icon: '⏹️' });
    }, []);

    const clearResults = useCallback(() => {
        setScannedDevices([]);
        setProgress(0);
    }, []);

    const startDetection = async (ids: number[], community?: string) => {
        try {
            await startBatchDetect(ids, community);
            setIsDetecting(true);
            setDetectionProgress(0);
            toast.success("Detecção em lote iniciada!");
        } catch (e: any) {
            toast.error(e.response?.data?.detail || "Erro ao iniciar detecção.");
        }
    };

    const stopDetection = async () => {
        try {
            await stopBatchDetect();
            setIsDetecting(false);
            toast("Detecção parada pelo usuário.");
        } catch (e) {
            setIsDetecting(false);
        }
    };

    // Polling for Batch Detection Status (Dynamic Interval)
    useEffect(() => {
        let timeout: ReturnType<typeof setTimeout>;
        let mounted = true;

        const checkStatus = async () => {
            try {
                const status = await getBatchDetectStatus();
                if (mounted) {
                    setIsDetecting(status.is_running);
                    if (status.total > 0) {
                        setDetectionProgress(Math.round((status.processed / status.total) * 100));
                    }

                    // Poll fast if running, slow if idle
                    const nextInterval = status.is_running ? 2000 : 8000;
                    timeout = setTimeout(checkStatus, nextInterval);
                }
            } catch (e) {
                if (mounted) timeout = setTimeout(checkStatus, 10000);
            }
        };

        checkStatus();

        return () => {
            mounted = false;
            clearTimeout(timeout);
        };
    }, []);

    // Cleanup on Global Unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) eventSourceRef.current.close();
        };
    }, []);

    return (
        <ScannerContext.Provider value={{
            isScanning, progress, scannedDevices, startScan, stopScan, clearResults,
            showScannerModal, setShowScannerModal, scanRange,
            isDetecting, detectionProgress, startDetection, stopDetection
        }}>
            {children}
        </ScannerContext.Provider>
    );
};
