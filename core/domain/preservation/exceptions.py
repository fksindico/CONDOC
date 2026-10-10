"""
Exceções de Domínio para Preservação e Artefatos de Exportação — CONDC (Fase 7)
PRD Mestre v3.0 (Critérios CA-41, CA-42, CA-45, UI-33, UI-38)
"""

class PreservationDomainError(Exception):
    """Exceção base para preservação e artefatos de exportação."""
    pass


class PublicExportExposureError(PreservationDomainError):
    """UI-33: Lançada se notas internas confidenciais ou PII vazarem para o pacote externo público."""
    pass


class ManifestIntegrityError(PreservationDomainError):
    """Lançada se os hashes SHA-256 dos arquivos divergirem do manifesto de integridade."""
    pass


class ElectoralDeliberationForbiddenError(PreservationDomainError):
    """CA-45 / UI-38: Lançada se houver tentativa de introduzir votação ou apuração assemblear."""
    pass
