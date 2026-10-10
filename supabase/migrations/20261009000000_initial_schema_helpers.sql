-- ============================================================================
-- MIGRATION 20261009000000: Estrutura Base e Funções de Contexto RLS
-- Sistema: CONDC — Gestão de Documentos Normativos Condominiais
-- ============================================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Esquema do aplicativo
CREATE SCHEMA IF NOT EXISTS app;

-- Função auxiliar de auditoria para updated_at
CREATE OR REPLACE FUNCTION app.trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNÇÕES DE CONTEXTO RLS TRANSACIONAL (ADR-004)
-- Retornam o tenant e a conta configurados via SET LOCAL na transação corrente.
-- Retornam NULL se a transação não configurou os parâmetros (bloqueio seguro).
-- ============================================================================

CREATE OR REPLACE FUNCTION app.current_tenant_id()
RETURNS UUID AS $$
BEGIN
  RETURN NULLIF(current_setting('app.current_tenant_id', true), '')::UUID;
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION app.current_account_id()
RETURNS UUID AS $$
BEGIN
  RETURN NULLIF(current_setting('app.current_account_id', true), '')::UUID;
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- ============================================================================
-- COMENTÁRIOS DE SEGURANÇA E AUDITORIA
-- ============================================================================
COMMENT ON FUNCTION app.current_tenant_id() IS 'Retorna o UUID do condomínio ativo definido na transação via SET LOCAL app.current_tenant_id';
COMMENT ON FUNCTION app.current_account_id() IS 'Retorna o UUID da conta ativa definida na transação via SET LOCAL app.current_account_id';
