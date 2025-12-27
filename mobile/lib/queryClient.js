import { QueryClient } from '@tanstack/react-query';

// Cliente configurado para performance mobile
export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 2, // Tenta 2x se falhar
            staleTime: 1000 * 60, // Dados são "frescos" por 1 min (não refetch)
            cacheTime: 1000 * 60 * 5, // Cache dura 5 min na memória
            refetchOnWindowFocus: true, // Atualiza ao voltar pro app
            refetchOnReconnect: true, // Atualiza se a net voltar
        },
    },
});
