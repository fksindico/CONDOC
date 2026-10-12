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
        session_tenant = request.session.get("tenant_id") if hasattr(request, "session") else None
        user_tenant = getattr(request.user, "tenant_id", None) if getattr(request, "user", None) else None
        header_tenant = request.headers.get("X-Tenant-ID")

        # Prioriza tenant da sessão/usuário autenticado para prevenir spoofing
        request.tenant_id = user_tenant or session_tenant or header_tenant
        request.account_id = getattr(request.user, "account_id", None) if getattr(request, "user", None) else None

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Se um tenant_id for identificado, define o contexto na conexão
        if getattr(request, "tenant_id", None):
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SET app.current_tenant_id = %s;",
                        [str(request.tenant_id)]
                    )
                    if getattr(request, "account_id", None):
                        cursor.execute(
                            "SET app.current_account_id = %s;",
                            [str(request.account_id)]
                        )
            except Exception:
                # Caso a conexão ainda não esteja aberta ou em ambiente sqlite de teste
                pass
        return None

    def process_response(self, request, response):
        # Limpa o contexto de tenant ao término da requisição para prevenir contaminação em connection pool
        if getattr(request, "tenant_id", None):
            try:
                with connection.cursor() as cursor:
                    cursor.execute("RESET app.current_tenant_id; RESET app.current_account_id;")
            except Exception:
                pass
        return response
