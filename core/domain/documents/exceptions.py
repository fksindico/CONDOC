"""
Exceções de Domínio do Núcleo Documental — CONDC (Fase 3)
"""

class DocumentDomainError(Exception):
    """Exceção base do domínio de documentos."""
    pass


class CircularReferenceError(DocumentDomainError):
    """Tentativa de criar referência cíclica na árvore hierárquica de dispositivos."""
    pass


class ConcurrencyConflictError(DocumentDomainError):
    """Conflito de concorrência otimista (ETag ou revisão desatualizada - CA-23)."""
    pass


class SnapshotImmutableError(DocumentDomainError):
    """Tentativa de alterar ou violar a imutabilidade de um snapshot congelado (CA-41)."""
    pass


class TranscriptionStatusError(DocumentDomainError):
    """Operação inválida no ciclo de vida de transcrição da fonte."""
    pass


class PrivateNoteAccessForbiddenError(DocumentDomainError):
    """Tentativa de expor ou acessar notas internas sem autorização (CA-24)."""
    pass


class GrammarValidationError(DocumentDomainError):
    """Erro base para violação da gramática normativa LC 95."""
    pass


class MissingCaputError(GrammarValidationError):
    """Dispositivo de Artigo não possui Caput inicial obrigatório."""
    pass


class InvalidContainmentError(GrammarValidationError):
    """Violação da hierarquia estrita de contenção normativa."""
    pass


class MaxDepthExceededError(GrammarValidationError):
    """Profundidade máxima da árvore hierárquica excedida."""
    pass

