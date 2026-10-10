"""
Exceções de Domínio para Hardening e Restauração Consistente — CONDC (Fase 8 / CA-44)
"""

class HardeningDomainError(Exception):
    """Exceção base para o domínio de hardening e operações."""
    pass


class BackupIntegrityError(HardeningDomainError):
    """CA-44: Lançada quando há adulteração de checksum ou corrupção no pacote de backup."""
    pass


class InconsistentRestoreError(HardeningDomainError):
    """CA-44: Lançada se a restauração violar a consistência referencial entre banco e objetos."""
    pass


class SecurityHeaderViolationError(HardeningDomainError):
    """Lançada quando cabeçalhos mandatários de segurança (CSP, HSTS) estiverem ausentes."""
    pass
