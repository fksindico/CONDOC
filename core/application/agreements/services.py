"""
Serviços de Aplicação para Concordâncias Consultivas e Consolidação na Minuta — CONDC (Fase 6)
Implementa os casos de uso para os critérios CA-35 a CA-40, CA-45, V21-29 a V21-31, V21-34, V21-37.
"""
import uuid
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone

from domain.agreements.invariants import (
    DISCLAIMER_CONSULTATIVE_AGREEMENT,
    assert_campaign_allows_agreements,
    assert_author_cannot_agree_with_own_suggestion,
    assert_no_electoral_terms,
    calculate_agreement_metrics,
    sanitize_public_metrics_payload,
)
from domain.agreements.exceptions import (
    CampaignClosedForAgreementsError,
    AuthorCannotAgreeWithOwnSuggestionError,
    ElectoralVocabularyForbiddenError,
    SubstantialChangeAgreementTransferForbiddenError,
    IncorporationIntegrityError,
)
from domain.moderation.invariants import assert_participant_eligible
from domain.documents.invariants import calculate_revision_etag
from infrastructure.models import (
    Condominium,
    Account,
    Resident,
    UnitMembership,
    Provision,
    ProvisionRevision,
    ConsultationCampaign,
    CampaignParticipant,
    Suggestion,
    SuggestionRevision,
    PublishedSuggestionRevision,
    ConsultativeAgreement,
    AgreementEvent,
    SuggestionIncorporation,
    ConsultationSnapshot,
)


