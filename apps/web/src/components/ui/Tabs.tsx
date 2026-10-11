import React from 'react';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';

export interface TabItem {
  key: string;
  label: string;
  icon?: LucideIcon;
  badge?: string | number;
  href?: string;
  disabled?: boolean;
}

export interface TabsProps {
  items: TabItem[];
  activeKey?: string;
  onChange?: (key: string) => void;
  variant?: 'pills' | 'underline';
  className?: string;
  size?: 'sm' | 'md';
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  activeKey,
  onChange,
  variant = 'pills',
  className,
  size = 'md',
}) => {
  return (
    <div
      role="tablist"
      aria-orientation="horizontal"
      className={cn(
        'flex items-center gap-1.5 overflow-x-auto no-scrollbar scroll-smooth py-1',
        variant === 'underline' && 'border-b border-slate-200 gap-2',
        className
      )}
    >
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = activeKey === item.key;

        const baseStyles = cn(
          'inline-flex items-center justify-center font-medium transition-all duration-150 select-none whitespace-nowrap cursor-pointer',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-1',
          'min-h-[44px] px-3.5 py-2 text-xs sm:text-sm rounded-lg',
          size === 'sm' && 'text-xs px-3 py-1.5',
          item.disabled && 'opacity-40 cursor-not-allowed pointer-events-none'
        );

        const variantStyles =
          variant === 'pills'
            ? isActive
              ? 'bg-brand-50 text-brand-700 font-semibold border border-brand-200/80 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            : isActive
            ? 'text-brand-600 font-semibold border-b-2 border-brand-600 rounded-b-none pb-2.5 -mb-px bg-transparent'
            : 'text-slate-500 hover:text-slate-800 border-b-2 border-transparent rounded-b-none pb-2.5 -mb-px hover:border-slate-300 bg-transparent';

        const content = (
          <>
            {Icon && (
              <Icon
                className={cn(
                  'w-4 h-4 shrink-0 mr-2 transition-colors',
                  isActive ? 'text-brand-600' : 'text-slate-400 group-hover:text-slate-600'
                )}
                aria-hidden="true"
              />
            )}
            <span>{item.label}</span>
            {item.badge !== undefined && (
              <span
                className={cn(
                  'ml-2 px-1.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide',
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'bg-slate-200 text-slate-700'
                )}
              >
                {item.badge}
              </span>
            )}
          </>
        );

        if (item.href) {
          return (
            <Link
              key={item.key}
              to={item.href}
              role="tab"
              aria-selected={isActive}
              className={cn(baseStyles, variantStyles)}
              onClick={() => onChange?.(item.key)}
            >
              {content}
            </Link>
          );
        }

        return (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={isActive}
            disabled={item.disabled}
            className={cn(baseStyles, variantStyles)}
            onClick={() => onChange?.(item.key)}
          >
            {content}
          </button>
        );
      })}
    </div>
  );
};
