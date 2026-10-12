"""
Serializers REST API v1 — CONDC (Fase 1 e Fase 2)
Compatíveis com os contratos definidos em packages/api-contracts e PRD Mestre v3.0
"""
from rest_framework import serializers
from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    ResidentRegistration,
    Resident,
    UnitMembership,
    MembershipVerificationEvent,
    RoleAssignment,
    IdentityAccessEvent,
    ImportBatch,
    ImportRow,
    AccessInvitation,
    InvitationRedemption,
    Project,
    Document,
    SourceFile,
    SourceTranscription,
    Provision,
    ProvisionRevision,
    InternalNote,
    DocumentSnapshot,
    SnapshotItem,
    OriginMapping,
    CrossReference,
    ConsultationCampaign,
    CampaignParticipant,
    Suggestion,
    SuggestionRevision,
    PublishedSuggestionRevision,
    SuggestionEditorialDecision,
    SuggestionAttachment,
    ConsultativeAgreement,
    AgreementEvent,
    SuggestionIncorporation,
    ConsultationSnapshot,
    ExportArtifact,
)

# ============================================================================
# FASE 1: Identidade e Estrutura Física
# ============================================================================

class CondominiumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condominium
        fields = [
            'id', 'name', 'cnpj', 'status', 'timezone',
            'address_street', 'address_number', 'address_complement',
            'address_neighborhood', 'address_city', 'address_state', 'address_zip_code',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'condominium_id', 'code', 'name', 'kind', 'display_order', 'status', 'created_at']
        read_only_fields = ['id', 'condominium_id', 'created_at']


class UnitSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    building_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Unit
        fields = [
            'id', 'condominium_id', 'building_id', 'building_name',
            'code', 'floor_label', 'description', 'ideal_fraction', 'block',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'condominium_id', 'created_at']


class ResidentRegistrationCreateSerializer(serializers.ModelSerializer):
    unit_id = serializers.UUIDField(required=True)

    class Meta:
        model = ResidentRegistration
        fields = [
            'id', 'unit_id', 'full_name', 'phone_e164', 'email',
            'relationship', 'notes', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']


class UnitMembershipListSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source='unit.code', read_only=True)
    resident_name = serializers.CharField(source='resident.full_name', read_only=True)
    phone_e164 = serializers.CharField(source='resident.phone_e164', read_only=True)

    class Meta:
        model = UnitMembership
        fields = [
            'id', 'condominium_id', 'resident_id', 'resident_name', 'phone_e164',
            'unit_id', 'unit_code', 'category', 'verification_status',
            'membership_status', 'verification_method', 'reviewed_at',
            'started_at', 'ended_at'
        ]
        read_only_fields = fields



class VerifyMembershipActionSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=['validado', 'recusado', 'em_analise', 'revogado'])
    method = serializers.ChoiceField(choices=['documento', 'declaracao_sindico', 'cadastro_legado', 'presencial'])
    reason = serializers.CharField(min_length=5, max_length=1000)


class RoleAssignmentSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.full_name', read_only=True)
    account_email = serializers.CharField(source='account.email', read_only=True)

    class Meta:
        model = RoleAssignment
        fields = [
            'id', 'condominium_id', 'account_id', 'account_name',
            'account_email', 'role', 'valid_from', 'valid_until', 'status'
        ]
        read_only_fields = ['id', 'condominium_id', 'valid_from']


# ============================================================================
# FASE 2: Importação Cadastral e Convites
# ============================================================================

class ImportBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportBatch
        fields = [
            'id', 'condominium_id', 'file_name', 'file_hash', 'source_label',
            'status', 'revision', 'mapping', 'totals', 'error_message',
            'created_by_id', 'confirmed_by_id', 'confirmed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class ImportRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportRow
        fields = [
            'id', 'batch_id', 'row_number', 'classification',
            'issues', 'selected', 'action', 'normalized_data',
            'target_registration_id', 'target_version', 'result_id', 'created_at'
        ]
        read_only_fields = ['id', 'batch_id', 'row_number', 'classification', 'issues', 'result_id', 'created_at']


class ImportRowActionSerializer(serializers.Serializer):
    selected = serializers.BooleanField(required=True)
    action = serializers.ChoiceField(choices=[
        'create_registration', 'update_registration',
        'add_registration_for_unit', 'skip', 'request_manual_review'
    ], required=True)
    target_registration_id = serializers.UUIDField(required=False, allow_null=True)


class ImportConfirmActionSerializer(serializers.Serializer):
    expected_revision = serializers.IntegerField(required=True)
    acknowledge_selected_operations = serializers.BooleanField(required=True)


class AccessInvitationCreateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=[
        'individual_preconferido', 'individual_padrao',
        'unidade_fixa', 'torre_bloco', 'amplo', 'leitura'
    ])
    target_registration_id = serializers.UUIDField(required=False, allow_null=True)
    target_unit_id = serializers.UUIDField(required=False, allow_null=True)
    target_building_id = serializers.UUIDField(required=False, allow_null=True)
    expected_contact = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expires_in_days = serializers.IntegerField(default=7, min_value=1, max_value=90)
    max_redemptions = serializers.IntegerField(default=1, min_value=1, max_value=5000)


class AccessInvitationListSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source='target_unit.code', read_only=True)

    class Meta:
        model = AccessInvitation
        fields = [
            'id', 'condominium_id', 'kind', 'target_registration_id',
            'target_unit_id', 'unit_code', 'target_building_id', 'expected_contact',
            'expires_at', 'max_redemptions', 'redemption_count', 'status',
            'created_at', 'revoked_at', 'revoke_reason'
        ]
        read_only_fields = fields


class InvitationRevokeActionSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5, max_length=1000, required=True)


class InvitationInspectResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    status = serializers.CharField()
    kind = serializers.CharField()
    condominium_id = serializers.CharField()
    condominium_name = serializers.CharField()
    unit_label = serializers.CharField(allow_null=True)
    expires_at = serializers.CharField()
    requires_contact_confirmation = serializers.BooleanField()


class InvitationRedeemActionSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    provided_contact = serializers.CharField(required=False, allow_blank=True)


# ============================================================================
# FASE 3: Núcleo Documental, Dispositivos e Snapshots
# ============================================================================

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id', 'condominium_id', 'name', 'purpose', 'kind',
            'coordinator_account_id', 'status', 'settings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'project_id', 'condominium_id', 'type', 'title',
            'editorial_status', 'numbering_policy', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SourceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceFile
        fields = [
            'id', 'condominium_id', 'storage_key', 'filename', 'mime_type',
            'size_bytes', 'file_hash', 'uploaded_by_id', 'state', 'created_at'
        ]
        read_only_fields = ['id', 'file_hash', 'created_at']


class SourceTranscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceTranscription
        fields = [
            'id', 'document_id', 'condominium_id', 'source_file_id',
            'version', 'status', 'raw_text', 'corrected_text',
            'checked_by_id', 'checked_at', 'replaces_transcription_id', 'created_at'
        ]
        read_only_fields = ['id', 'version', 'status', 'checked_by_id', 'checked_at', 'created_at']


class TranscriptionConfirmActionSerializer(serializers.Serializer):
    corrected_text = serializers.CharField(required=False, allow_blank=True)


class TranscriptionCorrectActionSerializer(serializers.Serializer):
    corrected_text = serializers.CharField(required=True)


class ProvisionCreateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=[
        'titulo', 'capitulo', 'secao', 'subsecao', 'artigo',
        'caput', 'paragrafo', 'inciso', 'alinea', 'preambulo', 'anexo'
    ], default='artigo')
    label = serializers.CharField(max_length=100)
    text = serializers.CharField()
    parent_provision_id = serializers.UUIDField(required=False, allow_null=True)
    position = serializers.IntegerField(default=0)
    theme = serializers.CharField(max_length=100, required=False, allow_blank=True)
    change_type = serializers.ChoiceField(choices=[
        'mantido', 'alterado', 'incluido', 'excluido',
        'movido', 'renumerado', 'desmembrado', 'consolidado', 'reestruturado'
    ], default='mantido')


class ProvisionUpdateSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    label = serializers.CharField(max_length=100, required=False)
    parent_provision_id = serializers.UUIDField(required=False, allow_null=True)
    position = serializers.IntegerField(required=False)
    theme = serializers.CharField(max_length=100, required=False, allow_blank=True)
    change_type = serializers.ChoiceField(choices=[
        'mantido', 'alterado', 'incluido', 'excluido',
        'movido', 'renumerado', 'desmembrado', 'consolidado', 'reestruturado'
    ], default='alterado')


class InternalNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalNote
        fields = [
            'id', 'condominium_id', 'provision_id', 'revision_id',
            'author_account_id', 'content', 'visibility', 'category',
            'resolved_at', 'resolved_by_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentSnapshotCreateSerializer(serializers.Serializer):
    version_label = serializers.CharField(max_length=100, required=True)
    purpose = serializers.ChoiceField(choices=[
        'consulta_publica', 'marco_revisao', 'versao_final'
    ], default='consulta_publica')


# ============================================================================
# FASE 4: Comparação, Mapeamento de Origens, Renumeração e Exportação
# ============================================================================

class OriginMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OriginMapping
        fields = [
            'id', 'condominium_id', 'revision_id', 'source_provision_id',
            'relation_type', 'excerpt', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OriginMappingCreateSerializer(serializers.Serializer):
    source_provision_id = serializers.UUIDField(required=True)
    relation_type = serializers.ChoiceField(
        choices=['mantido', 'alterado', 'desmembrado', 'consolidado'],
        default='mantido'
    )
    excerpt = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class CrossReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossReference
        fields = [
            'id', 'condominium_id', 'revision_id', 'target_provision_id',
            'label_template', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']


class CrossReferenceCreateSerializer(serializers.Serializer):
    target_provision_id = serializers.UUIDField(required=True)
    label_template = serializers.CharField(max_length=100, default='art. {target_label}')


class RenumberingApplySerializer(serializers.Serializer):
    strategy = serializers.ChoiceField(
        choices=['preservar_original', 'renumeracao_automatica'],
        default='renumeracao_automatica'
    )


# ============================================================================
# FASE 5: Consulta Pública, Participação e Moderação Editorial
# ============================================================================

class ConsultationCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationCampaign
        fields = [
            'id', 'condominium_id', 'project_id', 'snapshot_id',
            'name', 'description', 'state', 'start_date', 'end_date',
            'settings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConsultationCampaignCreateSerializer(serializers.Serializer):
    project_id = serializers.UUIDField(required=True)
    snapshot_id = serializers.UUIDField(required=True)
    name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    settings = serializers.DictField(required=False, default=dict)


class CampaignParticipantSerializer(serializers.ModelSerializer):
    resident_name = serializers.CharField(source='resident.full_name', read_only=True)
    unit_code = serializers.CharField(source='reference_membership.unit.code', read_only=True)

    class Meta:
        model = CampaignParticipant
        fields = [
            'id', 'condominium_id', 'campaign_id', 'resident_id', 'resident_name',
            'reference_membership_id', 'unit_code', 'status', 'authorized_by_id',
            'authorized_at', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'authorized_at', 'created_at']


class CampaignParticipantCreateSerializer(serializers.Serializer):
    resident_id = serializers.UUIDField(required=True)
    reference_membership_id = serializers.UUIDField(required=True)


class SuggestionCreateSerializer(serializers.Serializer):
    participant_id = serializers.UUIDField(required=True)
    text = serializers.CharField(required=True)
    justification = serializers.CharField(required=True)
    category = serializers.ChoiceField(
        choices=['redacao', 'clareza', 'supressao', 'adicao', 'adequacao_legal', 'geral'],
        default='redacao'
    )
    target_provision_id = serializers.UUIDField(required=False, allow_null=True)
    alternative_text = serializers.CharField(required=False, allow_blank=True)


class SuggestionComplementCreateSerializer(serializers.Serializer):
    participant_id = serializers.UUIDField(required=True)
    text = serializers.CharField(required=True)
    justification = serializers.CharField(required=True)
    category = serializers.ChoiceField(
        choices=['redacao', 'clareza', 'supressao', 'adicao', 'adequacao_legal', 'geral'],
        default='redacao'
    )


class SuggestionUpdateSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    justification = serializers.CharField(required=True)
    alternative_text = serializers.CharField(required=False, allow_blank=True)


class TechnicalAnalysisActionSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=['em_analise', 'concluida'], required=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True)


class EditorialDecisionActionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=['acolhida', 'acolhida_parcial', 'rejeitada', 'duplicada'],
        required=True
    )
    public_shared_reason = serializers.CharField(required=True, min_length=5)
    internal_note = serializers.CharField(required=False, allow_blank=True)


class PublicationAuthorizeActionSerializer(serializers.Serializer):
    sanitized_text = serializers.CharField(required=False, allow_blank=True)
    sanitized_justification = serializers.CharField(required=False, allow_blank=True)


class PublicationHideActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=5)


class IdentityAccessActionSerializer(serializers.Serializer):
    justification = serializers.CharField(required=True, min_length=5)


# ============================================================================
# FASE 6: Concordâncias Consultivas e Consolidação na Minuta
# ============================================================================

class ConsultativeAgreementCreateSerializer(serializers.Serializer):
    participant_id = serializers.UUIDField(required=True)
    published_suggestion_revision_id = serializers.UUIDField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class ConsultativeAgreementSerializer(serializers.ModelSerializer):
    public_protocol = serializers.CharField(
        source='published_suggestion_revision.suggestion.public_protocol',
        read_only=True
    )

    class Meta:
        model = ConsultativeAgreement
        fields = [
            'id', 'condominium_id', 'participant_id', 'published_suggestion_revision_id',
            'public_protocol', 'active', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class AgreementWithdrawSerializer(serializers.Serializer):
    participant_id = serializers.UUIDField(required=True)
    published_suggestion_revision_id = serializers.UUIDField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class SuggestionIncorporationCreateSerializer(serializers.Serializer):
    target_provision_id = serializers.UUIDField(required=True)
    new_text = serializers.CharField(required=True)
    new_label = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class SuggestionIncorporationSerializer(serializers.ModelSerializer):
    public_protocol = serializers.CharField(source='suggestion.public_protocol', read_only=True)

    class Meta:
        model = SuggestionIncorporation
        fields = [
            'id', 'condominium_id', 'suggestion_id', 'public_protocol',
            'provision_revision_id', 'description', 'incorporated_by_id',
            'incorporated_at'
        ]
        read_only_fields = fields


class ConsultationSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationSnapshot
        fields = [
            'id', 'condominium_id', 'campaign_id', 'cut_timestamp',
            'total_eligible_participants', 'total_eligible_units',
            'stats_payload', 'disclaimer', 'created_by_id', 'created_at'
        ]
        read_only_fields = fields


# ============================================================================
# FASE 7: Preservação e Publicação de Conteúdo
# ============================================================================

class ExportArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportArtifact
        fields = [
            'id', 'condominium_id', 'document_id', 'snapshot_id',
            'kind', 'status', 'is_public', 'manifest_hash',
            'files_manifest', 'disclaimer', 'generated_by_id', 'created_at'
        ]
        read_only_fields = fields


class ManifestVerificationSerializer(serializers.Serializer):
    files_content_map = serializers.DictField(
        child=serializers.CharField(trim_whitespace=False, allow_blank=True),
        required=True
    )


class IdentityAccessEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor_account.full_name', read_only=True)
    actor_email = serializers.CharField(source='actor_account.email', read_only=True)

    class Meta:
        model = IdentityAccessEvent
        fields = [
            'id', 'condominium_id', 'actor_account_id', 'actor_name', 'actor_email',
            'target_type', 'target_id', 'purpose', 'created_at'
        ]
        read_only_fields = fields





