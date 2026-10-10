"""
Serviços de Aplicação para Comparação, Mapeamento de Origens, Renumeração e Exportação — CONDC (Fase 4)
Implementa os casos de uso para os critérios CA-19 a CA-22 e CA-42 do PRD Mestre v3.0.
"""
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from django.db import transaction

from domain.comparison.invariants import (
    assert_new_provision_has_no_fictitious_origin,
    validate_origin_mapping_relationship,
    assert_excluded_provision_not_in_clean_document,
    check_cross_reference_status,
    render_cross_reference_label,
    calculate_text_diff,
    sanitize_clean_export_payload,
    DISCLAIMER_PRELIMINARY_NOTICE,
)
from domain.comparison.exceptions import (
    FictitiousOriginError,
    ExcludedProvisionInCleanExportError,
    InvalidOriginMappingError,
    BrokenCrossReferenceError,
    RenumberingError,
    CleanExportIntegrityError,
)
from domain.documents.invariants import calculate_revision_etag
from infrastructure.models import (
    Condominium,
    Document,
    Provision,
    ProvisionRevision,
    SourceProvision,
    InternalNote,
    OriginMapping,
    CrossReference,
)


class OriginMappingService:
    """Gerencia o mapeamento explícito de origens N:M entre a minuta e a fonte original (CA-19, CA-21)."""

    @staticmethod
    @transaction.atomic
    def create_mapping(
        condominium_id: uuid.UUID,
        revision_id: uuid.UUID,
        source_provision_id: uuid.UUID,
        relation_type: str = 'mantido',
        excerpt: Optional[str] = None,
        reason: Optional[str] = None
    ) -> OriginMapping:
        """
        Cria uma relação de origem explícita entre uma revisão da minuta e um dispositivo original.
        Garante que novo dispositivo incluído não receba origem fictícia (CA-19).
        """
        revision = ProvisionRevision.objects.get(id=revision_id, condominium_id=condominium_id)
        source_prov = SourceProvision.objects.get(id=source_provision_id, condominium_id=condominium_id)

        # CA-19: Dispositivo incluído não inventa origem
        if revision.change_type == 'incluido':
            raise FictitiousOriginError(
                "Dispositivo classificado como 'incluido' (novo) não pode ter vinculação de origem com dispositivo antigo."
            )

        validate_origin_mapping_relationship(
            relation_type=relation_type,
            source_provisions_count=1,
            target_revisions_count=1
        )

        mapping = OriginMapping.objects.create(
            condominium_id=condominium_id,
            revision=revision,
            source_provision=source_prov,
            relation_type=relation_type,
            excerpt=excerpt,
            reason=reason
        )

        # Atualiza o change_type da revisão se for compatível com a relação
        if relation_type in ('desmembrado', 'consolidado') and revision.change_type != relation_type:
            revision.change_type = relation_type
            revision.save(update_fields=['change_type'])

        return mapping

    @staticmethod
    def list_mappings_for_revision(
        condominium_id: uuid.UUID,
        revision_id: uuid.UUID
    ) -> List[OriginMapping]:
        """Lista todos os mapeamentos de origem vinculados a uma revisão específica (N:M)."""
        return list(
            OriginMapping.objects.filter(
                condominium_id=condominium_id,
                revision_id=revision_id
            ).select_related('source_provision')
        )

    @staticmethod
    def list_mappings_for_source(
        condominium_id: uuid.UUID,
        source_provision_id: uuid.UUID
    ) -> List[OriginMapping]:
        """Lista todas as revisões da minuta que derivam de uma fonte original específica (desmembramento 1:N)."""
        return list(
            OriginMapping.objects.filter(
                condominium_id=condominium_id,
                source_provision_id=source_provision_id
            ).select_related('revision', 'revision__provision')
        )


