-- ============================================================================
-- MIGRATION 20261009000002: Fase 2 — Importação Cadastral e Convites de Acesso
-- Sistema: CONDC — Gestão de Documentos Normativos Condominiais
-- Critérios: CA-03 a CA-11, CA-43; V21-06 a V21-25; ADR-003, ADR-004
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. TABELA: app.import_batches
-- Lotes de importação de moradores via planilha (CSV/XLSX)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.import_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    source_label VARCHAR(100) NOT NULL DEFAULT 'upload_manual',
    status VARCHAR(50) NOT NULL DEFAULT 'received'
        CHECK (status IN (
            'received', 'parsing', 'awaiting_mapping', 'validating',
            'awaiting_review', 'applying', 'completed', 'failed', 'cancelled'
        )),
    revision INT NOT NULL DEFAULT 1,
    mapping JSONB NOT NULL DEFAULT '{}'::jsonb,
    totals JSONB NOT NULL DEFAULT '{
        "total_rows": 0,
        "selected_rows": 0,
        "create_registrations": 0,
        "update_registrations": 0,
        "add_unit_registrations": 0,
        "skipped_rows": 0,
        "blocking_issues": 0
    }'::jsonb,
    error_message TEXT,
    created_by_id UUID NOT NULL REFERENCES app.accounts(id),
    confirmed_by_id UUID REFERENCES app.accounts(id),
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_import_batches_tenant ON app.import_batches(condominium_id);
CREATE INDEX IF NOT EXISTS idx_import_batches_status ON app.import_batches(status);

-- ----------------------------------------------------------------------------
-- 2. TABELA: app.import_rows
-- Linhas do lote com isolamento, normalização, classificação e resolução
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.import_rows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES app.import_batches(id) ON DELETE CASCADE,
    row_number INT NOT NULL,
    raw_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    normalized_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    classification VARCHAR(50) NOT NULL DEFAULT 'nova_pendente'
        CHECK (classification IN (
            'nova_completa', 'nova_pendente', 'existente_igual',
            'atualizacao_proposta', 'vinculo_adicional', 'conflito_identidade',
            'unidade_desconhecida', 'formato_invalido', 'duplicada_no_arquivo'
        )),
    issues JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected BOOLEAN NOT NULL DEFAULT TRUE,
    action VARCHAR(50) NOT NULL DEFAULT 'create_registration'
        CHECK (action IN (
            'create_registration', 'update_registration',
            'add_registration_for_unit', 'skip', 'request_manual_review'
        )),
    target_registration_id UUID REFERENCES app.resident_registrations(id) ON DELETE SET NULL,
    target_version INT,
    result_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_import_row_batch_number UNIQUE (batch_id, row_number)
);

CREATE INDEX IF NOT EXISTS idx_import_rows_batch ON app.import_rows(batch_id);
CREATE INDEX IF NOT EXISTS idx_import_rows_classification ON app.import_rows(classification);

-- ----------------------------------------------------------------------------
-- 3. TABELA: app.access_invitations
-- Convites de acesso ao condomínio (tokens de uso único/controlado via hash SHA-256)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.access_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    campaign_id UUID, -- Opcional, para fases futuras de consulta pública
    kind VARCHAR(50) NOT NULL
        CHECK (kind IN (
            'individual_preconferido', 'individual_padrao',
            'unidade_fixa', 'torre_bloco', 'amplo', 'leitura'
        )),
    target_registration_id UUID REFERENCES app.resident_registrations(id) ON DELETE SET NULL,
    target_unit_id UUID REFERENCES app.units(id) ON DELETE SET NULL,
    target_building_id UUID REFERENCES app.buildings(id) ON DELETE SET NULL,
    expected_contact VARCHAR(255), -- E-mail ou telefone mascarado para conferência
    token_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 do token gerado
    expires_at TIMESTAMPTZ NOT NULL,
    max_redemptions INT NOT NULL DEFAULT 1,
    redemption_count INT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'ativo'
        CHECK (status IN ('ativo', 'expirado', 'esgotado', 'revogado')),
    created_by_id UUID NOT NULL REFERENCES app.accounts(id),
    revoked_by_id UUID REFERENCES app.accounts(id),
    revoked_at TIMESTAMPTZ,
    revoke_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_access_invitations_tenant ON app.access_invitations(condominium_id);
CREATE INDEX IF NOT EXISTS idx_access_invitations_hash ON app.access_invitations(token_hash);
CREATE INDEX IF NOT EXISTS idx_access_invitations_status ON app.access_invitations(status);

