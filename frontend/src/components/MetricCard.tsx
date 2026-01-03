import React from 'react';
import clsx from 'clsx';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
    title: string;
    value: string | number;
    description?: string;
    status?: 'good' | 'average' | 'poor' | 'neutral';
    icon?: LucideIcon;
    linkText?: string;
    onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
    title,
    value,
    description,
    status = 'neutral',
    icon: Icon,
    linkText,
    onClick
}) => {

    const getStatusColors = (status: string) => {
        switch (status) {
            case 'good': return 'text-emerald-400';
            case 'average': return 'text-amber-400';
            case 'poor': return 'text-rose-400';
            default: return 'text-slate-200';
        }
    };

    const statusColor = getStatusColors(status);

    return (
        <div className="bg-slate-900 border border-slate-700/50 rounded-lg p-5 flex flex-col justify-between h-32 hover:border-slate-600 transition-colors shadow-sm">

            {/* Header */}
            <div className="flex justify-between items-start mb-2">
                <h3 className="text-slate-400 text-sm font-medium flex items-center gap-2">
                    {title}
                    {Icon && <Icon size={14} className="text-slate-500" />}
                </h3>
            </div>

            {/* Value */}
            <div>
                <div className={clsx("text-3xl font-bold tracking-tight", statusColor)}>
                    {value}
                </div>
            </div>

            {/* Footer / Description */}
            <div className="mt-2 text-xs text-slate-500">
                {description}
                {linkText && (
                    <span
                        onClick={onClick}
                        className="ml-2 text-blue-400 hover:text-blue-300 cursor-pointer underline decoration-blue-400/30 underline-offset-2"
                    >
                        {linkText}
                    </span>
                )}
            </div>
        </div>
    );
};
