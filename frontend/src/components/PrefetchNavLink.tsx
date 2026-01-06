import React from 'react';
import { NavLink } from 'react-router-dom';
import type { NavLinkProps } from 'react-router-dom';

// Módulo de cache simples para rotas
const pageCache = new Set<string>();

interface PrefetchNavLinkProps extends Omit<NavLinkProps, 'children'> {
    to: string;
    children: React.ReactNode | ((props: { isActive: boolean; isPending: boolean }) => React.ReactNode);
    // Função para importar o módulo (ex: () => import('../pages/Reports'))
    prefetchPage?: () => Promise<any>;
}

export const PrefetchNavLink: React.FC<PrefetchNavLinkProps> = ({ children, to, prefetchPage, ...props }) => {

    const handleMouseEnter = () => {
        if (prefetchPage && !pageCache.has(to.toString())) {
            // Inicia o download do chunk JS em background
            prefetchPage();
            pageCache.add(to.toString());
        }
    };

    return (
        <NavLink
            to={to}
            {...props}
            onMouseEnter={handleMouseEnter}
        >
            {children}
        </NavLink>
    );
};
