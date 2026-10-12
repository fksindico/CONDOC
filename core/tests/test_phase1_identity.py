"""
Testes Automatizados da Fase 1 — Identidade, Multi-Tenancy e Estrutura Física
Critérios homologados: CA-01, CA-02, CA-06, CA-12, CA-13, CA-14, CA-15, CA-28, CA-33, CA-45; AR-04 a AR-09
"""
import uuid
import pytest
from django.test import Client
from django.utils import timezone

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    ResidentRegistration,
    Resident,
    UnitMembership,
    MembershipVerificationEvent,
    RoleAssignment,
    IdentityAccessEvent,
)
from application.identity.services import (
    CondominiumService,
    ResidentRegistrationService,
    MembershipVerificationService,
    RoleService,
    IdentityAuditService,
)
from domain.identity.invariants import (
    assert_no_electoral_intent,
    assert_same_tenant,
    assert_audit_purpose,
    assert_sindico_publication_authority,
)
from domain.identity.exceptions import (
    TenantMismatchError,
    ElectoralFeatureForbiddenError,
    MissingAuditPurposeError,
    UnauthorizedPublicationError,
    InvalidMembershipStatusError,
)

@pytest.mark.django_db
class TestPhase1DomainInvariants:
    """Testes das invariantes estritas do domínio e limites normativos."""

    def test_ca_45_proibicao_terminante_de_recursos_eleitorais(self):
        """CA-45: Nenhuma votação, eleição, apuração, quórum ou peso eleitoral."""
        with pytest.raises(ElectoralFeatureForbiddenError) as exc_info:
            assert_no_electoral_intent("Eleicao_Sindico_2026")
        assert "termo eleitoral ou deliberativo proibido" in str(exc_info.value).lower()

        with pytest.raises(ElectoralFeatureForbiddenError):
            assert_no_electoral_intent("Criar minuta", {"apuracao_quorum": True})

        # Termo permitido (estritamente consultivo e normativo)
        assert_no_electoral_intent("Revisao do Regimento Interno")

    def test_ca_01_isolamento_de_tenant_entre_condominios(self):
        """CA-01: Associação cruzada entre condomínios distintos é barrada."""
        condo_a_id = uuid.uuid4()
        condo_b_id = uuid.uuid4()

        with pytest.raises(TenantMismatchError):
            assert_same_tenant(condo_a_id, condo_b_id, "Recurso Condominial")

        # Mesmo tenant é permitido
        assert_same_tenant(condo_a_id, condo_a_id, "Recurso Válido")

    def test_ca_28_autoridade_exclusiva_de_publicacao_do_sindico(self):
        """CA-28: Administrador ou comissão sem papel de síndico NÃO pode publicar."""
        with pytest.raises(UnauthorizedPublicationError):
            assert_sindico_publication_authority(["administrador", "comissao", "juridico"])

        # Síndico ativo possui autoridade
        assert_sindico_publication_authority(["sindico", "morador"])

    def test_ca_33_exigencia_de_justificativa_para_acesso_a_identidade(self):
        """CA-33: Consulta de dados pessoais exige justificativa expressa para auditoria."""
        with pytest.raises(MissingAuditPurposeError):
            assert_audit_purpose("")

        with pytest.raises(MissingAuditPurposeError):
            assert_audit_purpose("abc")  # Curto demais

        assert_audit_purpose("Conferência de titularidade para revisão de minuta")


