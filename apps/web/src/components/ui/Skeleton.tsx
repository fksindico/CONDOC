import React from 'react';
import { cn } from '@/lib/utils';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, ...props }) => {
  return (
    <div
      className={cn(
        'animate-pulse rounded-lg bg-slate-200/80 motion-reduce:animate-none',
        className
      )}
      aria-hidden="true"
      {...props}
    />
  );
};

export const CardSkeleton: React.FC = () => (
  <div className="p-5 rounded-xl border border-slate-200 bg-white space-y-3">
    <div className="flex justify-between items-center">
      <Skeleton className="h-4 w-28" />
      <Skeleton className="h-5 w-16 rounded-full" />
    </div>
    <Skeleton className="h-6 w-3/4" />
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-2/3" />
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 4 }) => (
  <div className="p-4 space-y-3 bg-white">
    <div className="flex gap-4 border-b pb-3">
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-4 w-1/4" />
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex gap-4 py-2 border-b border-slate-50 items-center">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
      </div>
    ))}
  </div>
);
