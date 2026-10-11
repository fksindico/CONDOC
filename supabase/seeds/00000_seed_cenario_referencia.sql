-- ============================================================================
-- MASSA FICTÍCIA DE REFERÊNCIA — CONDC (CENÁRIO PADRÃO DE DESENVOLVIMENTO)
-- Arquivo: supabase/seeds/00000_seed_cenario_referencia.sql
-- Todos os dados são estritamente fictícios para testes e desenvolvimento.
-- ============================================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Esquema auxiliar se não existir
CREATE SCHEMA IF NOT EXISTS app;

-- 1. CONDOMÍNIOS DE TESTE (Isolamento Multi-Tenant)
INSERT INTO app.condominiums (id, name, cnpj, address_street, address_number, address_neighborhood, address_city, address_state, address_zip_code)
VALUES
  (
    'a0000000-0000-0000-0000-000000000001',
    'Condomínio Residencial Parque das Flores',
    '12.345.678/0001-90',
    'Rua das Palmeiras',
    '1000',
    'Jardim Primavera',
    'São Paulo',
    'SP',
    '01234-567'
  ),
  (
    'a0000000-0000-0000-0000-000000000002',
    'Condomínio Edifício Horizon',
    '98.765.432/0001-10',
    'Avenida Atlântica',
    '500',
    'Beira Mar',
    'Santos',
    'SP',
    '11000-000'
  )
ON CONFLICT (id) DO NOTHING;

-- 2. BLOCOS / TORRES (Condomínio 1: Parque das Flores)
INSERT INTO app.buildings (id, condominium_id, name, code, display_order)
VALUES
  ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'Torre A - Ipê Amarelo', 'TORRE_A', 1),
  ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'Torre B - Jacarandá', 'TORRE_B', 2)
ON CONFLICT (id) DO NOTHING;

-- 3. UNIDADES (Preservação de zeros e identificadores alfanuméricos)
INSERT INTO app.units (id, condominium_id, building_id, code, block, floor_label, ideal_fraction)
VALUES
  -- Torre A
  ('00000000-0000-0000-0000-000000000101', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', '101', 'A', '1', 0.0500),
  ('00000000-0000-0000-0000-000000000102', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', '102', 'A', '1', 0.0500),
  ('00000000-0000-0000-0000-000000000201', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', '201', 'A', '2', 0.0500),
  ('00000000-0000-0000-0000-000000000202', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', '202', 'A', '2', 0.0500),
  ('00000000-0000-0000-0000-000000000301', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', '301', 'A', '3', 0.0500),
  -- Torre B
  ('00000000-0000-0000-0000-000000000111', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', '101', 'B', '1', 0.0500),
  ('00000000-0000-0000-0000-000000000112', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', '102', 'B', '1', 0.0500),
  ('00000000-0000-0000-0000-000000000211', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', '201', 'B', '2', 0.0500),
  ('00000000-0000-0000-0000-000000000212', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', '202', 'B', '2', 0.0500),
  ('00000000-0000-0000-0000-000000000311', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', '301', 'B', '3', 0.0500)
ON CONFLICT (id) DO NOTHING;

-- 4. CONTAS FICTÍCIAS
INSERT INTO app.accounts (id, auth_user_id, full_name, email, phone, is_active, mfa_enabled)
VALUES
  (
    'c0000000-0000-0000-0000-000000000001',
    'f0000000-0000-0000-0000-000000000001',
    'Carlos Silva (Síndico)',
    'sindico@parquedasflores.com',
    '(11) 98765-4321',
    true,
    true
  ),
  (
    'c0000000-0000-0000-0000-000000000002',
    'f0000000-0000-0000-0000-000000000002',
    'Mariana Oliveira (Moradora A101)',
    'mariana.oliveira@exemplo.com',
    '(11) 91234-5678',
    true,
    false
  ),
  (
    'c0000000-0000-0000-0000-000000000003',
    'f0000000-0000-0000-0000-000000000003',
    'Roberto Santos (Proprietário B201 e B202)',
    'roberto.santos@exemplo.com',
    '(11) 99887-7665',
    true,
    false
  )
ON CONFLICT (id) DO NOTHING;

-- 5. ATRIBUIÇÃO DE PAPÉIS (Síndico Ativo com Mandato)
INSERT INTO app.role_assignments (id, condominium_id, account_id, role, status)
VALUES
  (
    'd0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'sindico',
    'active'
  )
ON CONFLICT (id) DO NOTHING;

-- 6. MORADORES (Residentes e Vínculos com Unidades)
INSERT INTO app.residents (id, condominium_id, account_id, full_name, phone_e164, status)
VALUES
  (
    'e0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000002',
    'Mariana Oliveira',
    '+5511912345678',
    'active'
  ),
  (
    'e0000000-0000-0000-0000-000000000003',
    'a0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000003',
    'Roberto Santos',
    '+5511998877665',
    'active'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO app.unit_memberships (id, condominium_id, resident_id, unit_id, category, verification_status, membership_status)
VALUES
  (
    'f0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    'e0000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000101',
    'proprietario_residente',
    'validado',
    'active'
  ),
  (
    'f0000000-0000-0000-0000-000000000003',
    'a0000000-0000-0000-0000-000000000001',
    'e0000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000211',
    'proprietario_nao_residente',
    'validado',
    'active'
  )
ON CONFLICT (id) DO NOTHING;