class AgreementService:
    """Gerencia manifestações consultivas de concordância, retiradas e métricas por pessoa/unidade."""

    @staticmethod
    @transaction.atomic
    def register_agreement(
        condominium_id: uuid.UUID,
        campaign_id: uuid.UUID,
        participant_id: uuid.UUID,
        published_suggestion_revision_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> ConsultativeAgreement:
        """
        CA-35: Registra manifestação de concordância consultiva sobre versão exata publicada.
        Cliques repetidos produzem exatamente 1 concordância ativa (idempotência).
        """
        campaign = ConsultationCampaign.objects.get(id=campaign_id, condominium_id=condominium_id)
        participant = CampaignParticipant.objects.select_related(
            'resident', 'resident__account', 'reference_membership'
        ).get(id=participant_id, condominium_id=condominium_id)

        pub_rev = PublishedSuggestionRevision.objects.select_related(
            'suggestion', 'suggestion_revision'
        ).get(id=published_suggestion_revision_id, condominium_id=condominium_id)

        # Invariantes de campanha e elegibilidade
        assert_campaign_allows_agreements(campaign.state, campaign.settings.get('allow_agreements', True))
        assert_participant_eligible(participant.status, participant.reference_membership.membership_status)

        # PRD 257: Autor não acrescenta concordância à própria contribuição
        author_acc_id = pub_rev.suggestion_revision.author_account_id
        participant_acc_id = participant.resident.account_id if participant.resident else None
        assert_author_cannot_agree_with_own_suggestion(author_acc_id, participant_acc_id)

        agreement = ConsultativeAgreement.objects.filter(
            participant=participant,
            published_suggestion_revision=pub_rev
        ).first()

        if agreement:
            if agreement.active:
                # CA-35: Já ativo -> cliques repetidos não duplicam nada
                return agreement

            # Estava inativo (retirado) -> reativa e registra evento
            agreement.active = True
            agreement.membership_at_action = participant.reference_membership
            agreement.save(update_fields=['active', 'membership_at_action', 'updated_at'])

            AgreementEvent.objects.create(
                condominium_id=condominium_id,
                agreement=agreement,
                action='reaffirm',
                reason=reason.strip() if reason else None
            )
            return agreement

        # Novo registro de concordância
        agreement = ConsultativeAgreement.objects.create(
            condominium_id=condominium_id,
            participant=participant,
            published_suggestion_revision=pub_rev,
            membership_at_action=participant.reference_membership,
            active=True
        )

        AgreementEvent.objects.create(
            condominium_id=condominium_id,
            agreement=agreement,
            action='agree',
            reason=reason.strip() if reason else None
        )

        return agreement

    @staticmethod
    @transaction.atomic
    def withdraw_agreement(
        condominium_id: uuid.UUID,
        campaign_id: Optional[uuid.UUID] = None,
        participant_id: Optional[uuid.UUID] = None,
        published_suggestion_revision_id: Optional[uuid.UUID] = None,
        reason: Optional[str] = None,
        agreement_id: Optional[uuid.UUID] = None,
    ) -> ConsultativeAgreement:
        """
        CA-36: Retirada de concordância consultiva.
        Atualiza active=False e preserva o evento histórico imutável em AgreementEvent.
        """
        if agreement_id:
            agreement = ConsultativeAgreement.objects.get(id=agreement_id, condominium_id=condominium_id)
        else:
            campaign = ConsultationCampaign.objects.get(id=campaign_id, condominium_id=condominium_id)
            assert_campaign_allows_agreements(campaign.state, campaign.settings.get('allow_agreements', True))

            agreement = ConsultativeAgreement.objects.get(
                condominium_id=condominium_id,
                participant_id=participant_id,
                published_suggestion_revision_id=published_suggestion_revision_id
            )

        if not agreement.active:
            # Já retirado
            return agreement

        agreement.active = False
        agreement.save(update_fields=['active', 'updated_at'])

        AgreementEvent.objects.create(
            condominium_id=condominium_id,
            agreement=agreement,
            action='withdraw',
            reason=reason.strip() if reason else None
        )

        return agreement

    @staticmethod
    def get_revision_agreement_stats(
        condominium_id: uuid.UUID,
        published_suggestion_revision_id: uuid.UUID,
        is_public_viewer: bool = False
    ) -> Dict[str, Any]:
        """
        CA-38 / CA-39 / V21-30 / V21-34 / UI-31 / S19:
        Calcula métricas com segregação estrita:
        1. Indivíduos concordantes (pessoas únicas).
        2. Unidades com ao menos uma concordância (unidades únicas).
        Se is_public_viewer=True e hide_counts=True, suprime contagens do payload (CA-38).
        """
        pub_rev = PublishedSuggestionRevision.objects.select_related(
            'suggestion', 'suggestion__campaign'
        ).get(id=published_suggestion_revision_id, condominium_id=condominium_id)

        campaign = pub_rev.suggestion.campaign

        # Coleta acordos ativos
        active_agrs = ConsultativeAgreement.objects.filter(
            condominium_id=condominium_id,
            published_suggestion_revision=pub_rev,
            active=True
        ).select_related('participant', 'membership_at_action')

        agreements_payload = [
            {
                "resident_id": str(a.participant.resident_id),
                "unit_id": str(a.membership_at_action.unit_id),
                "active": a.active
            }
            for a in active_agrs
        ]

        # Denominadores de elegibilidade na campanha
        total_eligible_residents = CampaignParticipant.objects.filter(
            campaign=campaign,
            status='habilitado'
        ).values('resident_id').distinct().count()

        total_eligible_units = CampaignParticipant.objects.filter(
            campaign=campaign,
            status='habilitado'
        ).values('reference_membership__unit_id').distinct().count()

        stats = calculate_agreement_metrics(
            active_agreements=agreements_payload,
            total_eligible_residents=total_eligible_residents,
            total_eligible_units=total_eligible_units
        )

        hide_counts = campaign.settings.get('hide_counts', False)
        if is_public_viewer:
            return sanitize_public_metrics_payload(stats, hide_counts=hide_counts)

        return stats

    @staticmethod
    @transaction.atomic
    def create_consultation_snapshot(
        condominium_id: uuid.UUID,
        campaign_id: uuid.UUID,
        created_by_id: Optional[uuid.UUID] = None
    ) -> ConsultationSnapshot:
        """CA-39: Fotografia estatística substitutiva e imutável da campanha."""
        campaign = ConsultationCampaign.objects.get(id=campaign_id, condominium_id=condominium_id)

        # Denominadores
        total_eligible_residents = CampaignParticipant.objects.filter(
            campaign=campaign,
            status='habilitado'
        ).values('resident_id').distinct().count()

        total_eligible_units = CampaignParticipant.objects.filter(
            campaign=campaign,
            status='habilitado'
        ).values('reference_membership__unit_id').distinct().count()

        # Coleta estatísticas de todas as sugestões publicadas da campanha
        pub_revs = PublishedSuggestionRevision.objects.filter(
            condominium_id=condominium_id,
            suggestion__campaign=campaign,
            is_active_publication=True
        )

        stats_by_suggestion = {}
        for pr in pub_revs:
            s = AgreementService.get_revision_agreement_stats(condominium_id, pr.id, is_public_viewer=False)
            stats_by_suggestion[str(pr.suggestion_id)] = s

        snapshot_record = ConsultationSnapshot.objects.create(
            condominium_id=condominium_id,
            campaign=campaign,
            cut_timestamp=timezone.now(),
            total_eligible_participants=total_eligible_residents,
            total_eligible_units=total_eligible_units,
            stats_payload=stats_by_suggestion,
            disclaimer=DISCLAIMER_CONSULTATIVE_AGREEMENT,
            created_by_id=created_by_id
        )
        return snapshot_record

    @staticmethod
    def list_my_agreements(condominium_id: uuid.UUID, participant_id: uuid.UUID) -> List[Dict[str, Any]]:
        """M11: Lista as concordâncias ativas registradas pelo participante."""
        agrs = ConsultativeAgreement.objects.filter(
            condominium_id=condominium_id,
            participant_id=participant_id,
            active=True
        ).select_related('published_suggestion_revision', 'published_suggestion_revision__suggestion')

        return [
            {
                "agreement_id": str(a.id),
                "published_suggestion_revision_id": str(a.published_suggestion_revision_id),
                "public_protocol": a.published_suggestion_revision.suggestion.public_protocol,
                "sanitized_public_text": a.published_suggestion_revision.sanitized_public_text,
                "active": a.active,
                "created_at": a.created_at.isoformat()
            }
            for a in agrs
        ]


class IncorporationService:
    """Gerencia a consolidação atômica de sugestões acolhidas na minuta normativa (CA-40, V21-37)."""

    @staticmethod
    @transaction.atomic
    def incorporate_suggestion(
        condominium_id: uuid.UUID,
        suggestion_id: uuid.UUID,
        target_provision_id: uuid.UUID,
        incorporated_by_id: uuid.UUID,
        new_text: str,
        description: Optional[str] = None,
        new_label: Optional[str] = None
    ) -> SuggestionIncorporation:
        """
        CA-40 / V21-37 / S17 / S18:
        Transação atômica que consolida a sugestão acolhida na minuta de trabalho:
        - Valida que a sugestão teve decisão editorial de acolhimento.
        - Cria nova revisão do dispositivo normativo (`ProvisionRevision`).
        - Atualiza a sugestão para `incorporation_status = 'incorporada'`.
        - Registra o vínculo formal em `SuggestionIncorporation`.
        Se qualquer passo falhar, reverte toda a transação.
        """
        suggestion = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
        if suggestion.editorial_decision not in ('acolhida', 'acolhida_parcial'):
            raise IncorporationIntegrityError(
                f"Sugestão não possui decisão editorial de acolhimento (decisão atual: '{suggestion.editorial_decision}'). "
                f"Apenas sugestões acolhidas podem ser incorporadas à minuta."
            )

        provision = Provision.objects.get(id=target_provision_id, condominium_id=condominium_id)
        latest_rev = ProvisionRevision.objects.filter(
            condominium_id=condominium_id,
            provision=provision
        ).order_by('-revision_number').first()

        if not latest_rev:
            raise IncorporationIntegrityError("Dispositivo normativo de destino não possui revisões válidas.")

        new_rev_number = latest_rev.revision_number + 1
        label = new_label.strip() if new_label else latest_rev.label
        text = new_text.strip()

        etag = calculate_revision_etag(
            provision_id=provision.id,
            revision_number=new_rev_number,
            text=text,
            label=label,
            parent_provision_id=latest_rev.parent_provision_id
        )

        new_rev = ProvisionRevision.objects.create(
            provision_id=provision.id,
            document_id=latest_rev.document_id,
            condominium_id=condominium_id,
            revision_number=new_rev_number,
            parent_provision_id=latest_rev.parent_provision_id,
            position=latest_rev.position,
            label=label,
            text=text,
            theme=latest_rev.theme,
            change_type='alterado',
            status='draft',
            author_account_id=incorporated_by_id,
            etag=etag
        )

        suggestion.incorporation_status = 'incorporada'
        suggestion.save(update_fields=['incorporation_status', 'updated_at'])

        incorporation = SuggestionIncorporation.objects.create(
            condominium_id=condominium_id,
            suggestion=suggestion,
            provision_revision=new_rev,
            description=description.strip() if description else f"Incorporação da contribuição {suggestion.public_protocol}.",
            incorporated_by_id=incorporated_by_id
        )

        return incorporation
