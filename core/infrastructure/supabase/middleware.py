"""
Middleware de Isolamento RLS — CONDC (ADR-004)
Aplica o contexto de tenant da requisição nas transações do banco de dados.
"""
from django.utils.deprecation import MiddlewareMixin
from django.db import connection

class TenantRLSMiddleware(MiddlewareMixin):
    """
    Injeta o tenant_id e account_id ativos na transação de banco se o usuário estiver autenticado.
    """
    def process_request(self, request):
        request.tenant_id = request.headers.get("X-Tenant-ID") or request.session.get("tenant_id")
        request.account_id = getattr(request.user, "account_id", None) if getattr(request, "user", None) else None

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Se um tenant_id for identificado, define o contexto na conexão
        if getattr(request, "tenant_id", None):
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SET LOCAL app.current_tenant_id = %s;",
                        [str(request.tenant_id)]
                    )
                    if getattr(request, "account_id", None):
                        cursor.execute(
                            "SET LOCAL app.current_account_id = %s;",
                            [str(request.account_id)]
                        )
            except Exception:
                # Caso a conexão ainda não esteja aberta ou em ambiente sqlite de teste
                pass
        return None
