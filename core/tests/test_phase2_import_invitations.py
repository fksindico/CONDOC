"""
Testes Automatizados da Fase 2 — Importação Cadastral e Convites de Acesso
Critérios homologados: CA-03 a CA-11, CA-43; V21-06 a V21-25; ADR-003, ADR-004
"""
import io
import uuid
import pytest
from datetime import timedelta
from django.test import Client
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    ResidentRegistration,
    Resident,
    UnitMembership,
    MembershipVerificationEvent,
    ImportBatch,
    ImportRow,
    AccessInvitation,
    InvitationRedemption,
    IdempotencyRecord,
)
from application.imports.services import ImportService
from application.invitations.services import InvitationService
from application.common.idempotency import IdempotencyService
from domain.imports.exceptions import (
    FormulaInjectionDetectedError,
    ImportPreviewOutdatedError,
    UnresolvedConflictError,
    UnknownUnitError,
    IdempotencyConflictError,
)
from domain.invitations.exceptions import (
    InvitationExpiredOrExhaustedError,
    InvitationRevokedError,
    InvalidExpectedContactError,
)

@pytest.fixture
def base_condominium_and_structure():
    """Fixture que provisiona um condomínio com 1 torre e 3 unidades para testes."""
    condo = Condominium.objects.create(name="Residencial Bosque das Águas", cnpj="12.345.678/0001-90")
    building = Building.objects.create(condominium=condo, code="T1", name="Torre das Águas")
    unit101 = Unit.objects.create(condominium=condo, building=building, code="0101")
    unit102 = Unit.objects.create(condominium=condo, building=building, code="0102")
    unit201 = Unit.objects.create(condominium=condo, building=building, code="0201")
    admin = Account.objects.create(auth_user_id=uuid.uuid4(), email="admin@bosque.com", full_name="Administrador do Lote")
    return {
        "condo": condo,
        "building": building,
        "units": [unit101, unit102, unit201],
        "admin": admin
    }


