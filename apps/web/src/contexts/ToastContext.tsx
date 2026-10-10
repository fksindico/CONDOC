import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
}

interface ToastContextType {
  toast: {
    success: (message: string, title?: string) => void;
    error: (message: string, title?: string) => void;
    warning: (message: string, title?: string) => void;
    info: (message: string, title?: string) => void;
  };
  showToast: (toast: Omit<ToastItem, 'id'>) => void;
  dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    ({ type, title, message, duration = 4000 }: Omit<ToastItem, 'id'>) => {
      const id = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const newToast: ToastItem = { id, type, title, message, duration };

      setToasts((prev) => [...prev.slice(-4), newToast]); // Mantém no máximo 5 toasts simultâneos

      if (duration > 0) {
        setTimeout(() => {
          dismissToast(id);
        }, duration);
      }
    },
    [dismissToast]
  );

  const toast = {
    success: (message: string, title?: string) => showToast({ type: 'success', message, title }),
    error: (message: string, title?: string) => showToast({ type: 'error', message, title }),
    warning: (message: string, title?: string) => showToast({ type: 'warning', message, title }),
    info: (message: string, title?: string) => showToast({ type: 'info', message, title }),
  };

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />,
    error: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />,
    info: <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />,
  };

  const borderStyles = {
    success: 'border-emerald-200 bg-white/95 text-slate-800 shadow-emerald-500/10',
    error: 'border-rose-200 bg-white/95 text-slate-800 shadow-rose-500/10',
    warning: 'border-amber-200 bg-white/95 text-slate-800 shadow-amber-500/10',
    info: 'border-blue-200 bg-white/95 text-slate-800 shadow-blue-500/10',
  };

  return (
    <ToastContext.Provider value={{ toast, showToast, dismissToast }}>
      {children}

      {/* Container Flutuante de Notificações Toast */}
      <div
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-3 sm:px-0"
        aria-live="polite"
        role="region"
        aria-label="Notificações do sistema"
      >
        {toasts.map((item) => (
          <div
            key={item.id}
            className={cn(
              'pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border shadow-lg backdrop-blur-md transition-all duration-200 ease-out transform translate-y-0 opacity-100 animate-in slide-in-from-bottom-2',
              borderStyles[item.type]
            )}
            role="status"
          >
            {icons[item.type]}
            <div className="flex-1 min-w-0 pr-1">
              {item.title && <h5 className="font-semibold text-xs text-slate-900 leading-snug">{item.title}</h5>}
              <p className="text-xs text-slate-600 leading-relaxed mt-0.5 break-words">{item.message}</p>
            </div>
            <button
              onClick={() => dismissToast(item.id)}
              className="text-slate-400 hover:text-slate-600 rounded-md p-0.5 transition-colors cursor-pointer"
              aria-label="Fechar notificação"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast deve ser utilizado dentro de um ToastProvider');
  }
  return context;
};
