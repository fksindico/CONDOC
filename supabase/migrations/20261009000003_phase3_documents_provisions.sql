-- ============================================================================
-- MIGRATION: 20261009000003_phase3_documents_provisions.sql
-- FASE 3: Núcleo Documental, OCR/Transcrição, Dispositivos Estruturados, Notas Internas e Snapshots
-- Compatível com PRD Mestre v3.0 (Seções 11, 12, 13, 14, 15, 22.4 e Critérios CA-17, CA-18, CA-23, CA-24, CA-41)
-- ============================================================================

-- 1. PROJETOS DOCUMENTAIS (app.projects)
CREATE TABLE IF NOT EXISTS app.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    purpose TEXT,
    kind VARCHAR(50) NOT NULL DEFAULT 'revisao'
        CHECK (kind IN ('criacao', 'revisao', 'conjunta')),
    coordinator_account_id UUID REFERENCES app.accounts(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'preparacao'
        CHECK (status IN (
            'preparacao', 'estruturacao', 'redacao', 'consulta',
            'consolidacao', 'revisao_opcional', 'final_trabalho',
            'publicado', 'arquivado'
        )),
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. DOCUMENTOS (app.documents)
CREATE TABLE IF NOT EXISTS app.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES app.projects(id) ON DELETE CASCADE,
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL DEFAULT 'regimento_interno'
        CHECK (type IN ('convencao', 'regimento_interno', 'anexo_normativo')),
    title VARCHAR(255) NOT NULL,
    editorial_status VARCHAR(50) NOT NULL DEFAULT 'rascunho'
        CHECK (editorial_status IN (
            'rascunho', 'em_revisao', 'aprovado_para_consulta',
            'congelado', 'consolidado'
        )),
    numbering_policy VARCHAR(50) NOT NULL DEFAULT 'preservar_original'
        CHECK (numbering_policy IN ('preservar_original', 'renumeracao_automatica')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. ARQUIVOS ORIGINAIS DE ENTRADA (app.source_files)
CREATE TABLE IF NOT EXISTS app.source_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    storage_key VARCHAR(500) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    file_hash VARCHAR(64) NOT NULL, -- SHA-256
    uploaded_by_id UUID NOT NULL REFERENCES app.accounts(id),
    state VARCHAR(50) NOT NULL DEFAULT 'uploaded'
        CHECK (state IN ('uploaded', 'processing_ocr', 'ocr_completed', 'ocr_failed', 'ready')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. TRANSCRIÇÕES DO ORIGINAL / OCR (app.source_transcriptions)
CREATE TABLE IF NOT EXISTS app.source_transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES app.documents(id) ON DELETE CASCADE,
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    source_file_id UUID NOT NULL REFERENCES app.source_files(id) ON DELETE CASCADE,
    version INT NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'under_review', 'confirmed', 'superseded')),
    raw_text TEXT NOT NULL,
    corrected_text TEXT,
    checked_by_id UUID REFERENCES app.accounts(id),
    checked_at TIMESTAMPTZ,
    replaces_transcription_id UUID REFERENCES app.source_transcriptions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. DISPOSITIVOS DA FONTE ORIGINAL (app.source_provisions)
CREATE TABLE IF NOT EXISTS app.source_provisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcription_id UUID NOT NULL REFERENCES app.source_transcriptions(id) ON DELETE CASCADE,
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES app.source_provisions(id) ON DELETE CASCADE,
    kind VARCHAR(50) NOT NULL DEFAULT 'artigo'
        CHECK (kind IN (
            'titulo', 'capitulo', 'secao', 'subsecao', 'artigo',
            'caput', 'paragrafo', 'inciso', 'alinea', 'preambulo', 'anexo'
        )),
    label VARCHAR(100) NOT NULL,
    display_order INT NOT NULL DEFAULT 0,
    text TEXT NOT NULL,
    page_number INT,
    confidence_score NUMERIC(5, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. DISPOSITIVOS NORMATIVOS COM IDENTIDADE ESTÁVEL (app.provisions)
CREATE TABLE IF NOT EXISTS app.provisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES app.documents(id) ON DELETE CASCADE,
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    kind VARCHAR(50) NOT NULL DEFAULT 'artigo'
        CHECK (kind IN (
            'titulo', 'capitulo', 'secao', 'subsecao', 'artigo',
            'caput', 'paragrafo', 'inciso', 'alinea', 'preambulo', 'anexo'
        )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. REVISÕES HISTÓRICAS DO DISPOSITIVO (app.provision_revisions)
CREATE TABLE IF NOT EXISTS app.provision_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provision_id UUID NOT NULL REFERENCES app.provisions(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES app.documents(id) ON DELETE CASCADE,
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    revision_number INT NOT NULL DEFAULT 1,
    parent_provision_id UUID REFERENCES app.provisions(id) ON DELETE SET NULL,
    position INT NOT NULL DEFAULT 0,
    label VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    theme VARCHAR(100),
    change_type VARCHAR(50) NOT NULL DEFAULT 'mantido'
        CHECK (change_type IN (
            'mantido', 'alterado', 'incluido', 'excluido',
            'movido', 'renumerado', 'desmembrado', 'consolidado', 'reestruturado'
        )),
    status VARCHAR(50) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'review_pending', 'approved', 'archived')),
    author_account_id UUID REFERENCES app.accounts(id) ON DELETE SET NULL,
    etag VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provision_id, revision_number)
);