@pytest.mark.django_db
class TestPhase2ImportBatchLifecycle:
    """Testes da máquina de estados, proteção de fórmulas e integridade da importação."""

    def test_ca_03_v21_06_upload_cria_lote_sem_alterar_cadastros(self, base_condominium_and_structure):
        """CA-03 & V21-06: Upload de arquivo cria lote e linhas sem modificar a base cadastral."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]

        csv_content = (
            "Nome;Torre/Bloco;Unidade;Telefone;Email;Relação\n"
            "Carlos Drummond;T1;0101;+5511999990001;carlos@exemplo.com;proprietario_residente\n"
            "Clarice Lispector;T1;0102;+5511999990002;clarice@exemplo.com;inquilino\n"
        ).encode('utf-8')

        file_obj = io.BytesIO(csv_content)
        batch = ImportService.create_batch_from_file(
            condominium_id=condo.id,
            file_obj=file_obj,
            actor_id=admin.id,
            file_name="moradores.csv"
        )

        assert batch.status == "awaiting_review"
        assert batch.rows.count() == 2
        # INVARIANTE: Nenhum cadastro prévio ou conta foi gerada antes da confirmação explícita
        assert ResidentRegistration.objects.filter(condominium=condo).count() == 0
        assert Account.objects.filter(email="carlos@exemplo.com").count() == 0

    def test_v21_07_formula_injection_rejeitada(self, base_condominium_and_structure):
        """V21-07: Fórmulas maliciosas disfarçadas em células são bloqueadas (CWE-1236)."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]

        malicious_csv = (
            "Nome;Torre/Bloco;Unidade;Telefone;Email;Relação\n"
            "=cmd|' /C calc'!A0;T1;0101;+5511999990001;malicious@exemplo.com;inquilino\n"
        ).encode('utf-8')

        file_obj = io.BytesIO(malicious_csv)
        with pytest.raises(FormulaInjectionDetectedError):
            ImportService.create_batch_from_file(
                condominium_id=condo.id,
                file_obj=file_obj,
                actor_id=admin.id,
                file_name="malicious.csv"
            )

    def test_v21_08_preservacao_de_zeros_iniciais(self, base_condominium_and_structure):
        """V21-08: Zeros à esquerda em unidades e blocos são preservados rigorosamente."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]

        csv_content = (
            "Nome;Torre/Bloco;Unidade;Telefone;Email;Relação\n"
            "Machado de Assis;T1;0101;+5511999990003;machado@exemplo.com;proprietario_residente\n"
        ).encode('utf-8')

        file_obj = io.BytesIO(csv_content)
        batch = ImportService.create_batch_from_file(
            condominium_id=condo.id,
            file_obj=file_obj,
            actor_id=admin.id,
            file_name="zeros.csv"
        )

        row = batch.rows.first()
        assert row.normalized_data["unidade"] == "0101"
        assert row.normalized_data["unidade"] != "101"

    def test_ca_04_unidade_desconhecida_nao_e_criada_silenciosamente(self, base_condominium_and_structure):
        """CA-04: Unidade não cadastrada vira erro impeditivo e bloqueia aplicação silenciosa."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]

        csv_content = (
            "Nome;Torre/Bloco;Unidade;Telefone;Email;Relação\n"
            "Cecília Meireles;T1;9999;+5511999990004;cecilia@exemplo.com;inquilino\n"
        ).encode('utf-8')

        file_obj = io.BytesIO(csv_content)
        batch = ImportService.create_batch_from_file(
            condominium_id=condo.id,
            file_obj=file_obj,
            actor_id=admin.id,
            file_name="unidade_inexistente.csv"
        )

        row = batch.rows.first()
        assert row.classification == "unidade_desconhecida"
        assert row.selected is False
        assert any(i["code"] == "UNKNOWN_UNIT" for i in row.issues)

        # Não cria a unidade silenciosamente
        assert Unit.objects.filter(condominium=condo, code="9999").count() == 0

        # Tentativa de confirmar sem resolver deve falhar
        with pytest.raises(UnresolvedConflictError):
            ImportService.update_row_resolution(
                condominium_id=condo.id,
                batch_id=batch.id,
                row_id=row.id,
                selected=True,
                action='create_registration',
                actor_id=admin.id
            )

    def test_v21_09_v21_13_concorrencia_otimista_e_revisao_desatualizada(self, base_condominium_and_structure):
        """V21-09 & V21-13: Alteração de mapeamento incrementa revisão; revisão antiga é rejeitada."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]

        csv_content = (
            "Nome;Torre/Bloco;Unidade;Telefone;Email;Relação\n"
            "Guimarães Rosa;T1;0101;+5511999990005;rosa@exemplo.com;proprietario_residente\n"
        ).encode('utf-8')

        file_obj = io.BytesIO(csv_content)
        batch = ImportService.create_batch_from_file(
            condominium_id=condo.id,
            file_obj=file_obj,
            actor_id=admin.id,
            file_name="revisao.csv"
        )

        initial_rev = batch.revision
        # Atualiza mapping
        updated_batch = ImportService.update_mapping(
            condominium_id=condo.id,
            batch_id=batch.id,
            mapping_data={"columns": {"nome": "Nome", "unidade": "Unidade"}},
            actor_id=admin.id
        )
        assert updated_batch.revision == initial_rev + 1

        # Tentativa de confirmação com a revisão inicial antiga (If-Match falho)
        with pytest.raises(ImportPreviewOutdatedError):
            ImportService.confirm_and_apply_batch(
                condominium_id=condo.id,
                batch_id=batch.id,
                expected_revision=initial_rev,
                actor_id=admin.id
            )

    def test_v21_17_v21_18_confirmacao_cria_apenas_registros_previos(self, base_condominium_and_structure):
        """V21-17 & V21-18: Aplicação do lote cria pré-cadastros SEM enviar convites e SEM criar contas."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]

        csv_content = (
            "Nome;Torre/Bloco;Unidade;Telefone;Email;Relação\n"
            "Graciliano Ramos;T1;0101;+5511999990006;graciliano@exemplo.com;proprietario_residente\n"
        ).encode('utf-8')

        file_obj = io.BytesIO(csv_content)
        batch = ImportService.create_batch_from_file(
            condominium_id=condo.id,
            file_obj=file_obj,
            actor_id=admin.id,
            file_name="aplicar.csv"
        )

        # Confirma com a revisão correta
        result = ImportService.confirm_and_apply_batch(
            condominium_id=condo.id,
            batch_id=batch.id,
            expected_revision=batch.revision,
            actor_id=admin.id
        )

        assert result["status"] == "completed"
        assert result["applied_operations"]["created_registrations"] == 1
        assert result["sends_invitations"] is False
        assert result["creates_credentials"] is False

        # Verifica criação do pré-cadastro
        reg = ResidentRegistration.objects.get(condominium=condo, email="graciliano@exemplo.com")
        assert reg.status == "pendente"
        assert reg.source == "importacao"

        # Garante que ZERO contas e ZERO convites foram disparados
        assert Account.objects.filter(email="graciliano@exemplo.com").count() == 0
        assert AccessInvitation.objects.filter(condominium=condo).count() == 0


