-- ============================================================================
-- FASE 6: CONCORDÂNCIAS CONSULTIVAS E CONSOLIDAÇÃO NA MINUTA
-- Arquitetura e Governança do PRD Mestre v3.0 (Critérios CA-35 a CA-40, CA-45, V21-29 a V21-31, V21-34, V21-37)
-- ============================================================================

-- 1. Tipo Enumerado de Ações de Concordância Consultiva
DO $$ BEGIN
    CREATE TYPE app.agreement_action AS ENUM ('agree', 'withdraw', 'reaffirm', 'invalidate');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Tabela: Concordâncias Consultivas (ConsultativeAgreement - CA-35, CA-37)
CREATE TABLE IF NOT EXISTS app.consultative_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES app.campaign_participants(id) ON DELETE RESTRICT,
    published_suggestion_revision_id UUID NOT NULL REFERENCES app.published_suggestion_revisions(id) ON DELETE CASCADE,
    membership_at_action_id UUID NOT NULL REFERENCES app.unit_memberships(id) ON DELETE RESTRICT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    UNIQUE (participant_id, published_suggestion_revision_id)
);

CREATE INDEX IF NOT EXISTS idx_agreements_condo ON app.consultative_agreements(condominium_id);
CREATE INDEX IF NOT EXISTS idx_agreements_participant ON app.consultative_agreements(participant_id);
CREATE INDEX IF NOT EXISTS idx_agreements_pub_rev ON app.consultative_agreements(published_suggestion_revision_id);
CREATE INDEX IF NOT EXISTS idx_agreements_active ON app.consultative_agreements(active);

-- 3. Tabela: Eventos de Concordância e Retirada (AgreementEvent - CA-36)
CREATE TABLE IF NOT EXISTS app.agreement_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    agreement_id UUID NOT NULL REFERENCES app.consultative_agreements(id) ON DELETE CASCADE,
    action app.agreement_action NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_agreement_events_condo ON app.agreement_events(condominium_id);
CREATE INDEX IF NOT EXISTS idx_agreement_events_agr ON app.agreement_events(agreement_id);

-- 4. Tabela: Incorporação de Sugestão na Minuta (SuggestionIncorporation - CA-40)
CREATE TABLE IF NOT EXISTS app.suggestion_incorporations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    suggestion_id UUID NOT NULL REFERENCES app.suggestions(id) ON DELETE CASCADE,
    provision_revision_id UUID NOT NULL REFERENCES app.provision_revisions(id) ON DELETE CASCADE,
    description TEXT,
    incorporated_by_id UUID NOT NULL REFERENCES app.accounts(id),
    incorporated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_incorporations_condo ON app.suggestion_incorporations(condominium_id);
CREATE INDEX IF NOT EXISTS idx_incorporations_sug ON app.suggestion_incorporations(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_incorporations_prov_rev ON app.suggestion_incorporations(provision_revision_id);

-- 5. Tabela: Fotografia Estatística Imutável (ConsultationSnapshot - CA-39)
CREATE TABLE IF NOT EXISTS app.consultation_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES app.consultation_campaigns(id) ON DELETE CASCADE,
    cut_timestamp TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    total_eligible_participants INT NOT NULL DEFAULT 0,
    total_eligible_units INT NOT NULL DEFAULT 0,
    stats_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    disclaimer TEXT NOT NULL,
    created_by_id UUID REFERENCES app.accounts(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_consultation_snaps_condo ON app.consultation_snapshots(condominium_id);
CREATE INDEX IF NOT EXISTS idx_consultation_snaps_camp ON app.consultation_snapshots(campaign_id);

-- 6. Habilitação de RLS para todas as tabelas
ALTER TABLE app.consultative_agreements ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.agreement_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.suggestion_incorporations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.consultation_snapshots ENABLE ROW LEVEL SECURITY;

-- 7. Políticas RLS de Isolamento Multi-Tenancy
DO $$ BEGIN
    CREATE POLICY rls_consultative_agreements ON app.consultative_agreements
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_agreement_events ON app.agreement_events
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_suggestion_incorporations ON app.suggestion_incorporations
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE POLICY rls_consultation_snapshots ON app.consultation_snapshots
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;
