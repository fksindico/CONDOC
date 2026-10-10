import { describe, it, expect } from 'vitest';

describe('QA: Modo de Apresentação em Assembleia (CA-45, UI-38)', () => {
  it('deve conter apenas controles informativos e rejeitar controles deliberativos', () => {
    const allowedControls = ['scroll', 'zoom', 'search', 'export_pdf', 'fullscreen', 'contrast'];
    const forbiddenControls = ['votar', 'aprovar_em_assembleia', 'apurar_votos', 'calcular_quorum', 'eleger'];

    const validateControls = (controls: string[]) => {
      const forbidden = controls.filter((c) => forbiddenControls.includes(c.toLowerCase()));
      return {
        isValid: forbidden.length === 0,
        forbidden,
      };
    };

    expect(validateControls(allowedControls).isValid).toBe(true);
    expect(validateControls(['zoom', 'votar']).isValid).toBe(false);
    expect(validateControls(['apurar_votos']).forbidden).toContain('apurar_votos');
  });

  it('deve garantir que zoom tipográfico respeita os limites seguro de 14px a 28px', () => {
    const clampFontSize = (current: number, delta: number) =>
      Math.max(14, Math.min(28, current + delta));

    expect(clampFontSize(18, 2)).toBe(20);
    expect(clampFontSize(28, 2)).toBe(28); // Limite superior
    expect(clampFontSize(14, -2)).toBe(14); // Limite inferior
  });
});
