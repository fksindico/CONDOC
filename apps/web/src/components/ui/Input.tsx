import React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', label, error, helperText, icon, id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full space-y-1">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-semibold text-slate-700 tracking-tight">
            {label}
          </label>
        )}
        <div className="relative rounded-lg shadow-2xs">
          {icon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              {icon}
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            type={type}
            className={cn(
              'w-full text-xs sm:text-sm rounded-lg border bg-white px-3 py-2 text-slate-900 transition-colors',
              'placeholder:text-slate-400',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-brand-500',
              'disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed',
              icon ? 'pl-9' : 'pl-3',
              error
                ? 'border-rose-400 focus-visible:ring-rose-400 text-rose-900'
                : 'border-slate-300 hover:border-slate-400 focus:border-brand-500',
              className
            )}
            aria-invalid={Boolean(error)}
            {...props}
          />
        </div>
        {error && <p className="text-[11px] text-rose-600 font-medium tracking-tight">{error}</p>}
        {helperText && !error && <p className="text-[11px] text-slate-500">{helperText}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
