-- ============================================================================
-- MIGRATION: 20261009000004_phase4_comparison_origins_export.sql
-- FASE 4: Comparação, Mapeamento de Origens, Renumeração, DePara e Exportação Preliminar
-- Compatível com PRD Mestre v3.0 (Seções 13, 14, 22.4 e Critérios CA-19 a CA-22, CA-42)
-- ============================================================================

-- 1. MAPEAMENTO EXPLÍCITO DE ORIGENS (app.origin_mappings)
-- Relação muitos-para-muitos entre revisões da minuta e dispositivos da fonte original (CA-21)
CREATE TABLE IF NOT EXISTS app.origin_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    revision_id UUID NOT NULL REFERENCES app.provision_revisions(id) ON DELETE CASCADE,
    source_provision_id UUID NOT NULL REFERENCES app.source_provisions(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL DEFAULT 'mantido'
        CHECK (relation_type IN ('mantido', 'alterado', 'desmembrado', 'consolidado')),
    excerpt TEXT,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. REFERÊNCIAS CRUZADAS ESTRUTURADAS (app.cross_references)
-- Apontam sempre para o UUID estável do dispositivo (Provision.id), mantendo integridade na renumeração (CA-22)
CREATE TABLE IF NOT EXISTS app.cross_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    revision_id UUID NOT NULL REFERENCES app.provision_revisions(id) ON DELETE CASCADE,
    target_provision_id UUID NOT NULL REFERENCES app.provisions(id) ON DELETE CASCADE,
    label_template VARCHAR(100) NOT NULL DEFAULT 'art. {target_label}',
    status VARCHAR(50) NOT NULL DEFAULT 'valido'
        CHECK (status IN ('valido', 'quebrado', 'pendente')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- ÍNDICES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_origin_mappings_condo ON app.origin_mappings(condominium_id);
CREATE INDEX IF NOT EXISTS idx_origin_mappings_rev ON app.origin_mappings(revision_id);
CREATE INDEX IF NOT EXISTS idx_origin_mappings_source ON app.origin_mappings(source_provision_id);
CREATE INDEX IF NOT EXISTS idx_cross_references_condo ON app.cross_references(condominium_id);
CREATE INDEX IF NOT EXISTS idx_cross_references_rev ON app.cross_references(revision_id);
CREATE INDEX IF NOT EXISTS idx_cross_references_target ON app.cross_references(target_provision_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
ALTER TABLE app.origin_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.origin_mappings FORCE ROW LEVEL SECURITY;
ALTER TABLE app.cross_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.cross_references FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_origin_mappings_tenant ON app.origin_mappings
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_cross_references_tenant ON app.cross_references
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
