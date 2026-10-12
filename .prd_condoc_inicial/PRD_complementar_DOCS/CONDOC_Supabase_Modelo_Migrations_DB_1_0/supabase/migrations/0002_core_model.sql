-- DB-1.0: nucleo cadastral/documental; ambiente novo apenas.
BEGIN;
SET LOCAL ROLE condoc_owner;

CREATE TABLE app_acl.accounts (
  id uuid PRIMARY KEY,
  auth_user_id uuid UNIQUE,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (status IN ('active','suspended','archived')),
  CHECK (auth_user_id IS NULL OR auth_user_id = id)
);

CREATE TABLE app_acl.permissions (
  code text PRIMARY KEY,
  description text NOT NULL
);

CREATE TABLE app_acl.roles (
  code text PRIMARY KEY,
  description text NOT NULL
);

CREATE TABLE app_acl.role_permissions (
  role_code text NOT NULL,
  permission_code text NOT NULL,
  PRIMARY KEY (role_code, permission_code)
);

CREATE TABLE app.condominiums (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  status text NOT NULL DEFAULT 'active',
  timezone text NOT NULL DEFAULT 'America/Sao_Paulo',
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (length(btrim(name)) > 0),
  CHECK (status IN ('active','inactive'))
);

CREATE TABLE app_acl.role_assignments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  account_id uuid NOT NULL,
  role_code text NOT NULL,
  valid_from timestamptz NOT NULL DEFAULT now(),
  valid_until timestamptz,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (status IN ('active','revoked')),
  CHECK (valid_until IS NULL OR valid_until > valid_from)
);

CREATE TABLE app.buildings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  code text NOT NULL,
  name text NOT NULL,
  kind text NOT NULL DEFAULT 'tower',
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, code),
  CHECK (code = upper(btrim(code)) AND length(code)>0),
  CHECK (kind IN ('tower','block','single')),
  CHECK (status IN ('active','inactive'))
);

CREATE TABLE app.units (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  building_id uuid NOT NULL,
  code text NOT NULL,
  floor_label text,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, building_id, code),
  CHECK (code = upper(btrim(code)) AND length(code)>0),
  CHECK (status IN ('active','inactive'))
);

CREATE TABLE app_private.residents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  account_id uuid NOT NULL,
  full_name text NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, account_id),
  UNIQUE (condominium_id, id, account_id),
  CHECK (length(btrim(full_name))>0),
  CHECK (status IN ('pending','active','suspended','archived'))
);

CREATE TABLE app_private.unit_memberships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  resident_id uuid NOT NULL,
  unit_id uuid NOT NULL,
  relationship_type text NOT NULL,
  verification_status text NOT NULL DEFAULT 'declared',
  membership_status text NOT NULL DEFAULT 'active',
  validation_method text,
  review_reason text,
  reviewed_by uuid,
  reviewed_at timestamptz,
  started_at timestamptz NOT NULL DEFAULT now(),
  ended_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (relationship_type IN ('owner','tenant','family_resident','other_authorized')),
  CHECK (verification_status IN ('declared','under_review','validated','rejected')),
  CHECK (membership_status IN ('active','suspended','ended')),
  CHECK ((membership_status='ended') = (ended_at IS NOT NULL)),
  CHECK (ended_at IS NULL OR ended_at >= started_at),
  CHECK (verification_status NOT IN ('validated','rejected') OR (validation_method IS NOT NULL AND review_reason IS NOT NULL AND length(btrim(review_reason))>0 AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE TABLE app_private.resident_registrations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  unit_id uuid NOT NULL,
  full_name text NOT NULL,
  contact_email text,
  contact_phone text,
  relationship_type text NOT NULL DEFAULT 'other_authorized',
  source text NOT NULL,
  external_reference text,
  status text NOT NULL DEFAULT 'pending',
  linked_resident_id uuid,
  preverified_by uuid,
  preverified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (length(btrim(full_name))>0),
  CHECK (status IN ('pending','ready','linked','archived'))
);

CREATE TABLE app.projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  name text NOT NULL,
  kind text NOT NULL,
  status text NOT NULL DEFAULT 'preparation',
  coordinator_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (kind IN ('creation','revision','joint_revision')),
  CHECK (length(btrim(name))>0)
);

