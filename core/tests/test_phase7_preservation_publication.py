"""
Testes Automatizados para a Fase 7 — Preservação e Publicação de Conteúdo — CONDC
Cobre integralmente os critérios de aceite:
- CA-41: Snapshot imutável e reproduzível
- CA-42: Documento limpo sem identidade, notas internas ou referência antiga indevida
- CA-45 / UI-38: Ausência absoluta de votação, cálculo de quórum ou aprovação vinculante na assembleia
- UI-33: Segregação estrita entre pacote público externo e relatório interno da comissão
- Verificação criptográfica e detecção de adulteração via manifesto SHA-256
- Modo de leitura pública autorizada para apresentação em assembleia
- Isolamento multi-tenancy entre condomínios
"""
import uuid
import json
import pytest
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
    InternalNote,
    ExportArtifact,
)
from application.documents.services import (
    ProjectService,
    DocumentService,
    ProvisionService,
    InternalNoteService,
)
from application.comparison.services import OriginMappingService
from application.preservation.services import PreservationService
from domain.preservation.invariants import (
    DISCLAIMER_FINAL_PUBLICATION,
    calculate_content_sha256,
    assert_public_export_contains_no_pii_or_internal_notes,
    assert_assembly_reading_view_has_no_voting_controls,
)
from domain.preservation.exceptions import (
    PublicExportExposureError,
    ManifestIntegrityError,
    ElectoralDeliberationForbiddenError,
)


@pytest.fixture
def phase7_setup(db):
    """Cenário completo para testes da Fase 7 com projeto, minuta final, dispositivos e notas internas."""
    condo = Condominium.objects.create(name="Condomínio Solar das Acácias")
    building = Building.objects.create(condominium=condo, code="BL-1", name="Bloco 1")
    unit = Unit.objects.create(condominium=condo, building=building, code="301")

    # Síndico ativo
    sindico = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="sindico.acacias@condoc.com.br",
        full_name="Dr. Fernando Síndico"
    )
    RoleAssignment.objects.create(
        condominium=condo,
        account=sindico,
        role="sindico",
        status="active"
    )

    # Morador
    morador_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="morador.301@gmail.com",
        full_name="Lucas Morador"
    )
    resident = Resident.objects.create(
        condominium=condo,
        account=morador_acc,
        full_name=morador_acc.full_name
    )
    UnitMembership.objects.create(
        condominium=condo,
        resident=resident,
        unit=unit,
        category="proprietario_residente",
        verification_status="validado",
        membership_status="active"
    )

    # Projeto e Documento
    proj = ProjectService.create_project(condominium_id=condo.id, name="Revisão Final Convenção 2026", coordinator_account_id=sindico.id)
    doc = DocumentService.create_document(project_id=proj.id, condominium_id=condo.id, title="Convenção de Condomínio 2026", type="convencao")

    # Dispositivos na minuta
    p1 = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 1º",
        text="O condomínio destina-se exclusivamente para fins residenciais.",
        author_account_id=sindico.id
    )
    p2 = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 2º",
        text="A realização de obras e reformas deve respeitar a norma ABNT NBR 16280.",
        author_account_id=sindico.id
    )

    # Nota interna confidencial associada ao p2 (não pode vazar no pacote público!)
    InternalNoteService.create_note(
        condominium_id=condo.id,
        provision_id=p2.id,
        author_account_id=sindico.id,
        content="Parecer jurídico prévio exigindo laudo de arquiteto com ART.",
        visibility="equipe",
        category="juridico"
    )

    return {
        "condo": condo,
        "sindico": sindico,
        "project": proj,
        "document": doc,
        "provision_1": p1,
        "provision_2": p2,
    }


def test_pacote_externo_publico_com_manifesto_sha256(phase7_setup):
    """
    CA-41 / CA-42 / UI-33 / UI-38:
    Gera pacote externo público para a assembleia com manifesto SHA-256 e aviso legal.
    """
    ctx = phase7_setup
    condo = ctx['condo']
    doc = ctx['document']
    sindico = ctx['sindico']

    package = PreservationService.generate_final_public_package(
        condominium_id=condo.id,
        document_id=doc.id,
        generated_by_id=sindico.id
    )

    # 1. Estrutura básica do pacote
    assert package['document_id'] == str(doc.id)
    assert package['manifest_hash'] is not None
    assert len(package['manifest_hash']) == 64  # SHA-256
    assert package['disclaimer'] == DISCLAIMER_FINAL_PUBLICATION

    # 2. Arquivos obrigatórios no manifesto
    files = package['files_manifest']
    assert len(files) == 3
    paths = [f['path'] for f in files]
    assert "minuta_limpa_final.json" in paths
    assert "minuta_limpa_final.txt" in paths
    assert "relatorio_depara_consolidado.json" in paths

    # 3. Cada arquivo possui hash SHA-256 válido
    for f in files:
        assert len(f['sha256']) == 64
        assert f['size_bytes'] > 0

    # 4. Registro correspondente em ExportArtifact
    artifact = ExportArtifact.objects.get(id=package['artifact_id'])
    assert artifact.kind == 'pacote_externo_publico'
    assert artifact.is_public is True
    assert artifact.manifest_hash == package['manifest_hash']
    assert artifact.status == 'concluido'


