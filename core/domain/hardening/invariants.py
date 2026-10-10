"""
Invariantes de Domínio para Hardening e Restauração Consistente — CONDC (Fase 8 / CA-44)
"""
import hashlib
from typing import Any, Dict, List

from .exceptions import (
    BackupIntegrityError,
    InconsistentRestoreError,
    SecurityHeaderViolationError,
)

MANDATORY_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
}


def calculate_sha256(data: bytes) -> str:
    """Calcula hash SHA-256 de dados binários."""
    return hashlib.sha256(data).hexdigest()


def assert_backup_checksums_match(expected_sha256: str, actual_data: bytes, component_name: str) -> None:
    """
    CA-44: Valida integridade criptográfica de cada componente do backup antes da restauração.
    """
    calculated = calculate_sha256(actual_data)
    if calculated != expected_sha256:
        raise BackupIntegrityError(
            f"Adulteração ou corrupção detectada no componente '{component_name}'. "
            f"Esperado: {expected_sha256}, Calculado: {calculated}."
        )


def assert_security_headers_present(headers_dict: Dict[str, str]) -> None:
    """Valida se os cabeçalhos de segurança obrigatórios estão presentes nas respostas HTTP."""
    for header, expected_val in MANDATORY_SECURITY_HEADERS.items():
        val = headers_dict.get(header)
        if not val or val.lower() != expected_val.lower():
            raise SecurityHeaderViolationError(
                f"Cabeçalho obrigatório de segurança '{header}' ausente ou incorreto (esperado: '{expected_val}', obtido: '{val}')."
            )
