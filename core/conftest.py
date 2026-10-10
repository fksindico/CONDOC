"""
Configuração do Pytest — CONDC
Inicializa o esquema app no SQLite in-memory para testes locais com models managed=False (Fases 1 e 2).
"""
import pytest
from django.db import connection

SCHEMA_SQL = """
ATTACH DATABASE ':memory:' AS app;

CREATE TABLE IF NOT EXISTS app.condominiums (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cnpj TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    timezone TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
    address_street TEXT,
    address_number TEXT,
    address_complement TEXT,
    address_neighborhood TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.buildings (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'tower',
    display_order INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.units (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    building_id TEXT REFERENCES buildings(id) ON DELETE SET NULL,
    code TEXT NOT NULL,
    floor_label TEXT,
    description TEXT,
    ideal_fraction REAL,
    block TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.accounts (
    id TEXT PRIMARY KEY,
    auth_user_id TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    is_active INTEGER NOT NULL DEFAULT 1,
    mfa_enabled INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.resident_registrations (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    unit_id TEXT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    phone_e164 TEXT,
    email TEXT,
    relationship TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    external_reference TEXT,
    status TEXT NOT NULL DEFAULT 'pendente',
    preverified_by TEXT REFERENCES accounts(id),
    preverified_at TIMESTAMP,
    linked_resident_id TEXT,
    linked_membership_id TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.residents (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    phone_e164 TEXT,
    phone_verified_at TIMESTAMP,
    email_verified_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.unit_memberships (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    resident_id TEXT NOT NULL REFERENCES residents(id) ON DELETE CASCADE,
    unit_id TEXT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'pendente',
    membership_status TEXT NOT NULL DEFAULT 'active',
    verification_method TEXT,
    reviewed_by TEXT REFERENCES accounts(id),
    reviewed_at TIMESTAMP,
    review_reason TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.membership_verification_events (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    membership_id TEXT NOT NULL REFERENCES unit_memberships(id) ON DELETE CASCADE,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    method TEXT NOT NULL,
    reason TEXT NOT NULL,
    actor_account_id TEXT REFERENCES accounts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.role_assignments (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.identity_access_events (
    id TEXT PRIMARY KEY,
    condominium_id TEXT REFERENCES condominiums(id) ON DELETE CASCADE,
    actor_account_id TEXT NOT NULL REFERENCES accounts(id),
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.import_batches (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    source_label TEXT NOT NULL DEFAULT 'upload_manual',
    status TEXT NOT NULL DEFAULT 'received',
    revision INTEGER NOT NULL DEFAULT 1,
    mapping TEXT NOT NULL DEFAULT '{}',
    totals TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    created_by_id TEXT NOT NULL REFERENCES accounts(id),
    confirmed_by_id TEXT REFERENCES accounts(id),
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.import_rows (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batches(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    raw_data TEXT NOT NULL DEFAULT '{}',
    normalized_data TEXT NOT NULL DEFAULT '{}',
    classification TEXT NOT NULL DEFAULT 'nova_pendente',
    issues TEXT NOT NULL DEFAULT '[]',
    selected INTEGER NOT NULL DEFAULT 1,
    action TEXT NOT NULL DEFAULT 'create_registration',
    target_registration_id TEXT REFERENCES resident_registrations(id),
    target_version INTEGER,
    result_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (batch_id, row_number)
);

CREATE TABLE IF NOT EXISTS app.access_invitations (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    campaign_id TEXT,
    kind TEXT NOT NULL,
    target_registration_id TEXT REFERENCES resident_registrations(id),
    target_unit_id TEXT REFERENCES units(id),
    target_building_id TEXT REFERENCES buildings(id),
    expected_contact TEXT,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    max_redemptions INTEGER NOT NULL DEFAULT 1,
    redemption_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ativo',
    created_by_id TEXT NOT NULL REFERENCES accounts(id),
    revoked_by_id TEXT REFERENCES accounts(id),
    revoked_at TIMESTAMP,
    revoke_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.invitation_redemptions (
    id TEXT PRIMARY KEY,
    invitation_id TEXT NOT NULL REFERENCES access_invitations(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    resident_id TEXT REFERENCES residents(id),
    membership_id TEXT REFERENCES unit_memberships(id),
    idempotency_key TEXT,
    ip_address_masked TEXT,
    user_agent TEXT,
    redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.delivery_attempts (
    id TEXT PRIMARY KEY,
    invitation_id TEXT NOT NULL REFERENCES access_invitations(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    destination_masked TEXT,
    status TEXT NOT NULL DEFAULT 'nao_enviada',
    provider_ref TEXT,
    error_code TEXT,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.idempotency_records (
    id TEXT PRIMARY KEY,
    tenant_id TEXT,
    actor_account_id TEXT,
    operation TEXT NOT NULL,
    key TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    response_code INTEGER NOT NULL,
    response_body TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, operation, key)
);

CREATE TABLE IF NOT EXISTS app.projects (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    purpose TEXT,
    kind TEXT NOT NULL DEFAULT 'revisao',
    coordinator_account_id TEXT REFERENCES accounts(id),
    status TEXT NOT NULL DEFAULT 'preparacao',
    settings TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    type TEXT NOT NULL DEFAULT 'regimento_interno',
    title TEXT NOT NULL,
    editorial_status TEXT NOT NULL DEFAULT 'rascunho',
    numbering_policy TEXT NOT NULL DEFAULT 'preservar_original',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.source_files (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    storage_key TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    uploaded_by_id TEXT NOT NULL REFERENCES accounts(id),
    state TEXT NOT NULL DEFAULT 'ready',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.source_transcriptions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    source_file_id TEXT NOT NULL REFERENCES source_files(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'draft',
    raw_text TEXT NOT NULL,
    corrected_text TEXT,
    checked_by_id TEXT REFERENCES accounts(id),
    checked_at TIMESTAMP,
    replaces_transcription_id TEXT REFERENCES source_transcriptions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.source_provisions (
    id TEXT PRIMARY KEY,
    transcription_id TEXT NOT NULL REFERENCES source_transcriptions(id) ON DELETE CASCADE,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    parent_id TEXT REFERENCES source_provisions(id),
    kind TEXT NOT NULL DEFAULT 'artigo',
    label TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    text TEXT NOT NULL,
    page_number INTEGER,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.provisions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    kind TEXT NOT NULL DEFAULT 'artigo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.provision_revisions (
    id TEXT PRIMARY KEY,
    provision_id TEXT NOT NULL REFERENCES provisions(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    revision_number INTEGER NOT NULL DEFAULT 1,
    parent_provision_id TEXT REFERENCES provisions(id),
    position INTEGER NOT NULL DEFAULT 0,
    label TEXT NOT NULL,
    text TEXT NOT NULL,
    theme TEXT,
    change_type TEXT NOT NULL DEFAULT 'mantido',
    status TEXT NOT NULL DEFAULT 'draft',
    author_account_id TEXT REFERENCES accounts(id),
    etag TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (provision_id, revision_number)
);

CREATE TABLE IF NOT EXISTS app.internal_notes (
    id TEXT PRIMARY KEY,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    provision_id TEXT NOT NULL REFERENCES provisions(id) ON DELETE CASCADE,
    revision_id TEXT REFERENCES provision_revisions(id),
    author_account_id TEXT NOT NULL REFERENCES accounts(id),
    content TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'equipe',
    category TEXT NOT NULL DEFAULT 'redacao',
    resolved_at TIMESTAMP,
    resolved_by_id TEXT REFERENCES accounts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.document_snapshots (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    condominium_id TEXT NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL,
    purpose TEXT NOT NULL DEFAULT 'consulta_publica',
    frozen_by_id TEXT NOT NULL REFERENCES accounts(id),
    frozen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.snapshot_items (
    id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES document_snapshots(id) ON DELETE CASCADE,
    provision_id TEXT NOT NULL REFERENCES provisions(id) ON DELETE CASCADE,
    provision_revision_id TEXT NOT NULL REFERENCES provision_revisions(id),
    rendered_label TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    parent_provision_id TEXT REFERENCES provisions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (snapshot_id, provision_id)
);
"""

@pytest.fixture(autouse=True)
def setup_sqlite_app_schema(db):
    """Garante que as tabelas do esquema app existam no SQLite durante a execução dos testes."""
    with connection.cursor() as cursor:
        for statement in SCHEMA_SQL.split(';'):
            stmt = statement.strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                except Exception:
                    pass