CREATE TABLE app.files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  bucket text NOT NULL,
  object_key text NOT NULL,
  mime_type text NOT NULL,
  size_bytes bigint NOT NULL,
  sha256 text NOT NULL,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (bucket, object_key),
  CHECK (size_bytes >= 0),
  CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  CHECK (status IN ('active','quarantined','deleted'))
);

CREATE TABLE app_private.file_metadata (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  file_id uuid NOT NULL,
  original_filename text NOT NULL,
  uploaded_by uuid NOT NULL,
  restricted_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, file_id),
  CHECK (jsonb_typeof(restricted_metadata)='object')
);

CREATE TABLE app.configuration_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  family_id uuid NOT NULL,
  kind text NOT NULL,
  version integer NOT NULL,
  name text NOT NULL,
  payload jsonb NOT NULL,
  sha256 text NOT NULL,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, family_id, version),
  CHECK (kind IN ('style','layout','table_style','template','block_catalog','numbering','font_manifest')),
  CHECK (version>0),
  CHECK (jsonb_typeof(payload)='object'),
  CHECK (sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE app.documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  project_id uuid NOT NULL,
  kind text NOT NULL,
  title text NOT NULL,
  editorial_status text NOT NULL DEFAULT 'draft',
  revision_lock bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (kind IN ('convention','internal_regulation')),
  CHECK (revision_lock > 0),
  CHECK (editorial_status IN ('draft','in_review','final_working','archived'))
);

CREATE TABLE app.source_transcriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  file_id uuid,
  version integer NOT NULL,
  content jsonb NOT NULL,
  checked_by uuid,
  checked_at timestamptz,
  sha256 text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, document_id, id),
  UNIQUE (condominium_id, document_id, version),
  CHECK (version>0),
  CHECK (jsonb_typeof(content)='object'),
  CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  CHECK ((checked_by IS NULL) = (checked_at IS NULL))
);

CREATE TABLE app.source_blocks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  transcription_id uuid NOT NULL,
  parent_id uuid,
  kind text NOT NULL,
  label text,
  position integer NOT NULL,
  body jsonb NOT NULL,
  page_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, document_id, id),
  CHECK (position>=0),
  CHECK (jsonb_typeof(body)='object'),
  CHECK (jsonb_typeof(page_refs)='array')
);

CREATE TABLE app.document_nodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  kind text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, document_id, id)
);

CREATE TABLE app.node_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  node_id uuid NOT NULL,
  revision integer NOT NULL,
  parent_node_id uuid,
  position integer NOT NULL,
  label text,
  body jsonb NOT NULL,
  numbering jsonb NOT NULL DEFAULT '{}'::jsonb,
  style_ref jsonb NOT NULL DEFAULT '{}'::jsonb,
  change_type text NOT NULL,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, document_id, id),
  UNIQUE (condominium_id, document_id, node_id, id),
  UNIQUE (condominium_id, node_id, revision),
  CHECK (revision>0 AND position>=0),
  CHECK (parent_node_id IS NULL OR parent_node_id<>node_id),
  CHECK (jsonb_typeof(body)='object'),
  CHECK (jsonb_typeof(numbering)='object' AND jsonb_typeof(style_ref)='object'),
  CHECK (change_type IN ('maintained','changed','included','excluded','moved','renumbered','split','merged','restructured'))
);

CREATE TABLE app.origin_mappings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  node_revision_id uuid NOT NULL,
  source_block_id uuid NOT NULL,
  relation_type text NOT NULL,
  excerpt jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (jsonb_typeof(excerpt)='object')
);

CREATE TABLE app.cross_references (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  source_document_id uuid NOT NULL,
  source_revision_id uuid NOT NULL,
  target_document_id uuid NOT NULL,
  target_node_id uuid NOT NULL,
  body_pointer text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id)
);

CREATE TABLE app.document_notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  kind text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, document_id, id),
  CHECK (kind IN ('footnote','endnote'))
);

CREATE TABLE app.note_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  note_id uuid NOT NULL,
  revision integer NOT NULL,
  body jsonb NOT NULL,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, document_id, note_id, id),
  UNIQUE (condominium_id, note_id, revision),
  CHECK (revision>0),
  CHECK (jsonb_typeof(body)='object')
);

CREATE TABLE app.note_references (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  source_revision_id uuid NOT NULL,
  note_id uuid NOT NULL,
  body_pointer text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id)
);

