"""
Exceções de Domínio para Comparação, Mapeamento de Origens, Renumeração e Exportação — CONDC (Fase 4)
Compatível com PRD Mestre v3.0 (Critérios CA-19 a CA-22, CA-42).
"""

class ComparisonDomainError(Exception):
    """Exceção base do domínio de comparação e exportação."""
    pass


class FictitiousOriginError(ComparisonDomainError):
    """Tentativa de criar vinculação de origem fictícia em dispositivo novo/incluído (CA-19)."""
    pass


class ExcludedProvisionInCleanExportError(ComparisonDomainError):
    """Tentativa indevida de incluir dispositivo excluído no documento limpo (CA-20, CA-42)."""
    pass


class InvalidOriginMappingError(ComparisonDomainError):
    """Inconsistência ou tipo inválido em mapeamento de origem N:M (CA-21)."""
    pass


class BrokenCrossReferenceError(ComparisonDomainError):
    """Referência cruzada estruturada com alvo inexistente ou quebrado (CA-22)."""
    pass


class RenumberingError(ComparisonDomainError):
    """Erro ou inconsistência no processo de renumeração estruturada (CA-22)."""
    pass


class CleanExportIntegrityError(ComparisonDomainError):
    """Tentativa de expor dados de identidade, notas internas ou referências antigas em export limpo (CA-42)."""
    pass
