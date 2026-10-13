import pytest
import uuid
from rest_framework.test import APIClient
from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    ResidentRegistration,
    Resident,
    Account,
    UnitMembership,
)

@pytest.mark.django_db
class TestCondominiumDashboardMetrics:
    def setup_method(self):
        self.client = APIClient()
        self.condo_id = uuid.uuid4()
        self.condo = Condominium.objects.create(
            id=self.condo_id,
            name="Condomínio Teste Métricas Reais",
            status="active"
        )
        self.building = Building.objects.create(
            id=uuid.uuid4(),
            condominium=self.condo,
            code="T1",
            name="Torre 1",
            status="active"
        )
        self.unit = Unit.objects.create(
            id=uuid.uuid4(),
            condominium=self.condo,
            building=self.building,
            code="101",
            status="active"
        )

    def test_metrics_empty_condo(self):
        response = self.client.get(f"/api/v1/condominiums/{self.condo_id}/dashboard-metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["residents_count"] == 0
        assert data["units_count"] == 1
        assert data["buildings_count"] == 1
        assert data["consultations_open"] == 0
        assert data["suggestions_pending"] == 0

    def test_metrics_with_residents_and_memberships(self):
        # Cria pré-cadastro
        ResidentRegistration.objects.create(
            id=uuid.uuid4(),
            condominium=self.condo,
            unit=self.unit,
            full_name="Morador Pré-cadastrado",
            status="pendente"
        )

        # Cria membro validado
        account = Account.objects.create(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            email="membro@teste.com",
            full_name="Membro Efetivo"
        )
        resident = Resident.objects.create(
            id=uuid.uuid4(),
            condominium=self.condo,
            account=account,
            full_name="Membro Efetivo",
            status="active"
        )
        UnitMembership.objects.create(
            id=uuid.uuid4(),
            condominium=self.condo,
            resident=resident,
            unit=self.unit,
            category="proprietario_residente",
            verification_status="validado",
            membership_status="active"
        )

        response = self.client.get(f"/api/v1/condominiums/{self.condo_id}/dashboard-metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["registrations_count"] == 1
        assert data["memberships_count"] == 1
        assert data["residents_count"] == 2
        assert data["units_count"] == 1
        assert data["buildings_count"] == 1
