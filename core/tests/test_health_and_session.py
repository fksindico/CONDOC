"""
Testes de Integridade da API e Sessão — CONDOC (Fase 0)
"""
import pytest
from django.test import Client

@pytest.mark.django_db
def test_health_check_endpoint():
    """Valida se o endpoint /api/health responde 200 OK."""
    client = Client()
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'operational'
    assert 'timestamp' in data

def test_session_info_unauthenticated():
    """Valida retorno de sessão vazia para requisição não autenticada."""
    client = Client()
    response = client.get('/api/v1/auth/session')
    assert response.status_code == 200
    data = response.json()
    assert data['authenticated'] is False
    assert data['account'] is None
