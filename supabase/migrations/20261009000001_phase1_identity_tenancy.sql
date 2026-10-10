-- ============================================================================
-- MIGRATION 20261009000001: Fase 1 — Identidade, Estrutura Física e Multi-Tenancy
-- Sistema: CONDC — Gestão de Documentos Normativos Condominiais
-- Critérios: CA-01, CA-02, CA-06, CA-12, CA-13, CA-14, CA-15, CA-16, CA-33; AR-04 a AR-09
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CONDOMÍNIOS (Tenancy Raiz)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.condominiums (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'archived')),
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Sao_Paulo',
    address_street VARCHAR(255),
    address_number VARCHAR(50),
    address_complement VARCHAR(255),
    address_neighborhood VARCHAR(100),
    address_city VARCHAR(100),
    address_state VARCHAR(2),
    address_zip_code VARCHAR(10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_condominiums_updated_at
BEFORE UPDATE ON app.condominiums
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

-- ----------------------------------------------------------------------------
-- 2. PRÉDIOS / BLOCOS / TORRES (Estrutura Física)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(50) NOT NULL DEFAULT 'tower' CHECK (kind IN ('tower', 'block', 'single')),
    display_order INT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_building_tenant_code UNIQUE (condominium_id, code)
);

CREATE TRIGGER trg_buildings_updated_at
BEFORE UPDATE ON app.buildings
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE INDEX IF NOT EXISTS idx_buildings_tenant ON app.buildings(condominium_id);

-- ----------------------------------------------------------------------------
-- 3. UNIDADES AUTÔNOMAS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    building_id UUID REFERENCES app.buildings(id) ON DELETE SET NULL,
    code VARCHAR(50) NOT NULL,
    floor_label VARCHAR(50),
    description TEXT,
    ideal_fraction NUMERIC(12, 8),
    block VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_unit_building_code UNIQUE (condominium_id, building_id, code)
);

CREATE TRIGGER trg_units_updated_at
BEFORE UPDATE ON app.units
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE INDEX IF NOT EXISTS idx_units_tenant ON app.units(condominium_id);
CREATE INDEX IF NOT EXISTS idx_units_building ON app.units(building_id);

-- ----------------------------------------------------------------------------
-- 4. CONTAS DE USUÁRIO (Supabase Auth Subject)
-- Desacoplada de condomínios específicos; armazena o perfil global do usuário.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'inactive')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_accounts_updated_at
BEFORE UPDATE ON app.accounts
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

-- ----------------------------------------------------------------------------
-- 5. PRÉ-CADASTRO DE MORADORES (Manual ou Importação)
-- CA-02: Cadastro manual cria registro prévio SEM credencial ou conta automática.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.resident_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    unit_id UUID NOT NULL REFERENCES app.units(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    phone_e164 VARCHAR(30),
    email VARCHAR(255),
    relationship VARCHAR(50) NOT NULL CHECK (relationship IN (
        'proprietario_residente',
        'proprietario_nao_residente',
        'inquilino',
        'dependente',
        'procurador',
        'outro'
    )),
    source VARCHAR(50) NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'importacao', 'auto_cadastro')),
    external_reference VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pendente' CHECK (status IN (
        'pendente', 'pre_aprovado', 'ativado', 'rejeitado', 'cancelado'
    )),
    preverified_by UUID REFERENCES app.accounts(id),
    preverified_at TIMESTAMPTZ,
    linked_resident_id UUID,
    linked_membership_id UUID,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_resident_registrations_updated_at
BEFORE UPDATE ON app.resident_registrations
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE INDEX IF NOT EXISTS idx_registrations_tenant ON app.resident_registrations(condominium_id);
CREATE INDEX IF NOT EXISTS idx_registrations_unit ON app.resident_registrations(unit_id);
CREATE INDEX IF NOT EXISTS idx_registrations_email ON app.resident_registrations(email);
CREATE INDEX IF NOT EXISTS idx_registrations_phone ON app.resident_registrations(phone_e164);

-- ----------------------------------------------------------------------------
-- 6. MORADORES EFETIVOS (Perfil contextualizado ao condomínio)
-- Unique tenant + account_id (uma conta possui apenas um perfil por condomínio).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.residents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES app.accounts(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    phone_e164 VARCHAR(30),
    phone_verified_at TIMESTAMPTZ,
    email_verified_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_resident_tenant_account UNIQUE (condominium_id, account_id)
);

