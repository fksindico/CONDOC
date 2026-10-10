"""
Serializers REST API v1 — CONDC (Fase 1: Identidade e Multi-tenancy)
Compatíveis com os contratos definidos em packages/api-contracts
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
)

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
