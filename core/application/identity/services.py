"""
Serviços de Aplicação de Identidade e Multi-tenancy — CONDC (Fase 1)
Orquestração transacional de casos de uso respeitando isolamento RLS e invariantes.
"""
import uuid
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone

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
)
from domain.identity.invariants import (
    assert_no_electoral_intent,
    assert_same_tenant,
    assert_audit_purpose,
    assert_sindico_publication_authority,
)
from domain.identity.exceptions import (
    DomainError,
    TenantMismatchError,
    InvalidMembershipStatusError,
)

class CondominiumService:
    @staticmethod
    def create_condominium(name: str, cnpj: Optional[str] = None, timezone: str = 'America/Sao_Paulo', **address_kwargs) -> Condominium:
        assert_no_electoral_intent(name)
        return Condominium.objects.create(
            name=name,
            cnpj=cnpj,
            timezone=timezone,
            **address_kwargs
        )

    @staticmethod
    def create_building(condominium_id: uuid.UUID, code: str, name: str, kind: str = 'tower', display_order: int = 0) -> Building:
        return Building.objects.create(
            condominium_id=condominium_id,
            code=code,
            name=name,
            kind=kind,
            display_order=display_order
        )

    @staticmethod
    def create_unit(condominium_id: uuid.UUID, code: str, building_id: Optional[uuid.UUID] = None, ideal_fraction: Optional[float] = None, **kwargs) -> Unit:
        if building_id:
            building = Building.objects.get(id=building_id)
            assert_same_tenant(condominium_id, building.condominium_id, "Prédio/Bloco")

        return Unit.objects.create(
            condominium_id=condominium_id,
            building_id=building_id,
            code=code,
            ideal_fraction=ideal_fraction,
            **kwargs
        )


class ResidentRegistrationService:
    """
    CA-02: Cadastro manual cria registro prévio SEM credencial ou conta automática.
    """
    @staticmethod
    def create_manual_registration(
        condominium_id: uuid.UUID,
        unit_id: uuid.UUID,
        full_name: str,
        relationship: str,
        phone_e164: Optional[str] = None,
        email: Optional[str] = None,
        notes: Optional[str] = None,
        preverified_by: Optional[uuid.UUID] = None,
    ) -> ResidentRegistration:
        unit = unit_id if isinstance(unit_id, Unit) else Unit.objects.get(id=unit_id)
        assert_same_tenant(condominium_id, unit.condominium_id, "Unidade")

        return ResidentRegistration.objects.create(
            condominium_id=condominium_id,
            unit=unit,
            full_name=full_name,
            relationship=relationship,
            phone_e164=phone_e164,
            email=email,
            source='manual',
            status='pendente',
            notes=notes,
            preverified_by_id=preverified_by
        )


class MembershipVerificationService:
    """
    CA-12, CA-15: Validação auditada documental de vínculo.
    Confirmação de e-mail/telefone NÃO valida residência.
    """
    VALID_STATUSES = {'pendente', 'em_analise', 'validado', 'recusado', 'revogado'}

    @classmethod
    @transaction.atomic
    def verify_membership(
        cls,
        condominium_id: uuid.UUID,
        membership_id: uuid.UUID,
        new_status: str,
        method: str,
        reason: str,
        actor_account_id: uuid.UUID
    ) -> UnitMembership:
        if new_status not in cls.VALID_STATUSES:
            raise InvalidMembershipStatusError(f"Status '{new_status}' inválido para verificação de vínculo.")

        membership = UnitMembership.objects.select_for_update().get(id=membership_id)
        assert_same_tenant(condominium_id, membership.condominium_id, "Vínculo de Unidade")

        previous_status = membership.verification_status
        membership.verification_status = new_status
        membership.verification_method = method
        membership.reviewed_by_id = actor_account_id
        membership.reviewed_at = timezone.now()
        membership.review_reason = reason

        if new_status in ('recusado', 'revogado'):
            membership.membership_status = 'ended'
            membership.ended_at = timezone.now()
        elif new_status == 'validado':
            membership.membership_status = 'active'

        membership.save()

        # Criação mandatória do evento imutável de auditoria documental
        MembershipVerificationEvent.objects.create(
            condominium_id=condominium_id,
            membership_id=membership.id,
            previous_status=previous_status,
            new_status=new_status,
            method=method,
            reason=reason,
            actor_account_id=actor_account_id
        )

        return membership


class RoleService:
    @staticmethod
    def assign_role(
        condominium_id: uuid.UUID,
        account_id: uuid.UUID,
        role: str,
        valid_until: Optional[Any] = None
    ) -> RoleAssignment:
        assert_no_electoral_intent(role)
        return RoleAssignment.objects.create(
            condominium_id=condominium_id,
            account_id=account_id,
            role=role.lower(),
            valid_until=valid_until,
            status='active'
        )

    @staticmethod
    def list_roles_for_account(condominium_id: uuid.UUID, account_id: uuid.UUID) -> List[str]:
        now = timezone.now()
        assignments = RoleAssignment.objects.filter(
            condominium_id=condominium_id,
            account_id=account_id,
            status='active'
        )
        active_roles = []
        for a in assignments:
            if a.valid_until is None or a.valid_until > now:
                active_roles.append(a.role)
        return active_roles


class IdentityAuditService:
    """
    CA-33: Toda visualização ou exportação de dados de identificação pessoal exige justificativa e auditoria.
    """
    @staticmethod
    def log_access(
        actor_account_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        purpose: str,
        condominium_id: Optional[uuid.UUID] = None
    ) -> IdentityAccessEvent:
        assert_audit_purpose(purpose)
        return IdentityAccessEvent.objects.create(
            condominium_id=condominium_id,
            actor_account_id=actor_account_id,
            target_type=target_type,
            target_id=target_id,
            purpose=purpose.strip()
        )
