-- ============================================================================
-- FASE 7: PRESERVAÇÃO E PACOTES DE PUBLICAÇÃO FINAL
-- Arquitetura e Governança do PRD Mestre v3.0 (Critérios CA-41, CA-42, CA-45, UI-33, UI-38)
-- ============================================================================

-- 1. Tipos Enumerados para Artefatos de Exportação e Preservação
DO $$ BEGIN
    CREATE TYPE app.export_artifact_kind AS ENUM (
        'pacote_externo_publico',
        'relatorio_interno_comissao',
        'minuta_final_limpa',
        'relatorio_depara_final'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE app.export_artifact_status AS ENUM ('gerando', 'concluido', 'falha');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Tabela: Artefatos de Exportação e Preservação (ExportArtifact)
CREATE TABLE IF NOT EXISTS app.export_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    document_id UUID REFERENCES app.documents(id) ON DELETE CASCADE,
    snapshot_id UUID REFERENCES app.document_snapshots(id) ON DELETE SET NULL,
    kind app.export_artifact_kind NOT NULL,
    status app.export_artifact_status NOT NULL DEFAULT 'concluido',
    is_public BOOLEAN NOT NULL DEFAULT true,
    manifest_hash TEXT NOT NULL,
    files_manifest JSONB NOT NULL DEFAULT '[]'::jsonb,
    disclaimer TEXT NOT NULL,
    generated_by_id UUID REFERENCES app.accounts(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_artifacts_condo ON app.export_artifacts(condominium_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_doc ON app.export_artifacts(document_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_kind ON app.export_artifacts(kind);
CREATE INDEX IF NOT EXISTS idx_artifacts_public ON app.export_artifacts(is_public);

-- 3. Habilitação de RLS
ALTER TABLE app.export_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.export_artifacts FORCE ROW LEVEL SECURITY;

-- 4. Política de Isolamento Multi-Tenancy
DO $$ BEGIN
    CREATE POLICY rls_export_artifacts ON app.export_artifacts
        FOR ALL USING (condominium_id = app.current_tenant_id());
EXCEPTION WHEN duplicate_object THEN null; END $$;
