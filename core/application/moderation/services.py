"""
Serviços de Aplicação para Consulta Pública, Sugestões e Moderação Editorial — CONDC (Fase 5)
Implementa os casos de uso para os critérios CA-25 a CA-34, V21-02 a V21-05, V21-26 a V21-28, V21-32, V21-36.
"""
import uuid
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone

from domain.moderation.invariants import (
    generate_suggestion_protocol,
    assert_campaign_allows_suggestions,
    assert_participant_eligible,
    assert_can_publish_suggestion,
    assert_analysis_does_not_auto_publish,
    assert_identity_access_authorized,
    assert_suggestion_not_hidden,
    sanitize_public_suggestion_dto,
    sanitize_author_suggestion_dto,
)
from domain.moderation.exceptions import (
    CampaignNotOpenError,
    ParticipantNotEligibleError,
    UnauthorizedPublicationError,
    AutoPublicationForbiddenError,
    HiddenSuggestionAccessError,
    IdentityAccessWithoutJustificationError,
    PrivateNoteExposureError,
    AttachmentNotApprovedError,
    ComplementWithoutParentError,
)
from infrastructure.models import (
    Condominium,
    Account,
    Resident,
    UnitMembership,
    Project,
    DocumentSnapshot,
    SnapshotItem,
    Provision,
    ProvisionRevision,
    SourceFile,
    ConsultationCampaign,
    CampaignParticipant,
    Suggestion,
    SuggestionRevision,
    PublishedSuggestionRevision,
    SuggestionEditorialDecision,
    IdentityAccessEvent,
    SuggestionAttachment,
)


