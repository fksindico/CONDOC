"""
Gerenciador de Contexto RLS Transacional — CONDC (ADR-004)
Garante isolamento multi-tenant a nível de banco via SET LOCAL.
"""
from contextlib import contextmanager
from django.db import connection, transaction
import uuid

@contextmanager
def tenant_context(tenant_id: str | uuid.UUID, account_id: str | uuid.UUID | None = None):
    """
    Define as variáveis de contexto RLS restritas à transação atual.
    O modificador LOCAL garante que as variáveis sejam limpas automaticamente
    no COMMIT ou ROLLBACK, prevenindo contaminação de conexões em pool.
    """
    tenant_str = str(tenant_id)
    account_str = str(account_id) if account_id else ""

    # Garante que opera dentro de transação atômica
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SET LOCAL app.current_tenant_id = %s;",
                [tenant_str]
            )
            if account_str:
                cursor.execute(
                    "SET LOCAL app.current_account_id = %s;",
                    [account_str]
                )
        try:
            yield
        finally:
            # Ao sair do bloco, a transação commita ou aborta e as variáveis expiram.
            pass