-- 8. NOTAS INTERNAS PRIVADAS (app.internal_notes)
CREATE TABLE IF NOT EXISTS app.internal_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    provision_id UUID NOT NULL REFERENCES app.provisions(id) ON DELETE CASCADE,
    revision_id UUID REFERENCES app.provision_revisions(id) ON DELETE CASCADE,
    author_account_id UUID NOT NULL REFERENCES app.accounts(id),
    content TEXT NOT NULL,
    visibility VARCHAR(50) NOT NULL DEFAULT 'equipe'
        CHECK (visibility IN ('equipe', 'juridico', 'gestao')),
    category VARCHAR(50) NOT NULL DEFAULT 'redacao'
        CHECK (category IN ('juridico', 'redacao', 'duvida', 'alerta')),
    resolved_at TIMESTAMPTZ,
    resolved_by_id UUID REFERENCES app.accounts(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. SNAPSHOTS CONGELADOS E IMUTÁVEIS (app.document_snapshots)
CREATE TABLE IF NOT EXISTS app.document_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES app.documents(id) ON DELETE CASCADE,
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    version_label VARCHAR(100) NOT NULL,
    purpose VARCHAR(50) NOT NULL DEFAULT 'consulta_publica'
        CHECK (purpose IN ('consulta_publica', 'marco_revisao', 'versao_final')),
    frozen_by_id UUID NOT NULL REFERENCES app.accounts(id),
    frozen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 sobre toda a árvore congelada
    is_immutable BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. ITENS DE DISPOSITIVOS NO SNAPSHOT (app.snapshot_items)
CREATE TABLE IF NOT EXISTS app.snapshot_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id UUID NOT NULL REFERENCES app.document_snapshots(id) ON DELETE CASCADE,
    provision_id UUID NOT NULL REFERENCES app.provisions(id) ON DELETE CASCADE,
    provision_revision_id UUID NOT NULL REFERENCES app.provision_revisions(id) ON DELETE RESTRICT,
    rendered_label VARCHAR(100) NOT NULL,
    position INT NOT NULL DEFAULT 0,
    parent_provision_id UUID REFERENCES app.provisions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (snapshot_id, provision_id)
);

-- ============================================================================
-- ÍNDICES DE PERFORMANCE E CHAVES ESTRANGEIRAS
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_projects_condo ON app.projects(condominium_id);
CREATE INDEX IF NOT EXISTS idx_documents_project ON app.documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_condo ON app.documents(condominium_id);
CREATE INDEX IF NOT EXISTS idx_source_files_condo ON app.source_files(condominium_id);
CREATE INDEX IF NOT EXISTS idx_source_transcriptions_doc ON app.source_transcriptions(document_id);
CREATE INDEX IF NOT EXISTS idx_provisions_doc ON app.provisions(document_id);
CREATE INDEX IF NOT EXISTS idx_provision_revisions_prov ON app.provision_revisions(provision_id);
CREATE INDEX IF NOT EXISTS idx_internal_notes_prov ON app.internal_notes(provision_id);
CREATE INDEX IF NOT EXISTS idx_document_snapshots_doc ON app.document_snapshots(document_id);
CREATE INDEX IF NOT EXISTS idx_snapshot_items_snap ON app.snapshot_items(snapshot_id);

-- ============================================================================
-- HABILITAÇÃO E POLÍTICAS DE ROW LEVEL SECURITY (RLS)
-- ============================================================================
ALTER TABLE app.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.source_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.source_transcriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.source_provisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.provisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.provision_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.internal_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.document_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.snapshot_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_projects_tenant ON app.projects
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_documents_tenant ON app.documents
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_source_files_tenant ON app.source_files
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_source_transcriptions_tenant ON app.source_transcriptions
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_source_provisions_tenant ON app.source_provisions
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_provisions_tenant ON app.provisions
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_provision_revisions_tenant ON app.provision_revisions
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_internal_notes_tenant ON app.internal_notes
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_document_snapshots_tenant ON app.document_snapshots
    FOR ALL
    USING (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY rls_snapshot_items_tenant ON app.snapshot_items
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM app.document_snapshots s
            WHERE s.id = snapshot_items.snapshot_id
            AND s.condominium_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    );
