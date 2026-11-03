import React from 'react';
import { LucideIcon, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  icon?: LucideIcon;
  iconColor?: string;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendDirection = 'neutral',
  icon: Icon,
  iconColor = 'text-indigo-400',
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`group relative overflow-hidden rounded-2xl border border-[#e7e9f4] bg-white p-4 shadow-[0_4px_18px_rgba(39,51,104,0.045)] transition-all duration-200 sm:p-5 ${
        onClick ? 'cursor-pointer hover:-translate-y-0.5 hover:border-[#cfd4f5] hover:shadow-[0_10px_24px_rgba(59,68,137,0.09)]' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-[#687391] sm:text-[13px]">{title}</span>
        {Icon && (
          <div className="rounded-xl bg-[#f0f1ff] p-2.5 transition-transform duration-200 group-hover:scale-105">
            <Icon className={`h-[18px] w-[18px] ${iconColor.replace('400', '600')}`} strokeWidth={1.9} />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline justify-between gap-2">
        <span className="text-[27px] font-bold tracking-tight text-[#17203d]">{value}</span>
        {trend && (
          <div
            className={`flex items-center text-xs font-semibold ${
              trendDirection === 'up'
                ? 'text-emerald-600'
                : trendDirection === 'down'
                ? 'text-rose-600'
                : 'text-[#77819d]'
            }`}
          >
            {trendDirection === 'up' && <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />}
            {trendDirection === 'down' && <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />}
            {trend}
          </div>
        )}
      </div>

      {subtitle && <p className="mt-1 text-[11px] leading-5 text-[#8992aa]">{subtitle}</p>}
    </div>
  );
};
