"""
Autenticação de Sessão BFF — CONDC (ADR-002)
Autentica requisições via cookies de sessão HttpOnly ou tokens delegados pelo BFF.
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser

class AuthenticatedAccount:
    """Representação simplificada de conta autenticada."""
    def __init__(self, account_id, email, full_name, tenant_id=None, roles=None):
        self.account_id = account_id
        self.id = account_id
        self.email = email
        self.full_name = full_name
        self.tenant_id = tenant_id
        self.roles = roles or []
        self.is_authenticated = True

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

class BFFSessionAuthentication(BaseAuthentication):
    """
    Autenticação baseada em sessão BFF com cookies HttpOnly seguros.
    """
    def authenticate(self, request):
        # 1. Verifica se existe sessão ativa com account_id
        account_id = request.session.get("account_id")
        email = request.session.get("email")
        full_name = request.session.get("full_name")
        tenant_id = request.session.get("tenant_id") or request.headers.get("X-Tenant-ID")

        if not account_id:
            # Em modo de desenvolvimento sem sessão configurada, permite requisições públicas
            # mas não autentica usuário
            return None

        user = AuthenticatedAccount(
            account_id=account_id,
            email=email,
            full_name=full_name,
            tenant_id=tenant_id,
            roles=request.session.get("roles", [])
        )
        return (user, None)
