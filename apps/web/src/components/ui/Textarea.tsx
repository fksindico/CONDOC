import React from 'react';
import { cn } from '@/lib/utils';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, id, rows = 3, ...props }, ref) => {
    const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full space-y-1">
        {label && (
          <label htmlFor={textareaId} className="block text-xs font-semibold text-slate-700 tracking-tight">
            {label}
          </label>
        )}
        <div className="relative rounded-lg shadow-2xs">
          <textarea
            id={textareaId}
            ref={ref}
            rows={rows}
            className={cn(
              'w-full text-xs sm:text-sm rounded-lg border bg-white p-3 text-slate-900 transition-colors',
              'placeholder:text-slate-400',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-brand-500',
              'disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed',
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

Textarea.displayName = 'Textarea';
