import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'outline-white' | 'white' | 'destructive' | 'ghost' | 'link';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  children,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 motion-reduce:transition-none active:scale-[0.99] motion-reduce:transform-none focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-brand-500 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none select-none';

  const variants = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm focus-visible:ring-brand-500',
    secondary: 'bg-slate-100 text-slate-800 hover:bg-slate-200 focus-visible:ring-slate-400',
    outline: 'border border-slate-300 text-slate-700 hover:bg-slate-50 focus-visible:ring-brand-500 bg-white shadow-2xs',
    'outline-white': 'border border-white/50 text-white hover:bg-white/15 hover:border-white bg-transparent focus-visible:ring-white',
    white: 'bg-white text-slate-900 hover:bg-slate-100 shadow-sm focus-visible:ring-white',
    destructive: 'bg-rose-600 text-white hover:bg-rose-700 shadow-sm focus-visible:ring-rose-500',
    ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus-visible:ring-slate-400',
    link: 'text-brand-600 hover:underline p-0 h-auto focus-visible:ring-0',
  };

  const sizes = {
    sm: 'text-xs px-3 py-2 min-h-[44px] gap-1.5',
    md: 'text-sm px-4 py-2 h-10 gap-2',
    lg: 'text-base px-5 py-2.5 h-12 gap-2.5',
  };

  return (
    <button
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 animate-spin text-current" />}
      {children}
    </button>
  );
};
