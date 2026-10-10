import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LegalDisclaimerBannerProps {
  className?: string;
  compact?: boolean;
}

export const LEGAL_DISCLAIMER_TEXT =
  'Manifestação consultiva sobre esta redação. Não constitui voto, eleição, quórum de assembleia, aprovação vinculante ou alteração da Convenção/Regimento.';

export const LegalDisclaimerBanner: React.FC<LegalDisclaimerBannerProps> = ({ className, compact = false }) => {
  return (
    <div
      className={cn(
        'bg-slate-100 border border-slate-200 text-slate-700 rounded-lg flex items-center gap-2.5 text-xs',
        compact ? 'px-3 py-1.5 text-[11px]' : 'p-3',
        className
      )}
    >
      <ShieldAlert className="w-4 h-4 text-slate-500 shrink-0" />
      <span className="leading-tight font-medium tracking-tight">
        <strong>Aviso Legal Obrigatório:</strong> {LEGAL_DISCLAIMER_TEXT}
      </span>
    </div>
  );
};
