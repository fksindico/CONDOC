"""
Views da API v1 — CONDC
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
import uuid

class SessionInfoView(APIView):
    """
    Retorna o estado da sessão do usuário autenticado (BFF).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if not getattr(request.user, "is_authenticated", False):
            return Response(
                {
                    "authenticated": False,
                    "account": None,
                },
                status=status.HTTP_200_OK
            )

        return Response({
            "authenticated": True,
            "account": {
                "account_id": getattr(request.user, "account_id", None),
                "full_name": getattr(request.user, "full_name", ""),
                "email": getattr(request.user, "email", ""),
                "tenant_id": getattr(request.user, "tenant_id", None),
                "roles": getattr(request.user, "roles", []),
            }
        })