-- ----------------------------------------------------------------------------
-- 4. TABELA: app.invitation_redemptions
-- Trilha imutável de resgate de convites por contas de usuário
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.invitation_redemptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invitation_id UUID NOT NULL REFERENCES app.access_invitations(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES app.accounts(id),
    resident_id UUID REFERENCES app.residents(id) ON DELETE SET NULL,
    membership_id UUID REFERENCES app.unit_memberships(id) ON DELETE SET NULL,
    idempotency_key VARCHAR(128),
    ip_address_masked VARCHAR(64),
    user_agent TEXT,
    redeemed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invitation_redemptions_invitation ON app.invitation_redemptions(invitation_id);
CREATE INDEX IF NOT EXISTS idx_invitation_redemptions_account ON app.invitation_redemptions(account_id);

-- ----------------------------------------------------------------------------
-- 5. TABELA: app.delivery_attempts
-- Registro de tentativas de distribuição e entrega de convites
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.delivery_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invitation_id UUID NOT NULL REFERENCES app.access_invitations(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL
        CHECK (channel IN ('email', 'manual_link', 'qr_code', 'export')),
    destination_masked VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'nao_enviada'
        CHECK (status IN ('nao_enviada', 'enfileirada', 'enviada', 'falhou')),
    provider_ref VARCHAR(255),
    error_code VARCHAR(100),
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_delivery_attempts_invitation ON app.delivery_attempts(invitation_id);

-- ----------------------------------------------------------------------------
-- 6. TABELA: app.idempotency_records
-- Registro operacional de idempotência para operações críticas de mutação
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.idempotency_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES app.condominiums(id) ON DELETE CASCADE,
    actor_account_id UUID REFERENCES app.accounts(id) ON DELETE SET NULL,
    operation VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    response_code INT NOT NULL,
    response_body JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_idempotency_tenant_operation_key UNIQUE (tenant_id, operation, key)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_lookup ON app.idempotency_records(tenant_id, operation, key);
CREATE INDEX IF NOT EXISTS idx_idempotency_expiry ON app.idempotency_records(expires_at);

-- ----------------------------------------------------------------------------
-- TRIGGERS DE UPDATED_AT
-- ----------------------------------------------------------------------------
CREATE TRIGGER trg_import_batches_updated_at
BEFORE UPDATE ON app.import_batches
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE TRIGGER trg_import_rows_updated_at
BEFORE UPDATE ON app.import_rows
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE TRIGGER trg_access_invitations_updated_at
BEFORE UPDATE ON app.access_invitations
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

-- ----------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) MANDATÓRIO (ADR-004)
-- ----------------------------------------------------------------------------
ALTER TABLE app.import_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.import_batches FORCE ROW LEVEL SECURITY;

CREATE POLICY import_batches_tenant_isolation ON app.import_batches
FOR ALL
USING (condominium_id = app.current_tenant_id())
WITH CHECK (condominium_id = app.current_tenant_id());

ALTER TABLE app.import_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.import_rows FORCE ROW LEVEL SECURITY;

CREATE POLICY import_rows_tenant_isolation ON app.import_rows
FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM app.import_batches b
        WHERE b.id = import_rows.batch_id
          AND b.condominium_id = app.current_tenant_id()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM app.import_batches b
        WHERE b.id = import_rows.batch_id
          AND b.condominium_id = app.current_tenant_id()
    )
);

ALTER TABLE app.access_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.access_invitations FORCE ROW LEVEL SECURITY;

CREATE POLICY access_invitations_tenant_isolation ON app.access_invitations
FOR ALL
USING (condominium_id = app.current_tenant_id())
WITH CHECK (condominium_id = app.current_tenant_id());

ALTER TABLE app.invitation_redemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.invitation_redemptions FORCE ROW LEVEL SECURITY;

CREATE POLICY invitation_redemptions_tenant_isolation ON app.invitation_redemptions
FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM app.access_invitations i
        WHERE i.id = invitation_redemptions.invitation_id
          AND i.condominium_id = app.current_tenant_id()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM app.access_invitations i
        WHERE i.id = invitation_redemptions.invitation_id
          AND i.condominium_id = app.current_tenant_id()
    )
);

ALTER TABLE app.delivery_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.delivery_attempts FORCE ROW LEVEL SECURITY;

CREATE POLICY delivery_attempts_tenant_isolation ON app.delivery_attempts
FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM app.access_invitations i
        WHERE i.id = delivery_attempts.invitation_id
          AND i.condominium_id = app.current_tenant_id()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM app.access_invitations i
        WHERE i.id = delivery_attempts.invitation_id
          AND i.condominium_id = app.current_tenant_id()
    )
);

ALTER TABLE app.idempotency_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.idempotency_records FORCE ROW LEVEL SECURITY;

CREATE POLICY idempotency_records_tenant_isolation ON app.idempotency_records
FOR ALL
USING (tenant_id = app.current_tenant_id())
WITH CHECK (tenant_id = app.current_tenant_id());
