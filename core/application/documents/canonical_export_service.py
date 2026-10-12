"""
Serviço de Exportação Canônica, Preflight e Instanciação de Templates — CONDOC (ED-OSS-2.0)
Conecta os módulos de domínio (Gramática LC 95, Preflight e Renderizador python-docx/LibreOffice)
com a camada de persistência e modelos do Django.
"""
import os
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
from django.db import transaction
from django.utils import timezone

from infrastructure.models import (
    Condominium,
    Project,
    Document,
    DocumentSnapshot,
    Provision,
    ProvisionRevision,
    InternalNote,
    ExportArtifact,
    Account,
)
from domain.documents.preflight import PreflightValidator, PreflightReport
from domain.documents.renderer import CanonicalDocumentRenderer, RenderResult
from domain.documents.templates import (
    instantiate_regimento,
    instantiate_convencao,
    flatten_document_provisions,
)
from domain.documents.invariants import calculate_revision_etag


KIND_GRAMMAR_TO_DB = {
    'document_root': 'titulo',
    'cover_block': 'titulo',
    'document_heading': 'titulo',
    'preamble': 'preambulo',
    'legal_title': 'titulo',
    'chapter': 'capitulo',
    'legal_section': 'secao',
    'subsection': 'subsecao',
    'article': 'artigo',
    'caput': 'caput',
    'legal_paragraph': 'paragrafo',
    'inciso': 'inciso',
    'alinea': 'alinea',
    'item': 'item',
    'normative_table': 'anexo',
    'signature_group': 'anexo',
    'condoc_page_break': 'anexo',
    # Pass-through para tipos já no formato DB
    'titulo': 'titulo',
    'capitulo': 'capitulo',
    'secao': 'secao',
    'subsecao': 'subsecao',
    'artigo': 'artigo',
    'paragrafo': 'paragrafo',
    'anexo': 'anexo',
}

KIND_DB_TO_GRAMMAR = {
    'titulo': 'legal_title',
    'capitulo': 'chapter',
    'secao': 'legal_section',
    'subsecao': 'subsection',
    'artigo': 'article',
    'caput': 'caput',
    'paragrafo': 'legal_paragraph',
    'inciso': 'inciso',
    'alinea': 'alinea',
    'item': 'item',
    'preambulo': 'preamble',
    'anexo': 'anexo',
}


def extract_text_from_body(body: Any) -> str:
    """Extrai texto representativo a partir de strings simples ou estruturas ricas de blocos/runs/dict."""
    if not body:
        return ""
    if isinstance(body, str):
        return body.strip()
    if isinstance(body, dict):
        if 'text' in body and isinstance(body['text'], str):
            return body['text'].strip()
        if 'content' in body:
            return extract_text_from_body(body['content'])
        if 'runs' in body and isinstance(body['runs'], list):
            return extract_text_from_body(body['runs'])
        if 'children' in body and isinstance(body['children'], list):
            return extract_text_from_body(body['children'])
        if 'paragraphs' in body and isinstance(body['paragraphs'], list):
            return extract_text_from_body(body['paragraphs'])
        for key in ('val', 'value', 'label', 'raw'):
            if key in body and isinstance(body[key], str):
                return body[key].strip()
        return ""
    if isinstance(body, (list, tuple)):
        parts = []
        for item in body:
            if isinstance(item, str):
                parts.append(item.strip())
            elif isinstance(item, dict):
                parts.append(extract_text_from_body(item))
            elif isinstance(item, (list, tuple)):
                parts.append(extract_text_from_body(item))
            else:
                parts.append(str(item).strip())
        return " ".join(p for p in parts if p).strip()
    return str(body).strip()