class CampaignService:
    """Gerencia o ciclo de vida das campanhas de consulta pública vinculadas a snapshots imutáveis."""

    @staticmethod
    def create_campaign(
        condominium_id: uuid.UUID,
        project_id: uuid.UUID,
        snapshot_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> ConsultationCampaign:
        """Cria campanha no estado inicial 'rascunho' vinculada a um snapshot congelado."""
        default_settings = {
            "allow_suggestions": True,
            "allow_complements": True,
            "allow_agreements": True,
            "hide_counts": False
        }
        if settings:
            default_settings.update(settings)

        return ConsultationCampaign.objects.create(
            condominium_id=condominium_id,
            project_id=project_id,
            snapshot_id=snapshot_id,
            name=name.strip(),
            description=description.strip() if description else None,
            state='rascunho',
            settings=default_settings
        )

    @staticmethod
    def open_campaign(campaign_id: uuid.UUID, condominium_id: uuid.UUID) -> ConsultationCampaign:
        """Abre a campanha para consulta e recebimento de sugestões."""
        campaign = ConsultationCampaign.objects.get(id=campaign_id, condominium_id=condominium_id)
        campaign.state = 'aberta'
        campaign.start_date = timezone.now()
        campaign.save(update_fields=['state', 'start_date', 'updated_at'])
        return campaign

    @staticmethod
    def close_campaign(campaign_id: uuid.UUID, condominium_id: uuid.UUID) -> ConsultationCampaign:
        """Encerra a campanha de consulta pública."""
        campaign = ConsultationCampaign.objects.get(id=campaign_id, condominium_id=condominium_id)
        campaign.state = 'encerrada'
        campaign.end_date = timezone.now()
        campaign.save(update_fields=['state', 'end_date', 'updated_at'])
        return campaign

    @staticmethod
    def register_participant(
        condominium_id: uuid.UUID,
        campaign_id: uuid.UUID,
        resident_id: uuid.UUID,
        reference_membership_id: uuid.UUID,
        authorized_by_id: Optional[uuid.UUID] = None
    ) -> CampaignParticipant:
        """Habilita um morador com vínculo validado a participar da campanha."""
        membership = UnitMembership.objects.get(id=reference_membership_id, condominium_id=condominium_id)
        return CampaignParticipant.objects.create(
            condominium_id=condominium_id,
            campaign_id=campaign_id,
            resident_id=resident_id,
            reference_membership=membership,
            status='habilitado',
            authorized_by_id=authorized_by_id,
            authorized_at=timezone.now()
        )

    @staticmethod
    def get_campaign_snapshot_tree(campaign_id: uuid.UUID, condominium_id: uuid.UUID) -> List[Dict[str, Any]]:
        """M05: Reconstrói a árvore de dispositivos normativos do snapshot congelado da campanha."""
        campaign = ConsultationCampaign.objects.get(id=campaign_id, condominium_id=condominium_id)
        items = SnapshotItem.objects.filter(snapshot_id=campaign.snapshot_id).select_related('provision_revision')
        tree = [
            {
                "provision_id": str(it.provision_id),
                "label": it.rendered_label,
                "text": it.provision_revision.text,
                "position": it.position,
                "revision_number": it.provision_revision.revision_number
            }
            for it in items
        ]
        return sorted(tree, key=lambda x: (x['position'], x['label']))


class SuggestionService:
    """Gerencia envio, revisão e consulta de sugestões privadas e públicas (CA-25, CA-29, CA-30, CA-31, CA-34)."""

    @staticmethod
    @transaction.atomic
    def create_suggestion(
        condominium_id: uuid.UUID,
        campaign_id: uuid.UUID,
        participant_id: uuid.UUID,
        text: str,
        justification: str,
        category: str = 'redacao',
        target_provision_id: Optional[uuid.UUID] = None,
        alternative_text: Optional[str] = None,
        author_account_id: Optional[uuid.UUID] = None
    ) -> Suggestion:
        """
        CA-25 / V21-26: Envia sugestão privada com protocolo único e registro da versão consultada.
        Nasce privada ('nao_publicada') e com as 4 dimensões de moderação pendentes.
        """
        campaign = ConsultationCampaign.objects.get(id=campaign_id, condominium_id=condominium_id)
        participant = CampaignParticipant.objects.select_related('reference_membership').get(
            id=participant_id,
            condominium_id=condominium_id
        )

        # Invariantes de abertura de campanha e elegibilidade do participante
        assert_campaign_allows_suggestions(campaign.state, campaign.settings.get('allow_suggestions', True))
        assert_participant_eligible(participant.status, participant.reference_membership.membership_status)

        # Identifica a versão exata consultada do dispositivo no snapshot
        target_snap_rev = None
        if target_provision_id:
            snap_item = SnapshotItem.objects.filter(
                snapshot_id=campaign.snapshot_id,
                provision_id=target_provision_id
            ).first()
            if snap_item:
                target_snap_rev = snap_item.provision_revision

        # Gera protocolo único legível
        current_count = Suggestion.objects.filter(condominium_id=condominium_id).count() + 1
        protocol = generate_suggestion_protocol(current_count)

        suggestion = Suggestion.objects.create(
            public_protocol=protocol,
            condominium_id=condominium_id,
            campaign=campaign,
            participant=participant,
            submitted_membership=participant.reference_membership,
            target_provision_id=target_provision_id,
            target_snapshot_revision=target_snap_rev,
            category=category,
            analysis_status='pendente',
            editorial_decision='pendente',
            publication_status='nao_publicada',
            incorporation_status='nao_incorporada'
        )

        SuggestionRevision.objects.create(
            condominium_id=condominium_id,
            suggestion=suggestion,
            version_number=1,
            text=text.strip(),
            justification=justification.strip(),
            alternative_text=alternative_text.strip() if alternative_text else None,
            author_account_id=author_account_id
        )

        return suggestion

    @staticmethod
    @transaction.atomic
    def create_complement_suggestion(
        condominium_id: uuid.UUID,
        parent_published_suggestion_id: uuid.UUID,
        participant_id: uuid.UUID,
        text: str,
        justification: str,
        category: str = 'redacao',
        author_account_id: Optional[uuid.UUID] = None
    ) -> Suggestion:
        """
        CA-30 / V21-27: Complemento de uma sugestão publicada existente.
        Nasce privado e passa pelo ciclo de moderação de forma independente.
        """
        parent_sug = Suggestion.objects.get(
            id=parent_published_suggestion_id,
            condominium_id=condominium_id
        )
        if parent_sug.publication_status != 'publicada':
            raise ComplementWithoutParentError("Complemento só pode ser submetido sobre sugestão pública autorizada.")

        campaign = parent_sug.campaign
        participant = CampaignParticipant.objects.select_related('reference_membership').get(
            id=participant_id,
            condominium_id=condominium_id
        )

        assert_campaign_allows_suggestions(campaign.state, campaign.settings.get('allow_complements', True))
        assert_participant_eligible(participant.status, participant.reference_membership.membership_status)

        current_count = Suggestion.objects.filter(condominium_id=condominium_id).count() + 1
        protocol = generate_suggestion_protocol(current_count)

        complement = Suggestion.objects.create(
            public_protocol=protocol,
            condominium_id=condominium_id,
            campaign=campaign,
            participant=participant,
            submitted_membership=participant.reference_membership,
            target_provision_id=parent_sug.target_provision_id,
            target_snapshot_revision=parent_sug.target_snapshot_revision,
            category=category,
            analysis_status='pendente',
            editorial_decision='pendente',
            publication_status='nao_publicada',
            incorporation_status='nao_incorporada',
            parent_published_suggestion=parent_sug
        )

        SuggestionRevision.objects.create(
            condominium_id=condominium_id,
            suggestion=complement,
            version_number=1,
            text=text.strip(),
            justification=justification.strip(),
            author_account_id=author_account_id
        )

        return complement

    @staticmethod
    @transaction.atomic
    def update_suggestion(
        suggestion_id: uuid.UUID,
        condominium_id: uuid.UUID,
        author_account_id: Optional[uuid.UUID],
        new_text: str,
        new_justification: str,
        alternative_text: Optional[str] = None
    ) -> SuggestionRevision:
        """
        CA-31 / V21-28: Edição de sugestão cria nova versão numerada (v2, v3).
        Se a sugestão já tiver sido publicada, a nova versão fica pendente de nova moderação/autorização
        sem sobrescrever nem publicar automaticamente.
        """
        suggestion = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
        latest_rev = SuggestionRevision.objects.filter(suggestion=suggestion).order_by('-version_number').first()
        next_ver = (latest_rev.version_number + 1) if latest_rev else 1

        new_rev = SuggestionRevision.objects.create(
            condominium_id=condominium_id,
            suggestion=suggestion,
            version_number=next_ver,
            text=new_text.strip(),
            justification=new_justification.strip(),
            alternative_text=alternative_text.strip() if alternative_text else None,
            author_account_id=author_account_id
        )

        # Se estava publicada, a edição gera estado pendente para a nova versão
        if suggestion.publication_status == 'publicada':
            suggestion.analysis_status = 'pendente'
            suggestion.editorial_decision = 'pendente'
            # A publicação ativa existente é mantida congelada no histórico enquanto a nova está em análise
            suggestion.save(update_fields=['analysis_status', 'editorial_decision', 'updated_at'])

        return new_rev

    @staticmethod
    def list_public_suggestions(
        condominium_id: uuid.UUID,
        campaign_id: uuid.UUID,
        target_provision_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        CA-26 / CA-29 / UI-25: Lista estritamente as sugestões publicadas pelo síndico e não ocultas.
        Retorna DTOs 100% sanitizados sem autoria nem identificadores pessoais.
        """
        query = PublishedSuggestionRevision.objects.filter(
            condominium_id=condominium_id,
            suggestion__campaign_id=campaign_id,
            suggestion__publication_status='publicada',
            is_active_publication=True,
            hidden_at__isnull=True
        ).select_related('suggestion', 'suggestion__target_provision')

        if target_provision_id:
            query = query.filter(suggestion__target_provision_id=target_provision_id)

        results = []
        for pub_rev in query:
            sug = pub_rev.suggestion
            dto = {
                "id": str(sug.id),
                "public_protocol": sug.public_protocol,
                "category": sug.category,
                "sanitized_public_text": pub_rev.sanitized_public_text,
                "sanitized_justification": pub_rev.sanitized_justification,
                "target_provision_id": str(sug.target_provision_id) if sug.target_provision_id else None,
                "target_provision_label": sug.target_provision.kind if sug.target_provision else None,
                "editorial_decision": sug.editorial_decision,
                "created_at": sug.created_at.isoformat(),
                "parent_published_suggestion_id": str(sug.parent_published_suggestion_id) if sug.parent_published_suggestion_id else None
            }
            results.append(sanitize_public_suggestion_dto(dto))

        return results

    @staticmethod
    def get_public_suggestion(condominium_id: uuid.UUID, suggestion_id: uuid.UUID) -> Dict[str, Any]:
        """
        CA-32 / V21-36: Retorna detalhe de sugestão pública.
        Se estiver oculta pelo síndico, bloqueia acesso imediatamente.
        """
        sug = Suggestion.objects.select_related('target_provision').get(
            id=suggestion_id,
            condominium_id=condominium_id
        )
        pub_rev = PublishedSuggestionRevision.objects.filter(
            suggestion=sug,
            is_active_publication=True
        ).first()

        hidden_at = pub_rev.hidden_at if pub_rev else None
        assert_suggestion_not_hidden(hidden_at, sug.publication_status)

        if sug.publication_status != 'publicada' or not pub_rev:
            raise HiddenSuggestionAccessError("Sugestão não possui versão pública autorizada.")

        dto = {
            "id": str(sug.id),
            "public_protocol": sug.public_protocol,
            "category": sug.category,
            "sanitized_public_text": pub_rev.sanitized_public_text,
            "sanitized_justification": pub_rev.sanitized_justification,
            "target_provision_id": str(sug.target_provision_id) if sug.target_provision_id else None,
            "target_provision_label": sug.target_provision.kind if sug.target_provision else None,
            "editorial_decision": sug.editorial_decision,
            "created_at": sug.created_at.isoformat(),
            "parent_published_suggestion_id": str(sug.parent_published_suggestion_id) if sug.parent_published_suggestion_id else None
        }
        return sanitize_public_suggestion_dto(dto)

    @staticmethod
    def list_my_suggestions(condominium_id: uuid.UUID, participant_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        M09 / M10 / V21-32: Lista as sugestões do próprio morador.
        O morador vê seus próprios textos e o status de moderação, mas NUNCA notas internas da gestão.
        """
        suggestions = Suggestion.objects.filter(
            condominium_id=condominium_id,
            participant_id=participant_id
        ).order_by('-created_at')

        results = []
        for sug in suggestions:
            latest_rev = SuggestionRevision.objects.filter(suggestion=sug).order_by('-version_number').first()
            decision = SuggestionEditorialDecision.objects.filter(suggestion=sug).order_by('-decided_at').first()

            dto = {
                "id": str(sug.id),
                "public_protocol": sug.public_protocol,
                "category": sug.category,
                "version_number": latest_rev.version_number if latest_rev else 1,
                "text": latest_rev.text if latest_rev else "",
                "justification": latest_rev.justification if latest_rev else "",
                "analysis_status": sug.analysis_status,
                "editorial_decision": sug.editorial_decision,
                "publication_status": sug.publication_status,
                "public_shared_reason": decision.public_shared_reason if decision else None,
                "created_at": sug.created_at.isoformat(),
                "updated_at": sug.updated_at.isoformat()
            }
            results.append(sanitize_author_suggestion_dto(dto))

        return results

    @staticmethod
    def add_attachment(
        condominium_id: uuid.UUID,
        suggestion_id: uuid.UUID,
        source_file_id: uuid.UUID
    ) -> SuggestionAttachment:
        """CA-34: Registra anexo em sugestão privada. Nasce como não aprovado para publicação pública."""
        suggestion = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
        source_file = SourceFile.objects.get(id=source_file_id, condominium_id=condominium_id)

        return SuggestionAttachment.objects.create(
            condominium_id=condominium_id,
            suggestion=suggestion,
            source_file=source_file,
            is_publicly_approved=False
        )


class ModerationService:
    """Gerencia as 4 dimensões de moderação editorial e mesa de publicação (CA-26, CA-27, CA-28, CA-32, CA-33, CA-34)."""

    @staticmethod
    def list_moderation_queue(
        condominium_id: uuid.UUID,
        campaign_id: Optional[uuid.UUID] = None,
        analysis_status: Optional[str] = None,
        publication_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        S16 / CA-26: Fila de moderação para a comissão e conselho com os 4 indicadores de estado.
        Não expõe a identidade do morador por padrão no payload.
        """
        query = Suggestion.objects.filter(condominium_id=condominium_id).select_related(
            'campaign', 'target_provision'
        ).order_by('-created_at')

        if campaign_id:
            query = query.filter(campaign_id=campaign_id)
        if analysis_status:
            query = query.filter(analysis_status=analysis_status)
        if publication_status:
            query = query.filter(publication_status=publication_status)

        items = []
        for sug in query:
            latest_rev = SuggestionRevision.objects.filter(suggestion=sug).order_by('-version_number').first()
            items.append({
                "id": str(sug.id),
                "public_protocol": sug.public_protocol,
                "campaign_name": sug.campaign.name,
                "category": sug.category,
                "version_number": latest_rev.version_number if latest_rev else 1,
                "text": latest_rev.text if latest_rev else "",
                "justification": latest_rev.justification if latest_rev else "",
                "target_provision_id": str(sug.target_provision_id) if sug.target_provision_id else None,
                "analysis_status": sug.analysis_status,
                "editorial_decision": sug.editorial_decision,
                "publication_status": sug.publication_status,
                "incorporation_status": sug.incorporation_status,
                "created_at": sug.created_at.isoformat()
            })
        return items

    @staticmethod
    @transaction.atomic
    def perform_technical_analysis(
        suggestion_id: uuid.UUID,
        condominium_id: uuid.UUID,
        analyst_account_id: uuid.UUID,
        new_status: str
    ) -> Suggestion:
        """
        S17 / CA-27: Realiza análise técnica da sugestão.
        Garante rigorosamente que a análise NÃO publica a sugestão automaticamente.
        """
        suggestion = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
        assert_analysis_does_not_auto_publish(new_status, suggestion.editorial_decision, suggestion.publication_status)

        suggestion.analysis_status = new_status
        suggestion.save(update_fields=['analysis_status', 'updated_at'])
        return suggestion

    @staticmethod
    @transaction.atomic
    def register_editorial_decision(
        suggestion_id: uuid.UUID,
        condominium_id: uuid.UUID,
        decider_account_id: uuid.UUID,
        decision: str,
        public_shared_reason: str,
        internal_note: Optional[str] = None
    ) -> SuggestionEditorialDecision:
        """
        S17 / CA-27: Registra decisão editorial (acolhida, acolhida_parcial, rejeitada, duplicada).
        Exige resposta compartilhável pública obrigatória.
        Garante que a decisão NÃO publica a sugestão automaticamente.
        """
        suggestion = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
        assert_analysis_does_not_auto_publish(suggestion.analysis_status, decision, suggestion.publication_status)

        dec_record = SuggestionEditorialDecision.objects.create(
            condominium_id=condominium_id,
            suggestion=suggestion,
            decision=decision,
            public_shared_reason=public_shared_reason.strip(),
            internal_note=internal_note.strip() if internal_note else None,
            decided_by_id=decider_account_id
        )

        suggestion.editorial_decision = decision
        suggestion.save(update_fields=['editorial_decision', 'updated_at'])
        return dec_record

    @staticmethod
    @transaction.atomic
    def authorize_publication(
        suggestion_id: uuid.UUID,
        condominium_id: uuid.UUID,
        actor_role: str,
        authorizer_account_id: uuid.UUID,
        sanitized_text: Optional[str] = None,
        sanitized_justification: Optional[str] = None
    ) -> PublishedSuggestionRevision:
        """
        S18 / CA-28 / V21-03 / V21-04:
        Mesa de publicação do síndico.
        Apenas o síndico ativo com mandato pode autorizar a publicação pública da versão sanitizada.
        Administradores sem papel de síndico são recusados com UnauthorizedPublicationError.
        """
        assert_can_publish_suggestion(actor_role)

        suggestion = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
        latest_rev = SuggestionRevision.objects.filter(suggestion=suggestion).order_by('-version_number').first()

        pub_text = sanitized_text.strip() if sanitized_text else latest_rev.text
        pub_just = sanitized_justification.strip() if sanitized_justification else latest_rev.justification

        # Desativa publicações anteriores da mesma sugestão se houver
        PublishedSuggestionRevision.objects.filter(
            suggestion=suggestion,
            is_active_publication=True
        ).update(is_active_publication=False)

        pub_rev = PublishedSuggestionRevision.objects.create(
            condominium_id=condominium_id,
            suggestion=suggestion,
            suggestion_revision=latest_rev,
            sanitized_public_text=pub_text,
            sanitized_justification=pub_just,
            authorized_by_id=authorizer_account_id,
            authorized_at=timezone.now(),
            is_active_publication=True
        )

        suggestion.publication_status = 'publicada'
        suggestion.save(update_fields=['publication_status', 'updated_at'])

        return pub_rev

    @staticmethod
    @transaction.atomic
    def hide_published_suggestion(
        suggestion_id: uuid.UUID,
        condominium_id: uuid.UUID,
        actor_role: str,
        actor_account_id: uuid.UUID,
        reason: str
    ) -> PublishedSuggestionRevision:
        """
        CA-32 / V21-36: Ocultação da publicação pelo síndico.
        Bloqueia a sugestão imediatamente de listagens, links diretos, buscas e interações.
        """
        assert_can_publish_suggestion(actor_role)

        suggestion = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
        pub_rev = PublishedSuggestionRevision.objects.filter(
            suggestion=suggestion,
            is_active_publication=True
        ).first()

        if pub_rev:
            pub_rev.hidden_at = timezone.now()
            pub_rev.hidden_by_id = actor_account_id
            pub_rev.hide_reason = reason.strip()
            pub_rev.is_active_publication = False
            pub_rev.save(update_fields=['hidden_at', 'hidden_by_id', 'hide_reason', 'is_active_publication'])

        suggestion.publication_status = 'oculta'
        suggestion.save(update_fields=['publication_status', 'updated_at'])

        return pub_rev

    @staticmethod
    @transaction.atomic
    def access_suggestion_identity(
        suggestion_id: uuid.UUID,
        condominium_id: uuid.UUID,
        actor_role: str,
        actor_account_id: uuid.UUID,
        justification: str
    ) -> Dict[str, Any]:
        """
        CA-33 / V21-33: Consulta justificada e auditada de dados de autoria/identidade da sugestão.
        Exige papel de gestão ('sindico' ou 'admin') e justificativa fundamentada de pelo menos 5 caracteres.
        Registra evento em app.identity_access_events.
        """
        assert_identity_access_authorized(actor_role, justification)

        suggestion = Suggestion.objects.select_related(
            'participant', 'participant__resident', 'participant__resident__account',
            'participant__reference_membership', 'participant__reference_membership__unit'
        ).get(id=suggestion_id, condominium_id=condominium_id)

        resident = suggestion.participant.resident
        membership = suggestion.participant.reference_membership

        # Registra auditoria obrigatória
        IdentityAccessEvent.objects.create(
            condominium_id=condominium_id,
            actor_account_id=actor_account_id,
            target_type='suggestion_author',
            target_id=suggestion.id,
            purpose=justification.strip()
        )

        return {
            "suggestion_id": str(suggestion.id),
            "public_protocol": suggestion.public_protocol,
            "resident_id": str(resident.id),
            "full_name": resident.full_name,
            "email": resident.account.email if resident.account else None,
            "phone_e164": resident.phone_e164,
            "unit_id": str(membership.unit_id),
            "unit_code": membership.unit.code
        }

    @staticmethod
    def approve_attachment_publication(
        attachment_id: uuid.UUID,
        condominium_id: uuid.UUID,
        actor_role: str,
        actor_account_id: uuid.UUID
    ) -> SuggestionAttachment:
        """CA-34: Autorização explícita do síndico para tornar público anexo de sugestão."""
        assert_can_publish_suggestion(actor_role)

        attachment = SuggestionAttachment.objects.get(id=attachment_id, condominium_id=condominium_id)
        attachment.is_publicly_approved = True
        attachment.approved_by_id = actor_account_id
        attachment.save(update_fields=['is_publicly_approved', 'approved_by_id'])
        return attachment
