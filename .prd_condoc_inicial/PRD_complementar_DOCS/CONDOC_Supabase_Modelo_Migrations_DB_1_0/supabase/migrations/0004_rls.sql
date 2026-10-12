-- Contexto confiavel e ACL privada; nao expor via Data API.
BEGIN;
SET LOCAL ROLE condoc_owner;
CREATE FUNCTION app_acl.actor_id() RETURNS uuid LANGUAGE sql STABLE
SET search_path = '' AS $$
  SELECT nullif(pg_catalog.current_setting('condoc.actor_id', true),'')::uuid
$$;
CREATE FUNCTION app_acl.tenant_id() RETURNS uuid LANGUAGE sql STABLE
SET search_path = '' AS $$
  SELECT nullif(pg_catalog.current_setting('condoc.tenant_id', true),'')::uuid
$$;
CREATE FUNCTION app_acl.actor_active() RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = '' AS $$
  SELECT EXISTS(SELECT 1 FROM app_acl.accounts a
    WHERE a.id = app_acl.actor_id() AND a.status='active' AND a.auth_user_id IS NOT NULL)
$$;
CREATE FUNCTION app_acl.has_permission(p_code text) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = '' AS $$
  SELECT app_acl.actor_active() AND app_acl.tenant_id() IS NOT NULL
  AND (
    p_code NOT IN ('identity.read','contact.read','identity.export')
    OR EXISTS (
      SELECT 1 FROM app_acl.role_assignments r
      WHERE r.account_id=app_acl.actor_id() AND r.condominium_id=app_acl.tenant_id()
        AND r.role_code IN ('syndic','admin') AND r.status='active'
        AND r.valid_from<=now() AND (r.valid_until IS NULL OR r.valid_until>now())
    )
  )
  AND (
    p_code<>'suggestion.publish'
    OR EXISTS (
      SELECT 1 FROM app_acl.role_assignments r
      WHERE r.account_id=app_acl.actor_id() AND r.condominium_id=app_acl.tenant_id()
        AND r.role_code='syndic' AND r.status='active'
        AND r.valid_from<=now() AND (r.valid_until IS NULL OR r.valid_until>now())
    )
  )
  AND (
    EXISTS (
      SELECT 1 FROM app_acl.role_assignments r
      JOIN app_acl.role_permissions p ON p.role_code=r.role_code
      WHERE r.account_id=app_acl.actor_id() AND r.condominium_id=app_acl.tenant_id()
        AND r.status='active' AND r.valid_from<=now()
        AND (r.valid_until IS NULL OR r.valid_until>now()) AND p.permission_code=p_code
    )
    OR EXISTS (
      SELECT 1 FROM app_acl.account_permission_grants g
      WHERE g.account_id=app_acl.actor_id() AND g.condominium_id=app_acl.tenant_id()
        AND g.permission_code=p_code AND g.status='active'
        AND (g.valid_until IS NULL OR g.valid_until>now())
    )
  )
$$;
CREATE FUNCTION app_acl.is_same_tenant(p_tenant uuid) RETURNS boolean LANGUAGE sql STABLE
SET search_path = '' AS $$
 SELECT p_tenant=app_acl.tenant_id() AND app_acl.actor_active()
$$;
REVOKE ALL ON ALL TABLES IN SCHEMA app_acl FROM PUBLIC, anon, authenticated, service_role, condoc_runtime;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA app_acl FROM PUBLIC, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA app, app_private, app_acl, app_audit TO condoc_runtime;
GRANT EXECUTE ON FUNCTION app_acl.actor_id(), app_acl.tenant_id(), app_acl.actor_active(), app_acl.has_permission(text), app_acl.is_same_tenant(uuid) TO condoc_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE condoc_owner IN SCHEMA app,app_private,app_acl,app_audit REVOKE ALL ON TABLES FROM PUBLIC,anon,authenticated,service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE condoc_owner IN SCHEMA app,app_private,app_acl,app_audit REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

ALTER TABLE app.condominiums ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.condominiums FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.condominiums FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.condominiums TO condoc_runtime;
CREATE POLICY read_rows ON app.condominiums FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(id) AND app_acl.has_permission('tenant.read'));
CREATE POLICY insert_rows ON app.condominiums FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(id) AND app_acl.has_permission('tenant.manage'));
GRANT UPDATE ON TABLE app.condominiums TO condoc_runtime;
CREATE POLICY update_rows ON app.condominiums FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(id) AND app_acl.has_permission('tenant.manage')) WITH CHECK (app_acl.is_same_tenant(id) AND app_acl.has_permission('tenant.manage'));

