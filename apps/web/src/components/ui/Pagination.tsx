import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  totalItems?: number;
  pageSize?: number;
  showSummary?: boolean;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  page,
  totalPages,
  onPageChange,
  totalItems,
  pageSize = 10,
  showSummary = false,
  className,
}) => {
  if (totalPages <= 1 && !totalItems) {
    return null;
  }

  // Gera páginas para exibir com elipses
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (page <= 3) {
        pages.push(1, 2, 3, 4, '...', totalPages);
      } else if (page >= totalPages - 2) {
        pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      } else {
        pages.push(1, '...', page - 1, page, page + 1, '...', totalPages);
      }
    }

    return pages;
  };

  const startItem = totalItems ? Math.min((page - 1) * pageSize + 1, totalItems) : 0;
  const endItem = totalItems ? Math.min(page * pageSize, totalItems) : 0;

  return (
    <nav
      aria-label="Paginação"
      className={cn(
        'flex flex-col sm:flex-row items-center justify-between gap-3 py-3 px-2 text-xs sm:text-sm text-slate-600',
        className
      )}
    >
      {showSummary && totalItems !== undefined ? (
        <div className="text-slate-500 font-medium order-2 sm:order-1">
          Mostrando <span className="font-semibold text-slate-900">{startItem}</span> a{' '}
          <span className="font-semibold text-slate-900">{endItem}</span> de{' '}
          <span className="font-semibold text-slate-900">{totalItems}</span> registros
        </div>
      ) : (
        <div className="order-2 sm:order-1" />
      )}

      <div className="flex items-center gap-1 order-1 sm:order-2">
        {/* Botão Anterior */}
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className={cn(
            'inline-flex items-center justify-center min-h-[44px] min-w-[44px] px-2.5 rounded-lg border border-slate-200 bg-white text-slate-700 font-medium transition-all shadow-2xs',
            'hover:bg-slate-50 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
            'disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none'
          )}
          aria-label="Página anterior"
        >
          <ChevronLeft className="w-4 h-4 mr-1 shrink-0" aria-hidden="true" />
          <span className="hidden sm:inline">Anterior</span>
        </button>

        {/* Páginas Numéricas */}
        <div className="flex items-center gap-1">
          {getPageNumbers().map((p, idx) => {
            if (p === '...') {
              return (
                <span
                  key={`ellipsis-${idx}`}
                  className="px-2 py-1 text-slate-400 select-none text-xs"
                  aria-hidden="true"
                >
                  …
                </span>
              );
            }

            const pageNum = p as number;
            const isCurrent = pageNum === page;

            return (
              <button
                key={pageNum}
                type="button"
                onClick={() => onPageChange(pageNum)}
                aria-current={isCurrent ? 'page' : undefined}
                className={cn(
                  'inline-flex items-center justify-center min-h-[44px] min-w-[44px] px-3 rounded-lg text-xs sm:text-sm font-semibold transition-all select-none',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                  isCurrent
                    ? 'bg-brand-600 text-white shadow-2xs'
                    : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                )}
              >
                {pageNum}
              </button>
            );
          })}
        </div>

        {/* Botão Próxima */}
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className={cn(
            'inline-flex items-center justify-center min-h-[44px] min-w-[44px] px-2.5 rounded-lg border border-slate-200 bg-white text-slate-700 font-medium transition-all shadow-2xs',
            'hover:bg-slate-50 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
            'disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none'
          )}
          aria-label="Próxima página"
        >
          <span className="hidden sm:inline">Próxima</span>
          <ChevronRight className="w-4 h-4 ml-1 shrink-0" aria-hidden="true" />
        </button>
      </div>
    </nav>
  );
};