CREATE TABLE app.region_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  region_family_id uuid NOT NULL,
  revision integer NOT NULL,
  kind text NOT NULL,
  variant text NOT NULL,
  state text NOT NULL,
  body jsonb,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, document_id, id),
  UNIQUE (condominium_id, region_family_id, revision),
  CHECK (revision>0),
  CHECK (kind IN ('header','footer')),
  CHECK (variant IN ('default','first','odd','even')),
  CHECK (state IN ('template','explicit','cleared')),
  CHECK (body IS NULL OR jsonb_typeof(body)='object'),
  CHECK (state<>'explicit' OR body IS NOT NULL)
);

CREATE TABLE app.document_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  version_label text NOT NULL,
  status text NOT NULL DEFAULT 'building',
  manifest jsonb NOT NULL DEFAULT '{}'::jsonb,
  sha256 text,
  frozen_by uuid,
  frozen_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, document_id, id),
  UNIQUE (condominium_id, document_id, version_label),
  CHECK (status IN ('building','frozen')),
  CHECK (jsonb_typeof(manifest)='object'),
  CHECK (status<>'frozen' OR (sha256 ~ '^[0-9a-f]{64}$' AND frozen_by IS NOT NULL AND frozen_at IS NOT NULL))
);

CREATE TABLE app.snapshot_nodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  snapshot_id uuid NOT NULL,
  node_id uuid NOT NULL,
  revision_id uuid NOT NULL,
  rendered_label text,
  position integer NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, snapshot_id, node_id),
  CHECK (position>=0)
);

CREATE TABLE app.snapshot_notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  snapshot_id uuid NOT NULL,
  note_id uuid NOT NULL,
  revision_id uuid NOT NULL,
  rendered_number text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, snapshot_id, note_id)
);

CREATE TABLE app.snapshot_configurations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  snapshot_id uuid NOT NULL,
  slot text NOT NULL,
  configuration_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, snapshot_id, slot)
);

CREATE TABLE app.snapshot_regions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  snapshot_id uuid NOT NULL,
  region_revision_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, snapshot_id, region_revision_id)
);

CREATE TABLE app_private.internal_annotations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid NOT NULL,
  node_id uuid,
  author_id uuid NOT NULL,
  visibility text NOT NULL,
  content text NOT NULL,
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (visibility IN ('author_only','review_team','management'))
);

CREATE TABLE app_private.import_batches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  file_id uuid NOT NULL,
  kind text NOT NULL,
  status text NOT NULL,
  revision integer NOT NULL DEFAULT 1,
  mapping jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid NOT NULL,
  confirmed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (kind IN ('residents','document')),
  CHECK (revision>0),
  CHECK (jsonb_typeof(mapping)='object')
);

CREATE TABLE app_private.import_rows (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  batch_id uuid NOT NULL,
  row_number integer NOT NULL,
  data jsonb NOT NULL,
  classification text NOT NULL,
  selected boolean NOT NULL DEFAULT false,
  action text,
  errors jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, batch_id, row_number),
  CHECK (row_number>0),
  CHECK (jsonb_typeof(data)='object' AND jsonb_typeof(errors)='array')
);

CREATE TABLE app.render_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  snapshot_id uuid NOT NULL,
  requested_by uuid NOT NULL,
  profile text NOT NULL,
  status text NOT NULL DEFAULT 'queued',
  options jsonb NOT NULL DEFAULT '{}'::jsonb,
  idempotency_key text NOT NULL,
  started_at timestamptz,
  finished_at timestamptz,
  error_code text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, requested_by, idempotency_key),
  CHECK (profile IN ('draft','clean_working','final_presentation','de_para','internal','preservation')),
  CHECK (status IN ('queued','preflight','rendering','finalizing','validating','ready','failed','cancelled')),
  CHECK (jsonb_typeof(options)='object'),
  CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at>=started_at)
);

CREATE TABLE app.export_artifacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  render_job_id uuid NOT NULL,
  file_id uuid NOT NULL,
  kind text NOT NULL,
  manifest jsonb NOT NULL,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  UNIQUE (condominium_id, render_job_id, kind),
  CHECK (kind IN ('docx','pdf','json','validation_report')),
  CHECK (jsonb_typeof(manifest)='object')
);

