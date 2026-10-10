"""
Exceções de Domínio para Convites de Acesso — CONDC (Fase 2)
"""
from domain.identity.exceptions import DomainError

class InvitationExpiredOrExhaustedError(DomainError):
    """Convite expirou por data ou atingiu o número máximo de resgates permitidos."""
    pass

class InvitationRevokedError(DomainError):
    """Convite foi revogado pela administração e não permite novos resgates (CA-11, V21-23)."""
    pass

class InvalidExpectedContactError(DomainError):
    """Contato fornecido no resgate não corresponde ao contato previsto no convite pré-conferido (CA-09, V21-22)."""
    pass

class InvitationRedemptionForbiddenError(DomainError):
    """Operação de resgate não autorizada ou condições de elegibilidade não satisfeitas."""
    pass
