import React from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | 'default'
    | 'success'
    | 'warning'
    | 'danger'
    | 'info'
    | 'outline'
    | 'incluido'
    | 'alterado'
    | 'mantido'
    | 'excluido'
    | 'desmembrado'
    | 'consolidado';
}

export const Badge: React.FC<BadgeProps> = ({ className, variant = 'default', children, ...props }) => {
  const baseStyles = 'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium tracking-wide';

  const variants = {
    default: 'bg-slate-100 text-slate-700 border border-slate-200',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border border-amber-200',
    danger: 'bg-rose-50 text-rose-700 border border-rose-200',
    info: 'bg-blue-50 text-blue-700 border border-blue-200',
    outline: 'border border-slate-300 text-slate-700 bg-transparent',
    // Tipos de Mudança Normativa (CA-20, CA-21, etc.)
    incluido: 'bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold',
    alterado: 'bg-blue-100 text-blue-800 border border-blue-300 font-semibold',
    mantido: 'bg-slate-100 text-slate-700 border border-slate-200',
    excluido: 'bg-rose-100 text-rose-800 border border-rose-300 line-through font-semibold',
    desmembrado: 'bg-purple-100 text-purple-800 border border-purple-300 font-semibold',
    consolidado: 'bg-indigo-100 text-indigo-800 border border-indigo-300 font-semibold',
  };

  return (
    <span className={cn(baseStyles, variants[variant], className)} {...props}>
      {children}
    </span>
  );
};
