"""
Serviços de Aplicação para Convites de Acesso — CONDC (Fase 2)
Implementa criação segura com tokens SHA-256, inspeção sem efeitos colaterais,
resgate controlado com diferenciação entre individual pré-conferido e compartilhado,
e revogação que bloqueia novos resgates sem apagar contas ativadas.
Critérios atendidos: CA-07 a CA-11, CA-43; V21-19 a V21-24; ADR-003, ADR-004.
"""
import secrets
import uuid
from typing import Optional, Tuple, Dict, Any
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
    AccessInvitation,
    InvitationRedemption,
    DeliveryAttempt,
)
from domain.identity.invariants import assert_same_tenant
from domain.invitations.invariants import (
    hash_invitation_token,
    assert_invitation_active,
    assert_expected_contact_match,
)
from domain.invitations.exceptions import (
    InvitationExpiredOrExhaustedError,
    InvitationRevokedError,
    InvalidExpectedContactError,
    InvitationRedemptionForbiddenError,
)

class InvitationService:
    @classmethod
    def create_invitation(
        cls,
        condominium_id: uuid.UUID,
        kind: str,
        created_by_id: uuid.UUID,
        expires_at,
        target_registration_id: Optional[uuid.UUID] = None,
        target_unit_id: Optional[uuid.UUID] = None,
        target_building_id: Optional[uuid.UUID] = None,
        expected_contact: Optional[str] = None,
        max_redemptions: int = 1,
        campaign_id: Optional[uuid.UUID] = None
    ) -> Tuple[AccessInvitation, str]:
        """
        Criação de convite com token criptográfico opaco.
        O token em texto claro é retornado apenas no momento da criação.
        No banco persiste-se estritamente o hash SHA-256 (token_hash).
        """
        # Validação de tenant
        condo = Condominium.objects.get(id=condominium_id)

        # Gera token criptográfico opaco (32 bytes urlsafe = 43 caracteres seguros)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_invitation_token(raw_token)

        # Se for individual vinculado a pré-cadastro, preenche unidade e contato esperado se ausente
        if target_registration_id:
            reg = ResidentRegistration.objects.get(id=target_registration_id)
            assert_same_tenant(condominium_id, reg.condominium_id, "Pré-cadastro")
            if not target_unit_id:
                target_unit_id = reg.unit_id
            if not expected_contact:
                expected_contact = reg.email or reg.phone_e164

        if target_unit_id:
            unit = Unit.objects.get(id=target_unit_id)
            assert_same_tenant(condominium_id, unit.condominium_id, "Unidade")

        invitation = AccessInvitation.objects.create(
            condominium_id=condominium_id,
            campaign_id=campaign_id,
            kind=kind,
            target_registration_id=target_registration_id,
            target_unit_id=target_unit_id,
            target_building_id=target_building_id,
            expected_contact=expected_contact,
            token_hash=token_hash,
            expires_at=expires_at,
            max_redemptions=max_redemptions,
            redemption_count=0,
            status='ativo',
            created_by_id=created_by_id
        )

        return invitation, raw_token

    @classmethod
    def inspect_invitation(cls, raw_token: str) -> Dict[str, Any]:
        """
        CA-10, V21-19: GET no convite NUNCA consome nem autentica.
        UI-11: Link não revela dados internos de moradores ou contatos antes da verificação.
        Retorna apenas informações essenciais e sanitizadas sobre o condomínio e a validade.
        """
        token_hash = hash_invitation_token(raw_token)
        try:
            invitation = AccessInvitation.objects.select_related('condominium', 'target_unit').get(token_hash=token_hash)
        except AccessInvitation.DoesNotExist:
            return {
                "valid": False,
                "error": "Convite não encontrado ou inválido."
            }

        now = timezone.now()
        is_active = (
            invitation.status == 'ativo' and
            now < invitation.expires_at and
            invitation.redemption_count < invitation.max_redemptions
        )

        unit_label = None
        if invitation.target_unit:
            unit_label = invitation.target_unit.code

        return {
            "valid": is_active,
            "status": invitation.status,
            "kind": invitation.kind,
            "condominium_id": str(invitation.condominium.id),
            "condominium_name": invitation.condominium.name,
            "unit_label": unit_label,
            "expires_at": invitation.expires_at.isoformat(),
            "requires_contact_confirmation": (invitation.kind == 'individual_preconferido')
        }

    @classmethod
    @transaction.atomic
    def redeem_invitation(
        cls,
        raw_token: str,
        account_id: uuid.UUID,
        provided_contact: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resgate controlado do convite (POST com transação atômica).
        CA-07: Mantém contas individuais mesmo para convite de unidade fixa.
        CA-08, V21-20: Convite compartilhado/amplo exige conferência e cria vínculo 'pendente'.
        CA-09, V21-22: Individual pré-conferido exige contato previsto confirmado.
        CA-15, V21-21: Contato por si só não valida residência.
        """
        token_hash = hash_invitation_token(raw_token)

        try:
            invitation = AccessInvitation.objects.select_for_update().select_related(
                'condominium', 'target_unit', 'target_registration'
            ).get(token_hash=token_hash)
        except AccessInvitation.DoesNotExist:
            raise InvitationRedemptionForbiddenError("Convite não encontrado.")

        # Validações de integridade do estado do convite
        assert_invitation_active(
            status=invitation.status,
            expires_at=invitation.expires_at,
            redemption_count=invitation.redemption_count,
            max_redemptions=invitation.max_redemptions
        )

        # CA-09, V21-22: Se individual pré-conferido, valida contato
        if invitation.kind == 'individual_preconferido':
            assert_expected_contact_match(invitation.expected_contact, provided_contact)

        account = Account.objects.get(id=account_id)
        condominium = invitation.condominium

        # 1. Busca ou cria o perfil de Resident no condomínio para esta conta
        resident, _ = Resident.objects.get_or_create(
            condominium=condominium,
            account=account,
            defaults={"full_name": account.full_name}
        )

        # 2. Determina a unidade associada ao convite
        target_unit = invitation.target_unit
        if not target_unit and invitation.target_registration:
            target_unit = invitation.target_registration.unit

        membership = None
        if target_unit:
            # CA-08, V21-20, CA-15:
            # Individual pré-conferido com contato conferido pode nascer 'validado'.
            # Convites compartilhados (unidade_fixa, torre_bloco, amplo) nascem 'pendente'.
            if invitation.kind == 'individual_preconferido':
                verification_status = 'validado'
                verification_method = 'individual_preconferido'
                membership_status = 'active'
            else:
                verification_status = 'pendente'
                verification_method = 'autodeclarado_convite'
                membership_status = 'active'

            membership = UnitMembership.objects.create(
                condominium=condominium,
                resident=resident,
                unit=target_unit,
                category=invitation.target_registration.relationship if invitation.target_registration else 'proprietario_residente',
                verification_status=verification_status,
                membership_status=membership_status,
                verification_method=verification_method,
                reviewed_by_id=invitation.created_by_id if verification_status == 'validado' else None,
                reviewed_at=timezone.now() if verification_status == 'validado' else None,
                review_reason="Resgate de convite individual pré-conferido com contato validado" if verification_status == 'validado' else None
            )

            # Se nasceu validado, registra o evento imutável de verificação
            if verification_status == 'validado':
                MembershipVerificationEvent.objects.create(
                    condominium=condominium,
                    membership=membership,
                    previous_status='pendente',
                    new_status='validado',
                    method=verification_method,
                    reason="Resgate de convite individual pré-conferido com contato conferido.",
                    actor_account_id=invitation.created_by_id
                )

        # 3. Incrementa contador de resgates e atualiza status
        invitation.redemption_count += 1
        if invitation.redemption_count >= invitation.max_redemptions:
            invitation.status = 'esgotado'
        invitation.save(update_fields=['redemption_count', 'status', 'updated_at'])

        # 4. Registra histórico imutável de resgate
        redemption = InvitationRedemption.objects.create(
            invitation=invitation,
            account=account,
            resident=resident,
            membership=membership,
            idempotency_key=idempotency_key,
            ip_address_masked=ip_address,
            user_agent=user_agent
        )

        return {
            "redemption_id": str(redemption.id),
            "condominium_id": str(condominium.id),
            "resident_id": str(resident.id),
            "membership_id": str(membership.id) if membership else None,
            "verification_status": membership.verification_status if membership else None,
            "kind": invitation.kind,
            "status": "resgatado"
        }

    @classmethod
    @transaction.atomic
    def revoke_invitation(
        cls,
        condominium_id: uuid.UUID,
        invitation_id: uuid.UUID,
        actor_id: uuid.UUID,
        reason: str
    ) -> AccessInvitation:
        """
        CA-11, V21-23, V21-24: Revogar convite impede novos resgates.
        NÃO suspende nem apaga perfis ou contas de moradores já ativadas por resgates anteriores.
        """
        invitation = AccessInvitation.objects.select_for_update().get(
            id=invitation_id,
            condominium_id=condominium_id
        )

        invitation.status = 'revogado'
        invitation.revoked_at = timezone.now()
        invitation.revoked_by_id = actor_id
        invitation.revoke_reason = reason.strip()
        invitation.save(update_fields=['status', 'revoked_at', 'revoked_by', 'revoke_reason', 'updated_at'])

        return invitation
