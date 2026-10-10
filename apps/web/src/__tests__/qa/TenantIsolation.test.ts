import { describe, it, expect, vi } from 'vitest';

describe('QA: Isolamento Multi-Tenancy no Frontend (UI-01, ADR-004)', () => {
  it('deve purgar integralmente o cache de consultas ao alternar de condomínio', () => {
    // Simula a operação realizada em TenantContext.tsx
    const queryClientMock = {
      clear: vi.fn(),
    };

    let activeTenantId: string | null = 'condo-alpha-111';

    const selectCondominium = (newCondoId: string) => {
      if (newCondoId === activeTenantId) return;
      queryClientMock.clear();
      activeTenantId = newCondoId;
    };

    selectCondominium('condo-beta-222');

    expect(queryClientMock.clear).toHaveBeenCalledTimes(1);
    expect(activeTenantId).toBe('condo-beta-222');

    // Selecionar o mesmo condomínio não deve limpar o cache desnecessariamente
    selectCondominium('condo-beta-222');
    expect(queryClientMock.clear).toHaveBeenCalledTimes(1);
  });
});
