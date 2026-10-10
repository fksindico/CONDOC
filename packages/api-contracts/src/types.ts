/**
 * Tipos TypeScript Canônicos — CONDC API v1
 * Baseados no PRD Mestre v3.0 e Contrato_API_v3.md
 *
 * ATENÇÃO: É estritamente vedada a inclusão de modelos, campos ou enumerações
 * relacionados a votação, eleições, quórum ou deliberação assemblear.
 */

// ==========================================
// Identidade e Multi-tenancy
// ==========================================

export type UUID = string;
export type ISODateString = string;

export interface Condominium {
  id: UUID;
  name: string;
  cnpj: string;
  address_street: string;
  address_number: string;
  address_complement?: string;
  address_neighborhood: string;
  address_city: string;
  address_state: string;
  address_zip_code: string;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface Building {
  id: UUID;
  condominium_id: UUID;
  name: string;
  code?: string;
  display_order: number;
  created_at: ISODateString;
}

export interface Unit {
  id: UUID;
  condominium_id: UUID;
  building_id?: UUID;
  code: string;
  unit_number?: string; // alias retrocompatível
  ideal_fraction?: number;
  block?: string;
  floor?: string;
  floor_label?: string;
  status?: string;
  created_at: ISODateString;
}

export type RoleType =
  | 'sindico'
  | 'subsindico'
  | 'conselheiro'
  | 'comissao'
  | 'juridico'
  | 'administrador'
  | 'morador';

export interface Account {
  id: UUID;
  auth_user_id: UUID;
  full_name: string;
  email: string;
  phone?: string;
  is_active: boolean;
  mfa_enabled: boolean;
  created_at: ISODateString;
}

export type ResidentCategory =
  | 'proprietario_residente'
  | 'proprietario_nao_residente'
  | 'inquilino'
  | 'dependente'
  | 'procurador';

export type VerificationStatus =
  | 'pendente'
  | 'em_analise'
  | 'validado'
  | 'recusado'
  | 'revogado';

export interface UnitMembership {
  id: UUID;
  condominium_id: UUID;
  unit_id: UUID;
  resident_id?: UUID;
  account_id?: UUID;
  category: ResidentCategory;
  verification_status: VerificationStatus;
  verification_method?: 'documento' | 'declaracao_sindico' | 'cadastro_legado' | 'presencial';
  verified_at?: ISODateString;
  verified_by?: UUID;
  valid_from: ISODateString;
  valid_until?: ISODateString;
  membership_status?: 'active' | 'suspended' | 'ended';
  created_at: ISODateString;
}

// ==========================================
// Convites e Importação
// ==========================================

export type InvitationType = 'individual' | 'por_unidade' | 'amplo';
export type InvitationStatus = 'ativo' | 'usado' | 'expirado' | 'revogado';

export interface AccessInvitation {
  id: UUID;
  condominium_id: UUID;
  target_unit_id?: UUID;
  target_email?: string;
  invitation_type: InvitationType;
  status: InvitationStatus;
  max_uses: number;
  uses_count: number;
  expires_at: ISODateString;
  created_at: ISODateString;
}

export type ImportBatchStatus =
  | 'received'
  | 'parsing'
  | 'awaiting_mapping'
  | 'validating'
  | 'awaiting_review'
  | 'applying'
  | 'completed'
  | 'failed';

export interface ImportBatch {
  id: UUID;
  condominium_id: UUID;
  file_name: string;
  status: ImportBatchStatus;
  total_rows: number;
  valid_rows: number;
  conflict_rows: number;
  created_at: ISODateString;
}

// ==========================================
// Núcleo Documental
// ==========================================

export type ProjectType = 'criacao' | 'revisao' | 'conjunta' | 'convencao' | 'regimento_interno' | 'estatuto' | 'outro';
export type ProjectStatus = 'preparacao' | 'estruturacao' | 'redacao' | 'consulta' | 'consolidacao' | 'revisao_opcional' | 'final_trabalho' | 'publicado' | 'arquivado' | 'em_elaboracao' | 'em_consulta' | 'concluido';

export interface Project {
  id: UUID;
  condominium_id: UUID;
  name: string;
  purpose?: string;
  kind: ProjectType;
  status: ProjectStatus;
  coordinator_account_id?: UUID;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export type DocumentProject = Project; // alias retrocompatível

export interface Document {
  id: UUID;
  project_id: UUID;
  condominium_id: UUID;
  title: string;
  type: 'convencao' | 'regimento_interno' | 'anexo_normativo';
  editorial_status: 'rascunho' | 'em_revisao' | 'aprovado_para_consulta' | 'congelado' | 'consolidado';
  numbering_policy: string;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export type ProvisionType =
  | 'titulo'
  | 'capitulo'
  | 'secao'
  | 'artigo'
  | 'caput'
  | 'paragrafo'
  | 'inciso'
  | 'alinea'
  | 'item';

export interface Provision {
  id: UUID;
  document_id?: UUID;
  project_id?: UUID;
  parent_id?: UUID;
  kind?: ProvisionType;
  provision_type?: ProvisionType;
  created_at: ISODateString;
  updated_at?: ISODateString;
}

export interface ProvisionRevision {
  id: UUID;
  provision_id: UUID;
  document_id?: UUID;
  condominium_id?: UUID;
  revision_number: number;
  label?: string;
  text: string;
  content_text?: string;
  content_html?: string;
  theme?: string;
  change_type?: 'mantido' | 'alterado' | 'incluido' | 'excluido' | 'renumerado' | 'desmembrado' | 'consolidado';
  etag?: string;
  justification?: string;
  author_account_id?: UUID;
  created_at: ISODateString;
}

export type OriginRelationType = 'mantido' | 'alterado' | 'desmembrado' | 'consolidado';
export type OriginMappingType = OriginRelationType | 'inalterado' | 'modificado' | 'novo_sem_origem' | 'excluido';

export interface OriginMapping {
  id: UUID;
  condominium_id?: UUID;
  revision_id?: UUID;
  new_provision_id?: UUID;
  source_provision_id?: UUID;
  relation_type?: OriginRelationType;
  mapping_type?: OriginMappingType;
  excerpt?: string;
  reason?: string;
  notes?: string;
  created_at?: ISODateString;
}

export interface CrossReference {
  id: UUID;
  condominium_id: UUID;
  revision_id: UUID;
  target_provision_id: UUID;
  label_template: string;
  status: 'valido' | 'quebrado' | 'suspenso';
  created_at: ISODateString;
}

export interface DocumentSnapshot {
  id: UUID;
  document_id?: UUID;
  project_id?: UUID;
  version_label?: string;
  purpose?: string;
  snapshot_number?: number;
  label?: string;
  content_hash?: string;
  immutable_hash?: string;
  is_immutable?: boolean;
  frozen_at?: ISODateString;
  created_at: ISODateString;
}

// ==========================================
// Campanhas Consultivas e Moderação
// ==========================================

export type CampaignStatus = 'rascunho' | 'aberta' | 'pausada' | 'encerrada' | 'em_consolidacao';

export interface ConsultationCampaign {
  id: UUID;
  condominium_id: UUID;
  project_id: UUID;
  snapshot_id: UUID;
  name: string;
  title?: string;
  description?: string;
  state?: CampaignStatus;
  status?: CampaignStatus;
  start_date?: ISODateString;
  end_date?: ISODateString;
  starts_at?: ISODateString;
  ends_at?: ISODateString;
  settings?: Record<string, unknown>;
  hide_counts?: boolean;
  created_at: ISODateString;
  updated_at?: ISODateString;
}

export type AnalysisStatus = 'pendente' | 'em_analise' | 'concluida';
export type PublicationStatus = 'nao_publicada' | 'publicada' | 'oculta';
export type IncorporationStatus = 'nao_incorporada' | 'incorporada';

export type EditorialDecision =
  | 'pendente'
  | 'acolhida'
  | 'acolhida_parcial'
  | 'acolhida_parcialmente'
  | 'rejeitada'
  | 'nao_acolhida'
  | 'duplicada';

export interface Suggestion {
  id: UUID;
  public_protocol: string;
  public_id?: string;
  campaign_id: UUID;
  target_provision_id?: UUID;
  target_snapshot_revision_id?: UUID;
  category: 'redacao' | 'clareza' | 'supressao' | 'adicao' | 'adequacao_legal' | 'geral';
  analysis_status: AnalysisStatus;
  editorial_decision: EditorialDecision;
  publication_status: PublicationStatus;
  incorporation_status: IncorporationStatus;
  parent_published_suggestion_id?: UUID;
  created_at: ISODateString;
  updated_at?: ISODateString;
}

export interface ConsultativeAgreement {
  id: UUID;
  condominium_id?: UUID;
  participant_id?: UUID;
  published_suggestion_revision_id?: UUID;
  active: boolean;
  campaign_id?: UUID;
  account_id?: UUID;
  unit_id?: UUID;
  created_at: ISODateString;
  updated_at?: ISODateString;
}

export interface ExportArtifact {
  id: UUID;
  condominium_id: UUID;
  document_id?: UUID;
  snapshot_id?: UUID;
  kind: 'pacote_externo_publico' | 'relatorio_interno_comissao' | 'minuta_final_limpa' | 'relatorio_depara_final';
  status: 'gerando' | 'concluido' | 'falha';
  is_public: boolean;
  manifest_hash: string;
  files_manifest: Array<{
    path: string;
    sha256: string;
    size_bytes: number;
    mime_type: string;
  }>;
  disclaimer: string;
  created_at: ISODateString;
}

// ==========================================
// Tratamento de Erros e Respostas Padrão
// ==========================================

export interface ApiError {
  code: string;
  message: string;
  request_id: string;
  details?: Record<string, string[]>;
}

export interface ApiResponse<T> {
  data: T;
  request_id: string;
}