@pytest.mark.django_db
class TestPhase1ServicesAndLifecycle:
    """Testes dos serviços de aplicação e ciclo de vida dos modelos."""

    def test_ca_02_cadastro_manual_cria_registro_previo_sem_credencial(self):
        """CA-02: Cadastro manual cria registro prévio sem gerar credencial automática."""
        condo = Condominium.objects.create(name="Condomínio Solar das Palmeiras", cnpj="11.222.333/0001-44")
        unit = Unit.objects.create(condominium=condo, code="101")

        reg = ResidentRegistrationService.create_manual_registration(
            condominium_id=condo.id,
            unit_id=unit.id,
            full_name="Carlos Drummond",
            relationship="proprietario_residente",
            email="carlos@exemplo.com",
            phone_e164="+5511999998888"
        )

        assert reg.status == "pendente"
        assert reg.source == "manual"
        assert reg.full_name == "Carlos Drummond"
        # Garante que NENHUMA conta de usuário foi gerada automaticamente
        assert Account.objects.filter(email="carlos@exemplo.com").count() == 0

    def test_ca_13_multiplos_moradores_na_mesma_unidade(self):
        """CA-13: Vários moradores podem ter vínculos na mesma unidade."""
        condo = Condominium.objects.create(name="Edifício Horizonte")
        unit = Unit.objects.create(condominium=condo, code="302")

        acc1 = Account.objects.create(auth_user_id=uuid.uuid4(), email="morador1@exemplo.com", full_name="Morador Um")
        acc2 = Account.objects.create(auth_user_id=uuid.uuid4(), email="morador2@exemplo.com", full_name="Morador Dois")

        res1 = Resident.objects.create(condominium=condo, account=acc1, full_name=acc1.full_name)
        res2 = Resident.objects.create(condominium=condo, account=acc2, full_name=acc2.full_name)

        mb1 = UnitMembership.objects.create(
            condominium=condo, resident=res1, unit=unit, category="proprietario_residente"
        )
        mb2 = UnitMembership.objects.create(
            condominium=condo, resident=res2, unit=unit, category="dependente"
        )

        memberships = UnitMembership.objects.filter(unit=unit)
        assert memberships.count() == 2
        assert {m.resident.full_name for m in memberships} == {"Morador Um", "Morador Dois"}

    def test_ca_14_pessoa_com_multiplas_unidades_tem_vinculos_separados(self):
        """CA-14: Pessoa com várias unidades possui conta única e vínculos distintos."""
        condo = Condominium.objects.create(name="Residencial Jardins")
        unit_a = Unit.objects.create(condominium=condo, code="101")
        unit_b = Unit.objects.create(condominium=condo, code="102")

        acc = Account.objects.create(auth_user_id=uuid.uuid4(), email="investidor@exemplo.com", full_name="Investidor Silva")
        resident = Resident.objects.create(condominium=condo, account=acc, full_name=acc.full_name)

        UnitMembership.objects.create(condominium=condo, resident=resident, unit=unit_a, category="proprietario_nao_residente")
        UnitMembership.objects.create(condominium=condo, resident=resident, unit=unit_b, category="proprietario_nao_residente")

        # Uma única conta de autenticação
        assert Account.objects.filter(email="investidor@exemplo.com").count() == 1
        # Dois vínculos distintos de unidade
        assert UnitMembership.objects.filter(resident=resident).count() == 2

    def test_ca_12_ca_15_validacao_auditada_de_vinculo_documental(self):
        """CA-12 & CA-15: Validação documental auditada com trilha imutável."""
        condo = Condominium.objects.create(name="Condomínio Parque")
        unit = Unit.objects.create(condominium=condo, code="401")

        admin_acc = Account.objects.create(auth_user_id=uuid.uuid4(), email="sindico@parque.com", full_name="Síndico João")
        morador_acc = Account.objects.create(auth_user_id=uuid.uuid4(), email="morador@parque.com", full_name="Moradora Ana")
        resident = Resident.objects.create(condominium=condo, account=morador_acc, full_name=morador_acc.full_name)

        membership = UnitMembership.objects.create(
            condominium=condo,
            resident=resident,
            unit=unit,
            category="inquilino",
            verification_status="pendente"
        )

        # Validação com auditoria
        updated_membership = MembershipVerificationService.verify_membership(
            condominium_id=condo.id,
            membership_id=membership.id,
            new_status="validado",
            method="documento",
            reason="Apresentado contrato de locação com firmas reconhecidas",
            actor_account_id=admin_acc.id
        )

        assert updated_membership.verification_status == "validado"
        assert updated_membership.reviewed_by_id == admin_acc.id

        # Verifica se o evento de auditoria foi gravado
        event = MembershipVerificationEvent.objects.get(membership=membership)
        assert event.new_status == "validado"
        assert event.previous_status == "pendente"
        assert event.method == "documento"
        assert "contrato de locação" in event.reason

    def test_ca_06_conta_em_outro_condominio_nao_e_revelada(self):
        """CA-06: Consulta em um condomínio nunca revela ou enumera contas/residentes de outro condomínio."""
        condo_a = Condominium.objects.create(name="Condomínio Alpha")
        condo_b = Condominium.objects.create(name="Condomínio Beta")

        acc_global = Account.objects.create(auth_user_id=uuid.uuid4(), email="morador.multi@exemplo.com", full_name="Morador Multi")

        # Vinculado apenas no condomínio Alpha
        Resident.objects.create(condominium=condo_a, account=acc_global, full_name=acc_global.full_name)

        # Busca no condomínio Beta não deve retornar nenhum residente nem enumerar existência
        residents_beta = Resident.objects.filter(condominium=condo_b)
        assert residents_beta.count() == 0
        assert not residents_beta.filter(account=acc_global).exists()

    def test_ca_16_mudanca_de_unidade_preserva_historico(self):
        """CA-16: Mudança de unidade encerra vínculo anterior mas preserva histórico e eventos."""
        condo = Condominium.objects.create(name="Condomínio Estrela")
        unit_antiga = Unit.objects.create(condominium=condo, code="101")
        unit_nova = Unit.objects.create(condominium=condo, code="202")

        acc = Account.objects.create(auth_user_id=uuid.uuid4(), email="joao@estrela.com", full_name="João Silva")
        resident = Resident.objects.create(condominium=condo, account=acc, full_name=acc.full_name)

        # Vínculo anterior
        mb_antigo = UnitMembership.objects.create(
            condominium=condo, resident=resident, unit=unit_antiga, category="inquilino", verification_status="validado"
        )
        # Evento de validação na unidade antiga
        MembershipVerificationEvent.objects.create(
            condominium=condo, membership=mb_antigo, previous_status="pendente", new_status="validado",
            method="documento", reason="Contrato antigo", actor_account_id=acc.id
        )

        # Encerramento do vínculo antigo
        mb_antigo.membership_status = "ended"
        mb_antigo.ended_at = timezone.now()
        mb_antigo.save()

        # Novo vínculo na nova unidade
        mb_novo = UnitMembership.objects.create(
            condominium=condo, resident=resident, unit=unit_nova, category="proprietario_residente", verification_status="pendente"
        )

        # Histórico da unidade antiga preservado
        assert UnitMembership.objects.filter(unit=unit_antiga, resident=resident).count() == 1
        assert MembershipVerificationEvent.objects.filter(membership=mb_antigo).count() == 1
        # Novo vínculo ativo
        assert mb_novo.membership_status == "active"
        assert mb_novo.unit.code == "202"

    def test_ca_33_auditoria_de_acesso_a_dados_de_identidade(self):
        """CA-33: Consulta de dados de morador registra evento com justificativa."""
        actor = Account.objects.create(auth_user_id=uuid.uuid4(), email="auditor@exemplo.com", full_name="Auditor")
        target_id = uuid.uuid4()

        event = IdentityAuditService.log_access(
            actor_account_id=actor.id,
            target_type="resident",
            target_id=target_id,
            purpose="Verificação de elegibilidade para comissão de regimento"
        )

        assert event.actor_account_id == actor.id
        assert event.target_type == "resident"
        assert "elegibilidade" in event.purpose


