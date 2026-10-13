"""
Testes de Integridade, Unicidade e Correspondência Exata — CONDC
Cobertura exaustiva de Condomínios, Torres/Blocos (Buildings) e Unidades (Units).
Invariantes: UQ-BUILDING-01, UQ-UNIT-01, Isolamento Tenancy e CRUD Completo.
"""
import uuid
import pytest
from django.test import Client
from django.db import IntegrityError

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    Resident,
    UnitMembership,
)
from application.identity.services import CondominiumService, UnitMembershipService
from domain.identity.exceptions import (
    DomainError,
    DuplicateBuildingError,
    DuplicateUnitError,
    TenantMismatchError,
)


@pytest.mark.django_db
class TestCondominiumUnitsIntegrity:
    """Suíte exaustiva de testes de unicidade, edição e integridade referencial."""

    def test_condominium_creation_edition_and_persistence(self):
        """
        1. Criação, edição e persistência de Condomínio.
        Cria 'Condomínio Residencial Parque dos Pássaros', edita endereço/fuso horário
        e verifica correspondência exata nos campos persistidos no banco e via API REST.
        """
        client = Client()

        # Criação via CondominiumService
        condo = CondominiumService.create_condominium(
            name="Condomínio Residencial Parque dos Pássaros",
            cnpj="12.345.678/0001-90",
            timezone="America/Sao_Paulo",
            address_street="Avenida dos Bosques",
            address_number="500",
            address_neighborhood="Jardins",
            address_city="São Paulo",
            address_state="SP",
            address_zip_code="01234-567"
        )
        assert condo.id is not None
        assert condo.name == "Condomínio Residencial Parque dos Pássaros"
        assert condo.status == "active"

        # Edição via CondominiumService
        updated_condo = CondominiumService.update_condominium(
            condominium_id=condo.id,
            timezone="America/Manaus",
            address_street="Avenida dos Pássaros do Norte",
            address_number="1000",
            address_city="Manaus",
            address_state="AM"
        )
        assert updated_condo.timezone == "America/Manaus"
        assert updated_condo.address_street == "Avenida dos Pássaros do Norte"
        assert updated_condo.address_number == "1000"
        assert updated_condo.address_city == "Manaus"
        assert updated_condo.address_state == "AM"

        # Verificação via API REST GET
        resp_get = client.get(f'/api/v1/condominiums/{condo.id}')
        assert resp_get.status_code == 200
        data_get = resp_get.json()
        assert data_get["id"] == str(condo.id)
        assert data_get["name"] == "Condomínio Residencial Parque dos Pássaros"
        assert data_get["timezone"] == "America/Manaus"
        assert data_get["address_street"] == "Avenida dos Pássaros do Norte"
        assert data_get["address_city"] == "Manaus"

        # Edição via API REST PATCH
        resp_patch = client.patch(
            f'/api/v1/condominiums/{condo.id}',
            {"address_complement": "Bloco Administrativo", "timezone": "America/Fortaleza"},
            content_type="application/json"
        )
        assert resp_patch.status_code == 200
        assert resp_patch.json()["address_complement"] == "Bloco Administrativo"
        assert resp_patch.json()["timezone"] == "America/Fortaleza"

        # Soft Delete via DELETE
        resp_del = client.delete(f'/api/v1/condominiums/{condo.id}')
        assert resp_del.status_code == 204
        condo.refresh_from_db()
        assert condo.status in ("archived", "inactive")

    def test_buildings_creation_edition_and_uniqueness(self):
        """
        2. Criação, edição e garantia de unicidade estrita de Torres/Blocos.
        Cria 'Torre A - Canários' (código 'TA') e 'Torre B - Gaivotas' (código 'TB').
        Tentativa de duplicar 'TA' no mesmo condomínio deve falhar com DuplicateBuildingError (400).
        Tentativa de alterar o código da Torre B para 'TA' deve falhar com 400.
        """
        client = Client()

        condo = CondominiumService.create_condominium(
            name="Condomínio Residencial Parque dos Pássaros"
        )

        # 1. Criação de Torre A e Torre B
        torre_a = CondominiumService.create_building(
            condominium_id=condo.id,
            code="TA",
            name="Torre A - Canários",
            kind="tower",
            display_order=1
        )
        torre_b = CondominiumService.create_building(
            condominium_id=condo.id,
            code="TB",
            name="Torre B - Gaivotas",
            kind="tower",
            display_order=2
        )
        assert torre_a.code == "TA"
        assert torre_b.code == "TB"

        # 2. Rejeição no serviço de criação: duplicate building code
        with pytest.raises(DuplicateBuildingError):
            CondominiumService.create_building(
                condominium_id=condo.id,
                code="TA",
                name="Torre A Clonada"
            )

        # 3. Rejeição via API REST POST: 400 Bad Request
        resp_dup = client.post(
            f'/api/v1/condominiums/{condo.id}/buildings',
            {
                "code": "TA",
                "name": "Outra Torre A",
                "kind": "tower"
            },
            content_type="application/json"
        )
        assert resp_dup.status_code == 400
        assert "já existe para este condomínio" in resp_dup.json()["error"]

        # 4. Edição de Torre A com sucesso
        updated_ta = CondominiumService.update_building(
            building_id=torre_a.id,
            name="Torre A - Canários Imperial",
            display_order=10
        )
        assert updated_ta.name == "Torre A - Canários Imperial"
        assert updated_ta.display_order == 10

        # 5. Tentativa de edição de Torre B para código 'TA' via serviço -> DuplicateBuildingError
        with pytest.raises(DuplicateBuildingError):
            CondominiumService.update_building(
                building_id=torre_b.id,
                code="TA"
            )

        # 6. Tentativa de edição de Torre B para código 'TA' via API REST -> 400
        resp_patch_dup = client.patch(
            f'/api/v1/condominiums/{condo.id}/buildings/{torre_b.id}',
            {"code": "TA"},
            content_type="application/json"
        )
        assert resp_patch_dup.status_code == 400
        assert "já existe para este condomínio" in resp_patch_dup.json()["error"]

        # 7. Unicidade por Tenant: mesmo código 'TA' em OUTRO condomínio deve ser PERMITIDO
        condo_outro = CondominiumService.create_condominium(name="Condomínio Residencial Mirante")
        torre_outro = CondominiumService.create_building(
            condominium_id=condo_outro.id,
            code="TA",
            name="Torre A do Outro Condomínio"
        )
        assert torre_outro.id is not None
        assert torre_outro.code == "TA"

        # 8. Verificação de Constraint UNIQUE no banco de dados SQLite
        with pytest.raises(IntegrityError):
            Building.objects.create(
                condominium=condo,
                code="TA",
                name="Torre DB Duplicate Direct"
            )

    def test_units_creation_and_duplication_rejection(self):
        """
        3. Criação de Unidades e rejeição imediata de duplicação.
        Cria '101' e '102' na Torre A.
        Tentativa de criar duplicata '101' na Torre A deve falhar com DuplicateUnitError (400).
        Criar '101' na Torre B deve suceder sem conflito.
        """
        client = Client()

        condo = CondominiumService.create_condominium(name="Condomínio Residencial Parque dos Pássaros")
        torre_a = CondominiumService.create_building(condominium_id=condo.id, code="TA", name="Torre A - Canários")
        torre_b = CondominiumService.create_building(condominium_id=condo.id, code="TB", name="Torre B - Gaivotas")

        # 1. Cria '101' e '102' na Torre A via API REST
        resp_101 = client.post(
            f'/api/v1/condominiums/{condo.id}/units',
            {
                "building_id": str(torre_a.id),
                "code": "101",
                "floor_label": "1º Andar",
                "ideal_fraction": 0.025
            },
            content_type="application/json"
        )
        assert resp_101.status_code == 201
        unit_101_id = resp_101.json()["id"]

        resp_102 = client.post(
            f'/api/v1/condominiums/{condo.id}/units',
            {
                "building_id": str(torre_a.id),
                "code": "102",
                "floor_label": "1º Andar",
                "ideal_fraction": 0.025
            },
            content_type="application/json"
        )
        assert resp_102.status_code == 201

        # 2. Tentativa de duplicar '101' na Torre A via CondominiumService -> DuplicateUnitError
        with pytest.raises(DuplicateUnitError):
            CondominiumService.create_unit(
                condominium_id=condo.id,
                building_id=torre_a.id,
                code="101"
            )

        # 3. Tentativa de duplicar '101' na Torre A via API REST -> 400 Bad Request
        resp_dup = client.post(
            f'/api/v1/condominiums/{condo.id}/units',
            {
                "building_id": str(torre_a.id),
                "code": "101",
                "floor_label": "1º Andar Duplicado"
            },
            content_type="application/json"
        )
        assert resp_dup.status_code == 400
        assert resp_dup.json()["error"] == "Unidade com este código já existe para esta torre/condomínio."

        # 4. Criar '101' na Torre B -> DEVE SUCEDER!
        resp_101_tb = client.post(
            f'/api/v1/condominiums/{condo.id}/units',
            {
                "building_id": str(torre_b.id),
                "code": "101",
                "floor_label": "1º Andar Torre B",
                "ideal_fraction": 0.025
            },
            content_type="application/json"
        )
        assert resp_101_tb.status_code == 201
        assert resp_101_tb.json()["code"] == "101"
        assert resp_101_tb.json()["building_id"] == str(torre_b.id)

        # 5. Tentativa direta de violar UNIQUE constraint no banco de dados SQLite
        with pytest.raises(IntegrityError):
            Unit.objects.create(
                condominium=condo,
                building=torre_a,
                code="101"
            )

    def test_exact_correspondence_verification(self):
        """
        4. Verificação de Correspondência Exata (Condomínio X, Torre Y, Apartamento Z).
        Garante que a unidade 101 na Torre A aponta com precisão para:
        - Condomínio 'Residencial Parque dos Pássaros'
        - Torre 'Torre A - Canários'
        - Unidade '101'
        tanto na camada ORM quanto no payload JSON da API REST v1.
        """
        client = Client()

        condo = CondominiumService.create_condominium(
            name="Condomínio Residencial Parque dos Pássaros",
            cnpj="98.765.432/0001-11"
        )
        torre_a = CondominiumService.create_building(
            condominium_id=condo.id,
            code="TA",
            name="Torre A - Canários"
        )
        torre_b = CondominiumService.create_building(
            condominium_id=condo.id,
            code="TB",
            name="Torre B - Gaivotas"
        )

        unit_a_101 = CondominiumService.create_unit(
            condominium_id=condo.id,
            building_id=torre_a.id,
            code="101",
            floor_label="1º Andar",
            description="Apartamento 101 Torre Canários Face Norte",
            ideal_fraction=0.0125
        )

        unit_b_101 = CondominiumService.create_unit(
            condominium_id=condo.id,
            building_id=torre_b.id,
            code="101",
            floor_label="1º Andar",
            description="Apartamento 101 Torre Gaivotas Face Sul",
            ideal_fraction=0.0125
        )

        # Verificação ORM no Banco de Dados
        unit_db = Unit.objects.select_related('condominium', 'building').get(id=unit_a_101.id)
        assert unit_db.condominium.id == condo.id
        assert unit_db.condominium.name == "Condomínio Residencial Parque dos Pássaros"
        assert unit_db.building.id == torre_a.id
        assert unit_db.building.name == "Torre A - Canários"
        assert unit_db.building.code == "TA"
        assert unit_db.code == "101"
        assert unit_db.description == "Apartamento 101 Torre Canários Face Norte"

        # Verificação via API REST GET Unit Detail
        resp_a = client.get(f'/api/v1/condominiums/{condo.id}/units/{unit_a_101.id}')
        assert resp_a.status_code == 200
        data_a = resp_a.json()

        assert data_a["id"] == str(unit_a_101.id)
        assert data_a["condominium_id"] == str(condo.id)
        assert data_a["building_id"] == str(torre_a.id)
        assert data_a["building_name"] == "Torre A - Canários"
        assert data_a["code"] == "101"
        assert data_a["floor_label"] == "1º Andar"
        assert data_a["description"] == "Apartamento 101 Torre Canários Face Norte"

        # Verificação do isolamento com a unidade homônima da Torre B
        resp_b = client.get(f'/api/v1/condominiums/{condo.id}/units/{unit_b_101.id}')
        assert resp_b.status_code == 200
        data_b = resp_b.json()

        assert data_b["building_id"] == str(torre_b.id)
        assert data_b["building_name"] == "Torre B - Gaivotas"
        assert data_b["id"] != data_a["id"]

        # Listagem de unidades filtrada por condomínio
        resp_list = client.get(f'/api/v1/condominiums/{condo.id}/units')
        assert resp_list.status_code == 200
        units_list = resp_list.json()
        assert len(units_list) == 2
        codes_and_buildings = {(u["code"], u["building_name"]) for u in units_list}
        assert ("101", "Torre A - Canários") in codes_and_buildings
        assert ("101", "Torre B - Gaivotas") in codes_and_buildings

    def test_unit_edition_and_uniqueness_on_update(self):
        """
        5. Edição de Unidades e checagem de unicidade em atualizações.
        - Edita descrição da unidade 102 -> persiste com sucesso.
        - Tenta alterar o código da unidade 102 para 101 na mesma torre -> rejeitado com 400 DuplicateUnitError!
        - Altera código da unidade 102 para 103 -> aceito com sucesso.
        - Tenta mover a unidade 101 da Torre B para a Torre A (onde 101 já existe) -> rejeitado com 400!
        - Deleta unidade (soft delete) -> marca como inativa.
        """
        client = Client()

        condo = CondominiumService.create_condominium(name="Condomínio Residencial Parque dos Pássaros")
        torre_a = CondominiumService.create_building(condominium_id=condo.id, code="TA", name="Torre A")
        torre_b = CondominiumService.create_building(condominium_id=condo.id, code="TB", name="Torre B")

        unit_101_ta = CondominiumService.create_unit(condominium_id=condo.id, building_id=torre_a.id, code="101")
        unit_102_ta = CondominiumService.create_unit(condominium_id=condo.id, building_id=torre_a.id, code="102")
        unit_101_tb = CondominiumService.create_unit(condominium_id=condo.id, building_id=torre_b.id, code="101")

        # 1. Edição de descrição da 102 com sucesso
        updated_102 = CondominiumService.update_unit(
            unit_id=unit_102_ta.id,
            description="Apartamento 102 Reformado",
            floor_label="1º Andar"
        )
        assert updated_102.description == "Apartamento 102 Reformado"
        assert updated_102.code == "102"

        # 2. Tentativa via serviço: mudar código da 102 para 101 na Torre A -> DuplicateUnitError
        with pytest.raises(DuplicateUnitError):
            CondominiumService.update_unit(
                unit_id=unit_102_ta.id,
                code="101"
            )

        # 3. Tentativa via API REST PATCH: mudar código da 102 para 101 na Torre A -> 400
        resp_patch_dup = client.patch(
            f'/api/v1/condominiums/{condo.id}/units/{unit_102_ta.id}',
            {"code": "101"},
            content_type="application/json"
        )
        assert resp_patch_dup.status_code == 400
        assert resp_patch_dup.json()["error"] == "Unidade com este código já existe para esta torre/condomínio."

        # 4. Alteração da unidade 102 para código '103' -> DEVE FUNCIONAR
        resp_patch_ok = client.patch(
            f'/api/v1/condominiums/{condo.id}/units/{unit_102_ta.id}',
            {"code": "103", "floor_label": "1º Andar - Apto 103"},
            content_type="application/json"
        )
        assert resp_patch_ok.status_code == 200
        assert resp_patch_ok.json()["code"] == "103"

        # 5. Tentativa de mover 101 da Torre B para a Torre A onde já existe 101 -> 400
        resp_move_dup = client.patch(
            f'/api/v1/condominiums/{condo.id}/units/{unit_101_tb.id}',
            {"building_id": str(torre_a.id)},
            content_type="application/json"
        )
        assert resp_move_dup.status_code == 400
        assert resp_move_dup.json()["error"] == "Unidade com este código já existe para esta torre/condomínio."

        # 6. Tentativa de associar a unidade a uma torre de OUTRO condomínio -> TenantMismatchError (400)
        condo_outro = CondominiumService.create_condominium(name="Outro Condomínio")
        torre_outro = CondominiumService.create_building(condominium_id=condo_outro.id, code="TX", name="Torre X")

        resp_move_other_tenant = client.patch(
            f'/api/v1/condominiums/{condo.id}/units/{unit_101_tb.id}',
            {"building_id": str(torre_outro.id)},
            content_type="application/json"
        )
        assert resp_move_other_tenant.status_code == 400
        assert "pertence a outro condomínio" in resp_move_other_tenant.json()["error"]

        # 7. Soft Delete da unidade
        resp_del = client.delete(f'/api/v1/condominiums/{condo.id}/units/{unit_101_tb.id}')
        assert resp_del.status_code == 204
        unit_101_tb.refresh_from_db()
        assert unit_101_tb.status == "inactive"

    def test_sanitation_purge_lifecycle(self):
        """
        Ciclo Completo de Saneamento / Expurgo Definitivo:
        1. Condomínio Ativo -> tentativa de expurgo permanente DEVE FALHAR (400).
        2. Condomínio Arquivado -> expurgo permanente SUCCEDE (204) e remove do banco.
        3. Torre/Bloco Ativo -> tentativa de expurgo permanente DEVE FALHAR (400).
        4. Torre Inativada -> expurgo permanente SUCCEDE (204) e remove do banco.
        5. Unidade Ativa -> tentativa de expurgo permanente DEVE FALHAR (400).
        6. Unidade Inativada -> expurgo permanente SUCCEDE (204) e remove do banco.
        7. Vínculo de Morador Ativo -> tentativa de expurgo permanente DEVE FALHAR (400).
        8. Vínculo Revogado/Encerrado -> expurgo permanente SUCCEDE (204) e remove do banco.
        """
        client = Client()

        # --- A. Condomínio ---
        condo = CondominiumService.create_condominium(
            name="Condomínio Teste Saneamento",
            timezone="America/Sao_Paulo"
        )
        assert condo.status == "active"

        # Tentativa de expurgo em condomínio ativo deve retornar 400
        resp_purge_active = client.delete(f'/api/v1/condominiums/{condo.id}?permanent=true')
        assert resp_purge_active.status_code == 400
        assert "Apenas condomínios previamente arquivados ou inativos" in resp_purge_active.json()["error"]
        assert Condominium.objects.filter(id=condo.id).exists()

        # Arquiva o condomínio
        resp_archive = client.delete(f'/api/v1/condominiums/{condo.id}')
        assert resp_archive.status_code == 204
        condo.refresh_from_db()
        assert condo.status == "archived"

        # Expurgo permanente com sucesso
        resp_purge_archived = client.delete(f'/api/v1/condominiums/{condo.id}?permanent=true')
        assert resp_purge_archived.status_code == 204
        assert not Condominium.objects.filter(id=condo.id).exists()

        # --- B. Torre / Bloco ---
        condo2 = CondominiumService.create_condominium(name="Condomínio Torres Saneamento")
        torre = CondominiumService.create_building(
            condominium_id=condo2.id,
            code="T-SAN",
            name="Torre Saneamento"
        )
        assert torre.status == "active"

        # Tentativa de expurgo em torre ativa deve retornar 400
        resp_purge_tower_active = client.delete(f'/api/v1/condominiums/{condo2.id}/buildings/{torre.id}?permanent=true')
        assert resp_purge_tower_active.status_code == 400
        assert "Apenas torres/blocos previamente inativados" in resp_purge_tower_active.json()["error"]
        assert Building.objects.filter(id=torre.id).exists()

        # Inativa a torre
        resp_inactivate_tower = client.delete(f'/api/v1/condominiums/{condo2.id}/buildings/{torre.id}')
        assert resp_inactivate_tower.status_code == 204
        torre.refresh_from_db()
        assert torre.status == "inactive"

        # Expurgo permanente da torre inativada
        resp_purge_tower_done = client.delete(f'/api/v1/condominiums/{condo2.id}/buildings/{torre.id}?permanent=true')
        assert resp_purge_tower_done.status_code == 204
        assert not Building.objects.filter(id=torre.id).exists()

        # --- C. Unidade Autônoma ---
        unit = CondominiumService.create_unit(
            condominium_id=condo2.id,
            code="SAN-101",
            ideal_fraction=0.01
        )
        assert unit.status == "active"

        # Tentativa de expurgo em unidade ativa deve retornar 400
        resp_purge_unit_active = client.delete(f'/api/v1/condominiums/{condo2.id}/units/{unit.id}?permanent=true')
        assert resp_purge_unit_active.status_code == 400
        assert "Apenas unidades previamente inativadas" in resp_purge_unit_active.json()["error"]
        assert Unit.objects.filter(id=unit.id).exists()

        # Inativa a unidade
        resp_inactivate_unit = client.delete(f'/api/v1/condominiums/{condo2.id}/units/{unit.id}')
        assert resp_inactivate_unit.status_code == 204
        unit.refresh_from_db()
        assert unit.status == "inactive"

        # Expurgo permanente da unidade inativada
        resp_purge_unit_done = client.delete(f'/api/v1/condominiums/{condo2.id}/units/{unit.id}?permanent=true')
        assert resp_purge_unit_done.status_code == 204
        assert not Unit.objects.filter(id=unit.id).exists()

        # --- D. Vínculo de Morador (UnitMembership) ---
        unit_morador = CondominiumService.create_unit(
            condominium_id=condo2.id,
            code="SAN-202"
        )
        account = Account.objects.create(
            auth_user_id=uuid.uuid4(),
            email="morador.san@exemplo.com",
            full_name="Morador Saneamento"
        )
        resident = Resident.objects.create(
            condominium_id=condo2.id,
            account=account,
            full_name="Morador Saneamento"
        )
        membership = UnitMembership.objects.create(
            condominium_id=condo2.id,
            resident=resident,
            unit=unit_morador,
            category="proprietario_residente",
            membership_status="active",
            verification_status="validado"
        )

        # Tentativa de expurgo em vínculo ativo deve retornar 400
        resp_purge_mem_active = client.delete(f'/api/v1/condominiums/{condo2.id}/memberships/{membership.id}?permanent=true')
        assert resp_purge_mem_active.status_code == 400
        assert "Apenas vínculos de moradores previamente encerrados" in resp_purge_mem_active.json()["error"]
        assert UnitMembership.objects.filter(id=membership.id).exists()

        # Revoga/Encerra o vínculo
        resp_revoke_mem = client.delete(f'/api/v1/condominiums/{condo2.id}/memberships/{membership.id}')
        assert resp_revoke_mem.status_code == 204
        membership.refresh_from_db()
        assert membership.membership_status == "ended"

        # Expurgo permanente do vínculo revogado/encerrado
        resp_purge_mem_done = client.delete(f'/api/v1/condominiums/{condo2.id}/memberships/{membership.id}?permanent=true')
        assert resp_purge_mem_done.status_code == 204
        assert not UnitMembership.objects.filter(id=membership.id).exists()

    def test_batch_generate_units_and_public_structure(self):
        """
        Valida a geração de apartamentos em lote com padrão andar+sufixo (ex: 3º ao 5º andar, 6 por andar)
        e a disponibilização da estrutura predial no endpoint da consulta pública para o morador.
        """
        client = Client()
        condo = CondominiumService.create_condominium(
            name="Condomínio Reserva dos Manacás",
            timezone="America/Sao_Paulo"
        )

        # 1. Geração em lote via API REST
        batch_payload = {
            "new_building_name": "Torre Manacá",
            "new_building_code": "MANACA",
            "start_floor": 3,
            "end_floor": 5,
            "units_per_floor": 6,
            "suffix_digits": 2,
        }
        resp_batch = client.post(
            f"/api/v1/condominiums/{condo.id}/units/batch-generate",
            data=batch_payload,
            content_type="application/json"
        )
        assert resp_batch.status_code == 201
        data = resp_batch.json()
        assert data["created_count"] == 18
        assert data["existing_count"] == 0
        assert data["total_units"] == 18
        assert "301" in data["sample_codes"]
        assert "306" in data["sample_codes"]

        # 2. Confirma persistência e labels de andares no banco
        units_3rd = Unit.objects.filter(condominium=condo, code__startswith="3").order_by("code")
        assert units_3rd.count() == 6
        assert list(units_3rd.values_list("code", flat=True)) == ["301", "302", "303", "304", "305", "306"]
        assert units_3rd.first().floor_label == "3º Andar"

        # 3. Idempotência: rodar novamente não duplica nem falha
        resp_batch_idem = client.post(
            f"/api/v1/condominiums/{condo.id}/units/batch-generate",
            data=batch_payload,
            content_type="application/json"
        )
        assert resp_batch_idem.status_code == 201
        data_idem = resp_batch_idem.json()
        assert data_idem["created_count"] == 0
        assert data_idem["existing_count"] == 18
        assert Unit.objects.filter(condominium=condo).count() == 18

        # 4. Cria consulta pública e verifica estrutura no endpoint público
        from application.consultation.services import SimplifiedConsultationService
        from django.core.files.uploadedfile import SimpleUploadedFile
        pdf_file = SimpleUploadedFile("regimento.pdf", b"%PDF-1.4 dummy", content_type="application/pdf")
        consultation = SimplifiedConsultationService.create_consultation(
            condominium_id=condo.id,
            title="Revisão Regimento Interno Manacás",
            document_type="regimento",
            pdf_file=pdf_file
        )

        resp_public = client.get(f"/api/v1/public/consultations/{consultation.public_token}")
        assert resp_public.status_code == 200
        pub_data = resp_public.json()
        assert "structure" in pub_data
        struct = pub_data["structure"]
        assert struct["total_units"] == 18
        assert len(struct["buildings"]) == 1
        bldg = struct["buildings"][0]
        assert bldg["name"] == "Torre Manacá"
        assert len(bldg["units"]) == 18
        assert bldg["units"][0]["code"] == "301"
        assert bldg["units"][-1]["code"] == "506"

