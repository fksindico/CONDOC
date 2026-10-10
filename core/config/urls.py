"""
Roteamento Principal de URLs — CONDC Core Backend
"""
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db import connection

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint de verificação de integridade operacional do Core.
    """
    db_status = "ok"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception as e:
        db_status = f"error: {str(e)}"

    return Response({
        "status": "operational",
        "service": "CONDC Core API",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": timezone.now().isoformat(),
    })

urlpatterns = [
    path('api/health', health_check, name='health_check'),
    path('api/v1/', include('api.v1.urls')),
]