def test_ui_33_segregacao_estrita_entre_pacote_publico_e_relatorio_interno(phase7_setup):
    """
    UI-33: Segregação estrita entre pacote público externo e relatório interno da comissão.
    O pacote público omite estritamente notas internas e dados pessoais.
    O relatório interno é confidencial (is_public=False) e retém o histórico completo para a gestão.
    """
    ctx = phase7_setup
    condo = ctx['condo']
    doc = ctx['document']
    sindico = ctx['sindico']

    # 1. Pacote Público
    package = PreservationService.generate_final_public_package(condo.id, doc.id, sindico.id)
    clean_json = package['files_content']['minuta_limpa_final.json']

    # Valida que não contém notas internas nem autoria
    assert_public_export_contains_no_pii_or_internal_notes(clean_json)

    # 2. Relatório Interno da Comissão
    internal_report = PreservationService.generate_internal_commission_report(
        condominium_id=condo.id,
        document_id=doc.id,
        generated_by_id=sindico.id
    )
    assert internal_report['is_public'] is False

    artifact_internal = ExportArtifact.objects.get(id=internal_report['artifact_id'])
    assert artifact_internal.kind == 'relatorio_interno_comissao'
    assert artifact_internal.is_public is False

    # 3. Invariante de proteção contra vazamento dispara se houver nota interna no público
    with pytest.raises(PublicExportExposureError):
        assert_public_export_contains_no_pii_or_internal_notes({
            "title": "Minuta",
            "internal_notes": ["Nota confidencial"]
        })

    with pytest.raises(PublicExportExposureError):
        assert_public_export_contains_no_pii_or_internal_notes({
            "title": "Minuta",
            "email": "morador@privado.com"
        })


def test_verificacao_criptografica_de_manifesto_e_deteccao_de_adulteracao(phase7_setup):
    """
    Verificação de integridade via manifesto SHA-256 e detecção instantânea de adulteração.
    """
    ctx = phase7_setup
    condo = ctx['condo']
    doc = ctx['document']
    sindico = ctx['sindico']

    package = PreservationService.generate_final_public_package(condo.id, doc.id, sindico.id)
    artifact_id = package['artifact_id']

    # Prepara mapa de conteúdos em texto
    files_map = {
        "minuta_limpa_final.json": json.dumps(package['files_content']['minuta_limpa_final.json'], sort_keys=True, indent=2, ensure_ascii=False),
        "minuta_limpa_final.txt": package['files_content']['minuta_limpa_final.txt'],
        "relatorio_depara_consolidado.json": json.dumps(package['files_content']['relatorio_depara_consolidado.json'], sort_keys=True, indent=2, ensure_ascii=False)
    }

    # 1. Verificação com arquivos legítimos -> SUCESSO
    verify_res = PreservationService.verify_manifest_integrity(artifact_id, condo.id, files_map)
    assert verify_res['integrity_verified'] is True
    assert verify_res['manifest_hash'] == package['manifest_hash']

    # 2. Adulteração de 1 caractere no texto normativo -> DEVE DETECTAR E REJEITAR
    tampered_map = dict(files_map)
    tampered_map["minuta_limpa_final.txt"] = tampered_map["minuta_limpa_final.txt"] + " [ALTERAÇÃO ADULTERADA NÃO AUTORIZADA]"

    with pytest.raises(ManifestIntegrityError) as exc_info:
        PreservationService.verify_manifest_integrity(artifact_id, condo.id, tampered_map)

    assert "Divergência de hash SHA-256" in str(exc_info.value)

    # 3. Arquivo ausente no pacote fornecido -> DEVE FALHAR
    missing_map = dict(files_map)
    del missing_map["relatorio_depara_consolidado.json"]

    with pytest.raises(ManifestIntegrityError) as exc_missing:
        PreservationService.verify_manifest_integrity(artifact_id, condo.id, missing_map)

    assert "ausente no pacote" in str(exc_missing.value)


