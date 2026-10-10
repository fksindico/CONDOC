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
    ImportBatch,
    ImportRow,
    AccessInvitation,
    InvitationRedemption,
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

    class Meta:
        model = UnitMembership
        fields = [
            'id', 'condominium_id', 'resident_id', 'resident_name',
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
