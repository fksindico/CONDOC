import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home, LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: LucideIcon;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  showHome?: boolean;
  className?: string;
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  showHome = false,
  className,
}) => {
  const allItems: BreadcrumbItem[] = showHome
    ? [{ label: 'Painel', href: '/painel', icon: Home }, ...items]
    : items;

  return (
    <nav
      aria-label="Navegação estrutural"
      className={cn('flex items-center text-xs sm:text-sm text-slate-500 py-1.5', className)}
    >
      <ol className="flex items-center gap-1.5 flex-wrap">
        {allItems.map((item, index) => {
          const isLast = index === allItems.length - 1;
          const Icon = item.icon;

          return (
            <li key={index} className="inline-flex items-center gap-1.5">
              {index > 0 && (
                <ChevronRight
                  className="w-3.5 h-3.5 text-slate-400 shrink-0"
                  aria-hidden="true"
                />
              )}
              {isLast || !item.href ? (
                <span
                  className="font-semibold text-slate-900 truncate max-w-[180px] sm:max-w-xs"
                  aria-current={isLast ? 'page' : undefined}
                >
                  {Icon && <Icon className="w-3.5 h-3.5 mr-1 inline shrink-0" aria-hidden="true" />}
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.href}
                  className="inline-flex items-center text-slate-600 hover:text-brand-600 font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded px-1 py-0.5 truncate max-w-[150px] sm:max-w-xs"
                >
                  {Icon && <Icon className="w-3.5 h-3.5 mr-1 inline shrink-0" aria-hidden="true" />}
                  <span>{item.label}</span>
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