@pytest.mark.django_db
class TestPhase1APIEndpoints:
    """Testes dos controladores REST da API v1."""

    def test_fluxo_completo_api_estrutura_e_cadastros(self):
        client = Client()

        # 1. Criação do Condomínio via API
        resp = client.post('/api/v1/condominiums', {
            "name": "Condomínio Jardins da Serra",
            "cnpj": "12.345.678/0001-99",
            "timezone": "America/Sao_Paulo"
        }, content_type='application/json')
        assert resp.status_code == 201
        condo_data = resp.json()
        condo_id = condo_data['id']

        # 2. Criação de Torre/Bloco
        resp_b = client.post(f'/api/v1/condominiums/{condo_id}/buildings', {
            "code": "T1",
            "name": "Torre Primavera",
            "kind": "tower"
        }, content_type='application/json')
        assert resp_b.status_code == 201
        b_id = resp_b.json()['id']

        # 3. Criação de Unidade
        resp_u = client.post(f'/api/v1/condominiums/{condo_id}/units', {
            "building_id": b_id,
            "code": "101",
            "floor_label": "1º Andar"
        }, content_type='application/json')
        assert resp_u.status_code == 201
        unit_id = resp_u.json()['id']

        # 4. Pré-cadastro manual de morador (CA-02)
        resp_r = client.post(f'/api/v1/condominiums/{condo_id}/registrations', {
            "unit_id": unit_id,
            "full_name": "Maria Joaquina",
            "relationship": "proprietario_residente",
            "email": "maria@exemplo.com"
        }, content_type='application/json')
        assert resp_r.status_code == 201
        assert resp_r.json()['status'] == 'pendente'

        # 5. Listagem de condomínios
        resp_list = client.get('/api/v1/condominiums')
        assert resp_list.status_code == 200
        assert len(resp_list.json()) >= 1

    def test_resident_registration_crud_and_lifecycle(self):
        """Validação completa de criação, listagem com unit_code, edição e exclusão de pré-cadastros."""
        client = Client()
        condo = Condominium.objects.create(name="Residencial das Orquídeas", cnpj="99.888.777/0001-66")
        condo_other = Condominium.objects.create(name="Outro Condomínio", cnpj="11.222.333/0001-55")
        unit1 = Unit.objects.create(condominium=condo, code="402B")
        unit2 = Unit.objects.create(condominium=condo, code="501A")

        # 1. Criação de pré-cadastro
        resp_create = client.post(f'/api/v1/condominiums/{condo.id}/registrations', {
            "unit_id": str(unit1.id),
            "full_name": "Ana Clara Siqueira",
            "relationship": "proprietario_residente",
            "phone_e164": "+5511988887777",
            "email": "ana.clara@exemplo.com",
            "notes": "Mudança prevista para o fim do mês"
        }, content_type='application/json')
        assert resp_create.status_code == 201
        reg_data = resp_create.json()
        reg_id = reg_data['id']
        assert reg_data['full_name'] == "Ana Clara Siqueira"
        assert reg_data['unit_code'] == "402B"
        assert reg_data['status'] == "pendente"

        # 2. Listagem de pré-cadastros (verifica presença do registro e do unit_code)
        resp_list = client.get(f'/api/v1/condominiums/{condo.id}/registrations')
        assert resp_list.status_code == 200
        items = resp_list.json()
        assert len(items) == 1
        assert items[0]['id'] == reg_id
        assert items[0]['unit_code'] == "402B"
        assert items[0]['full_name'] == "Ana Clara Siqueira"

        # 3. Consulta de detalhe
        resp_get = client.get(f'/api/v1/condominiums/{condo.id}/registrations/{reg_id}')
        assert resp_get.status_code == 200
        assert resp_get.json()['full_name'] == "Ana Clara Siqueira"

        # 4. Atualização parcial (PATCH)
        resp_patch = client.patch(f'/api/v1/condominiums/{condo.id}/registrations/{reg_id}', {
            "full_name": "Ana Clara Siqueira de Souza",
            "unit_id": str(unit2.id),
            "phone_e164": "+5511977776666"
        }, content_type='application/json')
        assert resp_patch.status_code == 200
        patched = resp_patch.json()
        assert patched['full_name'] == "Ana Clara Siqueira de Souza"
        assert patched['unit_code'] == "501A"
        assert patched['phone_e164'] == "+5511977776666"

        # 5. Isolamento Multi-tenant (condomínio incorreto não acessa)
        resp_cross = client.get(f'/api/v1/condominiums/{condo_other.id}/registrations/{reg_id}')
        assert resp_cross.status_code == 404

        # 6. Exclusão do pré-cadastro
        resp_del = client.delete(f'/api/v1/condominiums/{condo.id}/registrations/{reg_id}')
        assert resp_del.status_code == 204

        # Confirma que foi excluído
        resp_get_after = client.get(f'/api/v1/condominiums/{condo.id}/registrations/{reg_id}')
        assert resp_get_after.status_code == 404