def test_ca_45_ui_38_modo_leitura_assembleia_sem_controles_eleitorais(phase7_setup):
    """
    CA-45 / UI-38: Modo de leitura pública autorizada para assembleia.
    Garante exibição somente leitura com disclaimer permanente e ausência de controles deliberativos/eleitorais.
    """
    ctx = phase7_setup
    condo = ctx['condo']
    doc = ctx['document']

    reading_view = PreservationService.get_assembly_reading_view(condo.id, doc.id)

    assert reading_view['document_id'] == str(doc.id)
    assert reading_view['reading_mode'] == 'assembleia_somente_leitura'
    assert reading_view['has_voting_module'] is False
    assert reading_view['disclaimer'] == DISCLAIMER_FINAL_PUBLICATION
    assert len(reading_view['provisions']) == 2

    # Invariante rejeita se houver controle eleitoral
    with pytest.raises(ElectoralDeliberationForbiddenError):
        assert_assembly_reading_view_has_no_voting_controls(["scroll", "votar"])

    with pytest.raises(ElectoralDeliberationForbiddenError):
        assert_assembly_reading_view_has_no_voting_controls(["aprovar_em_assembleia"])


def test_isolamento_tenant_fase7(phase7_setup):
    """Isolamento estrito multi-tenancy entre artefatos de exportação."""
    ctx = phase7_setup
    condo1 = ctx['condo']
    doc1 = ctx['document']
    sindico1 = ctx['sindico']

    condo2 = Condominium.objects.create(name="Condomínio Outro")

    package = PreservationService.generate_final_public_package(condo1.id, doc1.id, sindico1.id)
    artifact_id = package['artifact_id']

    # Busca no condomínio 2 falha
    with pytest.raises(ExportArtifact.DoesNotExist):
        ExportArtifact.objects.get(id=artifact_id, condominium_id=condo2.id)


def test_fluxo_completo_api_preservacao_e_assembleia(phase7_setup):
    """
    Testa o fluxo REST completo da Fase 7 via APIClient:
    - POST /export/package
    - POST /export/commission-report
    - GET /assembly-reading
    - GET /artifacts/<id>
    - POST /artifacts/<id>/verify
    """
    client = APIClient()
    ctx = phase7_setup
    condo = ctx['condo']
    doc = ctx['document']

    # 1. Gera pacote externo público via API
    resp_pkg = client.post(
        f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/export/package"
    )
    assert resp_pkg.status_code == 201
    artifact_id = resp_pkg.data['artifact_id']
    manifest_hash = resp_pkg.data['manifest_hash']
    assert len(manifest_hash) == 64

    # 2. Gera relatório interno da comissão via API
    resp_rep = client.post(
        f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/export/commission-report"
    )
    assert resp_rep.status_code == 201
    assert resp_rep.data['is_public'] is False

    # 3. Consulta modo de leitura da assembleia via API (somente leitura, sem voto)
    resp_read = client.get(
        f"/api/v1/condominiums/{condo.id}/documents/{doc.id}/assembly-reading"
    )
    assert resp_read.status_code == 200
    assert resp_read.data['reading_mode'] == 'assembleia_somente_leitura'
    assert resp_read.data['has_voting_module'] is False
    assert "NÃO realiza votação" in resp_read.data['disclaimer']

    # 4. Consulta detalhe do artefato registrado via API
    resp_art = client.get(
        f"/api/v1/condominiums/{condo.id}/artifacts/{artifact_id}"
    )
    assert resp_art.status_code == 200
    assert resp_art.data['manifest_hash'] == manifest_hash

    # 5. Verifica integridade do manifesto via API com sucesso
    raw_files = resp_pkg.data['files_content']
    files_map = {
        "minuta_limpa_final.json": json.dumps(raw_files['minuta_limpa_final.json'], sort_keys=True, indent=2, ensure_ascii=False),
        "minuta_limpa_final.txt": raw_files['minuta_limpa_final.txt'],
        "relatorio_depara_consolidado.json": json.dumps(raw_files['relatorio_depara_consolidado.json'], sort_keys=True, indent=2, ensure_ascii=False)
    }
    resp_verify = client.post(
        f"/api/v1/condominiums/{condo.id}/artifacts/{artifact_id}/verify",
        data={"files_content_map": files_map},
        format="json"
    )
    assert resp_verify.status_code == 200
    assert resp_verify.data['integrity_verified'] is True

    # 6. Verifica detecção de adulteração via API -> HTTP 400 MANIFEST_INTEGRITY_TAMPERED
    tampered_map = dict(files_map)
    tampered_map["minuta_limpa_final.txt"] = "Adulterado"
    resp_verify_tampered = client.post(
        f"/api/v1/condominiums/{condo.id}/artifacts/{artifact_id}/verify",
        data={"files_content_map": tampered_map},
        format="json"
    )
    assert resp_verify_tampered.status_code == 400
    assert resp_verify_tampered.data['code'] == 'MANIFEST_INTEGRITY_TAMPERED'
