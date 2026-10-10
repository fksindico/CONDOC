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
  unit_number: string;
  ideal_fraction?: number;
  block?: string;
  floor?: string;
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
  account_id: UUID;
  category: ResidentCategory;
  verification_status: VerificationStatus;
  verification_method?: 'documento' | 'declaracao_sindico' | 'cadastro_legado';
  verified_at?: ISODateString;
  verified_by?: UUID;
  valid_from: ISODateString;
  valid_until?: ISODateString;
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

export type ProjectType = 'convencao' | 'regimento_interno' | 'estatuto' | 'outro';
export type ProjectStatus = 'em_elaboracao' | 'em_consulta' | 'concluido' | 'arquivado';

export interface DocumentProject {
  id: UUID;
  condominium_id: UUID;
  title: string;
  project_type: ProjectType;
  status: ProjectStatus;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export type ProvisionType =
  | 'titulo'
  | 'capitulo'
  | 'secao'
  | 'artigo'
  | 'paragrafo'
  | 'inciso'
  | 'alinea'
  | 'item';

export interface Provision {
  id: UUID;
  project_id: UUID;
  parent_id?: UUID;
  provision_type: ProvisionType;
  prefix: string;
  order_index: number;
  current_revision_id: UUID;
  created_at: ISODateString;
}

export interface ProvisionRevision {
  id: UUID;
  provision_id: UUID;
  revision_number: number;
  content_html: string;
  content_text: string;
  justification?: string;
  created_by: UUID;
  created_at: ISODateString;
}

export type OriginMappingType =
  | 'inalterado'
  | 'modificado'
  | 'novo_sem_origem'
  | 'desmembrado'
  | 'consolidado'
  | 'excluido';

export interface OriginMapping {
  id: UUID;
  new_provision_id?: UUID;
  source_provision_id?: UUID;
  mapping_type: OriginMappingType;
  notes?: string;
}

export interface DocumentSnapshot {
  id: UUID;
  project_id: UUID;
  snapshot_number: number;
  label: string;
  immutable_hash: string;
  created_at: ISODateString;
}

// ==========================================
// Campanhas Consultivas e Moderação
// ==========================================

export type CampaignStatus = 'rascunho' | 'aberta' | 'em_consolidacao' | 'encerrada';

export interface ConsultationCampaign {
  id: UUID;
  condominium_id: UUID;
  project_id: UUID;
  snapshot_id: UUID;
  title: string;
  description?: string;
  starts_at: ISODateString;
  ends_at: ISODateString;
  status: CampaignStatus;
  hide_counts: boolean;
  created_at: ISODateString;
}

export type EditorialDecision =
  | 'pendente'
  | 'acolhida'
  | 'acolhida_parcialmente'
  | 'nao_acolhida'
  | 'duplicada';

export interface Suggestion {
  id: UUID;
  public_id: string; // ID opaco desvinculado do autor
  campaign_id: UUID;
  provision_id: UUID;
  snapshot_id: UUID;
  suggested_text: string;
  justification?: string;
  editorial_decision: EditorialDecision;
  editorial_notes?: string;
  is_published: boolean;
  published_at?: ISODateString;
  published_by?: UUID; // Apenas Síndico ativo
  created_at: ISODateString;
}

export interface ConsultativeAgreement {
  id: UUID;
  campaign_id: UUID;
  target_type: 'provision_revision' | 'suggestion_revision';
  target_id: UUID;
  account_id: UUID;
  unit_id: UUID;
  agreed_at: ISODateString;
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