ALTER TABLE app.buildings ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.buildings FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.buildings FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.buildings TO condoc_runtime;
CREATE POLICY read_rows ON app.buildings FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('unit.read'));
CREATE POLICY insert_rows ON app.buildings FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('unit.manage'));
GRANT UPDATE ON TABLE app.buildings TO condoc_runtime;
CREATE POLICY update_rows ON app.buildings FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('unit.manage')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('unit.manage'));

ALTER TABLE app.units ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.units FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.units FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.units TO condoc_runtime;
CREATE POLICY read_rows ON app.units FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('unit.read'));
CREATE POLICY insert_rows ON app.units FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('unit.manage'));
GRANT UPDATE ON TABLE app.units TO condoc_runtime;
CREATE POLICY update_rows ON app.units FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('unit.manage')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('unit.manage'));

ALTER TABLE app_private.residents ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.residents FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.residents FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.residents TO condoc_runtime;
CREATE POLICY read_rows ON app_private.residents FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND (account_id=app_acl.actor_id() OR app_acl.has_permission('identity.read')));
CREATE POLICY insert_rows ON app_private.residents FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage'));
GRANT UPDATE ON TABLE app_private.residents TO condoc_runtime;
CREATE POLICY update_rows ON app_private.residents FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage'));

ALTER TABLE app_private.unit_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.unit_memberships FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.unit_memberships FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.unit_memberships TO condoc_runtime;
CREATE POLICY read_rows ON app_private.unit_memberships FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('identity.read'));
CREATE POLICY insert_rows ON app_private.unit_memberships FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.validate'));
GRANT UPDATE ON TABLE app_private.unit_memberships TO condoc_runtime;
CREATE POLICY update_rows ON app_private.unit_memberships FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.validate')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.validate'));

ALTER TABLE app_private.resident_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.resident_registrations FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.resident_registrations FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.resident_registrations TO condoc_runtime;
CREATE POLICY read_rows ON app_private.resident_registrations FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('identity.read') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read'));
CREATE POLICY insert_rows ON app_private.resident_registrations FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read'));
GRANT UPDATE ON TABLE app_private.resident_registrations TO condoc_runtime;
CREATE POLICY update_rows ON app_private.resident_registrations FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read'));

ALTER TABLE app.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.projects FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.projects FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.projects TO condoc_runtime;
CREATE POLICY read_rows ON app.projects FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.projects FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));
GRANT UPDATE ON TABLE app.projects TO condoc_runtime;
CREATE POLICY update_rows ON app.projects FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.files ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.files FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.files FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.files TO condoc_runtime;
CREATE POLICY read_rows ON app.files FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('file.read'));
CREATE POLICY insert_rows ON app.files FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('file.manage'));
GRANT UPDATE ON TABLE app.files TO condoc_runtime;
CREATE POLICY update_rows ON app.files FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('file.manage')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('file.manage'));

ALTER TABLE app_private.file_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.file_metadata FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.file_metadata FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.file_metadata TO condoc_runtime;
CREATE POLICY read_rows ON app_private.file_metadata FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('identity.read'));
CREATE POLICY insert_rows ON app_private.file_metadata FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('file.manage') AND uploaded_by=app_acl.actor_id());
GRANT UPDATE ON TABLE app_private.file_metadata TO condoc_runtime;
CREATE POLICY update_rows ON app_private.file_metadata FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('file.manage')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('file.manage'));

ALTER TABLE app.configuration_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.configuration_versions FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.configuration_versions FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.configuration_versions TO condoc_runtime;
CREATE POLICY read_rows ON app.configuration_versions FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.configuration_versions FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit') AND created_by=app_acl.actor_id());

ALTER TABLE app.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.documents FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.documents FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.documents TO condoc_runtime;
CREATE POLICY read_rows ON app.documents FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.documents FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));
GRANT UPDATE ON TABLE app.documents TO condoc_runtime;
CREATE POLICY update_rows ON app.documents FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.source_transcriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.source_transcriptions FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.source_transcriptions FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.source_transcriptions TO condoc_runtime;
CREATE POLICY read_rows ON app.source_transcriptions FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.source_transcriptions FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.source_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.source_blocks FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.source_blocks FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.source_blocks TO condoc_runtime;
CREATE POLICY read_rows ON app.source_blocks FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.source_blocks FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.document_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.document_nodes FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.document_nodes FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.document_nodes TO condoc_runtime;
CREATE POLICY read_rows ON app.document_nodes FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.document_nodes FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.node_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.node_revisions FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.node_revisions FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.node_revisions TO condoc_runtime;
CREATE POLICY read_rows ON app.node_revisions FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.node_revisions FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit') AND created_by=app_acl.actor_id());