@pytest.mark.django_db
class TestPhase2AccessInvitations:
    """Testes dos convites de acesso, segurança criptográfica e resgates controlados."""

    def test_ca_10_v21_19_get_inspecao_nao_consome_nem_autentica(self, base_condominium_and_structure):
        """CA-10 & V21-19: GET no convite NUNCA consome nem autentica e não altera contadores."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]
        unit = base_condominium_and_structure["units"][0]

        invitation, raw_token = InvitationService.create_invitation(
            condominium_id=condo.id,
            kind="unidade_fixa",
            created_by_id=admin.id,
            expires_at=timezone.now() + timedelta(days=7),
            target_unit_id=unit.id,
            max_redemptions=2
        )

        # Inspeciona via GET
        inspect_data = InvitationService.inspect_invitation(raw_token)
        assert inspect_data["valid"] is True
        assert inspect_data["condominium_name"] == condo.name
        assert inspect_data["unit_label"] == unit.code

        # Garante que o contador de resgates continua zero e o status ativo
        invitation.refresh_from_db()
        assert invitation.redemption_count == 0
        assert invitation.status == "ativo"

    def test_ca_07_convite_por_unidade_fixa_mantem_contas_individuais(self, base_condominium_and_structure):
        """CA-07: Convite por unidade fixa a unidade mas mantém contas de moradores separadas."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]
        unit = base_condominium_and_structure["units"][0]

        invitation, raw_token = InvitationService.create_invitation(
            condominium_id=condo.id,
            kind="unidade_fixa",
            created_by_id=admin.id,
            expires_at=timezone.now() + timedelta(days=7),
            target_unit_id=unit.id,
            max_redemptions=2
        )

        # Morador 1 resgata
        acc1 = Account.objects.create(auth_user_id=uuid.uuid4(), email="morador.a@exemplo.com", full_name="Morador A")
        res1 = InvitationService.redeem_invitation(raw_token=raw_token, account_id=acc1.id)
        assert res1["status"] == "resgatado"

        # Morador 2 resgata com o mesmo convite
        acc2 = Account.objects.create(auth_user_id=uuid.uuid4(), email="morador.b@exemplo.com", full_name="Morador B")
        res2 = InvitationService.redeem_invitation(raw_token=raw_token, account_id=acc2.id)
        assert res2["status"] == "resgatado"

        # Cada um possui seu vínculo e sua conta
        memberships = UnitMembership.objects.filter(unit=unit)
        assert memberships.count() == 2
        assert {m.resident.account.email for m in memberships} == {"morador.a@exemplo.com", "morador.b@exemplo.com"}

        # Convite agora está esgotado
        invitation.refresh_from_db()
        assert invitation.status == "esgotado"
        assert invitation.redemption_count == 2

    def test_ca_08_ca_15_convite_compartilhado_cria_vinculo_pendente(self, base_condominium_and_structure):
        """CA-08 & CA-15: Convite compartilhado/amplo NÃO valida residência; cria vínculo pendente."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]
        unit = base_condominium_and_structure["units"][1]

        invitation, raw_token = InvitationService.create_invitation(
            condominium_id=condo.id,
            kind="amplo",
            created_by_id=admin.id,
            expires_at=timezone.now() + timedelta(days=7),
            target_unit_id=unit.id,
            max_redemptions=10
        )

        acc = Account.objects.create(auth_user_id=uuid.uuid4(), email="morador.amplo@exemplo.com", full_name="Morador Amplo")
        res = InvitationService.redeem_invitation(raw_token=raw_token, account_id=acc.id)

        # O vínculo nasce PENDENTE de conferência documental
        assert res["verification_status"] == "pendente"
        membership = UnitMembership.objects.get(id=res["membership_id"])
        assert membership.verification_status == "pendente"

    def test_ca_09_v21_22_individual_preconferido_exige_contato_previsto(self, base_condominium_and_structure):
        """CA-09 & V21-22: Convite individual pré-conferido exige conferência estrita do contato previsto."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]
        unit = base_condominium_and_structure["units"][2]

        reg = ResidentRegistration.objects.create(
            condominium=condo,
            unit=unit,
            full_name="Castro Alves",
            email="castro.alves@exemplo.com",
            relationship="proprietario_residente"
        )

        invitation, raw_token = InvitationService.create_invitation(
            condominium_id=condo.id,
            kind="individual_preconferido",
            created_by_id=admin.id,
            expires_at=timezone.now() + timedelta(days=7),
            target_registration_id=reg.id,
            expected_contact="castro.alves@exemplo.com"
        )

        acc = Account.objects.create(auth_user_id=uuid.uuid4(), email="outro.email@exemplo.com", full_name="Castro Alves")

        # 1. Tentativa com contato errado é rejeitada
        with pytest.raises(InvalidExpectedContactError):
            InvitationService.redeem_invitation(
                raw_token=raw_token,
                account_id=acc.id,
                provided_contact="errado@exemplo.com"
            )

        # 2. Resgate com contato confirmado bate e nasce validado
        res = InvitationService.redeem_invitation(
            raw_token=raw_token,
            account_id=acc.id,
            provided_contact="castro.alves@exemplo.com"
        )
        assert res["verification_status"] == "validado"

        # Evento de auditoria registrado
        mb = UnitMembership.objects.get(id=res["membership_id"])
        event = MembershipVerificationEvent.objects.get(membership=mb)
        assert event.new_status == "validado"
        assert event.method == "individual_preconferido"

    def test_ca_11_v21_23_v21_24_revogacao_bloqueia_sem_apagar_ativados(self, base_condominium_and_structure):
        """CA-11, V21-23 & V21-24: Revogação impede novos resgates sem suspender perfis já ativados."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]
        unit = base_condominium_and_structure["units"][0]

        invitation, raw_token = InvitationService.create_invitation(
            condominium_id=condo.id,
            kind="unidade_fixa",
            created_by_id=admin.id,
            expires_at=timezone.now() + timedelta(days=7),
            target_unit_id=unit.id,
            max_redemptions=5
        )

        # 1º resgate bem-sucedido
        acc1 = Account.objects.create(auth_user_id=uuid.uuid4(), email="ativado@exemplo.com", full_name="Morador Ativado")
        res1 = InvitationService.redeem_invitation(raw_token=raw_token, account_id=acc1.id)
        assert res1["status"] == "resgatado"

        # Administrador revoga o convite
        InvitationService.revoke_invitation(
            condominium_id=condo.id,
            invitation_id=invitation.id,
            actor_id=admin.id,
            reason="Convite divulgado em canal público indevido"
        )

        # 2ª tentativa de resgate é bloqueada
        acc2 = Account.objects.create(auth_user_id=uuid.uuid4(), email="novo@exemplo.com", full_name="Novo Morador")
        with pytest.raises(InvitationRevokedError):
            InvitationService.redeem_invitation(raw_token=raw_token, account_id=acc2.id)

        # O perfil e o vínculo já ativados permanecem preservados
        mb_ativado = UnitMembership.objects.get(id=res1["membership_id"])
        assert mb_ativado.membership_status == "active"


@pytest.mark.django_db
class TestPhase2IdempotencyAndAPIRoutes:
    """Testes de idempotência operacional e integração via controladores REST."""

    def test_ca_05_v21_14_v21_15_idempotencia_operacional(self, base_condominium_and_structure):
        """CA-05, V21-14 & V21-15: Chave de idempotência retorna resultado cacheado ou 409 em conflito."""
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]

        payload_original = {"action": "confirm", "revision": 2}
        idempotency_key = "idemp_test_key_123"

        def _dummy_handler():
            return 200, {"success": True, "token": "abc"}

        # 1. Primeira execução: processa e grava
        code1, body1 = IdempotencyService.execute_with_idempotency(
            operation="test_op",
            key=idempotency_key,
            payload=payload_original,
            tenant_id=condo.id,
            actor_account_id=admin.id,
            handler=_dummy_handler
        )
        assert code1 == 200
        assert body1["success"] is True

        # 2. Reenvio com o mesmo payload: retorna exatamente a mesma resposta (CA-05, V21-14)
        code2, body2 = IdempotencyService.execute_with_idempotency(
            operation="test_op",
            key=idempotency_key,
            payload=payload_original,
            tenant_id=condo.id,
            actor_account_id=admin.id,
            handler=_dummy_handler
        )
        assert code2 == 200
        assert body2 == body1

        # 3. Reenvio com payload diferente: gera 409 Conflict (V21-15)
        payload_divergente = {"action": "confirm", "revision": 3}
        with pytest.raises(IdempotencyConflictError):
            IdempotencyService.execute_with_idempotency(
                operation="test_op",
                key=idempotency_key,
                payload=payload_divergente,
                tenant_id=condo.id,
                actor_account_id=admin.id,
                handler=_dummy_handler
            )

    def test_fluxo_completo_api_importacao_e_convites(self, base_condominium_and_structure):
        """Fluxo REST completo da Fase 2: Upload, Prévia, Confirmação, Criação de Convite, Inspeção e Resgate."""
        client = Client()
        condo = base_condominium_and_structure["condo"]
        admin = base_condominium_and_structure["admin"]

        # 1. Download do Template CSV
        resp_tpl = client.get(f'/api/v1/condominiums/{condo.id}/resident-imports/template')
        assert resp_tpl.status_code == 200
        assert "text/csv" in resp_tpl['Content-Type']

        # 2. Upload multipart do arquivo
        csv_file = SimpleUploadedFile(
            "moradores_api.csv",
            (
                "Nome;Torre/Bloco;Unidade;Telefone;Email;Relação\n"
                "Monteiro Lobato;T1;0101;+5511999990007;monteiro@exemplo.com;proprietario_residente\n"
            ).encode('utf-8'),
            content_type="text/csv"
        )
        resp_upload = client.post(
            f'/api/v1/condominiums/{condo.id}/resident-imports',
            {"file": csv_file, "actor_account_id": str(admin.id)},
            format='multipart'
        )
        assert resp_upload.status_code == 202
        batch_id = resp_upload.json()['id']
        rev = resp_upload.json()['revision']

        # 3. Consulta da Prévia
        resp_prev = client.get(f'/api/v1/condominiums/{condo.id}/resident-imports/{batch_id}/preview')
        assert resp_prev.status_code == 200
        prev_data = resp_prev.json()
        assert prev_data['can_confirm'] is True
        assert prev_data['sends_invitations'] is False
        assert prev_data['creates_credentials'] is False

        # 4. Confirmação do Lote
        resp_conf = client.post(
            f'/api/v1/condominiums/{condo.id}/resident-imports/{batch_id}/confirm',
            {
                "expected_revision": rev,
                "acknowledge_selected_operations": True
            },
            content_type='application/json'
        )
        assert resp_conf.status_code in (200, 202), resp_conf.content

        # 5. Criação de Convite via API
        resp_inv = client.post(
            f'/api/v1/condominiums/{condo.id}/invitations',
            {
                "kind": "unidade_fixa",
                "target_unit_id": str(base_condominium_and_structure["units"][0].id),
                "expires_in_days": 5,
                "max_redemptions": 2
            },
            content_type='application/json'
        )
        assert resp_inv.status_code == 201
        token = resp_inv.json()['token']

        # 6. Inspeção pública via GET (CA-10: não consome nem autentica)
        resp_insp = client.get(f'/api/v1/access/invitations/inspect?token={token}')
        assert resp_insp.status_code == 200
        assert resp_insp.json()['valid'] is True

        # 7. Resgate controlado via POST
        resp_red = client.post(
            '/api/v1/access/invitations/redeem',
            {
                "token": token,
                "account_email": "leitor.novo@exemplo.com",
                "account_full_name": "Novo Leitor"
            },
            content_type='application/json'
        )
        assert resp_red.status_code == 200
        assert resp_red.json()['status'] == "resgatado"