class CanonicalExportService:
    """Serviço de aplicação para governança canônica de documentos normativos."""

    @staticmethod
    def collect_document_nodes_and_notes(
        condominium_id: Union[str, uuid.UUID],
        document_id: Union[str, uuid.UUID],
        profile: str = 'clean_working'
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Recupera os nós ativos (últimas revisões não-excluídas) e notas do documento.
        Converte tipos e propriedades para a estrutura esperada pelo Preflight e Renderer.
        """
        provisions = Provision.objects.filter(
            condominium_id=condominium_id,
            document_id=document_id
        ).order_by('created_at')

        nodes: List[Dict[str, Any]] = []
        for prov in provisions:
            rev = ProvisionRevision.objects.filter(
                condominium_id=condominium_id,
                provision=prov
            ).order_by('-revision_number').first()

            if not rev or rev.change_type == 'excluido':
                continue

            grammar_kind = KIND_DB_TO_GRAMMAR.get(prov.kind, prov.kind)
            nodes.append({
                "id": str(prov.id),
                "parent_id": str(rev.parent_provision_id) if rev.parent_provision_id else None,
                "kind": grammar_kind,
                "type": grammar_kind,
                "label": rev.label or "",
                "rendered_label": rev.label or "",
                "text": rev.text or "",
                "body": rev.text or "",
                "position": rev.position,
                "change_type": rev.change_type,
            })

        # Ordena nós pela posição relativa
        nodes.sort(key=lambda n: n.get("position", 0))

        # Notas (se perfil for restrito à gestão ou clean)
        notes: List[Dict[str, Any]] = []
        if profile == 'internal_restricted':
            db_notes = InternalNote.objects.filter(
                condominium_id=condominium_id,
                provision__document_id=document_id
            )
            for n in db_notes:
                notes.append({
                    "id": str(n.id),
                    "provision_id": str(n.provision_id),
                    "content": n.content,
                    "category": n.category,
                    "visibility": n.visibility,
                })

        return nodes, notes

    @classmethod
    def run_preflight(
        cls,
        condominium_id: Union[str, uuid.UUID],
        document_id: Union[str, uuid.UUID],
        profile: str = 'clean_working'
    ) -> PreflightReport:
        """Executa auditoria prévia completa (Preflight) na árvore normativa."""
        nodes, notes = cls.collect_document_nodes_and_notes(condominium_id, document_id, profile=profile)
        return PreflightValidator.validate_document_tree(nodes, notes=notes, profile=profile)

    @classmethod
    def export_canonical_pair(
        cls,
        condominium_id: Union[str, uuid.UUID],
        document_id: Union[str, uuid.UUID],
        author_account_id: Optional[Union[str, uuid.UUID]] = None,
        profile: str = 'clean_working',
        output_dir: Optional[str] = None,
        force_without_soffice: bool = False
    ) -> RenderResult:
        """
        Executa o pipeline canônico integral:
        Preflight -> python-docx -> LibreOffice Headless -> PDF -> SHA-256 -> Manifesto -> DB Artifact.
        """
        condo = Condominium.objects.get(id=condominium_id)
        document = Document.objects.get(id=document_id, condominium_id=condominium_id)

        nodes, notes = cls.collect_document_nodes_and_notes(condominium_id, document_id, profile=profile)

        # Preflight
        preflight_report = PreflightValidator.validate_document_tree(nodes, notes=notes, profile=profile)
        if not preflight_report.is_valid and profile in ('final_presentation', 'clean_working'):
            return RenderResult(
                success=False,
                docx_path="",
                docx_sha256="",
                docx_size_bytes=0,
                pdf_path=None,
                pdf_sha256=None,
                pdf_size_bytes=None,
                manifest={},
                preflight_report=preflight_report,
                error_message=f"Preflight bloqueante detectado: {preflight_report.blocking_count} inconsistência(s) encontrada(s)."
            )

        # Snapshot de referência
        snapshot = DocumentSnapshot.objects.filter(
            document_id=document_id,
            condominium_id=condominium_id
        ).order_by('-frozen_at').first()
        snapshot_id = snapshot.id if snapshot else uuid.uuid4()

        result = CanonicalDocumentRenderer.render_canonical_pair(
            snapshot_id=str(snapshot_id),
            document_title=document.title,
            condominium_name=condo.name,
            nodes=nodes,
            notes=notes,
            profile=profile,
            output_dir=output_dir,
            force_without_soffice=force_without_soffice
        )

        # Registra artefato de exportação no banco
        if result.success:
            files_manifest = [
                {
                    "name": os.path.basename(result.docx_path),
                    "sha256": result.docx_sha256,
                    "size_bytes": result.docx_size_bytes,
                    "format": "docx"
                }
            ]
            if result.pdf_path:
                files_manifest.append({
                    "name": os.path.basename(result.pdf_path),
                    "sha256": result.pdf_sha256,
                    "size_bytes": result.pdf_size_bytes,
                    "format": "pdf"
                })

            ExportArtifact.objects.create(
                condominium_id=condominium_id,
                document=document,
                snapshot=snapshot,
                kind='minuta_final_limpa' if profile == 'final_presentation' else 'pacote_externo_publico',
                status='concluido',
                is_public=True,
                manifest_hash=result.docx_sha256,
                files_manifest=files_manifest,
                disclaimer="Documento gerado pelo pipeline canônico CONDOC ED-OSS-2.0. Não possui efeito vinculante até deliberação assemblear soberana.",
                generated_by_id=author_account_id
            )

        return result

    @classmethod
    @transaction.atomic
    def instantiate_template_to_document(
        cls,
        condominium_id: Union[str, uuid.UUID],
        project_id: Union[str, uuid.UUID],
        title: str,
        template_type: str = 'regimento',
        author_account_id: Optional[Union[str, uuid.UUID]] = None
    ) -> Tuple[Document, List[Provision]]:
        """
        Instancia um modelo normativo aberto completo (Regimento ou Convenção)
        criando o Documento e todos os nós na tabela app.provisions com UUIDs frescos e estáveis.
        """
        doc_type = 'regimento_interno' if template_type == 'regimento' else 'convencao'

        document = Document.objects.create(
            project_id=project_id,
            condominium_id=condominium_id,
            title=title.strip(),
            type=doc_type,
            editorial_status='rascunho',
            numbering_policy='renumeracao_automatica'
        )

        if template_type == 'regimento':
            instance = instantiate_regimento(condominium_id=condominium_id, title=title, renumber=True)
        else:
            instance = instantiate_convencao(condominium_id=condominium_id, title=title, renumber=True)

        flat_items = flatten_document_provisions(instance)

        created_provisions: List[Provision] = []
        provision_map: Dict[str, Provision] = {}

        # 1. Cria os registros de Provision
        for item in flat_items:
            nid = uuid.UUID(item["id"])
            raw_kind = item.get("kind", "artigo")
            db_kind = KIND_GRAMMAR_TO_DB.get(raw_kind, 'artigo')

            prov = Provision.objects.create(
                id=nid,
                document=document,
                condominium_id=condominium_id,
                kind=db_kind
            )
            provision_map[str(nid)] = prov
            created_provisions.append(prov)

        # 2. Cria as revisões iniciais (revisão 1) ligando parent_provision_id
        for item in flat_items:
            nid = str(item["id"])
            prov = provision_map[nid]
            parent_id_str = item.get("parent_id")
            parent_prov = provision_map.get(parent_id_str) if parent_id_str else None

            raw_label = item.get("rendered_label") or item.get("heading") or ""
            raw_text = item.get("body") or item.get("heading") or ""

            label = extract_text_from_body(raw_label)
            text = extract_text_from_body(raw_text)

            etag = calculate_revision_etag(
                provision_id=prov.id,
                revision_number=1,
                text=text,
                label=label,
                parent_provision_id=parent_prov.id if parent_prov else None
            )

            ProvisionRevision.objects.create(
                provision=prov,
                document=document,
                condominium_id=condominium_id,
                revision_number=1,
                parent_provision=parent_prov,
                position=item.get("position", 0),
                label=label,
                text=text,
                change_type='mantido',
                status='ativo',
                author_account_id=author_account_id,
                etag=etag
            )

        return document, created_provisions
