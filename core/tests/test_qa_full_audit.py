"""
Suíte Completa de Auditoria de QA e Cobertura Integral de Endpoints — CONDOC
Testa exaustivamente todas as rotas de api/v1/urls.py, validações de segurança,
isolamento multi-tenant, concorrência, cenários negativos e regras de negócio.
"""
import uuid
import json
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    Resident,
    UnitMembership,
    RoleAssignment,
    Project,
    Document,
    Provision,
    ProvisionRevision,
    DocumentSnapshot,
    SnapshotItem,
    OriginMapping,
    CrossReference,
    ConsultationCampaign,
    CampaignParticipant,
    Suggestion,
    SuggestionRevision,
    PublishedSuggestionRevision,
    ConsultativeAgreement,
    AgreementEvent,
    SuggestionIncorporation,
    ExportArtifact,
    ImportBatch,
    ImportRow,
    AccessInvitation,
)
from application.documents.services import (
    ProjectService,
    DocumentService,
    ProvisionService,
    SnapshotService,
)
from application.moderation.services import (
    CampaignService,
    SuggestionService,
    ModerationService,
)
from application.agreements.services import (
    AgreementService,
    IncorporationService,
)
from application.preservation.services import PreservationService


@pytest.fixture
def qa_context(db):
    """Cenário completo de QA com múltiplos condomínios, usuários, documentos e campanhas."""
    # Condomínio 1 (Principal)
    condo1 = Condominium.objects.create(name="Condomínio QA Central", cnpj="11.222.333/0001-44")
    b1 = Building.objects.create(condominium=condo1, code="TORRE_A", name="Torre Alpha")
    u101 = Unit.objects.create(condominium=condo1, building=b1, code="101", ideal_fraction=0.05)
    u102 = Unit.objects.create(condominium=condo1, building=b1, code="102", ideal_fraction=0.05)

    # Síndico ativo
    sindico_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="sindico.qa@condoc.com.br",
        full_name="Dr. Síndico QA"
    )
    RoleAssignment.objects.create(
        condominium=condo1,
        account=sindico_acc,
        role="sindico",
        status="active"
    )

    # Membro da Comissão (não síndico)
    comissao_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="membro.comissao@condoc.com.br",
        full_name="Paula Comissão"
    )
    RoleAssignment.objects.create(
        condominium=condo1,
        account=comissao_acc,
        role="comissao",
        status="active"
    )

    # Morador
    morador_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="morador.101@condoc.com.br",
        full_name="Marcos Morador"
    )
    res101 = Resident.objects.create(
        condominium=condo1,
        account=morador_acc,
        full_name=morador_acc.full_name,
        phone_e164="+5511987654321"
    )
    mb101 = UnitMembership.objects.create(
        condominium=condo1,
        resident=res101,
        unit=u101,
        category="proprietario_residente",
        verification_status="pendente",
        membership_status="active"
    )

    # Projeto e Documento
    proj1 = ProjectService.create_project(
        condominium_id=condo1.id,
        name="Projeto Revisão QA",
        coordinator_account_id=sindico_acc.id
    )
    doc1 = DocumentService.create_document(
        project_id=proj1.id,
        condominium_id=condo1.id,
        title="Regimento Interno QA 2026",
        type="regimento_interno"
    )
    prov1 = ProvisionService.create_provision(
        document_id=doc1.id,
        condominium_id=condo1.id,
        kind="artigo",
        label="Art. 1º",
        text="Norma inicial de conduta e convivência no condomínio.",
        author_account_id=sindico_acc.id
    )
    prov2 = ProvisionService.create_provision(
        document_id=doc1.id,
        condominium_id=condo1.id,
        kind="artigo",
        label="Art. 2º",
        text="Regras de utilização da área de lazer e churrasqueira.",
        author_account_id=sindico_acc.id
    )

    # Snapshot imutável
    snap1 = SnapshotService.create_snapshot(
        document_id=doc1.id,
        condominium_id=condo1.id,
        version_label="Snapshot QA v1.0",
        frozen_by_id=sindico_acc.id
    )

    # Campanha
    camp1 = CampaignService.create_campaign(
        condominium_id=condo1.id,
        project_id=proj1.id,
        snapshot_id=snap1.id,
        name="Consulta Pública QA"
    )

    # Participante
    part101 = CampaignService.register_participant(
        condominium_id=condo1.id,
        campaign_id=camp1.id,
        resident_id=res101.id,
        reference_membership_id=mb101.id,
        authorized_by_id=sindico_acc.id
    )

    # Condomínio 2 (Para testes de isolamento cruzado / Multi-tenant)
    condo2 = Condominium.objects.create(name="Condomínio Isolado B", cnpj="22.333.444/0001-55")

    return {
        "condo1": condo1,
        "condo2": condo2,
        "sindico_acc": sindico_acc,
        "comissao_acc": comissao_acc,
        "morador_acc": morador_acc,
        "resident": res101,
        "membership": mb101,
        "project": proj1,
        "document": doc1,
        "provision1": prov1,
        "provision2": prov2,
        "snapshot": snap1,
        "campaign": camp1,
        "participant": part101,
    }


