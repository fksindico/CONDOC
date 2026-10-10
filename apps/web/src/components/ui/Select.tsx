import React from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, helperText, id, children, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full space-y-1">
        {label && (
          <label htmlFor={selectId} className="block text-xs font-semibold text-slate-700 tracking-tight">
            {label}
          </label>
        )}
        <div className="relative rounded-lg shadow-2xs">
          <select
            id={selectId}
            ref={ref}
            className={cn(
              'w-full appearance-none text-xs sm:text-sm rounded-lg border bg-white pl-3 pr-8 py-2 text-slate-900 transition-colors cursor-pointer',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-brand-500',
              'disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed',
              error
                ? 'border-rose-400 focus-visible:ring-rose-400 text-rose-900'
                : 'border-slate-300 hover:border-slate-400 focus:border-brand-500',
              className
            )}
            aria-invalid={Boolean(error)}
            {...props}
          >
            {children}
          </select>
          <div className="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none text-slate-400">
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>
        {error && <p className="text-[11px] text-rose-600 font-medium tracking-tight">{error}</p>}
        {helperText && !error && <p className="text-[11px] text-slate-500">{helperText}</p>}
      </div>
    );
  }
);

Select.displayName = 'Select';
