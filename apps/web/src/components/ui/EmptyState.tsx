import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button, ButtonProps } from './Button';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  actionVariant?: ButtonProps['variant'];
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  actionVariant = 'primary',
  className,
}) => {
  return (
    <div
      className={cn(
        'text-center py-12 px-6 rounded-2xl border border-dashed border-slate-300 bg-white/60 flex flex-col items-center justify-center space-y-3',
        className
      )}
    >
      <div className="p-3.5 bg-slate-100 rounded-2xl text-slate-400 mb-1">
        <Icon className="w-8 h-8 text-slate-500" />
      </div>
      <div className="max-w-sm space-y-1">
        <h4 className="text-sm font-bold text-slate-900 tracking-tight">{title}</h4>
        <p className="text-xs text-slate-500 leading-relaxed">{description}</p>
      </div>
      {actionLabel && onAction && (
        <div className="pt-2">
          <Button size="sm" variant={actionVariant} onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
};
