"""
Invariantes de Domínio para Convites de Acesso — CONDC (Fase 2)
Regras de segurança, integridade criptográfica de tokens e validação de contatos.
"""
import hashlib
import re
from typing import Optional
from django.utils import timezone
from .exceptions import (
    InvitationExpiredOrExhaustedError,
    InvitationRevokedError,
    InvalidExpectedContactError,
)

def hash_invitation_token(token: str) -> str:
    """
    Calcula o hash SHA-256 de um token de convite opaco para armazenamento seguro.
    O token em texto claro NUNCA é persistido no banco de dados.
    """
    return hashlib.sha256(token.strip().encode('utf-8')).hexdigest()


def normalize_contact(contact: Optional[str]) -> str:
    """
    Normaliza e-mail (lowercase/strip) ou telefone (apenas dígitos).
    """
    if not contact:
        return ""
    c = contact.strip()
    if "@" in c:
        return c.lower()
    # Telefone: mantém apenas dígitos
    digits = re.sub(r'\D', '', c)
    return digits


def assert_invitation_active(
    status: str,
    expires_at,
    redemption_count: int,
    max_redemptions: int
) -> None:
    """
    Garante que o convite está ativo, dentro da validade e possui vagas de resgate.
    """
    if status == 'revogado':
        raise InvitationRevokedError("Este convite foi revogado pela administração do condomínio.")

    now = timezone.now()
    if status == 'expirado' or now >= expires_at:
        raise InvitationExpiredOrExhaustedError("Este convite já expirou e não pode mais ser utilizado.")

    if status == 'esgotado' or redemption_count >= max_redemptions:
        raise InvitationExpiredOrExhaustedError("Este convite atingiu o limite máximo de resgates permitidos.")


def assert_expected_contact_match(expected_contact: Optional[str], provided_contact: Optional[str]) -> None:
    """
    CA-09, V21-22: Para convites individuais pré-conferidos, exige correspondência
    estrita com o contato previsto (e-mail ou telefone).
    """
    if not expected_contact:
        return

    norm_expected = normalize_contact(expected_contact)
    norm_provided = normalize_contact(provided_contact)

    if not norm_provided:
        raise InvalidExpectedContactError(
            "Este convite individual pré-conferido exige a confirmação do contato cadastrado."
        )

    if norm_expected != norm_provided:
        raise InvalidExpectedContactError(
            "O contato informado não corresponde ao contato previsto para este convite individual pré-conferido."
        )
