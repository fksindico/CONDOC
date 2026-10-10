"""
Roteamento da API v1 — CONDC (Fase 1, Fase 2 e Fase 3)
"""
from django.urls import path
from .views import (
    # Fase 1
    SessionInfoView,
    CondominiumListCreateView,
    BuildingListCreateView,
    UnitListCreateView,
    ResidentRegistrationListCreateView,
    UnitMembershipListView,
    VerifyMembershipActionView,
    RoleAssignmentListCreateView,
    # Fase 2
    ResidentImportTemplateView,
    ResidentImportListCreateView,
    ResidentImportDetailView,
    ResidentImportMappingView,
    ResidentImportRowsListView,
    ResidentImportRowDetailView,
    ResidentImportPreviewView,
    ResidentImportConfirmView,
    AccessInvitationListCreateView,
    AccessInvitationRevokeView,
    PublicInvitationInspectView,
    PublicInvitationRedeemView,
    # Fase 3
    ProjectListCreateView,
    DocumentListCreateView,
    DocumentDetailView,
    SourceFileUploadView,
    TranscriptionDetailConfirmView,
    ProvisionListCreateView,
    ProvisionDetailUpdateView,
    ProvisionInternalNoteListCreateView,
    DocumentSnapshotListCreateView,
    DocumentSnapshotDetailView,
)

urlpatterns = [
    # Sessão e Auth BFF
    path('auth/session', SessionInfoView.as_view(), name='api_v1_session_info'),

    # Condomínios (Tenancy Raiz)
    path('condominiums', CondominiumListCreateView.as_view(), name='api_v1_condominiums'),

    # Torres / Blocos / Prédios
    path('condominiums/<uuid:condominium_id>/buildings', BuildingListCreateView.as_view(), name='api_v1_buildings'),

    # Unidades Autônomas
    path('condominiums/<uuid:condominium_id>/units', UnitListCreateView.as_view(), name='api_v1_units'),

    # Pré-cadastro manual de moradores (CA-02)
    path('condominiums/<uuid:condominium_id>/registrations', ResidentRegistrationListCreateView.as_view(), name='api_v1_registrations'),

    # Vínculos com Unidades (CA-13, CA-14)
    path('condominiums/<uuid:condominium_id>/memberships', UnitMembershipListView.as_view(), name='api_v1_memberships'),

    # Verificação Documental Auditada de Vínculo (CA-12, CA-15)
    path('condominiums/<uuid:condominium_id>/memberships/<uuid:membership_id>/verify', VerifyMembershipActionView.as_view(), name='api_v1_membership_verify'),

    # Atribuição de Papéis e Permissões (CA-28)
    path('condominiums/<uuid:condominium_id>/roles', RoleAssignmentListCreateView.as_view(), name='api_v1_roles'),

    # =========================================================================
    # FASE 2: IMPORTAÇÃO CADASTRAL
    # =========================================================================
    path('condominiums/<uuid:condominium_id>/resident-imports/template', ResidentImportTemplateView.as_view(), name='api_v1_import_template'),
    path('condominiums/<uuid:condominium_id>/resident-imports', ResidentImportListCreateView.as_view(), name='api_v1_import_batches'),
    path('condominiums/<uuid:condominium_id>/resident-imports/<uuid:batch_id>', ResidentImportDetailView.as_view(), name='api_v1_import_batch_detail'),
    path('condominiums/<uuid:condominium_id>/resident-imports/<uuid:batch_id>/mapping', ResidentImportMappingView.as_view(), name='api_v1_import_mapping'),
    path('condominiums/<uuid:condominium_id>/resident-imports/<uuid:batch_id>/rows', ResidentImportRowsListView.as_view(), name='api_v1_import_rows'),
    path('condominiums/<uuid:condominium_id>/resident-imports/<uuid:batch_id>/rows/<uuid:row_id>', ResidentImportRowDetailView.as_view(), name='api_v1_import_row_detail'),
    path('condominiums/<uuid:condominium_id>/resident-imports/<uuid:batch_id>/preview', ResidentImportPreviewView.as_view(), name='api_v1_import_preview'),
    path('condominiums/<uuid:condominium_id>/resident-imports/<uuid:batch_id>/confirm', ResidentImportConfirmView.as_view(), name='api_v1_import_confirm'),

    # =========================================================================
    # FASE 2: CONVITES DE ACESSO
    # =========================================================================
    path('condominiums/<uuid:condominium_id>/invitations', AccessInvitationListCreateView.as_view(), name='api_v1_invitations'),
    path('condominiums/<uuid:condominium_id>/invitations/<uuid:invitation_id>/revoke', AccessInvitationRevokeView.as_view(), name='api_v1_invitation_revoke'),
    path('access/invitations/inspect', PublicInvitationInspectView.as_view(), name='api_v1_public_invitation_inspect'),
    path('access/invitations/redeem', PublicInvitationRedeemView.as_view(), name='api_v1_public_invitation_redeem'),

    # =========================================================================
    # FASE 3: NÚCLEO DOCUMENTAL, DISPOSITIVOS E SNAPSHOTS
    # =========================================================================
    path('condominiums/<uuid:condominium_id>/projects', ProjectListCreateView.as_view(), name='api_v1_projects'),
    path('condominiums/<uuid:condominium_id>/projects/<uuid:project_id>/documents', DocumentListCreateView.as_view(), name='api_v1_documents'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>', DocumentDetailView.as_view(), name='api_v1_document_detail'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/source-files', SourceFileUploadView.as_view(), name='api_v1_source_files'),
    path('condominiums/<uuid:condominium_id>/transcriptions/<uuid:transcription_id>', TranscriptionDetailConfirmView.as_view(), name='api_v1_transcription_detail'),
    path('condominiums/<uuid:condominium_id>/transcriptions/<uuid:transcription_id>/<str:action>', TranscriptionDetailConfirmView.as_view(), name='api_v1_transcription_action'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/provisions', ProvisionListCreateView.as_view(), name='api_v1_provisions'),
    path('condominiums/<uuid:condominium_id>/provisions/<uuid:provision_id>', ProvisionDetailUpdateView.as_view(), name='api_v1_provision_detail'),
    path('condominiums/<uuid:condominium_id>/provisions/<uuid:provision_id>/notes', ProvisionInternalNoteListCreateView.as_view(), name='api_v1_provision_notes'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/snapshots', DocumentSnapshotListCreateView.as_view(), name='api_v1_document_snapshots'),
    path('condominiums/<uuid:condominium_id>/snapshots/<uuid:snapshot_id>', DocumentSnapshotDetailView.as_view(), name='api_v1_snapshot_detail'),
]
