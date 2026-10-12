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
    | 'renumerado'
    | 'desmembrado'
    | 'consolidado';
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({ className, variant = 'default', dot = false, children, ...props }) => {
  const baseStyles = 'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium tracking-wide transition-colors';

  const variants = {
    default: 'bg-slate-100 text-slate-700 border border-slate-200',
    success: 'bg-emerald-50 text-emerald-800 border border-emerald-200',
    warning: 'bg-amber-50 text-amber-800 border border-amber-200',
    danger: 'bg-rose-50 text-rose-800 border border-rose-200',
    info: 'bg-blue-50 text-blue-800 border border-blue-200',
    outline: 'border border-slate-300 text-slate-700 bg-transparent',
    // Tipos de Mudança Normativa (CA-20, CA-21, etc.)
    incluido: 'bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold',
    alterado: 'bg-blue-50 text-blue-800 border border-blue-300 font-semibold',
    mantido: 'bg-slate-100 text-slate-700 border border-slate-200',
    excluido: 'bg-rose-50 text-rose-800 border border-rose-300 line-through font-semibold',
    renumerado: 'bg-amber-50 text-amber-800 border border-amber-300 font-semibold',
    desmembrado: 'bg-purple-50 text-purple-800 border border-purple-300 font-semibold',
    consolidado: 'bg-indigo-50 text-indigo-800 border border-indigo-300 font-semibold',
  };

  const dotColors = {
    default: 'bg-slate-400',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500',
    info: 'bg-blue-500',
    outline: 'bg-slate-400',
    incluido: 'bg-emerald-500',
    alterado: 'bg-blue-500',
    mantido: 'bg-slate-400',
    excluido: 'bg-rose-500',
    renumerado: 'bg-amber-500',
    desmembrado: 'bg-purple-500',
    consolidado: 'bg-indigo-500',
  };

  return (
    <span className={cn(baseStyles, variants[variant], className)} {...props}>
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColors[variant])} aria-hidden="true" />}
      <span>{children}</span>
    </span>
  );
};
