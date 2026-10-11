"""
Exceções de Domínio de Identidade e Multi-tenancy — CONDC
"""

class DomainError(Exception):
    """Exceção base do domínio."""
    pass

class TenantMismatchError(DomainError):
    """Tentativa de associar recursos de condomínios distintos (CA-01)."""
    pass

class UnauthorizedPublicationError(DomainError):
    """Tentativa de publicar sem autorização exclusiva do síndico ativo (CA-28)."""
    pass

class InvalidMembershipStatusError(DomainError):
    """Tentativa de transição de status de vínculo inválida."""
    pass

class MissingAuditPurposeError(DomainError):
    """Tentativa de consultar identidade sem justificativa de auditoria (CA-33)."""
    pass

class ElectoralFeatureForbiddenError(DomainError):
    """Violação do limite inegociável: tentativa de invocar recurso eleitoral ou votação."""
    pass

class DuplicateBuildingError(DomainError):
    """Tentativa de registrar ou atualizar prédio/torre com código duplicado no condomínio."""
    pass

class DuplicateUnitError(DomainError):
    """Tentativa de registrar ou atualizar unidade autônoma com código duplicado na mesma torre/condomínio."""
    pass

