import { api } from '@/lib/api';

export interface StructureUnit {
  id: string;
  code: string;
  floor_label: string;
}

export interface StructureBuilding {
  id: string | null;
  name: string;
  code: string;
  units: StructureUnit[];
}

export interface PublicStructure {
  buildings: StructureBuilding[];
  total_units: number;
}

export interface PublicConsultation {
  id: string;
  title: string;
  document_type: 'regimento' | 'convencao';
  description?: string;
  pdf_original_name: string;
  pdf_size_bytes: number;
  public_token: string;
  status: 'aberta' | 'pausada' | 'encerrada';
  deadline?: string;
  thank_you_message?: string;
  default_thank_you_message?: string;
  condominium_name: string;
  pdf_download_url: string;
  structure?: PublicStructure;
  created_at: string;
}

export interface AdminConsultation extends PublicConsultation {
  condominium_id: string;
  suggestions_count: number;
  thank_you_message?: string;
  updated_at: string;
}

export interface SuggestionSubmission {
  resident_name: string;
  resident_phone: string;
  resident_email?: string;
  block_tower?: string;
  unit_code: string;
  target_reference: string;
  action_type: 'alterar' | 'remover' | 'incluir';
  suggestion_text: string;
  justification?: string;
}

export interface ConsultationSuggestionItem {
  id: string;
  condominium_id?: string;
  consultation_id?: string;
  protocol: string;
  resident_name: string;
  resident_phone: string;
  resident_email?: string;
  block_tower?: string;
  unit_code: string;
  target_reference: string;
  action_type: 'alterar' | 'remover' | 'incluir';
  suggestion_text: string;
  justification?: string;
  has_divergence?: boolean;
  divergence_details?: string;
  registered_email?: string;
  thank_you_message?: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface PublicLandingInfo {
  id: string;
  name: string;
  landing_title?: string | null;
  landing_subtitle?: string | null;
  landing_description?: string | null;
  landing_contact_email?: string | null;
  landing_contact_phone?: string | null;
  default_thank_you_message?: string | null;
  open_consultations: {
    id: string;
    title: string;
    document_type: 'regimento' | 'convencao';
    description?: string | null;
    public_token: string;
    pdf_original_name: string;
    deadline?: string | null;
  }[];
}

export const consultationService = {
  // Endpoints Públicos (Morador via Token e Landing Page)
  async getPublicLandingInfo(condoId?: string): Promise<PublicLandingInfo> {
    const url = condoId ? `/public/landing-info?condominium_id=${condoId}` : '/public/landing-info';
    const res = await api.get<PublicLandingInfo>(url);
    return res.data;
  },

  async getPublicConsultation(token: string): Promise<PublicConsultation> {
    const res = await api.get<PublicConsultation>(`/public/consultations/${token}`);
    return res.data;
  },

  async submitSuggestion(token: string, data: SuggestionSubmission): Promise<ConsultationSuggestionItem> {
    const res = await api.post<ConsultationSuggestionItem>(`/public/consultations/${token}/suggestions`, data);
    return res.data;
  },

  async getMySuggestions(token: string, params: { phone?: string; unit?: string; protocol?: string }): Promise<ConsultationSuggestionItem[]> {
    const query = new URLSearchParams();
    if (params.phone) query.append('phone', params.phone);
    if (params.unit) query.append('unit', params.unit);
    if (params.protocol) query.append('protocol', params.protocol);

    const res = await api.get<ConsultationSuggestionItem[]>(`/public/consultations/${token}/my-suggestions?${query.toString()}`);
    return res.data;
  },

  // Endpoints Administrativos (Síndico)
  async getAdminConsultations(condoId: string): Promise<AdminConsultation[]> {
    const res = await api.get<AdminConsultation[]>(`/condominiums/${condoId}/consultations`);
    return res.data;
  },

  async createAdminConsultation(condoId: string, formData: FormData): Promise<AdminConsultation> {
    const res = await api.post<AdminConsultation>(`/condominiums/${condoId}/consultations`, formData);
    return res.data;
  },

  async updateAdminConsultation(condoId: string, consultationId: string, data: Partial<AdminConsultation>): Promise<AdminConsultation> {
    const res = await api.patch<AdminConsultation>(`/condominiums/${condoId}/consultations/${consultationId}`, data);
    return res.data;
  },

  async deleteAdminConsultation(condoId: string, consultationId: string): Promise<void> {
    await api.delete<void>(`/condominiums/${condoId}/consultations/${consultationId}`);
  },

  async getAdminSuggestions(
    condoId: string,
    consultationId: string,
    filters?: { action_type?: string; unit_code?: string; block_tower?: string; search?: string; has_divergence?: boolean }
  ): Promise<ConsultationSuggestionItem[]> {
    const query = new URLSearchParams();
    if (filters?.action_type && filters.action_type !== 'todos') query.append('action_type', filters.action_type);
    if (filters?.unit_code) query.append('unit_code', filters.unit_code);
    if (filters?.block_tower) query.append('block_tower', filters.block_tower);
    if (filters?.search) query.append('search', filters.search);
    if (filters?.has_divergence !== undefined) query.append('has_divergence', String(filters.has_divergence));

    const res = await api.get<ConsultationSuggestionItem[]>(
      `/condominiums/${condoId}/consultations/${consultationId}/suggestions?${query.toString()}`
    );
    return res.data;
  },

  getExportUrl(condoId: string, consultationId: string): string {
    return `/api/v1/condominiums/${condoId}/consultations/${consultationId}/export`;
  },
};
