BEGIN;
SET LOCAL ROLE condoc_owner;
CREATE FUNCTION app.reject_mutation() RETURNS trigger LANGUAGE plpgsql
SET search_path = '' AS $$
BEGIN
 RAISE EXCEPTION 'Registro historico imutavel: criar nova revisao' USING ERRCODE='55000';
END;
$$;
CREATE FUNCTION app.guard_frozen_snapshot() RETURNS trigger LANGUAGE plpgsql
SET search_path = '' AS $$
BEGIN
 IF OLD.status='frozen' THEN
   RAISE EXCEPTION 'Snapshot congelado e imutavel' USING ERRCODE='55000';
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END;
$$;
CREATE FUNCTION app.guard_snapshot_child() RETURNS trigger LANGUAGE plpgsql
SET search_path = '' AS $$
DECLARE sid uuid; tid uuid; snap_state text;
BEGIN
 IF TG_OP='DELETE' THEN sid:=OLD.snapshot_id; tid:=OLD.condominium_id;
 ELSE sid:=NEW.snapshot_id; tid:=NEW.condominium_id;
 END IF;
 IF TG_OP='UPDATE' AND (NEW.snapshot_id<>OLD.snapshot_id OR NEW.condominium_id<>OLD.condominium_id) THEN
   RAISE EXCEPTION 'Filho de snapshot nao pode ser reatribuido' USING ERRCODE='55000';
 END IF;
 SELECT status INTO snap_state FROM app.document_snapshots
   WHERE condominium_id=tid AND id=sid FOR UPDATE;
 IF snap_state IS DISTINCT FROM 'building' THEN
   RAISE EXCEPTION 'Snapshot ausente ou congelado: filhos imutaveis' USING ERRCODE='55000';
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION app.reject_mutation(),app.guard_frozen_snapshot(),app.guard_snapshot_child() FROM PUBLIC,anon,authenticated,service_role;
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.configuration_versions FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.source_transcriptions FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.source_blocks FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.document_nodes FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.node_revisions FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.origin_mappings FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.cross_references FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.document_notes FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.note_revisions FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.note_references FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.region_revisions FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app.export_artifacts FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app_audit.events FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON app_audit.identity_access FOR EACH ROW EXECUTE FUNCTION app.reject_mutation();
CREATE TRIGGER guard_frozen BEFORE UPDATE OR DELETE ON app.document_snapshots FOR EACH ROW EXECUTE FUNCTION app.guard_frozen_snapshot();
CREATE TRIGGER guard_snapshot_child BEFORE INSERT OR UPDATE OR DELETE ON app.snapshot_nodes FOR EACH ROW EXECUTE FUNCTION app.guard_snapshot_child();
CREATE TRIGGER guard_snapshot_child BEFORE INSERT OR UPDATE OR DELETE ON app.snapshot_notes FOR EACH ROW EXECUTE FUNCTION app.guard_snapshot_child();
CREATE TRIGGER guard_snapshot_child BEFORE INSERT OR UPDATE OR DELETE ON app.snapshot_configurations FOR EACH ROW EXECUTE FUNCTION app.guard_snapshot_child();
CREATE TRIGGER guard_snapshot_child BEFORE INSERT OR UPDATE OR DELETE ON app.snapshot_regions FOR EACH ROW EXECUTE FUNCTION app.guard_snapshot_child();
COMMIT;