CREATE TABLE app_private.compatibility_issues (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  document_id uuid,
  import_batch_id uuid,
  kind text NOT NULL,
  severity text NOT NULL,
  status text NOT NULL DEFAULT 'open',
  location jsonb NOT NULL DEFAULT '{}'::jsonb,
  detail jsonb NOT NULL,
  decision_by uuid,
  decision_reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, id),
  CHECK (severity IN ('info','warning','blocking')),
  CHECK (status IN ('open','resolved','accepted_exception')),
  CHECK (jsonb_typeof(location)='object' AND jsonb_typeof(detail)='object')
);

CREATE TABLE app_audit.events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  actor_id uuid,
  action text NOT NULL,
  resource_type text NOT NULL,
  resource_id uuid,
  request_id text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (jsonb_typeof(metadata)='object')
);

CREATE TABLE app_audit.identity_access (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  actor_id uuid NOT NULL,
  resident_id uuid,
  resource_id uuid,
  purpose text,
  request_id text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app_private.resident_contacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  resident_id uuid NOT NULL,
  account_id uuid NOT NULL,
  phone_e164 text NOT NULL,
  contact_email text,
  phone_verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, resident_id),
  CHECK (phone_e164 ~ '^\+[1-9][0-9]{1,14}$')
);

CREATE TABLE app_acl.account_permission_grants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  condominium_id uuid NOT NULL,
  account_id uuid NOT NULL,
  permission_code text NOT NULL,
  valid_until timestamptz,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (condominium_id, account_id, permission_code),
  CHECK (status IN ('active','revoked'))
);

ALTER TABLE app_acl.accounts ADD CONSTRAINT fk_0_0 FOREIGN KEY (auth_user_id) REFERENCES auth.users (id) ON DELETE SET NULL;

ALTER TABLE app_acl.role_permissions ADD CONSTRAINT fk_3_0 FOREIGN KEY (role_code) REFERENCES app_acl.roles (code) ON DELETE RESTRICT;

ALTER TABLE app_acl.role_permissions ADD CONSTRAINT fk_3_1 FOREIGN KEY (permission_code) REFERENCES app_acl.permissions (code) ON DELETE RESTRICT;

ALTER TABLE app_acl.role_assignments ADD CONSTRAINT fk_5_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app_acl.role_assignments ADD CONSTRAINT fk_5_1 FOREIGN KEY (account_id) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_acl.role_assignments ADD CONSTRAINT fk_5_2 FOREIGN KEY (role_code) REFERENCES app_acl.roles (code) ON DELETE RESTRICT;

