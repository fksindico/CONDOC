import { describe, it, expect } from 'vitest';
import { LEGAL_DISCLAIMER_TEXT } from '../components/ui/LegalDisclaimerBanner';

describe('Aviso Legal Permanente de Consulta (UI-28, CA-35)', () => {
  it('deve conter a ressalva mandatória de não constituição de voto ou aprovação em assembleia', () => {
    expect(LEGAL_DISCLAIMER_TEXT).toContain('Manifestação consultiva sobre esta redação');
    expect(LEGAL_DISCLAIMER_TEXT).toContain('Não constitui voto');
    expect(LEGAL_DISCLAIMER_TEXT).toContain('quórum de assembleia');
    expect(LEGAL_DISCLAIMER_TEXT).toContain('aprovação vinculante');
  });
});