CREATE TRIGGER trg_residents_updated_at
BEFORE UPDATE ON app.residents
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE INDEX IF NOT EXISTS idx_residents_tenant ON app.residents(condominium_id);
CREATE INDEX IF NOT EXISTS idx_residents_account ON app.residents(account_id);

-- ----------------------------------------------------------------------------
-- 7. VÍNCULOS COM UNIDADES (UnitMembership)
-- CA-13: Vários moradores podem ter vínculos na mesma unidade.
-- CA-14: Pessoa com várias unidades tem vínculos separados, mas conta única.
-- CA-15: Confirmar e-mail não valida vínculo (validação documental auditada).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.unit_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    resident_id UUID NOT NULL REFERENCES app.residents(id) ON DELETE CASCADE,
    unit_id UUID NOT NULL REFERENCES app.units(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'proprietario_residente',
        'proprietario_nao_residente',
        'inquilino',
        'dependente',
        'procurador'
    )),
    verification_status VARCHAR(50) NOT NULL DEFAULT 'pendente' CHECK (verification_status IN (
        'pendente', 'em_analise', 'validado', 'recusado', 'revogado'
    )),
    membership_status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (membership_status IN (
        'active', 'ended', 'suspended'
    )),
    verification_method VARCHAR(50) CHECK (verification_method IN (
        'documento', 'declaracao_sindico', 'cadastro_legado', 'presencial'
    )),
    reviewed_by UUID REFERENCES app.accounts(id),
    reviewed_at TIMESTAMPTZ,
    review_reason TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_membership_dates CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE TRIGGER trg_unit_memberships_updated_at
BEFORE UPDATE ON app.unit_memberships
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON app.unit_memberships(condominium_id);
CREATE INDEX IF NOT EXISTS idx_memberships_resident ON app.unit_memberships(resident_id);
CREATE INDEX IF NOT EXISTS idx_memberships_unit ON app.unit_memberships(unit_id);

-- Índice único parcial: vínculo ativo não encerrado por condomínio, residente e unidade
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_unit_membership
ON app.unit_memberships(condominium_id, resident_id, unit_id)
WHERE (ended_at IS NULL AND membership_status = 'active');

-- ----------------------------------------------------------------------------
-- 8. TRILHA DE AUDITORIA DE VALIDAÇÃO DE VÍNCULO (MembershipVerificationEvent)
-- Trilha imutável: quem aprovou, método comprobatório, motivo e data.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.membership_verification_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    membership_id UUID NOT NULL REFERENCES app.unit_memberships(id) ON DELETE CASCADE,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    method VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    actor_account_id UUID REFERENCES app.accounts(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_events_tenant ON app.membership_verification_events(condominium_id);
CREATE INDEX IF NOT EXISTS idx_verification_events_membership ON app.membership_verification_events(membership_id);

-- ----------------------------------------------------------------------------
-- 9. PAPÉIS E PERMISSÕES ADMINISTRATIVAS (RoleAssignment e PermissionGrant)
-- CA-28: Autoridade exclusiva do síndico ativo para publicações.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES app.accounts(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN (
        'sindico', 'subsindico', 'conselheiro', 'comissao', 'juridico', 'administrador', 'morador'
    )),
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_role_dates CHECK (valid_until IS NULL OR valid_until >= valid_from)
);

CREATE TRIGGER trg_role_assignments_updated_at
BEFORE UPDATE ON app.role_assignments
FOR EACH ROW EXECUTE FUNCTION app.trigger_set_updated_at();

CREATE INDEX IF NOT EXISTS idx_role_assignments_tenant ON app.role_assignments(condominium_id);
CREATE INDEX IF NOT EXISTS idx_role_assignments_account ON app.role_assignments(account_id);

CREATE TABLE IF NOT EXISTS app.permission_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID NOT NULL REFERENCES app.condominiums(id) ON DELETE CASCADE,
    role_assignment_id UUID REFERENCES app.role_assignments(id) ON DELETE CASCADE,
    permission VARCHAR(100) NOT NULL,
    scope VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_permission_grants_tenant ON app.permission_grants(condominium_id);

-- ----------------------------------------------------------------------------
-- 10. SESSÕES SEGURAS DO BFF (CoreSession - ADR-002)
-- Guarda envelopes de sessão opacos protegidos por cookie HttpOnly.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.core_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_token_hash VARCHAR(64) NOT NULL UNIQUE,
    account_id UUID NOT NULL REFERENCES app.accounts(id) ON DELETE CASCADE,
    active_condominium_id UUID REFERENCES app.condominiums(id) ON DELETE SET NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_core_sessions_token ON app.core_sessions(session_token_hash);