ALTER TABLE app.buildings ADD CONSTRAINT fk_6_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app.units ADD CONSTRAINT fk_7_0 FOREIGN KEY (condominium_id, building_id) REFERENCES app.buildings (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.residents ADD CONSTRAINT fk_8_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app_private.residents ADD CONSTRAINT fk_8_1 FOREIGN KEY (account_id) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_private.unit_memberships ADD CONSTRAINT fk_9_0 FOREIGN KEY (condominium_id, resident_id) REFERENCES app_private.residents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.unit_memberships ADD CONSTRAINT fk_9_1 FOREIGN KEY (condominium_id, unit_id) REFERENCES app.units (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.unit_memberships ADD CONSTRAINT fk_9_2 FOREIGN KEY (reviewed_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_private.resident_registrations ADD CONSTRAINT fk_10_0 FOREIGN KEY (condominium_id, unit_id) REFERENCES app.units (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.resident_registrations ADD CONSTRAINT fk_10_1 FOREIGN KEY (condominium_id, linked_resident_id) REFERENCES app_private.residents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.resident_registrations ADD CONSTRAINT fk_10_2 FOREIGN KEY (preverified_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.projects ADD CONSTRAINT fk_11_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app.projects ADD CONSTRAINT fk_11_1 FOREIGN KEY (coordinator_id) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.files ADD CONSTRAINT fk_12_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app_private.file_metadata ADD CONSTRAINT fk_13_0 FOREIGN KEY (condominium_id, file_id) REFERENCES app.files (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.file_metadata ADD CONSTRAINT fk_13_1 FOREIGN KEY (uploaded_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.configuration_versions ADD CONSTRAINT fk_14_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app.configuration_versions ADD CONSTRAINT fk_14_1 FOREIGN KEY (created_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.documents ADD CONSTRAINT fk_15_0 FOREIGN KEY (condominium_id, project_id) REFERENCES app.projects (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.source_transcriptions ADD CONSTRAINT fk_16_0 FOREIGN KEY (condominium_id, document_id) REFERENCES app.documents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.source_transcriptions ADD CONSTRAINT fk_16_1 FOREIGN KEY (condominium_id, file_id) REFERENCES app.files (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.source_transcriptions ADD CONSTRAINT fk_16_2 FOREIGN KEY (checked_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.source_blocks ADD CONSTRAINT fk_17_0 FOREIGN KEY (condominium_id, document_id, transcription_id) REFERENCES app.source_transcriptions (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.source_blocks ADD CONSTRAINT fk_17_1 FOREIGN KEY (condominium_id, document_id, parent_id) REFERENCES app.source_blocks (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.document_nodes ADD CONSTRAINT fk_18_0 FOREIGN KEY (condominium_id, document_id) REFERENCES app.documents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.node_revisions ADD CONSTRAINT fk_19_0 FOREIGN KEY (condominium_id, document_id, node_id) REFERENCES app.document_nodes (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.node_revisions ADD CONSTRAINT fk_19_1 FOREIGN KEY (condominium_id, document_id, parent_node_id) REFERENCES app.document_nodes (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.node_revisions ADD CONSTRAINT fk_19_2 FOREIGN KEY (created_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.origin_mappings ADD CONSTRAINT fk_20_0 FOREIGN KEY (condominium_id, document_id, node_revision_id) REFERENCES app.node_revisions (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.origin_mappings ADD CONSTRAINT fk_20_1 FOREIGN KEY (condominium_id, document_id, source_block_id) REFERENCES app.source_blocks (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.cross_references ADD CONSTRAINT fk_21_0 FOREIGN KEY (condominium_id, source_document_id, source_revision_id) REFERENCES app.node_revisions (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.cross_references ADD CONSTRAINT fk_21_1 FOREIGN KEY (condominium_id, target_document_id, target_node_id) REFERENCES app.document_nodes (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.document_notes ADD CONSTRAINT fk_22_0 FOREIGN KEY (condominium_id, document_id) REFERENCES app.documents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.note_revisions ADD CONSTRAINT fk_23_0 FOREIGN KEY (condominium_id, document_id, note_id) REFERENCES app.document_notes (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.note_revisions ADD CONSTRAINT fk_23_1 FOREIGN KEY (created_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.note_references ADD CONSTRAINT fk_24_0 FOREIGN KEY (condominium_id, document_id, source_revision_id) REFERENCES app.node_revisions (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.note_references ADD CONSTRAINT fk_24_1 FOREIGN KEY (condominium_id, document_id, note_id) REFERENCES app.document_notes (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.region_revisions ADD CONSTRAINT fk_25_0 FOREIGN KEY (condominium_id, document_id) REFERENCES app.documents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.region_revisions ADD CONSTRAINT fk_25_1 FOREIGN KEY (created_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.document_snapshots ADD CONSTRAINT fk_26_0 FOREIGN KEY (condominium_id, document_id) REFERENCES app.documents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.document_snapshots ADD CONSTRAINT fk_26_1 FOREIGN KEY (frozen_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.snapshot_nodes ADD CONSTRAINT fk_27_0 FOREIGN KEY (condominium_id, document_id, snapshot_id) REFERENCES app.document_snapshots (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.snapshot_nodes ADD CONSTRAINT fk_27_1 FOREIGN KEY (condominium_id, document_id, node_id, revision_id) REFERENCES app.node_revisions (condominium_id, document_id, node_id, id) ON DELETE RESTRICT;

ALTER TABLE app.snapshot_notes ADD CONSTRAINT fk_28_0 FOREIGN KEY (condominium_id, document_id, snapshot_id) REFERENCES app.document_snapshots (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.snapshot_notes ADD CONSTRAINT fk_28_1 FOREIGN KEY (condominium_id, document_id, note_id, revision_id) REFERENCES app.note_revisions (condominium_id, document_id, note_id, id) ON DELETE RESTRICT;

ALTER TABLE app.snapshot_configurations ADD CONSTRAINT fk_29_0 FOREIGN KEY (condominium_id, snapshot_id) REFERENCES app.document_snapshots (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.snapshot_configurations ADD CONSTRAINT fk_29_1 FOREIGN KEY (condominium_id, configuration_id) REFERENCES app.configuration_versions (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.snapshot_regions ADD CONSTRAINT fk_30_0 FOREIGN KEY (condominium_id, document_id, snapshot_id) REFERENCES app.document_snapshots (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app.snapshot_regions ADD CONSTRAINT fk_30_1 FOREIGN KEY (condominium_id, document_id, region_revision_id) REFERENCES app.region_revisions (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.internal_annotations ADD CONSTRAINT fk_31_0 FOREIGN KEY (condominium_id, document_id) REFERENCES app.documents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.internal_annotations ADD CONSTRAINT fk_31_1 FOREIGN KEY (condominium_id, document_id, node_id) REFERENCES app.document_nodes (condominium_id, document_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.internal_annotations ADD CONSTRAINT fk_31_2 FOREIGN KEY (author_id) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_private.import_batches ADD CONSTRAINT fk_32_0 FOREIGN KEY (condominium_id, file_id) REFERENCES app.files (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.import_batches ADD CONSTRAINT fk_32_1 FOREIGN KEY (created_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_private.import_rows ADD CONSTRAINT fk_33_0 FOREIGN KEY (condominium_id, batch_id) REFERENCES app_private.import_batches (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.render_jobs ADD CONSTRAINT fk_34_0 FOREIGN KEY (condominium_id, snapshot_id) REFERENCES app.document_snapshots (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.render_jobs ADD CONSTRAINT fk_34_1 FOREIGN KEY (requested_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app.export_artifacts ADD CONSTRAINT fk_35_0 FOREIGN KEY (condominium_id, render_job_id) REFERENCES app.render_jobs (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.export_artifacts ADD CONSTRAINT fk_35_1 FOREIGN KEY (condominium_id, file_id) REFERENCES app.files (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app.export_artifacts ADD CONSTRAINT fk_35_2 FOREIGN KEY (created_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_private.compatibility_issues ADD CONSTRAINT fk_36_0 FOREIGN KEY (condominium_id, document_id) REFERENCES app.documents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.compatibility_issues ADD CONSTRAINT fk_36_1 FOREIGN KEY (condominium_id, import_batch_id) REFERENCES app_private.import_batches (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.compatibility_issues ADD CONSTRAINT fk_36_2 FOREIGN KEY (decision_by) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_audit.events ADD CONSTRAINT fk_37_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app_audit.events ADD CONSTRAINT fk_37_1 FOREIGN KEY (actor_id) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_audit.identity_access ADD CONSTRAINT fk_38_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app_audit.identity_access ADD CONSTRAINT fk_38_1 FOREIGN KEY (actor_id) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_audit.identity_access ADD CONSTRAINT fk_38_2 FOREIGN KEY (condominium_id, resident_id) REFERENCES app_private.residents (condominium_id, id) ON DELETE RESTRICT;

ALTER TABLE app_private.resident_contacts ADD CONSTRAINT fk_39_0 FOREIGN KEY (condominium_id, resident_id, account_id) REFERENCES app_private.residents (condominium_id, id, account_id) ON DELETE RESTRICT;

ALTER TABLE app_acl.account_permission_grants ADD CONSTRAINT fk_40_0 FOREIGN KEY (condominium_id) REFERENCES app.condominiums (id) ON DELETE RESTRICT;

ALTER TABLE app_acl.account_permission_grants ADD CONSTRAINT fk_40_1 FOREIGN KEY (account_id) REFERENCES app_acl.accounts (id) ON DELETE RESTRICT;

ALTER TABLE app_acl.account_permission_grants ADD CONSTRAINT fk_40_2 FOREIGN KEY (permission_code) REFERENCES app_acl.permissions (code) ON DELETE RESTRICT;

CREATE UNIQUE INDEX uq_open_unit_membership ON app_private.unit_memberships(condominium_id,resident_id,unit_id) WHERE ended_at IS NULL;

CREATE INDEX ix_role_actor_tenant ON app_acl.role_assignments(account_id,condominium_id,status);

CREATE INDEX ix_nodes_document ON app.document_nodes(condominium_id,document_id);

CREATE INDEX ix_revision_document ON app.node_revisions(condominium_id,document_id,node_id,revision DESC);

CREATE INDEX ix_render_queue ON app.render_jobs(status,created_at);

CREATE INDEX ix_import_queue ON app_private.import_batches(condominium_id,status,created_at);

CREATE INDEX ix_audit_tenant_date ON app_audit.events(condominium_id,created_at DESC);

COMMIT;
