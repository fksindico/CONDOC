"""
Exceções de Domínio para Concordâncias Consultivas e Consolidação — CONDC (Fase 6)
PRD Mestre v3.0 (Critérios CA-35 a CA-40, CA-45, V21-29 a V21-31, V21-34, V21-37)
"""

class AgreementDomainError(Exception):
    """Exceção base para concordâncias consultivas e consolidação."""
    pass


class CampaignClosedForAgreementsError(AgreementDomainError):
    """Lançada quando a campanha não está aberta para manifestações consultivas (UI-15)."""
    pass


class AuthorCannotAgreeWithOwnSuggestionError(AgreementDomainError):
    """PRD 257: Autor não pode acrescentar concordância à própria contribuição."""
    pass


class ElectoralVocabularyForbiddenError(AgreementDomainError):
    """CA-45: Proibição terminante de termos eleitorais, quórum de assembleia ou votação."""
    pass


class SubstantialChangeAgreementTransferForbiddenError(AgreementDomainError):
    """CA-37 / V21-29: Proibição de transferir apoios de versão anterior em mudança substancial."""
    pass


class IncorporationIntegrityError(AgreementDomainError):
    """CA-40 / V21-37: Falha de integridade na transação atômica de incorporação de sugestão."""
    pass
