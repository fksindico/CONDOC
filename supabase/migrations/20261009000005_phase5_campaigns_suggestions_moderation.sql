-- ============================================================================
-- FASE 5: CONSULTA PÚBLICA, PARTICIPAÇÃO E MODERAÇÃO EDITORIAL
-- Arquitetura e Governança do PRD Mestre v3.0 (Critérios CA-25 a CA-34, V21-26 a V21-28, V21-32, V21-36)
-- ============================================================================

-- 1. Tipos Enumerados de Campanhas, Moderação e Sugestões
DO $$ BEGIN
    CREATE TYPE app.campaign_state AS ENUM ('rascunho', 'aberta', 'pausada', 'encerrada');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE app.campaign_participant_status AS ENUM ('habilitado', 'suspenso', 'revogado');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE app.suggestion_category AS ENUM (
        'redacao', 'clareza', 'supressao', 'adicao', 'adequacao_legal', 'geral'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE app.analysis_status AS ENUM ('pendente', 'em_analise', 'concluida');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE app.editorial_decision_type AS ENUM (
        'pendente', 'acolhida', 'acolhida_parcial', 'rejeitada', 'duplicada'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE app.publication_status AS ENUM ('nao_publicada', 'publicada', 'oculta');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE app.incorporation_status AS ENUM ('nao_incorporada', 'incorporada');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Tabela: Campanhas de Consulta Pública (ConsultationCampaign)
CREATE TABLE IF NOT EXISTS app.consultation_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES app.projects(id) ON DELETE CASCADE,
    snapshot_id UUID NOT NULL REFERENCES app.document_snapshots(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    description TEXT,
    state app.campaign_state NOT NULL DEFAULT 'rascunho',
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_campaigns_condominium ON app.consultation_campaigns(condominium_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_project ON app.consultation_campaigns(project_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_snapshot ON app.consultation_campaigns(snapshot_id);

-- 3. Tabela: Participantes da Campanha (CampaignParticipant)
CREATE TABLE IF NOT EXISTS app.campaign_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES app.consultation_campaigns(id) ON DELETE CASCADE,
    resident_id UUID NOT NULL REFERENCES app.residents(id) ON DELETE CASCADE,
    reference_membership_id UUID NOT NULL REFERENCES app.unit_memberships(id) ON DELETE RESTRICT,
    status app.campaign_participant_status NOT NULL DEFAULT 'habilitado',
    authorized_by_id UUID REFERENCES app.accounts(id),
    authorized_at TIMESTAMPTZ DEFAULT timezone('utc', now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    UNIQUE (campaign_id, resident_id)
);

CREATE INDEX IF NOT EXISTS idx_participants_condo ON app.campaign_participants(condominium_id);
CREATE INDEX IF NOT EXISTS idx_participants_campaign ON app.campaign_participants(campaign_id);
CREATE INDEX IF NOT EXISTS idx_participants_resident ON app.campaign_participants(resident_id);

-- 4. Tabela: Sugestões dos Moradores (Suggestion - CA-25)
CREATE TABLE IF NOT EXISTS app.suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    public_protocol TEXT NOT NULL UNIQUE,
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES app.consultation_campaigns(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES app.campaign_participants(id) ON DELETE RESTRICT,
    submitted_membership_id UUID NOT NULL REFERENCES app.unit_memberships(id) ON DELETE RESTRICT,
    target_provision_id UUID REFERENCES app.provisions(id) ON DELETE SET NULL,
    target_snapshot_revision_id UUID REFERENCES app.provision_revisions(id) ON DELETE SET NULL,
    category app.suggestion_category NOT NULL DEFAULT 'redacao',
    analysis_status app.analysis_status NOT NULL DEFAULT 'pendente',
    editorial_decision app.editorial_decision_type NOT NULL DEFAULT 'pendente',
    publication_status app.publication_status NOT NULL DEFAULT 'nao_publicada',
    incorporation_status app.incorporation_status NOT NULL DEFAULT 'nao_incorporada',
    parent_published_suggestion_id UUID REFERENCES app.suggestions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_suggestions_condo ON app.suggestions(condominium_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_campaign ON app.suggestions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_participant ON app.suggestions(participant_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_target_prov ON app.suggestions(target_provision_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_protocol ON app.suggestions(public_protocol);

-- 5. Tabela: Revisões de Conteúdo da Sugestão (SuggestionRevision - CA-31)
CREATE TABLE IF NOT EXISTS app.suggestion_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    suggestion_id UUID NOT NULL REFERENCES app.suggestions(id) ON DELETE CASCADE,
    version_number INT NOT NULL DEFAULT 1,
    text TEXT NOT NULL,
    justification TEXT NOT NULL,
    alternative_text TEXT,
    author_account_id UUID REFERENCES app.accounts(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    UNIQUE (suggestion_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_sug_revisions_suggestion ON app.suggestion_revisions(suggestion_id);

-- 6. Tabela: Revisões Publicadas pelo Síndico (PublishedSuggestionRevision - CA-28, CA-29, CA-32)
CREATE TABLE IF NOT EXISTS app.published_suggestion_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    suggestion_id UUID NOT NULL REFERENCES app.suggestions(id) ON DELETE CASCADE,
    suggestion_revision_id UUID NOT NULL REFERENCES app.suggestion_revisions(id) ON DELETE CASCADE,
    sanitized_public_text TEXT NOT NULL,
    sanitized_justification TEXT NOT NULL,
    authorized_by_id UUID NOT NULL REFERENCES app.accounts(id),
    authorized_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    hidden_at TIMESTAMPTZ,
    hidden_by_id UUID REFERENCES app.accounts(id),
    hide_reason TEXT,
    is_active_publication BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_pub_sug_suggestion ON app.published_suggestion_revisions(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_pub_sug_active ON app.published_suggestion_revisions(is_active_publication);

-- 7. Tabela: Decisões Editoriais da Moderação (SuggestionEditorialDecision - CA-27)
CREATE TABLE IF NOT EXISTS app.suggestion_editorial_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    suggestion_id UUID NOT NULL REFERENCES app.suggestions(id) ON DELETE CASCADE,
    decision app.editorial_decision_type NOT NULL,
    public_shared_reason TEXT NOT NULL,
    internal_note TEXT,
    decided_by_id UUID NOT NULL REFERENCES app.accounts(id),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_sug_decisions_suggestion ON app.suggestion_editorial_decisions(suggestion_id);

-- 8. Tabela: Anexos de Sugestões (SuggestionAttachment - CA-34)
CREATE TABLE IF NOT EXISTS app.suggestion_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    suggestion_id UUID NOT NULL REFERENCES app.suggestions(id) ON DELETE CASCADE,
    source_file_id UUID NOT NULL REFERENCES app.source_files(id) ON DELETE CASCADE,
    is_publicly_approved BOOLEAN NOT NULL DEFAULT false,
    approved_by_id UUID REFERENCES app.accounts(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_sug_attachments_sug ON app.suggestion_attachments(suggestion_id);

-- 9. Habilitação de RLS para as novas tabelas
ALTER TABLE app.consultation_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.campaign_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.suggestion_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.published_suggestion_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.suggestion_editorial_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.suggestion_attachments ENABLE ROW LEVEL SECURITY;

-- 10. Políticas RLS de Isolamento Multi-Tenancy
DO $$ BEGIN
    CREATE POLICY rls_consultation_campaigns ON app.consultation_campaigns
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_campaign_participants ON app.campaign_participants
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_suggestions ON app.suggestions
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_suggestion_revisions ON app.suggestion_revisions
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_published_suggestion_revisions ON app.published_suggestion_revisions
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_suggestion_editorial_decisions ON app.suggestion_editorial_decisions
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_suggestion_attachments ON app.suggestion_attachments
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;
