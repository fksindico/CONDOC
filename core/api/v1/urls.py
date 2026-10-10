"""
Roteamento da API v1 — CONDC (Fase 1: Identidade, Estrutura Física e Sessão)
"""
from django.urls import path
from .views import (
    SessionInfoView,
    CondominiumListCreateView,
    BuildingListCreateView,
    UnitListCreateView,
    ResidentRegistrationListCreateView,
    UnitMembershipListView,
    VerifyMembershipActionView,
    RoleAssignmentListCreateView,
)

urlpatterns = [
    # Sessão e Auth BFF
    path('auth/session', SessionInfoView.as_view(), name='api_v1_session_info'),

    # Condomínios (Tenancy Raiz)
    path('condominiums', CondominiumListCreateView.as_view(), name='api_v1_condominiums'),

    # Torres / Blocos / Prédios
    path('condominiums/<uuid:condominium_id>/buildings', BuildingListCreateView.as_view(), name='api_v1_buildings'),

    # Unidades Autônomas
    path('condominiums/<uuid:condominium_id>/units', UnitListCreateView.as_view(), name='api_v1_units'),

    # Pré-cadastro manual de moradores (CA-02)
    path('condominiums/<uuid:condominium_id>/registrations', ResidentRegistrationListCreateView.as_view(), name='api_v1_registrations'),

    # Vínculos com Unidades (CA-13, CA-14)
    path('condominiums/<uuid:condominium_id>/memberships', UnitMembershipListView.as_view(), name='api_v1_memberships'),

    # Verificação Documental Auditada de Vínculo (CA-12, CA-15)
    path('condominiums/<uuid:condominium_id>/memberships/<uuid:membership_id>/verify', VerifyMembershipActionView.as_view(), name='api_v1_membership_verify'),

    # Atribuição de Papéis e Permissões (CA-28)
    path('condominiums/<uuid:condominium_id>/roles', RoleAssignmentListCreateView.as_view(), name='api_v1_roles'),
]
