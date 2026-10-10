"""
Configuração do Pytest — CONDC
Inicializa o esquema app no SQLite in-memory para testes locais com models managed=False.
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
                    # Em caso de banco já configurado ou SQLite em memória reinicializado
                    pass
