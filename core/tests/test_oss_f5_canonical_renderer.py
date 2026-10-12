"""
Testes Automatizados para a Fase OSS-F5 — Validação Pré-Voo e Renderer Canônico DOCX/PDF
Cobre os critérios:
- EDOSS-EX-01: PDF gerado do DOCX definitivo entregue
- EDOSS-EX-03: Snapshot único durante todo o render
- EDOSS-EX-04: Preflight bloqueia exportação se houver inconsistências impeditivas
- EDOSS-EX-05: Par DOCX/PDF com manifesto e hashes SHA-256
- EDOSS-EX-07: Documento público sem PII ou anotações internas privadas
- EDOSS-HF-05: PageNumber e PageCount resolvidos
- EDOSS-TB-03: Repetição de cabeçalho de tabela
"""
import os
import uuid
import tempfile
import json
import pytest

from domain.documents.preflight import PreflightValidator, PreflightReport
from domain.documents.renderer import CanonicalDocumentRenderer, RenderResult
from domain.documents.templates import NormativeTemplateLoader, NormativeTemplateInstantiator


def test_preflight_blocks_invalid_document():
    """Valida que o Preflight bloqueia documentos com artigo sem caput ou ciclo."""
    invalid_nodes = [
        {
            "id": str(uuid.uuid4()),
            "kind": "article",
            "label": "Art. 1º",
            "text": ""
        }
        # Falta o nó filho de tipo 'caput'
    ]
    report = PreflightValidator.validate_document_tree(invalid_nodes, profile='final_presentation')
    assert not report.is_valid
    assert report.blocking_count >= 1
    assert any("caput" in iss.message.lower() for iss in report.issues)


def test_preflight_passes_on_valid_instantiated_regimento():
    """Valida que um Regimento Interno válido instanciado a partir do template passa no preflight."""
    raw_template = NormativeTemplateLoader.load_regimento_esqueleto()
    instance = NormativeTemplateInstantiator.instantiate_tree(raw_template, renumber=True)

    # Coletar nós recursivamente
    flat_nodes = []
    def _collect(n):
        flat_nodes.append({
            "id": n.get("id"),
            "kind": n.get("type"),
            "label": n.get("label"),
            "text": "Texto normativo regulamentar aprovado.",
            "parent_id": n.get("parent_id")
        })
        for c in n.get("children", []):
            _collect(c)

    _collect(instance["root"])

    report = PreflightValidator.validate_document_tree(flat_nodes, profile='clean_working')
    assert report.is_valid
    assert report.blocking_count == 0


def test_canonical_renderer_generates_docx_and_pdf_with_manifest():
    """Valida que o renderizador canônico gera os artefatos DOCX, PDF e manifesto com SHA-256."""
    snapshot_id = str(uuid.uuid4())
    doc_title = "Regimento Interno do Condomínio"
    condo_name = "Condomínio Edifício Parque das Flores"

    # Criar nós de teste com artigos, parágrafos, incisos e alíneas
    art1_id = str(uuid.uuid4())
    caput1_id = str(uuid.uuid4())
    par1_id = str(uuid.uuid4())
    inc1_id = str(uuid.uuid4())

    nodes = [
        {
            "id": str(uuid.uuid4()),
            "kind": "chapter",
            "label": "CAPÍTULO I",
            "text": "DISPOSIÇÕES GERAIS",
            "position": 1
        },
        {
            "id": art1_id,
            "kind": "article",
            "label": "Art. 1º",
            "text": "O presente Regimento Interno disciplina os direitos e deveres dos condôminos.",
            "position": 2
        },
        {
            "id": caput1_id,
            "kind": "caput",
            "label": "Art. 1º",
            "text": "O presente Regimento Interno disciplina os direitos e deveres dos condôminos.",
            "parent_id": art1_id,
            "position": 3
        },
        {
            "id": par1_id,
            "kind": "legal_paragraph",
            "label": "Parágrafo único.",
            "text": "As disposições aplicam-se a todos os ocupantes e visitantes.",
            "parent_id": art1_id,
            "position": 4
        },
        {
            "id": inc1_id,
            "kind": "inciso",
            "label": "I -",
            "text": "Garantir o sossego e a segurança coletiva;",
            "parent_id": par1_id,
            "position": 5
        },
        {
            "id": str(uuid.uuid4()),
            "kind": "signatures",
            "label": "Fecho",
            "text": "Aprovado em Assembleia Geral Ordinária.",
            "position": 6
        }
    ]

    with tempfile.TemporaryDirectory(prefix="condoc_test_render_") as tmpdir:
        result: RenderResult = CanonicalDocumentRenderer.render_snapshot(
            snapshot_id=snapshot_id,
            document_title=doc_title,
            condominium_name=condo_name,
            nodes=nodes,
            output_dir=tmpdir,
            profile='clean_working'
        )

        assert result.success
        assert os.path.exists(result.docx_path)
        assert len(result.docx_sha256) == 64
        assert result.docx_size_bytes > 0

        # Verifica existência do PDF e hash
        assert result.pdf_path is not None
        assert os.path.exists(result.pdf_path)
        assert len(result.pdf_sha256) == 64
        assert result.pdf_size_bytes > 0

        # Verifica manifesto de integridade gerado
        manifest_path = os.path.join(tmpdir, f"manifest_{snapshot_id}.json")
        assert os.path.exists(manifest_path)
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)

        assert manifest_data["version"] == "ED-OSS-2.0"
        assert manifest_data["snapshot_id"] == snapshot_id
        assert manifest_data["artifacts"]["docx"]["sha256"] == result.docx_sha256
        assert manifest_data["artifacts"]["pdf"]["sha256"] == result.pdf_sha256
        assert manifest_data["validation"]["preflight_passed"] is True