class ComparisonService:
    """Realiza comparação lado a lado e gera relatório DePara estruturado (CA-20, CA-21)."""

    @staticmethod
    def compare_revision_with_source(
        condominium_id: uuid.UUID,
        revision_id: uuid.UUID,
        source_provision_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Compara o texto de uma revisão da minuta com sua fonte original e calcula diff granular."""
        revision = ProvisionRevision.objects.get(id=revision_id, condominium_id=condominium_id)

        source_prov = None
        if source_provision_id:
            source_prov = SourceProvision.objects.get(id=source_provision_id, condominium_id=condominium_id)
        else:
            mapping = OriginMapping.objects.filter(
                condominium_id=condominium_id,
                revision_id=revision_id
            ).select_related('source_provision').first()
            if not mapping:
                mapping = OriginMapping.objects.filter(
                    condominium_id=condominium_id,
                    revision__provision_id=revision.provision_id
                ).select_related('source_provision').order_by('-revision__revision_number').first()
            if mapping:
                source_prov = mapping.source_provision

        source_text = source_prov.text if source_prov else ""
        target_text = revision.text

        diff_result = calculate_text_diff(source_text, target_text)

        return {
            "revision_id": str(revision.id),
            "provision_id": str(revision.provision_id),
            "revision_label": revision.label,
            "change_type": revision.change_type,
            "source_provision_id": str(source_prov.id) if source_prov else None,
            "source_label": source_prov.label if source_prov else None,
            "diff": diff_result
        }

    @staticmethod
    def generate_depara_report(
        condominium_id: uuid.UUID,
        document_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Gera relatório DePara completo:
        - Mapeia origens antigas para novas redações (1:1, 1:N desmembrado, N:1 consolidado).
        - CA-19: Novos dispositivos constam explicitamente sem origem fictícia.
        - CA-20: Dispositivos excluídos constam claramente no DePara com justificativa compartilhável.
        """
        document = Document.objects.get(id=document_id, condominium_id=condominium_id)

        # Coleta a última revisão ativa de cada dispositivo da minuta
        latest_revisions: Dict[uuid.UUID, ProvisionRevision] = {}
        for rev in ProvisionRevision.objects.filter(
            condominium_id=condominium_id,
            document_id=document_id
        ).select_related('provision').order_by('provision_id', 'revision_number'):
            latest_revisions[rev.provision_id] = rev

        depara_entries: List[Dict[str, Any]] = []

        # 1. Processa cada revisão ativa da minuta
        for prov_id, rev in latest_revisions.items():
            mappings = OriginMappingService.list_mappings_for_revision(condominium_id, rev.id)
            if not mappings and rev.change_type != 'incluido':
                all_prov_mappings = OriginMapping.objects.filter(
                    condominium_id=condominium_id,
                    revision__provision_id=prov_id
                ).select_related('source_provision').order_by('-revision__revision_number')
                seen_sources = set()
                deduped = []
                for m in all_prov_mappings:
                    if m.source_provision_id not in seen_sources:
                        seen_sources.add(m.source_provision_id)
                        deduped.append(m)
                mappings = deduped

            if rev.change_type == 'incluido':
                # CA-19: Dispositivo novo incluído não tem origem
                depara_entries.append({
                    "entry_type": "incluido",
                    "draft_provision_id": str(prov_id),
                    "draft_label": rev.label,
                    "draft_text": rev.text,
                    "draft_position": rev.position,
                    "change_type": "incluido",
                    "sources": [],
                    "has_fictitious_origin": False,
                    "summary": f"Dispositivo novo incluído ({rev.label}) sem correspondente na convenção anterior."
                })
            elif rev.change_type == 'excluido':
                # CA-20: Dispositivo excluído da minuta permanece no DePara
                sources_data = [
                    {
                        "source_provision_id": str(m.source_provision_id),
                        "source_label": m.source_provision.label,
                        "source_text": m.source_provision.text,
                        "relation_type": m.relation_type,
                        "reason": m.reason
                    }
                    for m in mappings
                ]
                depara_entries.append({
                    "entry_type": "excluido",
                    "draft_provision_id": str(prov_id),
                    "draft_label": rev.label,
                    "draft_text": rev.text,
                    "draft_position": rev.position,
                    "change_type": "excluido",
                    "sources": sources_data,
                    "summary": f"Dispositivo ({rev.label}) excluído da minuta de trabalho. Mantido no histórico e DePara."
                })
            else:
                # Mantido, alterado, desmembrado, consolidado
                sources_data = [
                    {
                        "source_provision_id": str(m.source_provision_id),
                        "source_label": m.source_provision.label,
                        "source_text": m.source_provision.text,
                        "relation_type": m.relation_type,
                        "reason": m.reason
                    }
                    for m in mappings
                ]
                depara_entries.append({
                    "entry_type": rev.change_type,
                    "draft_provision_id": str(prov_id),
                    "draft_label": rev.label,
                    "draft_text": rev.text,
                    "draft_position": rev.position,
                    "change_type": rev.change_type,
                    "sources": sources_data,
                    "summary": f"Dispositivo ({rev.label}) derivado de {len(sources_data)} origem(ns) ({rev.change_type})."
                })

        # Ordena as entradas do relatório pela posição na minuta
        depara_entries.sort(key=lambda x: x.get('draft_position', 0))

        return {
            "document_id": str(document.id),
            "document_title": document.title,
            "total_entries": len(depara_entries),
            "total_new_provisions": sum(1 for e in depara_entries if e['entry_type'] == 'incluido'),
            "total_excluded_provisions": sum(1 for e in depara_entries if e['entry_type'] == 'excluido'),
            "entries": depara_entries
        }


class CrossReferenceService:
    """Gerencia referências cruzadas dinâmicas baseadas em UUID estável (CA-22)."""

    @staticmethod
    @transaction.atomic
    def create_cross_reference(
        condominium_id: uuid.UUID,
        revision_id: uuid.UUID,
        target_provision_id: uuid.UUID,
        label_template: str = 'art. {target_label}'
    ) -> CrossReference:
        """Cria uma referência cruzada estruturada apontando para o UUID permanente do alvo."""
        revision = ProvisionRevision.objects.get(id=revision_id, condominium_id=condominium_id)
        target_prov = Provision.objects.get(id=target_provision_id, condominium_id=condominium_id)

        # Obtém a última revisão do dispositivo alvo para determinar o status inicial
        target_rev = ProvisionRevision.objects.filter(
            condominium_id=condominium_id,
            provision=target_prov
        ).order_by('-revision_number').first()

        status = 'quebrado' if (target_rev and target_rev.change_type == 'excluido') else 'valido'

        return CrossReference.objects.create(
            condominium_id=condominium_id,
            revision=revision,
            target_provision=target_prov,
            label_template=label_template,
            status=status
        )

    @staticmethod
    def resolve_references_for_revision(
        condominium_id: uuid.UUID,
        revision_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Resolve todas as referências cruzadas que saem de uma revisão, renderizando os rótulos atualizados."""
        xrefs = CrossReference.objects.filter(
            condominium_id=condominium_id,
            revision_id=revision_id
        ).select_related('target_provision')

        resolved = []
        for xr in xrefs:
            # Obtém a revisão mais recente do alvo
            target_rev = ProvisionRevision.objects.filter(
                condominium_id=condominium_id,
                provision_id=xr.target_provision_id
            ).order_by('-revision_number').first()

            if not target_rev or target_rev.change_type == 'excluido':
                status = 'quebrado'
                rendered = f"[REFERÊNCIA QUEBRADA - {xr.label_template}]"
            else:
                status = 'valido'
                rendered = render_cross_reference_label(xr.label_template, target_rev.label)

            resolved.append({
                "id": str(xr.id),
                "target_provision_id": str(xr.target_provision_id),
                "target_label": target_rev.label if target_rev else None,
                "label_template": xr.label_template,
                "rendered_text": rendered,
                "status": status
            })

        return resolved


class RenumberingService:
    """Executa renumeração sequencial preservando UUIDs e integridade de referências (CA-22)."""

    @staticmethod
    def preview_renumbering(
        condominium_id: uuid.UUID,
        document_id: uuid.UUID,
        strategy: str = 'renumeracao_automatica'
    ) -> Dict[str, Any]:
        """
        Calcula a prévia da renumeração sem aplicar alterações:
        - Determina novas posições e rótulos para artigos ativos (ignora 'excluido' na sequência de números).
        - Identifica referências cruzadas afetadas e potenciais quebras.
        - Preserva estritamente os UUIDs (`Provision.id`).
        """
        provisions = Provision.objects.filter(
            condominium_id=condominium_id,
            document_id=document_id
        ).order_by('created_at')

        # Obtém última revisão de cada dispositivo
        latest_revisions: List[ProvisionRevision] = []
        for prov in provisions:
            rev = ProvisionRevision.objects.filter(
                condominium_id=condominium_id,
                provision=prov
            ).order_by('-revision_number').first()
            if rev:
                latest_revisions.append(rev)

        # Ordena pela posição atual
        latest_revisions.sort(key=lambda x: x.position)

        preview_items: List[Dict[str, Any]] = []
        article_counter = 1

        for rev in latest_revisions:
            old_label = rev.label
            is_excluded = (rev.change_type == 'excluido')

            if is_excluded:
                new_label = f"[EXCLUÍDO] {old_label}"
                new_position = rev.position
            else:
                if rev.provision.kind == 'artigo':
                    if article_counter <= 9:
                        new_label = f"Art. {article_counter}º"
                    else:
                        new_label = f"Art. {article_counter}"
                    article_counter += 1
                else:
                    new_label = old_label
                new_position = len(preview_items) + 1

            preview_items.append({
                "provision_id": str(rev.provision_id),
                "uuid_preserved": True,  # CA-22: UUID nunca se altera!
                "kind": rev.provision.kind,
                "old_label": old_label,
                "new_label": new_label,
                "old_position": rev.position,
                "new_position": new_position,
                "is_excluded": is_excluded,
                "label_changed": (old_label != new_label)
            })

        return {
            "document_id": str(document_id),
            "strategy": strategy,
            "total_provisions": len(preview_items),
            "total_articles_renumbered": article_counter - 1,
            "preview_items": preview_items
        }

    @staticmethod
    @transaction.atomic
    def apply_renumbering(
        condominium_id: uuid.UUID,
        document_id: uuid.UUID,
        author_account_id: Optional[uuid.UUID] = None,
        strategy: str = 'renumeracao_automatica'
    ) -> Dict[str, Any]:
        """
        Aplica a renumeração criando novas revisões dos dispositivos modificados (CA-22):
        - Preserva rigorosamente os UUIDs permanentes (`Provision.id`).
        - As notas internas associadas continuam íntegras sem quebra de integridade.
        - Atualiza o status das referências cruzadas (se o alvo mudou de rótulo ou foi excluído).
        """
        preview = RenumberingService.preview_renumbering(condominium_id, document_id, strategy)
        items_by_id = {item['provision_id']: item for item in preview['preview_items']}

        renumbered_count = 0

        for prov_id_str, item in items_by_id.items():
            if not item['label_changed'] and item['old_position'] == item['new_position']:
                continue  # Sem alteração necessária

            prov_id = uuid.UUID(prov_id_str)
            current_rev = ProvisionRevision.objects.filter(
                condominium_id=condominium_id,
                provision_id=prov_id
            ).order_by('-revision_number').first()

            if not current_rev:
                continue

            # Cria nova revisão registrando o evento de renumeração
            new_rev_number = current_rev.revision_number + 1
            new_change_type = current_rev.change_type if item['is_excluded'] else 'renumerado'

            new_etag = calculate_revision_etag(
                provision_id=prov_id,
                revision_number=new_rev_number,
                text=current_rev.text,
                label=item['new_label'],
                parent_provision_id=current_rev.parent_provision_id
            )

            new_rev = ProvisionRevision.objects.create(
                provision_id=prov_id,
                document_id=document_id,
                condominium_id=condominium_id,
                revision_number=new_rev_number,
                parent_provision_id=current_rev.parent_provision_id,
                position=item['new_position'],
                label=item['new_label'],
                text=current_rev.text,
                theme=current_rev.theme,
                change_type=new_change_type,
                status=current_rev.status,
                author_account_id=author_account_id,
                etag=new_etag
            )

            # Re-liga os mapeamentos de origem à nova revisão
            for m in OriginMapping.objects.filter(revision=current_rev):
                OriginMapping.objects.create(
                    condominium_id=condominium_id,
                    revision=new_rev,
                    source_provision=m.source_provision,
                    relation_type=m.relation_type,
                    excerpt=m.excerpt,
                    reason=m.reason
                )

            # Re-liga as referências cruzadas que partem desta revisão à nova revisão (CA-22)
            for xr in CrossReference.objects.filter(revision=current_rev):
                CrossReference.objects.create(
                    condominium_id=condominium_id,
                    revision=new_rev,
                    target_provision=xr.target_provision,
                    label_template=xr.label_template,
                    status=xr.status
                )

            renumbered_count += 1

        # Atualiza status de todas as referências cruzadas que apontam para dispositivos do documento
        excluded_ids = {
            item['provision_id'] for item in preview['preview_items'] if item['is_excluded']
        }
        active_ids = {
            item['provision_id'] for item in preview['preview_items'] if not item['is_excluded']
        }

        for xr in CrossReference.objects.filter(condominium_id=condominium_id):
            new_status = check_cross_reference_status(xr.target_provision_id, active_ids, excluded_ids)
            if xr.status != new_status:
                xr.status = new_status
                xr.save(update_fields=['status'])

        return {
            "document_id": str(document_id),
            "provisions_renumbered": renumbered_count,
            "strategy": strategy,
            "status": "completed"
        }


class ExportService:
    """Gera documentos limpos preliminares e pacotes DePara sanitizados (CA-20, CA-42)."""

    @staticmethod
    def export_clean_document(
        condominium_id: uuid.UUID,
        document_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        CA-42: Gera export limpo preliminar do documento normativo:
        - Exclui terminantemente qualquer dispositivo marcado com 'excluido' (CA-20).
        - Exclui terminantemente autoria e dados de pessoas.
        - Exclui terminantemente notas internas e opiniões jurídicas (CA-24).
        - Resolve referências cruzadas com rótulos renderizados.
        - Anexa aviso obrigatório de documento preliminar não aprovado.
        """
        document = Document.objects.select_related('project').get(
            id=document_id,
            condominium_id=condominium_id
        )

        provisions = Provision.objects.filter(
            condominium_id=condominium_id,
            document_id=document_id
        ).order_by('created_at')

        items_for_export = []
        for prov in provisions:
            rev = ProvisionRevision.objects.filter(
                condominium_id=condominium_id,
                provision=prov
            ).order_by('-revision_number').first()

            if not rev:
                continue

            # Se excluído, é ignorado para o documento limpo (CA-20)
            if rev.change_type == 'excluido':
                continue

            # Resolve referências cruzadas
            resolved_xrs = CrossReferenceService.resolve_references_for_revision(
                condominium_id=condominium_id,
                revision_id=rev.id
            )

            items_for_export.append({
                "provision_id": str(prov.id),
                "position": rev.position,
                "label": rev.label,
                "kind": prov.kind,
                "text": rev.text,
                "parent_provision_id": str(rev.parent_provision_id) if rev.parent_provision_id else None,
                "theme": rev.theme,
                "change_type": rev.change_type,
                "resolved_cross_references": resolved_xrs
            })

        return sanitize_clean_export_payload(
            document_title=document.title,
            document_type=document.type,
            provisions=items_for_export,
            project_name=document.project.name if document.project else None
        )

    @staticmethod
    def export_clean_text(
        condominium_id: uuid.UUID,
        document_id: uuid.UUID
    ) -> str:
        """Gera versão em texto corrido normativo limpo com cabeçalho de aviso prévio."""
        clean_data = ExportService.export_clean_document(condominium_id, document_id)

        lines = [
            f"=== {clean_data['document_title'].upper()} ===",
            f"Projeto: {clean_data.get('project_name') or 'N/A'}",
            f"Aviso Obrigatório: {clean_data['disclaimer']}",
            "",
            "--- DISPOSITIVOS NORMATIVOS ---",
            ""
        ]

        for prov in clean_data['provisions']:
            lines.append(f"{prov['label']} {prov['text']}")
            lines.append("")

        return "\n".join(lines)
