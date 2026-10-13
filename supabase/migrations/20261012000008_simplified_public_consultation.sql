-- ============================================================================
-- FASE 8 (SIMPLIFICAÇÃO): CONSULTAS PÚBLICAS DIRETAS EM PDF E SUGESTÕES ÁGEIS
-- Arquitetura Simplificada: Zero atrito para moradores, link tokenizado compartilhado
-- ============================================================================

-- 1. Tabela: Consultas Públicas Simplificadas de Documentos (PDF)
CREATE TABLE IF NOT EXISTS app.public_consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL DEFAULT 'regimento'
        CHECK (document_type IN ('regimento', 'convencao')),
    description TEXT,
    pdf_file_path VARCHAR(500) NOT NULL,
    pdf_original_name VARCHAR(255) NOT NULL,
    pdf_size_bytes BIGINT NOT NULL DEFAULT 0,
    public_token VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'aberta'
        CHECK (status IN ('aberta', 'pausada', 'encerrada')),
    deadline TIMESTAMPTZ,
    created_by_id UUID REFERENCES app.accounts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_public_consultations_condo ON app.public_consultations(condominium_id);
CREATE INDEX IF NOT EXISTS idx_public_consultations_token ON app.public_consultations(public_token);
CREATE INDEX IF NOT EXISTS idx_public_consultations_status ON app.public_consultations(status);

-- 2. Tabela: Sugestões dos Moradores na Consulta
CREATE TABLE IF NOT EXISTS app.consultation_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    consultation_id UUID NOT NULL REFERENCES app.public_consultations(id) ON DELETE CASCADE,
    protocol VARCHAR(30) NOT NULL UNIQUE,
    resident_name VARCHAR(255) NOT NULL,
    resident_phone VARCHAR(50) NOT NULL,
    resident_email VARCHAR(255),
    block_tower VARCHAR(100),
    unit_code VARCHAR(50) NOT NULL,
    target_reference VARCHAR(255) NOT NULL,
    action_type VARCHAR(20) NOT NULL
        CHECK (action_type IN ('alterar', 'remover', 'incluir')),
    suggestion_text TEXT NOT NULL,
    justification TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'recebida'
        CHECK (status IN ('recebida', 'em_analise', 'destaque', 'arquivada')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_consultation_suggestions_condo ON app.consultation_suggestions(condominium_id);
CREATE INDEX IF NOT EXISTS idx_consultation_suggestions_consultation ON app.consultation_suggestions(consultation_id);
CREATE INDEX IF NOT EXISTS idx_consultation_suggestions_protocol ON app.consultation_suggestions(protocol);
CREATE INDEX IF NOT EXISTS idx_consultation_suggestions_unit ON app.consultation_suggestions(unit_code);
CREATE INDEX IF NOT EXISTS idx_consultation_suggestions_action ON app.consultation_suggestions(action_type);

-- 3. Triggers para updated_at
CREATE TRIGGER trg_public_consultations_updated_at
BEFORE UPDATE ON app.public_consultations
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE TRIGGER trg_consultation_suggestions_updated_at
BEFORE UPDATE ON app.consultation_suggestions
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

-- 4. Row-Level Security (RLS) Mandatório (ADR-004)
ALTER TABLE app.public_consultations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.public_consultations FORCE ROW LEVEL SECURITY;

CREATE POLICY public_consultations_tenant_isolation ON app.public_consultations
FOR ALL
USING (condominium_id = app.current_tenant_id())
WITH CHECK (condominium_id = app.current_tenant_id());

ALTER TABLE app.consultation_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.consultation_suggestions FORCE ROW LEVEL SECURITY;

CREATE POLICY consultation_suggestions_tenant_isolation ON app.consultation_suggestions
FOR ALL
USING (condominium_id = app.current_tenant_id())
WITH CHECK (condominium_id = app.current_tenant_id());
