"""
Exceções de Domínio de Importação Cadastral — CONDC (Fase 2)
"""
try:
    from ..identity.exceptions import DomainError
except (ImportError, ValueError):
    from domain.identity.exceptions import DomainError

class FormulaInjectionDetectedError(DomainError):
    """Tentativa de injeção de fórmula maliciosa em campo de planilha (CWE-1236, V21-07)."""
    pass

class ImportPreviewOutdatedError(DomainError):
    """Revisão da prévia desatualizada no momento da confirmação (V21-13, CA-03)."""
    pass

class InvalidImportFileError(DomainError):
    """Arquivo inválido, corrompido, tipo MIME disfarçado ou limite excedido (V21-07)."""
    pass

class UnknownUnitError(DomainError):
    """Unidade desconhecida no condomínio não pode ser criada silenciosamente (CA-04)."""
    pass

class UnresolvedConflictError(DomainError):
    """Tentativa de aplicar lote contendo conflitos impeditivos não resolvidos (V21-10, V21-16)."""
    pass

class IdempotencyConflictError(DomainError):
    """Mesma chave de idempotência enviada com payload diferente (V21-15)."""
    pass

class BatchAlreadyProcessedError(DomainError):
    """Tentativa de alterar ou reconfirmar lote já concluído ou cancelado."""
    pass