ALTER TABLE app.origin_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.origin_mappings FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.origin_mappings FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.origin_mappings TO condoc_runtime;
CREATE POLICY read_rows ON app.origin_mappings FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.origin_mappings FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.cross_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.cross_references FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.cross_references FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.cross_references TO condoc_runtime;
CREATE POLICY read_rows ON app.cross_references FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.cross_references FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.document_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.document_notes FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.document_notes FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.document_notes TO condoc_runtime;
CREATE POLICY read_rows ON app.document_notes FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.document_notes FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.note_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.note_revisions FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.note_revisions FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.note_revisions TO condoc_runtime;
CREATE POLICY read_rows ON app.note_revisions FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.note_revisions FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit') AND created_by=app_acl.actor_id());

ALTER TABLE app.note_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.note_references FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.note_references FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.note_references TO condoc_runtime;
CREATE POLICY read_rows ON app.note_references FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.note_references FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app.region_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.region_revisions FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.region_revisions FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.region_revisions TO condoc_runtime;
CREATE POLICY read_rows ON app.region_revisions FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.region_revisions FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit') AND created_by=app_acl.actor_id());

ALTER TABLE app.document_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.document_snapshots FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.document_snapshots FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.document_snapshots TO condoc_runtime;
CREATE POLICY read_rows ON app.document_snapshots FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.document_snapshots FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT UPDATE ON TABLE app.document_snapshots TO condoc_runtime;
CREATE POLICY update_rows ON app.document_snapshots FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));

ALTER TABLE app.snapshot_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.snapshot_nodes FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.snapshot_nodes FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.snapshot_nodes TO condoc_runtime;
CREATE POLICY read_rows ON app.snapshot_nodes FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.snapshot_nodes FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT UPDATE ON TABLE app.snapshot_nodes TO condoc_runtime;
CREATE POLICY update_rows ON app.snapshot_nodes FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT DELETE ON TABLE app.snapshot_nodes TO condoc_runtime;
CREATE POLICY delete_rows ON app.snapshot_nodes FOR DELETE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));

ALTER TABLE app.snapshot_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.snapshot_notes FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.snapshot_notes FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.snapshot_notes TO condoc_runtime;
CREATE POLICY read_rows ON app.snapshot_notes FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.snapshot_notes FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT UPDATE ON TABLE app.snapshot_notes TO condoc_runtime;
CREATE POLICY update_rows ON app.snapshot_notes FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT DELETE ON TABLE app.snapshot_notes TO condoc_runtime;
CREATE POLICY delete_rows ON app.snapshot_notes FOR DELETE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));

ALTER TABLE app.snapshot_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.snapshot_configurations FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.snapshot_configurations FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.snapshot_configurations TO condoc_runtime;
CREATE POLICY read_rows ON app.snapshot_configurations FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.snapshot_configurations FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT UPDATE ON TABLE app.snapshot_configurations TO condoc_runtime;
CREATE POLICY update_rows ON app.snapshot_configurations FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT DELETE ON TABLE app.snapshot_configurations TO condoc_runtime;
CREATE POLICY delete_rows ON app.snapshot_configurations FOR DELETE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));

ALTER TABLE app.snapshot_regions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.snapshot_regions FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.snapshot_regions FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.snapshot_regions TO condoc_runtime;
CREATE POLICY read_rows ON app.snapshot_regions FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app.snapshot_regions FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT UPDATE ON TABLE app.snapshot_regions TO condoc_runtime;
CREATE POLICY update_rows ON app.snapshot_regions FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));
GRANT DELETE ON TABLE app.snapshot_regions TO condoc_runtime;
CREATE POLICY delete_rows ON app.snapshot_regions FOR DELETE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.freeze'));

ALTER TABLE app_private.internal_annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.internal_annotations FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.internal_annotations FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.internal_annotations TO condoc_runtime;
CREATE POLICY read_rows ON app_private.internal_annotations FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND (author_id=app_acl.actor_id() OR (visibility='review_team' AND app_acl.has_permission('annotation.read')) OR (visibility='management' AND app_acl.has_permission('annotation.management.read'))));
CREATE POLICY insert_rows ON app_private.internal_annotations FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('annotation.write') AND author_id=app_acl.actor_id());
GRANT UPDATE ON TABLE app_private.internal_annotations TO condoc_runtime;
CREATE POLICY update_rows ON app_private.internal_annotations FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('annotation.write') AND author_id=app_acl.actor_id()) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('annotation.write') AND author_id=app_acl.actor_id());

