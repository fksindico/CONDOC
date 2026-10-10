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
    # Fase 4
    ProvisionOriginMappingListCreateView,
    DocumentCompareView,
    DocumentDeParaReportView,
    DocumentCrossReferenceListCreateView,
    DocumentRenumberingView,
    DocumentExportCleanView,
    DocumentExportDeParaView,
    # Fase 5
    ConsultationCampaignListCreateView,
    ConsultationCampaignDetailView,
    CampaignParticipantListCreateView,
    CampaignDocumentSnapshotView,
    CampaignSuggestionListCreateView,
    SuggestionDetailView,
    SuggestionComplementCreateView,
    MySuggestionListView,
    ModerationQueueListView,
    ModerationTechnicalAnalysisView,
    ModerationEditorialDecisionView,
    ModerationPublicationAuthorizeView,
    ModerationPublicationHideView,
    ModerationIdentityAccessView,
    # Fase 6
    AgreementRegisterView,
    RevisionAgreementStatsView,
    MyAgreementListView,
    SuggestionIncorporationView,
    CampaignConsultationSnapshotView,
    # Fase 7
    DocumentFinalPublicPackageView,
    DocumentCommissionInternalReportView,
    DocumentAssemblyReadingView,
    ExportArtifactDetailView,
    ManifestVerifyView,
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

    # =========================================================================
    # FASE 4: COMPARAÇÃO, MAPEAMENTO DE ORIGENS, RENUMERAÇÃO E EXPORTAÇÃO
    # =========================================================================
    path('condominiums/<uuid:condominium_id>/provisions/<uuid:provision_id>/origin-mappings', ProvisionOriginMappingListCreateView.as_view(), name='api_v1_provision_origin_mappings'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/compare', DocumentCompareView.as_view(), name='api_v1_document_compare'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/depara', DocumentDeParaReportView.as_view(), name='api_v1_document_depara'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/cross-references', DocumentCrossReferenceListCreateView.as_view(), name='api_v1_document_cross_references'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/renumber', DocumentRenumberingView.as_view(), name='api_v1_document_renumber'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/export/clean', DocumentExportCleanView.as_view(), name='api_v1_document_export_clean'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/export/depara', DocumentExportDeParaView.as_view(), name='api_v1_document_export_depara'),

    # =========================================================================
    # FASE 5: CONSULTA PÚBLICA, PARTICIPAÇÃO E MODERAÇÃO EDITORIAL
    # =========================================================================
    path('condominiums/<uuid:condominium_id>/campaigns', ConsultationCampaignListCreateView.as_view(), name='api_v1_campaigns'),
    path('condominiums/<uuid:condominium_id>/campaigns/<uuid:campaign_id>', ConsultationCampaignDetailView.as_view(), name='api_v1_campaign_detail'),
    path('condominiums/<uuid:condominium_id>/campaigns/<uuid:campaign_id>/open', ConsultationCampaignDetailView.as_view(), {'action': 'open'}, name='api_v1_campaign_open'),
    path('condominiums/<uuid:condominium_id>/campaigns/<uuid:campaign_id>/close', ConsultationCampaignDetailView.as_view(), {'action': 'close'}, name='api_v1_campaign_close'),
    path('condominiums/<uuid:condominium_id>/campaigns/<uuid:campaign_id>/participants', CampaignParticipantListCreateView.as_view(), name='api_v1_campaign_participants'),
    path('condominiums/<uuid:condominium_id>/campaigns/<uuid:campaign_id>/document-snapshot', CampaignDocumentSnapshotView.as_view(), name='api_v1_campaign_document_snapshot'),
    path('condominiums/<uuid:condominium_id>/campaigns/<uuid:campaign_id>/suggestions', CampaignSuggestionListCreateView.as_view(), name='api_v1_campaign_suggestions'),
    path('condominiums/<uuid:condominium_id>/campaigns/<uuid:campaign_id>/snapshots', CampaignConsultationSnapshotView.as_view(), name='api_v1_campaign_snapshots'),
    path('condominiums/<uuid:condominium_id>/suggestions/<uuid:suggestion_id>', SuggestionDetailView.as_view(), name='api_v1_suggestion_detail'),
    path('condominiums/<uuid:condominium_id>/suggestions/<uuid:suggestion_id>/complements', SuggestionComplementCreateView.as_view(), name='api_v1_suggestion_complements'),
    path('condominiums/<uuid:condominium_id>/my-suggestions', MySuggestionListView.as_view(), name='api_v1_my_suggestions'),
    path('condominiums/<uuid:condominium_id>/moderation/queue', ModerationQueueListView.as_view(), name='api_v1_moderation_queue'),
    path('condominiums/<uuid:condominium_id>/moderation/suggestions/<uuid:suggestion_id>/analysis', ModerationTechnicalAnalysisView.as_view(), name='api_v1_moderation_analysis'),
    path('condominiums/<uuid:condominium_id>/moderation/suggestions/<uuid:suggestion_id>/decision', ModerationEditorialDecisionView.as_view(), name='api_v1_moderation_decision'),
    path('condominiums/<uuid:condominium_id>/moderation/suggestions/<uuid:suggestion_id>/publish', ModerationPublicationAuthorizeView.as_view(), name='api_v1_moderation_publish'),
    path('condominiums/<uuid:condominium_id>/moderation/suggestions/<uuid:suggestion_id>/hide', ModerationPublicationHideView.as_view(), name='api_v1_moderation_hide'),
    path('condominiums/<uuid:condominium_id>/moderation/suggestions/<uuid:suggestion_id>/identity', ModerationIdentityAccessView.as_view(), name='api_v1_moderation_identity'),

    # =========================================================================
    # FASE 6: CONCORDÂNCIAS CONSULTIVAS E CONSOLIDAÇÃO NA MINUTA
    # =========================================================================
    path('condominiums/<uuid:condominium_id>/suggestions/<uuid:suggestion_id>/agreements', AgreementRegisterView.as_view(), name='api_v1_agreements'),
    path('condominiums/<uuid:condominium_id>/suggestions/<uuid:suggestion_id>/stats', RevisionAgreementStatsView.as_view(), name='api_v1_suggestion_agreement_stats'),
    path('condominiums/<uuid:condominium_id>/my-agreements', MyAgreementListView.as_view(), name='api_v1_my_agreements'),
    path('condominiums/<uuid:condominium_id>/suggestions/<uuid:suggestion_id>/incorporate', SuggestionIncorporationView.as_view(), name='api_v1_suggestion_incorporate'),

    # =========================================================================
    # FASE 7: PRESERVAÇÃO E PACOTES DE PUBLICAÇÃO FINAL
    # =========================================================================
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/export/package', DocumentFinalPublicPackageView.as_view(), name='api_v1_document_export_package'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/export/commission-report', DocumentCommissionInternalReportView.as_view(), name='api_v1_document_commission_report'),
    path('condominiums/<uuid:condominium_id>/documents/<uuid:document_id>/assembly-reading', DocumentAssemblyReadingView.as_view(), name='api_v1_document_assembly_reading'),
    path('condominiums/<uuid:condominium_id>/artifacts/<uuid:artifact_id>', ExportArtifactDetailView.as_view(), name='api_v1_artifact_detail'),
    path('condominiums/<uuid:condominium_id>/artifacts/<uuid:artifact_id>/verify', ManifestVerifyView.as_view(), name='api_v1_artifact_verify'),
]