CREATE INDEX IF NOT EXISTS idx_core_sessions_account ON app.core_sessions(account_id);

-- ----------------------------------------------------------------------------
-- 11. AUDITORIA DE ACESSO A DADOS DE IDENTIDADE (CA-33)
-- Toda consulta de identidade, contato ou morador gera log auditável com motivo.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app.identity_access_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condominium_id UUID REFERENCES app.condominiums(id) ON DELETE CASCADE,
    actor_account_id UUID NOT NULL REFERENCES app.accounts(id),
    target_type VARCHAR(50) NOT NULL CHECK (target_type IN ('resident', 'registration', 'suggestion_author')),
    target_id UUID NOT NULL,
    purpose TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_identity_access_tenant ON app.identity_access_events(condominium_id);

-- ============================================================================
-- HABILITAÇÃO MANDATÓRIA DE ROW LEVEL SECURITY (RLS) E POLÍTICAS DE ISOLAMENTO
-- Conforme ADR-004 e AGENTS.md:
-- Todas as tabelas de negócio possuem isolamento transacional via app.current_tenant_id()
-- ============================================================================

-- 1. Condominiums
ALTER TABLE app.condominiums ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.condominiums FORCE ROW LEVEL SECURITY;

CREATE POLICY condominium_isolation_policy ON app.condominiums
FOR ALL USING (
    id = app.current_tenant_id()
) WITH CHECK (
    id = app.current_tenant_id()
);

-- 2. Buildings
ALTER TABLE app.buildings ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.buildings FORCE ROW LEVEL SECURITY;

CREATE POLICY building_isolation_policy ON app.buildings
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);

-- 3. Units
ALTER TABLE app.units ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.units FORCE ROW LEVEL SECURITY;

CREATE POLICY unit_isolation_policy ON app.units
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);

-- 4. Accounts (Isolamento por conta ou via contexto administrativo de tenant)
ALTER TABLE app.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.accounts FORCE ROW LEVEL SECURITY;

CREATE POLICY account_owner_or_admin_policy ON app.accounts
FOR ALL USING (
    id = app.current_account_id()
    OR EXISTS (
        SELECT 1 FROM app.residents r
        WHERE r.account_id = app.accounts.id
          AND r.condominium_id = app.current_tenant_id()
    )
) WITH CHECK (
    id = app.current_account_id()
);

-- 5. Resident Registrations
ALTER TABLE app.resident_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.resident_registrations FORCE ROW LEVEL SECURITY;

CREATE POLICY resident_registrations_isolation_policy ON app.resident_registrations
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);

-- 6. Residents
ALTER TABLE app.residents ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.residents FORCE ROW LEVEL SECURITY;

CREATE POLICY residents_isolation_policy ON app.residents
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);

-- 7. Unit Memberships
ALTER TABLE app.unit_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.unit_memberships FORCE ROW LEVEL SECURITY;

CREATE POLICY unit_memberships_isolation_policy ON app.unit_memberships
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);

-- 8. Membership Verification Events
ALTER TABLE app.membership_verification_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.membership_verification_events FORCE ROW LEVEL SECURITY;

CREATE POLICY verification_events_isolation_policy ON app.membership_verification_events
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);

-- 9. Role Assignments
ALTER TABLE app.role_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.role_assignments FORCE ROW LEVEL SECURITY;

CREATE POLICY role_assignments_isolation_policy ON app.role_assignments
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);

-- 10. Permission Grants
ALTER TABLE app.permission_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.permission_grants FORCE ROW LEVEL SECURITY;

CREATE POLICY permission_grants_isolation_policy ON app.permission_grants
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);

-- 11. Core Sessions
ALTER TABLE app.core_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.core_sessions FORCE ROW LEVEL SECURITY;

CREATE POLICY core_sessions_isolation_policy ON app.core_sessions
FOR ALL USING (
    account_id = app.current_account_id()
) WITH CHECK (
    account_id = app.current_account_id()
);

-- 12. Identity Access Events
ALTER TABLE app.identity_access_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.identity_access_events FORCE ROW LEVEL SECURITY;

CREATE POLICY identity_access_events_isolation_policy ON app.identity_access_events
FOR ALL USING (
    condominium_id = app.current_tenant_id()
) WITH CHECK (
    condominium_id = app.current_tenant_id()
);