ALTER TABLE app_private.import_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.import_batches FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.import_batches FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.import_batches TO condoc_runtime;
CREATE POLICY read_rows ON app_private.import_batches FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('import.read') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read'));
CREATE POLICY insert_rows ON app_private.import_batches FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('import.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read') AND created_by=app_acl.actor_id());
GRANT UPDATE ON TABLE app_private.import_batches TO condoc_runtime;
CREATE POLICY update_rows ON app_private.import_batches FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('import.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('import.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read'));

ALTER TABLE app_private.import_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.import_rows FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.import_rows FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.import_rows TO condoc_runtime;
CREATE POLICY read_rows ON app_private.import_rows FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('import.read') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read'));
CREATE POLICY insert_rows ON app_private.import_rows FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('import.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read'));
GRANT UPDATE ON TABLE app_private.import_rows TO condoc_runtime;
CREATE POLICY update_rows ON app_private.import_rows FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('import.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('import.manage') AND app_acl.has_permission('identity.read') AND app_acl.has_permission('contact.read'));

ALTER TABLE app.render_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.render_jobs FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.render_jobs FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.render_jobs TO condoc_runtime;
CREATE POLICY read_rows ON app.render_jobs FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('export.read') AND (profile<>'internal' OR app_acl.has_permission('export.internal')));
CREATE POLICY insert_rows ON app.render_jobs FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.export') AND (profile<>'internal' OR app_acl.has_permission('export.internal')) AND requested_by=app_acl.actor_id());
GRANT UPDATE ON TABLE app.render_jobs TO condoc_runtime;
CREATE POLICY update_rows ON app.render_jobs FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.export') AND (profile<>'internal' OR app_acl.has_permission('export.internal'))) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.export') AND (profile<>'internal' OR app_acl.has_permission('export.internal')));

ALTER TABLE app.export_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.export_artifacts FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app.export_artifacts FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app.export_artifacts TO condoc_runtime;
CREATE POLICY read_rows ON app.export_artifacts FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('export.read'));
CREATE POLICY insert_rows ON app.export_artifacts FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.export') AND created_by=app_acl.actor_id());

ALTER TABLE app_private.compatibility_issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.compatibility_issues FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.compatibility_issues FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.compatibility_issues TO condoc_runtime;
CREATE POLICY read_rows ON app_private.compatibility_issues FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.read'));
CREATE POLICY insert_rows ON app_private.compatibility_issues FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));
GRANT UPDATE ON TABLE app_private.compatibility_issues TO condoc_runtime;
CREATE POLICY update_rows ON app_private.compatibility_issues FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('document.edit'));

ALTER TABLE app_audit.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_audit.events FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_audit.events FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_audit.events TO condoc_runtime;
CREATE POLICY read_rows ON app_audit.events FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('audit.read'));
CREATE POLICY insert_rows ON app_audit.events FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('audit.append') AND actor_id=app_acl.actor_id());

ALTER TABLE app_audit.identity_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_audit.identity_access FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_audit.identity_access FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_audit.identity_access TO condoc_runtime;
CREATE POLICY read_rows ON app_audit.identity_access FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('audit.read'));
CREATE POLICY insert_rows ON app_audit.identity_access FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('audit.append') AND actor_id=app_acl.actor_id());

ALTER TABLE app_private.resident_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.resident_contacts FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE app_private.resident_contacts FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT ON TABLE app_private.resident_contacts TO condoc_runtime;
CREATE POLICY read_rows ON app_private.resident_contacts FOR SELECT TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND (account_id=app_acl.actor_id() OR app_acl.has_permission('contact.read')));
CREATE POLICY insert_rows ON app_private.resident_contacts FOR INSERT TO condoc_runtime WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage') AND app_acl.has_permission('contact.read'));
GRANT UPDATE ON TABLE app_private.resident_contacts TO condoc_runtime;
CREATE POLICY update_rows ON app_private.resident_contacts FOR UPDATE TO condoc_runtime USING (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage') AND app_acl.has_permission('contact.read')) WITH CHECK (app_acl.is_same_tenant(condominium_id) AND app_acl.has_permission('resident.manage') AND app_acl.has_permission('contact.read'));

COMMIT;