# ==============================================================================
# 1. TESTES DE ESTRUTURA, MEMBRESIAS E VALIDAÇÃO (FASES 1 E 2)
# ==============================================================================

def test_qa_endpoint_auth_login_and_logout(qa_context):
    """Testa ciclo de autenticação BFF: login, persistência de sessão e logout."""
    client = APIClient()
    condo = qa_context['condo1']
    sindico = qa_context['sindico_acc']

    # 1. Login com conta de síndico
    resp_login = client.post(
        "/api/v1/auth/login",
        data={"email": sindico.email, "condominium_id": str(condo.id)},
        format="json"
    )
    assert resp_login.status_code == 200
    assert resp_login.data['authenticated'] is True
    assert "sindico" in resp_login.data['account']['roles']

    # 2. Inspeciona sessão ativa
    resp_session = client.get("/api/v1/auth/session")
    assert resp_session.status_code == 200
    assert resp_session.data['authenticated'] is True
    assert resp_session.data['account']['email'] == sindico.email

    # 3. Logout
    resp_logout = client.post("/api/v1/auth/logout")
    assert resp_logout.status_code == 200
    assert resp_logout.data['authenticated'] is False

    # 4. Sessão deve estar vazia após logout
    resp_after = client.get("/api/v1/auth/session")
    assert resp_after.status_code == 200
    assert resp_after.data['authenticated'] is False


def test_qa_endpoint_memberships_list(qa_context):
    """Testa listagem de memberships via GET /api/v1/condominiums/<id>/memberships."""
    client = APIClient()
    condo = qa_context['condo1']
    resp = client.get(f"/api/v1/condominiums/{condo.id}/memberships")
    assert resp.status_code == 200
    assert len(resp.data) >= 1
    assert resp.data[0]['resident_name'] == "Marcos Morador"


def test_qa_endpoint_resident_registrations_lifecycle(qa_context):
    """Testa ciclo de vida completo de pré-cadastros de moradores: criação, listagem com unidade, edição e exclusão."""
    client = APIClient()
    condo = qa_context['condo1']
    unit = qa_context['membership'].unit

    # 1. Cria pré-cadastro manual (CA-02: sem credencial automática)
    resp_create = client.post(
        f"/api/v1/condominiums/{condo.id}/registrations",
        data={
            "unit_id": str(unit.id),
            "full_name": "Juliana Silveira",
            "relationship": "inquilino",
            "phone_e164": "+5511988881234",
            "email": "juliana@exemplo.com"
        },
        format="json"
    )
    assert resp_create.status_code == 201
    reg_id = resp_create.data['id']
    assert resp_create.data['full_name'] == "Juliana Silveira"
    assert resp_create.data['unit_code'] == "101"
    assert resp_create.data['source'] == "manual"
    assert resp_create.data['status'] == "pendente"

    # 2. Listagem de pré-cadastros deve conter o registro com código da unidade
    resp_list = client.get(f"/api/v1/condominiums/{condo.id}/registrations")
    assert resp_list.status_code == 200
    reg_found = next((r for r in resp_list.data if r['id'] == reg_id), None)
    assert reg_found is not None
    assert reg_found['full_name'] == "Juliana Silveira"
    assert reg_found['unit_code'] == "101"

    # 3. Consulta de detalhe
    resp_get = client.get(f"/api/v1/condominiums/{condo.id}/registrations/{reg_id}")
    assert resp_get.status_code == 200
    assert resp_get.data['full_name'] == "Juliana Silveira"

    # 4. Edição (PATCH) do pré-cadastro
    resp_patch = client.patch(
        f"/api/v1/condominiums/{condo.id}/registrations/{reg_id}",
        data={"full_name": "Juliana Silveira Ramos", "phone_e164": "+5511999990000"},
        format="json"
    )
    assert resp_patch.status_code == 200
    assert resp_patch.data['full_name'] == "Juliana Silveira Ramos"
    assert resp_patch.data['phone_e164'] == "+5511999990000"

    # 5. Exclusão do pré-cadastro
    resp_del = client.delete(f"/api/v1/condominiums/{condo.id}/registrations/{reg_id}")
    assert resp_del.status_code == 204

    # Confirma que não existe mais
    resp_after = client.get(f"/api/v1/condominiums/{condo.id}/registrations/{reg_id}")
    assert resp_after.status_code == 404


