"""
Exceções de Domínio para Campanhas de Consulta Pública, Sugestões e Moderação — CONDC (Fase 5)
PRD Mestre v3.0 (Critérios CA-25 a CA-34, V21-02 a V21-05, V21-26 a V21-28, V21-32, V21-36)
"""

class ModerationDomainError(Exception):
    """Exceção base para o domínio de moderação e consulta pública."""
    pass


class CampaignNotOpenError(ModerationDomainError):
    """Lançada quando se tenta interagir ou sugerir em campanha que não está aberta (CA-25, UI-15)."""
    pass


class ParticipantNotEligibleError(ModerationDomainError):
    """Lançada quando morador tenta interagir sem vínculo ativo/habilitado na campanha (V21-25, V21-39)."""
    pass


class UnauthorizedPublicationError(ModerationDomainError):
    """CA-28 / V21-03 / V21-04: Lançada quando ator sem papel de síndico ativo tenta autorizar publicação."""
    pass


class AutoPublicationForbiddenError(ModerationDomainError):
    """CA-27: Lançada se houver tentativa de publicação automática por mera análise técnica ou decisão editorial."""
    pass


class HiddenSuggestionAccessError(ModerationDomainError):
    """CA-32 / V21-36: Lançada quando se tenta acessar ou interagir com sugestão ocultada pelo síndico."""
    pass


class IdentityAccessWithoutJustificationError(ModerationDomainError):
    """CA-33 / V21-33: Lançada quando se tenta acessar dados de autoria/identidade sem justificativa obrigatória."""
    pass


class PrivateNoteExposureError(ModerationDomainError):
    """CA-24 / V21-32: Lançada se notas internas confidenciais forem expostas ao autor ou ao público."""
    pass


class AttachmentNotApprovedError(ModerationDomainError):
    """CA-34: Lançada quando anexo privado é acessado como público sem autorização específica."""
    pass


class ComplementWithoutParentError(ModerationDomainError):
    """CA-30: Lançada se um complemento tentar se vincular a sugestão inexistente ou inválida."""
    pass
