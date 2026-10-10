"""
Roteamento da API v1 — CONDC
"""
from django.urls import path
from .views import SessionInfoView

urlpatterns = [
    path('auth/session', SessionInfoView.as_view(), name='api_v1_session_info'),
]
