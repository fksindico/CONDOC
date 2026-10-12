"""
Tratamento Padronizado de Exceções — CONDC API v1
Segue o formato canônico de erro definido em Contrato_API_v3.md
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import uuid

logger = logging.getLogger("condoc.api")

def custom_exception_handler(exc, context):
    """
    Retorna respostas de erro estruturadas no padrão:
    {
      "code": "ERROR_CODE",
      "message": "Descrição humanizada",
      "request_id": "UUID",
      "details": { ... }
    }
    """
    response = exception_handler(exc, context)
    request_id = str(uuid.uuid4())

    if response is not None:
        custom_data = {
            "code": getattr(exc, "default_code", "API_ERROR").upper(),
            "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "request_id": request_id,
        }
        if isinstance(response.data, dict):
            custom_data["details"] = response.data
        elif isinstance(response.data, (list, tuple)):
            custom_data["details"] = {"errors": list(response.data)}
        else:
            custom_data["details"] = {"raw": response.data}
        response.data = custom_data
        return response

    # Erros não tratados (500)
    logger.exception("Erro 500 não tratado no endpoint [%s]: %s", request_id, exc)
    return Response(
        {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Ocorreu um erro interno no servidor.",
            "request_id": request_id,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
