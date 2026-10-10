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
        'bg-amber-50/80 border border-amber-200 text-amber-950 rounded-xl flex items-start sm:items-center gap-2.5 text-xs shadow-2xs',
        compact ? 'px-3 py-2 text-[11px]' : 'p-3.5',
        className
      )}
    >
      <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5 sm:mt-0" />
      <span className="leading-relaxed font-medium tracking-tight">
        <strong className="text-amber-900">Aviso Legal Obrigatório:</strong> {LEGAL_DISCLAIMER_TEXT}
      </span>
    </div>
  );
};
