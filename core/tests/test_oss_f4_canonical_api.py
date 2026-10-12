"""
Testes Automatizados de API para a Fase OSS-F4/F5 — Preflight, Instanciação e Exportação Canônica (CONDOC)
Valida:
1. Instanciação direta de templates OSS com novos UUIDs e hierarquia no DB.
2. Auditoria Preflight via endpoint HTTP.
3. Exportação Canônica Dual (DOCX + PDF) e geração de manifesto SHA-256.
4. Bloqueio automático de exportação quando preflight detecta inconsistência crítica.
"""
import uuid
import pytest
from rest_framework.test import APIClient
from django.utils import timezone

from infrastructure.models import (
    Condominium,
    Account,
    RoleAssignment,
    Project,
    Document,
    Provision,
    ProvisionRevision,
    ExportArtifact,
)


@pytest.fixture
def canonical_api_setup(db):
    """Cenário base para testes de endpoints canônicos."""
    condo = Condominium.objects.create(name="Residencial Ilhas Gregas")
    admin_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="sindico.canonico@condoc.local",
        full_name="Síndico Canônico"
    )
    RoleAssignment.objects.create(
        condominium=condo,
        account=admin_acc,
        role='sindico'
    )
    proj = Project.objects.create(
        condominium=condo,
        name="Projeto Reforma Regimento 2026",
        coordinator_account_id=admin_acc.id,
        status="em_andamento"
    )

    client = APIClient()
    client.force_authenticate(user=None)
    client.cookies['actor_account_id'] = str(admin_acc.id)
    client.cookies['condominium_id'] = str(condo.id)

    return {
        "condo": condo,
        "admin": admin_acc,
        "proj": proj,
        "client": client,
    }


def test_instantiate_template_endpoint_creates_document_and_provisions(canonical_api_setup):
    """Testa criação de Regimento Interno a partir do template OSS via endpoint HTTP."""
    client = canonical_api_setup["client"]
    condo = canonical_api_setup["condo"]
    proj = canonical_api_setup["proj"]

    url = f"/api/v1/condominiums/{condo.id}/projects/{proj.id}/documents/instantiate-template"
    payload = {
        "template_type": "regimento",
        "title": "Regimento Interno Oficial 2026"
    }

    response = client.post(url, payload, format='json')
    print("RESPONSE STATUS:", response.status_code, "DATA:", response.json())
    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "Regimento Interno Oficial 2026"
    assert data["type"] == "regimento_interno"
    assert data["provisions_count"] >= 30

    doc_id = uuid.UUID(data["id"])
    provisions_in_db = Provision.objects.filter(document_id=doc_id)
    assert provisions_in_db.count() == data["provisions_count"]

    # Verifica que revisões foram geradas e possuem labels normativos
    revisions = ProvisionRevision.objects.filter(document_id=doc_id)
    assert revisions.count() == data["provisions_count"]
    assert any("Art." in r.label for r in revisions)


def test_preflight_endpoint_validates_document_successfully(canonical_api_setup):
    """Testa auditoria prévia (Preflight) via endpoint HTTP para documento válido."""
    client = canonical_api_setup["client"]
    condo = canonical_api_setup["condo"]
    proj = canonical_api_setup["proj"]

    # 1. Instancia documento a partir do template
    instantiate_url = f"/api/v1/condominiums/{condo.id}/projects/{proj.id}/documents/instantiate-template"
    inst_resp = client.post(instantiate_url, {"template_type": "regimento"}, format='json')
    assert inst_resp.status_code == 201
    doc_id = inst_resp.json()["id"]

    # 2. Executa preflight
    preflight_url = f"/api/v1/condominiums/{condo.id}/documents/{doc_id}/preflight"
    response = client.post(preflight_url, {"profile": "clean_working"}, format='json')

    assert response.status_code == 200
    report = response.json()
    assert report["is_valid"] is True
    assert report["blocking_count"] == 0


def test_canonical_export_endpoint_generates_json_docx_and_pdf(canonical_api_setup):
    """Testa exportação canônica via endpoint nos formatos JSON, DOCX e PDF."""
    client = canonical_api_setup["client"]
    condo = canonical_api_setup["condo"]
    proj = canonical_api_setup["proj"]

    # Instancia documento
    inst_url = f"/api/v1/condominiums/{condo.id}/projects/{proj.id}/documents/instantiate-template"
    doc_id = client.post(inst_url, {"template_type": "regimento"}, format='json').json()["id"]

    export_url = f"/api/v1/condominiums/{condo.id}/documents/{doc_id}/export/canonical"

    # 1. Exportação JSON com manifesto
    resp_json = client.post(export_url, {"profile": "clean_working", "format": "json"}, format='json')
    print("EXPORT JSON RESP:", resp_json.json())
    assert resp_json.status_code == 200
    data = resp_json.json()
    assert data["success"] is True
    assert "artifacts" in data
    assert "docx" in data["artifacts"]
    assert len(data["artifacts"]["docx"]["sha256"]) == 64
    assert data["preflight_passed"] is True

    # 2. Verifica registro em app.export_artifacts
    artifact = ExportArtifact.objects.filter(document_id=doc_id).first()
    assert artifact is not None
    assert artifact.manifest_hash == data["artifacts"]["docx"]["sha256"]

    # 3. Download direto do DOCX
    resp_docx = client.post(export_url, {"profile": "clean_working", "format": "docx"}, format='json')
    assert resp_docx.status_code == 200
    assert resp_docx["Content-Type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(resp_docx.content) > 1000

    # 4. Download direto do PDF
    resp_pdf = client.post(export_url, {"profile": "clean_working", "format": "pdf"}, format='json')
    assert resp_pdf.status_code == 200
    assert resp_pdf["Content-Type"] == "application/pdf"
    assert len(resp_pdf.content) > 100


def test_canonical_export_blocks_when_preflight_fails(canonical_api_setup):
    """Garante que tentativa de exportação falha e retorna 400 se houver inconsistência estrutural."""
    client = canonical_api_setup["client"]
    condo = canonical_api_setup["condo"]
    proj = canonical_api_setup["proj"]

    # Cria documento com artigo órfão (sem caput)
    doc = Document.objects.create(
        project=proj,
        condominium=condo,
        title="Documento Inválido Sem Caput",
        type="regimento_interno"
    )
    art_prov = Provision.objects.create(
        id=uuid.uuid4(),
        document=doc,
        condominium=condo,
        kind="artigo"
    )
    ProvisionRevision.objects.create(
        provision=art_prov,
        document=doc,
        condominium=condo,
        revision_number=1,
        position=0,
        label="Art. 1º",
        text="",
        change_type="mantido",
        status="ativo"
    )
    # Não cria o Caput filho obrigatório

    export_url = f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/export/canonical"
    response = client.post(export_url, {"profile": "clean_working"}, format='json')

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "preflight" in data
    assert data["preflight"]["is_valid"] is False
    assert data["preflight"]["blocking_count"] >= 1
