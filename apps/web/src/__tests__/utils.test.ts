import { describe, it, expect } from 'vitest';
import { cn, formatDatePtBr, formatDateOnly } from '../lib/utils';

describe('Utilitários do Frontend', () => {
  it('cn deve mesclar classes Tailwind corretamente', () => {
    expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4');
    expect(cn('bg-red-500', undefined, null, false, 'bg-blue-500')).toBe('bg-blue-500');
  });

  it('formatDatePtBr deve formatar datas ISO para padrão brasileiro', () => {
    const iso = '2026-10-10T14:30:00Z';
    const formatted = formatDatePtBr(iso);
    expect(formatted).toMatch(/10\/10\/2026/);
  });

  it('formatDateOnly deve formatar somente dia/mês/ano', () => {
    const iso = '2026-10-10T14:30:00Z';
    const formatted = formatDateOnly(iso);
    expect(formatted).toMatch(/10\/10\/2026/);
  });
});
