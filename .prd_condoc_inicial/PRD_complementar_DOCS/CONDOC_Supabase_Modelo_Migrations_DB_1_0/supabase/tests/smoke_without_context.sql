-- Smoke test sem fixtures: executar SOMENTE em banco descartavel autorizado.
-- Nao substitui testes com identidades/tenants reais de teste.
BEGIN;
SET LOCAL ROLE condoc_runtime;
SELECT set_config('condoc.actor_id','',true);
SELECT set_config('condoc.tenant_id','',true);
DO $$
DECLARE n bigint;
BEGIN
 IF app_acl.actor_active() THEN RAISE EXCEPTION 'FAIL: ator vazio ativo'; END IF;
 IF app_acl.has_permission('document.read') THEN RAISE EXCEPTION 'FAIL: permissao sem ator'; END IF;
 SELECT count(*) INTO n FROM app.documents;
 IF n<>0 THEN RAISE EXCEPTION 'FAIL: leitura sem contexto'; END IF;
 SELECT count(*) INTO n FROM app_private.residents;
 IF n<>0 THEN RAISE EXCEPTION 'FAIL: identidade sem contexto'; END IF;
 IF has_table_privilege('condoc_runtime','app_acl.role_assignments','INSERT') THEN
   RAISE EXCEPTION 'FAIL: runtime pode conceder papel diretamente';
 END IF;
 IF has_table_privilege('condoc_runtime','app.node_revisions','UPDATE') THEN
   RAISE EXCEPTION 'FAIL: runtime altera revisao historica';
 END IF;
 IF has_table_privilege('condoc_runtime','app_audit.events','DELETE') THEN
   RAISE EXCEPTION 'FAIL: runtime apaga auditoria';
 END IF;
END $$;
ROLLBACK;
