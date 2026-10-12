"""
Serviço de Idempotência Operacional — CONDC (Fase 2)
Garante que requisições de mutação com o mesmo Idempotency-Key retornem o mesmo resultado
sem reexecução, e que payloads diferentes com a mesma chave retornem conflito 409 (CA-05, V21-14, V21-15).
"""
import hashlib
import json
import logging
import uuid
from datetime import timedelta
from typing import Optional, Tuple, Any, Callable
from django.db import IntegrityError
from django.utils import timezone
from infrastructure.models import IdempotencyRecord
from domain.imports.exceptions import IdempotencyConflictError

logger = logging.getLogger("condoc.idempotency")

class IdempotencyService:
    @staticmethod
    def calculate_payload_hash(payload: Any) -> str:
        """Calcula o hash SHA-256 canônico de um payload estruturado."""
        if payload is None:
            raw_str = ""
        elif isinstance(payload, (dict, list)):
            raw_str = json.dumps(payload, sort_keys=True, default=str)
        else:
            raw_str = str(payload)
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    @classmethod
    def execute_with_idempotency(
        cls,
        operation: str,
        key: Optional[str],
        payload: Any,
        tenant_id: Optional[uuid.UUID],
        actor_account_id: Optional[uuid.UUID],
        handler: Callable[[], Tuple[int, Any]],
        retention_hours: int = 24
    ) -> Tuple[int, Any]:
        """
        Executa uma ação garantindo idempotência estrita caso 'key' seja fornecida.
        Se 'key' for None ou vazia, executa diretamente o handler.
        """
        if not key:
            return handler()

        key = key.strip()
        payload_hash = cls.calculate_payload_hash(payload)

        # Procura registro prévio
        record = IdempotencyRecord.objects.filter(
            tenant_id=tenant_id,
            operation=operation,
            key=key
        ).first()

        if record:
            # Verifica se o payload é idêntico
            if record.payload_hash == payload_hash:
                # Retorna resultado prévio sem reexecutar (CA-05, V21-14)
                return record.response_code, record.response_body
            else:
                # Mesma chave com payload diferente -> 409 Conflict (V21-15)
                raise IdempotencyConflictError(
                    f"A chave de idempotência '{key}' já foi utilizada para a operação '{operation}' com outro payload."
                )

        # Executa o handler
        status_code, response_data = handler()

        # Salva o registro de idempotência caso tenha sido bem-sucedido (2xx / 4xx)
        try:
            expires_at = timezone.now() + timedelta(hours=retention_hours)
            IdempotencyRecord.objects.create(
                tenant_id=tenant_id,
                actor_account_id=actor_account_id,
                operation=operation,
                key=key,
                payload_hash=payload_hash,
                response_code=status_code,
                response_body=response_data if isinstance(response_data, (dict, list)) else {"result": response_data},
                expires_at=expires_at
            )
        except IntegrityError:
            # Concorrência detectada: outra thread gravou o registro simultaneamente
            existing = IdempotencyRecord.objects.filter(
                tenant_id=tenant_id,
                operation=operation,
                key=key
            ).first()
            if existing and existing.payload_hash != payload_hash:
                raise IdempotencyConflictError(
                    f"A chave de idempotência '{key}' já foi utilizada para a operação '{operation}' com outro payload."
                )
        except Exception as e:
            logger.warning("Falha ao persistir registro de idempotência [%s]: %s", key, e)

        return status_code, response_data
