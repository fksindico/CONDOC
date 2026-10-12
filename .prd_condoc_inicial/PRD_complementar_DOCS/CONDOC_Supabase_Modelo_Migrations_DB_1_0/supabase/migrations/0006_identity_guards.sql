BEGIN;
SET LOCAL ROLE condoc_owner;
CREATE FUNCTION app.guard_identity_columns() RETURNS trigger LANGUAGE plpgsql
SET search_path = '' AS $$
DECLARE oldj jsonb; newj jsonb; k text;
BEGIN
 oldj:=to_jsonb(OLD); newj:=to_jsonb(NEW);
 FOREACH k IN ARRAY ARRAY['id','condominium_id','created_at','account_id','resident_id','document_id','node_id','note_id','author_id','created_by','requested_by','uploaded_by','actor_id'] LOOP
   IF oldj ? k AND oldj->k IS DISTINCT FROM newj->k THEN
     RAISE EXCEPTION 'Coluna de identidade/origem imutavel: %',k USING ERRCODE='55000';
   END IF;
 END LOOP;
 RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION app.guard_identity_columns() FROM PUBLIC,anon,authenticated,service_role;
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.condominiums FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.buildings FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.units FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.residents FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.unit_memberships FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.resident_registrations FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.projects FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.files FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.file_metadata FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.documents FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.document_snapshots FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.snapshot_nodes FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.snapshot_notes FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.snapshot_configurations FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.snapshot_regions FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.internal_annotations FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.import_batches FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.import_rows FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app.render_jobs FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.compatibility_issues FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
CREATE TRIGGER guard_identity_columns BEFORE UPDATE ON app_private.resident_contacts FOR EACH ROW EXECUTE FUNCTION app.guard_identity_columns();
COMMIT;