def test_qa_endpoint_membership_verify_action(qa_context):
    """Testa validação documental de vínculo com método e motivo via POST /verify (CA-12, CA-15)."""
    client = APIClient()
    condo = qa_context['condo1']
    mb = qa_context['membership']

    # 1. Tentativa com motivo menor que 5 caracteres deve ser rejeitada
    resp_invalid = client.post(
        f"/api/v1/condominiums/{condo.id}/memberships/{mb.id}/verify",
        data={"new_status": "validado", "method": "documento", "reason": "ok"},
        format="json"
    )
    assert resp_invalid.status_code == 400

    # 2. Validação regular com motivo adequado
    resp_valid = client.post(
        f"/api/v1/condominiums/{condo.id}/memberships/{mb.id}/verify",
        data={
            "new_status": "validado",
            "method": "documento",
            "reason": "Escritura pública de compra e venda devidamente conferida."
        },
        format="json"
    )
    assert resp_valid.status_code == 200
    assert resp_valid.data['verification_status'] == "validado"


def test_qa_endpoint_roles_list_and_create(qa_context):
    """Testa listagem e atribuição de papéis via /api/v1/condominiums/<id>/roles (CA-28)."""
    client = APIClient()
    condo = qa_context['condo1']
    acc = qa_context['morador_acc']

    # 1. Listagem de papéis
    resp_list = client.get(f"/api/v1/condominiums/{condo.id}/roles")
    assert resp_list.status_code == 200
    assert len(resp_list.data) >= 2

    # 2. Atribuição de novo papel
    resp_post = client.post(
        f"/api/v1/condominiums/{condo.id}/roles",
        data={"account_id": str(acc.id), "role": "conselho"},
        format="json"
    )
    assert resp_post.status_code == 201
    assert resp_post.data['role'] == "conselho"


def test_qa_endpoint_invitation_revoke_action(qa_context):
    """Testa revogação de convite via POST /invitations/<id>/revoke com justificativa (CA-11)."""
    client = APIClient()
    condo = qa_context['condo1']

    # Cria convite
    resp_create = client.post(
        f"/api/v1/condominiums/{condo.id}/invitations",
        data={"kind": "amplo", "expires_in_days": 5, "max_redemptions": 10},
        format="json"
    )
    assert resp_create.status_code == 201
    invite_id = resp_create.data['id']

    # 1. Revogação com motivo curto deve falhar
    resp_fail = client.post(
        f"/api/v1/condominiums/{condo.id}/invitations/{invite_id}/revoke",
        data={"reason": "123"},
        format="json"
    )
    assert resp_fail.status_code == 400

    # 2. Revogação válida
    resp_ok = client.post(
        f"/api/v1/condominiums/{condo.id}/invitations/{invite_id}/revoke",
        data={"reason": "Cancelamento preventivo por vazamento de link."},
        format="json"
    )
    assert resp_ok.status_code == 200
    assert resp_ok.data['status'] in ('revogado', 'revoked')


# ==============================================================================
# 2. TESTES DE NÚCLEO DOCUMENTAL, EDICÃO E COMPARATIVOS (FASES 3 E 4)
# ==============================================================================

def test_qa_endpoint_document_detail(qa_context):
    """Testa recuperação detalhada de minuta via GET /documents/<id>."""
    client = APIClient()
    condo = qa_context['condo1']
    doc = qa_context['document']

    resp = client.get(f"/api/v1/condominiums/{condo.id}/documents/{doc.id}")
    assert resp.status_code == 200
    assert resp.data['title'] == "Regimento Interno QA 2026"
    assert resp.data['type'] == "regimento_interno"


