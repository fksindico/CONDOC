-- CONDOC DB-1.0: referencia para ambiente novo de desenvolvimento/homologacao.
-- Executar com role administrativa autorizada. Nao aplicar sobre schema existente sem gap/migration.
BEGIN;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'condoc_owner') THEN
    CREATE ROLE condoc_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'condoc_runtime') THEN
    CREATE ROLE condoc_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'condoc_api') THEN
    CREATE ROLE condoc_api LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('condoc_owner','condoc_runtime','condoc_api')
             AND (rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolreplication)) THEN
    RAISE EXCEPTION 'Roles CONDOC existentes possuem privilegios incompativeis';
  END IF;
END $$;
GRANT condoc_runtime TO condoc_api;
CREATE SCHEMA app AUTHORIZATION condoc_owner;
CREATE SCHEMA app_private AUTHORIZATION condoc_owner;
CREATE SCHEMA app_acl AUTHORIZATION condoc_owner;
CREATE SCHEMA app_audit AUTHORIZATION condoc_owner;
REVOKE ALL ON SCHEMA app, app_private, app_acl, app_audit FROM PUBLIC, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA auth TO condoc_owner;
GRANT REFERENCES (id) ON auth.users TO condoc_owner;
-- condoc_api nao recebe senha aqui. Provisionar segredo fora do arquivo/versionamento.
COMMIT;
