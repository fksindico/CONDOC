import { describe, it, expect } from 'vitest';
import { consultationService } from '../services/consultationService';

describe('Serviço de Consultas Simplificadas (Frontend)', () => {
  it('getExportUrl deve construir a URL correta de download CSV do condomínio e consulta', () => {
    const condoId = 'b0f80b9c-8515-46aa-bca4-d8350b55ec90';
    const consultationId = 'a1e20c3d-1122-3344-5566-778899aabbcc';
    const url = consultationService.getExportUrl(condoId, consultationId);
    expect(url).toBe(
      `/api/v1/condominiums/${condoId}/consultations/${consultationId}/export`
    );
  });
});