def test_qa_endpoint_provisions_concurrency_conflict(qa_context):
    """
    Testa controle estrito de concorrência otimista (CA-23 / UI-14):
    tentativa de update com If-Match divergente resulta em HTTP 412 (Precondition Failed).
    """
    client = APIClient()
    condo = qa_context['condo1']
    prov = qa_context['provision1']

    # Envia If-Match incorreto
    client.credentials(HTTP_IF_MATCH='"etag_obsoleto_invalido"')
    resp = client.patch(
        f"/api/v1/condominiums/{condo.id}/provisions/{prov.id}",
        data={"text": "Alteração concorrente não autorizada."},
        format="json"
    )
    assert resp.status_code == 412
    assert "concorr" in resp.data['error'].lower() or "conflito" in resp.data['error'].lower()


def test_qa_endpoint_renumber_preview_and_apply(qa_context):
    """Testa prévia e aplicação de renumeração via /renumber (CA-22)."""
    client = APIClient()
    condo = qa_context['condo1']
    doc = qa_context['document']

    # 1. Preview da renumeração (GET)
    resp_prev = client.get(f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/renumber")
    assert resp_prev.status_code == 200
    assert "preview_items" in resp_prev.data
    assert resp_prev.data['total_articles_renumbered'] >= 2

    # 2. Aplicação da renumeração (POST)
    resp_apply = client.post(
        f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/renumber",
        data={"strategy": "renumeracao_automatica"},
        format="json"
    )
    assert resp_apply.status_code == 200
    assert resp_apply.data['status'] == "completed"


def test_qa_endpoint_export_clean_text_and_json(qa_context):
    """Testa exportação limpa preliminar nos formatos JSON e Text (CA-42)."""
    client = APIClient()
    condo = qa_context['condo1']
    doc = qa_context['document']

    # 1. Formato JSON (padrão)
    resp_json = client.get(f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/export/clean")
    assert resp_json.status_code == 200
    assert "provisions" in resp_json.data
    assert "disclaimer" in resp_json.data

    # 2. Formato Texto Corrido
    resp_txt = client.get(f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/export/clean?format=text")
    assert resp_txt.status_code == 200
    assert resp_txt['Content-Type'].startswith('text/plain')
    assert "Art. 1º" in resp_txt.content.decode('utf-8')


def test_qa_endpoint_export_depara_report(qa_context):
    """Testa exportação do relatório DePara estruturado via /export/depara (CA-20, CA-21)."""
    client = APIClient()
    condo = qa_context['condo1']
    doc = qa_context['document']

    resp = client.get(f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/export/depara")
    assert resp.status_code == 200
    assert "entries" in resp.data
    assert "total_entries" in resp.data


# ==============================================================================
# 3. TESTES DE CAMPANHA, SUGESTÕES, MODERAÇÃO E CONCORDÂNCIAS (FASES 5 E 6)
# ==============================================================================

def test_qa_endpoint_campaign_state_transitions(qa_context):
    """Testa ciclo de vida da campanha: open e close via /campaigns/<id>/<action>."""
    client = APIClient()
    condo = qa_context['condo1']
    camp = qa_context['campaign']

    # 1. Abrir campanha
    resp_open = client.post(f"/api/v1/condominiums/{condo.id}/campaigns/{camp.id}/open")
    assert resp_open.status_code == 200
    assert resp_open.data['state'] == "aberta"

    # 2. Snapshot congelado da campanha (GET)
    resp_snap_tree = client.get(f"/api/v1/condominiums/{condo.id}/campaigns/{camp.id}/document-snapshot")
    assert resp_snap_tree.status_code == 200
    assert len(resp_snap_tree.data) >= 2

    # 3. Encerrar campanha
    resp_close = client.post(f"/api/v1/condominiums/{condo.id}/campaigns/{camp.id}/close")
    assert resp_close.status_code == 200
    assert resp_close.data['state'] == "encerrada"


def test_qa_endpoint_suggestion_complement_and_my_suggestions(qa_context):
    """Testa envio de complemento (CA-30) e listagem de minhas sugestões (M09)."""
    client = APIClient()
    condo = qa_context['condo1']
    camp = qa_context['campaign']
    part = qa_context['participant']
    sindico = qa_context['sindico_acc']

    # Reabre campanha
    CampaignService.open_campaign(camp.id, condo.id)

    # 1. Envia sugestão primária
    sug_primaria = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Regulamentar horário de carga e descarga.",
        justification="Evitar congestionamento no acesso da garagem."
    )
    # Síndico publica
    ModerationService.authorize_publication(
        suggestion_id=sug_primaria.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico.id
    )

    # 2. Envia complemento via POST /suggestions/<id>/complements (CA-30)
    resp_comp = client.post(
        f"/api/v1/condominiums/{condo.id}/suggestions/{sug_primaria.id}/complements",
        data={
            "participant_id": str(part.id),
            "text": "Fixar tolerância máxima de 20 minutos para descarga.",
            "justification": "Complemento necessário para dar precisão à regra.",
            "category": "redacao"
        },
        format="json"
    )
    assert resp_comp.status_code == 201
    assert resp_comp.data['parent_published_suggestion_id'] == str(sug_primaria.id)

    # 3. Consulta minhas sugestões (M09) via GET /my-suggestions
    resp_my = client.get(f"/api/v1/condominiums/{condo.id}/my-suggestions?participant_id={part.id}")
    assert resp_my.status_code == 200
    assert len(resp_my.data) >= 2


def test_qa_endpoint_moderation_unauthorized_publication_rejection(qa_context):
    """
    Testa garantia de que membros sem papel de síndico recebem HTTP 403
    ao tentar autorizar publicação (CA-28, UI-24).
    """
    client = APIClient()
    condo = qa_context['condo1']
    camp = qa_context['campaign']
    part = qa_context['participant']

    CampaignService.open_campaign(camp.id, condo.id)

    sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Proposta para teste de autorização restrita.",
        justification="Justificativa de teste."
    )

    # Membro da comissão tenta publicar passando role=comissao -> Deve receber 403
    resp_denied = client.post(
        f"/api/v1/condominiums/{condo.id}/moderation/suggestions/{sug.id}/publish?role=comissao",
        data={"sanitized_text": "Texto sanitizado"},
        format="json"
    )
    assert resp_denied.status_code == 403
    assert resp_denied.data['code'] == "UNAUTHORIZED_PUBLICATION_SINDICO_ONLY"


# ==============================================================================
# 4. TESTES DE PRESERVAÇÃO, ASSEMBLEIA E INTEGRIDADE CRIPTOGRÁFICA (FASE 7)
# ==============================================================================

def test_qa_endpoint_assembly_view_strict_safeguards(qa_context):
    """Testa que o modo assembleia (/assembly-reading) não possui controles eleitorais (CA-45, UI-38)."""
    client = APIClient()
    condo = qa_context['condo1']
    doc = qa_context['document']

    resp = client.get(f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/assembly-reading")
    assert resp.status_code == 200
    assert resp.data['has_voting_module'] is False
    assert resp.data['reading_mode'] == "assembleia_somente_leitura"
    assert "NÃO realiza votação" in resp.data['disclaimer']


def test_qa_endpoint_manifest_tamper_detection(qa_context):
    """
    Testa que qualquer adulteração de conteúdo no pacote de exportação
    é detectada imediatamente via /artifacts/<id>/verify (HTTP 400).
    """
    client = APIClient()
    condo = qa_context['condo1']
    doc = qa_context['document']

    # Gera pacote
    resp_pkg = client.post(f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/export/package")
    assert resp_pkg.status_code == 201
    art_id = resp_pkg.data['artifact_id']

    raw_files = resp_pkg.data['files_content']
    files_map = {
        "minuta_limpa_final.json": json.dumps(raw_files['minuta_limpa_final.json'], sort_keys=True, indent=2, ensure_ascii=False),
        "minuta_limpa_final.txt": raw_files['minuta_limpa_final.txt'],
        "relatorio_depara_consolidado.json": json.dumps(raw_files['relatorio_depara_consolidado.json'], sort_keys=True, indent=2, ensure_ascii=False)
    }

    # 1. Verificação legítima -> 200
    resp_ok = client.post(
        f"/api/v1/condominiums/{condo.id}/artifacts/{art_id}/verify",
        data={"files_content_map": files_map},
        format="json"
    )
    assert resp_ok.status_code == 200
    assert resp_ok.data['integrity_verified'] is True

    # 2. Verificação com conteúdo adulterado -> 400
    tampered_map = dict(files_map)
    tampered_map["minuta_limpa_final.txt"] = "TEXTO ADULTERADO FRAUDULENTO"

    resp_tampered = client.post(
        f"/api/v1/condominiums/{condo.id}/artifacts/{art_id}/verify",
        data={"files_content_map": tampered_map},
        format="json"
    )
    assert resp_tampered.status_code == 400
    assert resp_tampered.data['code'] == "MANIFEST_INTEGRITY_TAMPERED"


# ==============================================================================
# 5. TESTES DE ISOLAMENTO ENTRE MÚLTIPLOS CONDOMÍNIOS (MULTI-TENANT LEAK)
# ==============================================================================

def test_qa_multi_tenant_isolation_boundary(qa_context):
    """
    Testa isolamento estrito entre condomínios:
    Condomínio B não consegue acessar documentos, campanhas ou sugestões do Condomínio A.
    """
    client = APIClient()
    condo_a = qa_context['condo1']
    condo_b = qa_context['condo2']
    doc_a = qa_context['document']
    camp_a = qa_context['campaign']

    # 1. Documento de A acessado com tenant B na URL deve retornar 404
    resp_doc = client.get(f"/api/v1/condominiums/{condo_b.id}/documents/{doc_a.id}")
    assert resp_doc.status_code == 404

    # 2. Campanha de A acessada com tenant B deve retornar 404
    resp_camp = client.get(f"/api/v1/condominiums/{condo_b.id}/campaigns/{camp_a.id}")
    assert resp_camp.status_code == 404

    # 3. Pacote de exportação de A no tenant B deve retornar 404
    resp_pkg = client.post(f"/api/v1/condominiums/{condo_b.id}/documents/{doc_a.id}/export/package")
    assert resp_pkg.status_code == 404


def test_qa_audit_logs_endpoint(qa_context):
    """Testa consulta da trilha imutável de eventos de auditoria (S21A)."""
    from infrastructure.models import IdentityAccessEvent
    client = APIClient()
    condo = qa_context['condo1']
    sindico = qa_context['sindico_acc']

    # Registra evento de auditoria
    IdentityAccessEvent.objects.create(
        condominium=condo,
        actor_account=sindico,
        target_type="resident_identity",
        target_id=str(uuid.uuid4()),
        purpose="Conferência de titularidade em diligência administrativa (LGPD)."
    )

    resp = client.get(f"/api/v1/condominiums/{condo.id}/audit-logs")
    assert resp.status_code == 200
    assert len(resp.data) >= 1
    event = resp.data[0]
    assert str(event['condominium_id']) == str(condo.id)
    assert event['actor_name'] == sindico.full_name
    assert "Conferência" in event['purpose']


def test_qa_transcription_confirm_and_correct_endpoints(qa_context):
    """Testa homologação e correção humana de transcrição OCR (CA-17, CA-18)."""
    from infrastructure.models import SourceFile, SourceTranscription
    client = APIClient()
    condo = qa_context['condo1']
    doc = qa_context['document']
    sindico = qa_context['sindico_acc']

    source_file = SourceFile.objects.create(
        condominium=condo,
        uploaded_by=sindico,
        storage_key="test/sample.pdf",
        filename="regimento_antigo.pdf",
        mime_type="application/pdf",
        size_bytes=1024,
        file_hash="fakehash123",
        state="ready"
    )

    transcription = SourceTranscription.objects.create(
        document=doc,
        condominium=condo,
        source_file=source_file,
        version=1,
        status="under_review",
        raw_text="Artigo 1. Texto bruto escaneado com erro de OCR",
        corrected_text="Artigo 1. Texto bruto escaneado com erro de OCR"
    )

    # 1. Confirmação (CA-17)
    resp_confirm = client.post(
        f"/api/v1/condominiums/{condo.id}/transcriptions/{transcription.id}/confirm",
        data={"corrected_text": "Art. 1º Texto conferido manualmente."},
        format="json"
    )
    assert resp_confirm.status_code == 200
    assert resp_confirm.data['status'] == "confirmed"
    assert resp_confirm.data['corrected_text'] == "Art. 1º Texto conferido manualmente."

    # 2. Correção gerando nova versão homologada (CA-18)
    resp_correct = client.post(
        f"/api/v1/condominiums/{condo.id}/transcriptions/{transcription.id}/correct",
        data={"corrected_text": "Art. 1º Texto com emenda corretiva de transcrição."},
        format="json"
    )
    assert resp_correct.status_code == 201
    assert resp_correct.data['version'] == 2
    assert resp_correct.data['status'] == "confirmed"

