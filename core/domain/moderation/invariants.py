"""
Invariantes de Domínio para Campanhas de Consulta Pública e Moderação Editorial — CONDC (Fase 5)
PRD Mestre v3.0 (Critérios CA-25 a CA-34, V21-02 a V21-05, V21-26 a V21-28, V21-32, V21-36)
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from .exceptions import (
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


def generate_suggestion_protocol(counter: int, year: int = 2026) -> str:
    """CA-25: Gera protocolo legível único para a sugestão privada (ex: SUG-2026-000001)."""
    return f"SUG-{year}-{counter:06d}"


def assert_campaign_allows_suggestions(state: str, allow_suggestions: bool = True) -> None:
    """Valida se a campanha de consulta pública está aberta para receber novas sugestões."""
    if state != 'aberta':
        raise CampaignNotOpenError(
            f"Campanha não aceita novas sugestões no momento (estado atual: {state})."
        )
    if not allow_suggestions:
        raise CampaignNotOpenError("Envio de sugestões temporariamente desativado nas configurações da campanha.")


def assert_participant_eligible(participant_status: str, membership_status: str = 'active') -> None:
    """Valida se o morador participante possui habilitação ativa na campanha (V21-25, V21-39)."""
    if participant_status != 'habilitado':
        raise ParticipantNotEligibleError(
            f"Participante não está habilitado para interagir nesta campanha (status: {participant_status})."
        )
    if membership_status != 'active':
        raise ParticipantNotEligibleError("Vínculo do morador com a unidade não está ativo.")


def assert_can_publish_suggestion(actor_role: str) -> None:
    """
    CA-28 / V21-03 / V21-04:
    Apenas o síndico ativo possui autoridade para autorizar a publicação pública de uma sugestão sanitizada.
    Administrador sem papel de síndico, membros do conselho, comissão ou jurídico não podem publicar.
    """
    if actor_role != 'sindico':
        raise UnauthorizedPublicationError(
            f"Autorização de publicação pública é prerrogativa pessoal e exclusiva do síndico ativo. "
            f"Papel atual: '{actor_role}'."
        )


def assert_analysis_does_not_auto_publish(
    analysis_status: str,
    editorial_decision: str,
    intended_publication_status: str
) -> None:
    """
    CA-27: Conclusão de análise técnica ou acolhimento editorial não publicam automaticamente.
    A publicação exige autorização separada do síndico na mesa de publicação.
    """
    if intended_publication_status == 'publicada' and editorial_decision in ('acolhida', 'acolhida_parcial'):
        # Não pode publicar sem autorização expressa
        raise AutoPublicationForbiddenError(
            "Análise técnica ou acolhimento editorial não publicam sugestão automaticamente. "
            "Exige autorização prévia do síndico ativo na mesa de publicação."
        )


def assert_identity_access_authorized(user_role: str, justification: Optional[str]) -> None:
    """
    CA-33 / V21-33:
    Visualizar a identidade do autor de uma sugestão exige papel de gestão autorizado
    e justificativa fundamentada de pelo menos 5 caracteres, registrando auditoria.
    """
    if user_role not in ('sindico', 'admin'):
        raise IdentityAccessWithoutJustificationError(
            f"Papel '{user_role}' não possui permissão para consultar dados de identidade de moradores."
        )
    if not justification or len(justification.strip()) < 5:
        raise IdentityAccessWithoutJustificationError(
            "Justificativa fundamentada é obrigatória para acessar dados de autoria/identidade (mínimo 5 caracteres)."
        )


def assert_suggestion_not_hidden(hidden_at: Optional[Any], publication_status: str) -> None:
    """
    CA-32 / V21-36:
    Ocultação de sugestão pelo síndico bloqueia imediatamente em todas as superfícies
    (API pública, link direto, buscas, listagens e novas interações).
    """
    if hidden_at is not None or publication_status == 'oculta':
        raise HiddenSuggestionAccessError("Sugestão oculta pela administração do condomínio.")


def sanitize_public_suggestion_dto(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    CA-26 / UI-25 / V21-02:
    Sanitiza payload para visualização pública e da comissão/conselho:
    Remove estritamente autoria (nome, email, telefone, unidade) e notas internas restritas.
    """
    allowed_keys = {
        'id', 'public_protocol', 'category', 'sanitized_public_text',
        'sanitized_justification', 'public_shared_reason', 'target_provision_id',
        'target_provision_label', 'editorial_decision', 'created_at', 'parent_published_suggestion_id'
    }
    return {k: v for k, v in data.items() if k in allowed_keys}


def sanitize_author_suggestion_dto(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    CA-24 / V21-32:
    Retorna dados da sugestão para o próprio autor (M09 / M10):
    Permite ver seu protocolo, texto, status de análise, publicação e justificativa pública,
    mas NUNCA notas internas da equipe.
    """
    # Remove qualquer nota interna se presente
    clean = dict(data)
    clean.pop('internal_note', None)
    clean.pop('internal_notes', None)
    return clean
