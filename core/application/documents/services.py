"""
Serviços da Camada de Aplicação para o Núcleo Documental — CONDC (Fase 3)
Orquestra casos de uso para Projetos, Documentos, OCR/Transcrições (CA-17, CA-18),
Dispositivos e Revisões com Concorrência Otimista (CA-23), Notas Internas (CA-24)
e Snapshots Imutáveis (CA-41).
"""
import uuid
import hashlib
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone

from infrastructure.models import (
    Condominium,
    Account,
    Project,
    Document,
    SourceFile,
    SourceTranscription,
    SourceProvision,
    Provision,
    ProvisionRevision,
    InternalNote,
    DocumentSnapshot,
    SnapshotItem,
    OriginMapping,
    CrossReference,
)
from domain.documents.exceptions import (
    CircularReferenceError,
    ConcurrencyConflictError,
    SnapshotImmutableError,
    TranscriptionStatusError,
    PrivateNoteAccessForbiddenError,
)
from domain.documents.invariants import (
    calculate_revision_etag,
    assert_optimistic_concurrency,
    assert_no_circular_hierarchy,
    calculate_snapshot_hash,
    assert_snapshot_immutable,
    sanitize_public_provision_dto,
)


class ProjectService:
    @staticmethod
    def create_project(
        condominium_id: Any,
        name: str,
        purpose: Optional[str] = None,
        kind: str = 'revisao',
        coordinator_account_id: Optional[Any] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Project:
        return Project.objects.create(
            condominium_id=condominium_id,
            name=name.strip(),
            purpose=purpose.strip() if purpose else None,
            kind=kind,
            coordinator_account_id=coordinator_account_id,
            settings=settings or {},
            status='preparacao'
        )

    @staticmethod
    def list_projects(condominium_id: Any) -> List[Project]:
        return list(Project.objects.filter(condominium_id=condominium_id).order_by('-created_at'))


class DocumentService:
    @staticmethod
    def create_document(
        project_id: Any,
        condominium_id: Any,
        title: str,
        type: str = 'regimento_interno',
        numbering_policy: str = 'preservar_original'
    ) -> Document:
        return Document.objects.create(
            project_id=project_id,
            condominium_id=condominium_id,
            title=title.strip(),
            type=type,
            editorial_status='rascunho',
            numbering_policy=numbering_policy
        )

    @staticmethod
    def list_documents(project_id: Any) -> List[Document]:
        return list(Document.objects.filter(project_id=project_id).order_by('created_at'))


class SourceFileService:
    @staticmethod
    def register_source_file(
        condominium_id: Any,
        uploaded_by_id: Any,
        filename: str,
        mime_type: str,
        size_bytes: int,
        file_content: bytes,
        storage_key: Optional[str] = None
    ) -> SourceFile:
        """Registra arquivo original no Storage com cálculo de hash SHA-256 (CA-17, AR-10)."""
        file_hash = hashlib.sha256(file_content).hexdigest()
        key = storage_key or f"condos/{condominium_id}/sources/{file_hash}/{filename}"

        return SourceFile.objects.create(
            condominium_id=condominium_id,
            uploaded_by_id=uploaded_by_id,
            storage_key=key,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            file_hash=file_hash,
            state='ready'
        )


class TranscriptionService:
    """Gerencia transcrições de OCR e conferência humana (CA-17, CA-18)."""

    @staticmethod
    def create_initial_transcription(
        document_id: Any,
        condominium_id: Any,
        source_file_id: Any,
        raw_text: str
    ) -> SourceTranscription:
        return SourceTranscription.objects.create(
            document_id=document_id,
            condominium_id=condominium_id,
            source_file_id=source_file_id,
            version=1,
            status='under_review',
            raw_text=raw_text,
            corrected_text=raw_text
        )

    @staticmethod
    def confirm_transcription(
        transcription_id: Any,
        checked_by_id: Any,
        corrected_text: Optional[str] = None
    ) -> SourceTranscription:
        """
        CA-17: Conferência humana da transcrição do original.
        Valida que o documento original foi revisado por um operador humano.
        """
        transcription = SourceTranscription.objects.get(id=transcription_id)
        transcription.status = 'confirmed'
        transcription.checked_by_id = checked_by_id
        transcription.checked_at = timezone.now()
        if corrected_text is not None:
            transcription.corrected_text = corrected_text
        transcription.save()
        return transcription

    @staticmethod
    @transaction.atomic
    def correct_transcription(
        transcription_id: Any,
        checked_by_id: Any,
        corrected_text: str
    ) -> SourceTranscription:
        """
        CA-18: Corrigir transcrição gera nova versão sem simular alteração normativa.
        A versão anterior é marcada como superseded e uma nova é criada.
        """
        old_transcription = SourceTranscription.objects.get(id=transcription_id)
        old_transcription.status = 'superseded'
        old_transcription.save()

        new_transcription = SourceTranscription.objects.create(
            document_id=old_transcription.document_id,
            condominium_id=old_transcription.condominium_id,
            source_file_id=old_transcription.source_file_id,
            version=old_transcription.version + 1,
            status='confirmed',
            raw_text=old_transcription.raw_text,
            corrected_text=corrected_text,
            checked_by_id=checked_by_id,
            checked_at=timezone.now(),
            replaces_transcription_id=old_transcription.id
        )
        return new_transcription


class ProvisionService:
    """
    Gerencia o ciclo de vida dos dispositivos normativos com UUIDs estáveis,
    concorrência otimista (CA-23), detecção de ciclos na hierarquia e sanitização de notas (CA-24).
    """

    @staticmethod
    @transaction.atomic
    def create_provision(
        document_id: Any,
        condominium_id: Any,
        kind: str,
        label: str,
        text: str,
        parent_provision_id: Optional[Any] = None,
        position: int = 0,
        theme: Optional[str] = None,
        change_type: str = 'mantido',
        author_account_id: Optional[Any] = None
    ) -> Provision:
        """Cria dispositivo com UUID permanente e primeira revisão (v1)."""
        provision = Provision.objects.create(
            document_id=document_id,
            condominium_id=condominium_id,
            kind=kind
        )

        etag = calculate_revision_etag(
            provision_id=provision.id,
            revision_number=1,
            text=text,
            label=label,
            parent_provision_id=parent_provision_id
        )

        ProvisionRevision.objects.create(
            provision_id=provision.id,
            document_id=document_id,
            condominium_id=condominium_id,
            revision_number=1,
            parent_provision_id=parent_provision_id,
            position=position,
            label=label.strip(),
            text=text.strip(),
            theme=theme.strip() if theme else None,
            change_type=change_type,
            status='draft',
            author_account_id=author_account_id,
            etag=etag
        )
        return provision

    @staticmethod
    def get_latest_revision(provision_id: Any) -> ProvisionRevision:
        return ProvisionRevision.objects.filter(provision_id=provision_id).order_by('-revision_number').first()

    @staticmethod
    @transaction.atomic
    def update_provision(
        provision_id: Any,
        expected_etag: str,
        text: str,
        label: Optional[str] = None,
        parent_provision_id: Optional[Any] = None,
        position: Optional[int] = None,
        theme: Optional[str] = None,
        change_type: str = 'alterado',
        author_account_id: Optional[Any] = None
    ) -> ProvisionRevision:
        """
        CA-23: Edição com controle de concorrência otimista.
        Exige que expected_etag coincida com o ETag da última revisão existente.
        Se houver divergência, levanta ConcurrencyConflictError sem sobrescrever o banco.
        """
        latest_rev = ProvisionService.get_latest_revision(provision_id)
        if not latest_rev:
            raise ConcurrencyConflictError("Dispositivo não possui revisões registradas.")

        # Validação do ETag (If-Match)
        assert_optimistic_concurrency(latest_rev.etag, expected_etag)

        new_label = label.strip() if label is not None else latest_rev.label
        new_text = text.strip()
        new_parent_id = parent_provision_id if parent_provision_id is not None else latest_rev.parent_provision_id
        new_pos = position if position is not None else latest_rev.position
        new_theme = theme if theme is not None else latest_rev.theme

        # Validação de ciclos na hierarquia
        if new_parent_id:
            def _get_parent(pid: Any) -> Optional[Any]:
                rev = ProvisionService.get_latest_revision(pid)
                return rev.parent_provision_id if rev else None

            assert_no_circular_hierarchy(provision_id, new_parent_id, _get_parent)

        new_revision_number = latest_rev.revision_number + 1
        new_etag = calculate_revision_etag(
            provision_id=provision_id,
            revision_number=new_revision_number,
            text=new_text,
            label=new_label,
            parent_provision_id=new_parent_id
        )

        new_rev = ProvisionRevision.objects.create(
            provision_id=provision_id,
            document_id=latest_rev.document_id,
            condominium_id=latest_rev.condominium_id,
            revision_number=new_revision_number,
            parent_provision_id=new_parent_id,
            position=new_pos,
            label=new_label,
            text=new_text,
            theme=new_theme,
            change_type=change_type,
            status='draft',
            author_account_id=author_account_id,
            etag=new_etag
        )

        # Propaga mapeamentos de origem (CA-19 / CA-21) caso não seja dispositivo novo incluído
        if change_type != 'incluido':
            for m in OriginMapping.objects.filter(revision=latest_rev):
                OriginMapping.objects.create(
                    condominium_id=latest_rev.condominium_id,
                    revision=new_rev,
                    source_provision=m.source_provision,
                    relation_type=m.relation_type,
                    excerpt=m.excerpt,
                    reason=m.reason
                )

        # Propaga referências cruzadas que partem deste dispositivo (CA-22)
        for xr in CrossReference.objects.filter(revision=latest_rev):
            CrossReference.objects.create(
                condominium_id=latest_rev.condominium_id,
                revision=new_rev,
                target_provision=xr.target_provision,
                label_template=xr.label_template,
                status=xr.status
            )

        return new_rev

    @staticmethod
    def get_document_tree(document_id: Any, include_notes: bool = False) -> List[Dict[str, Any]]:
        """
        Retorna a estrutura em árvore de dispositivos na revisão mais recente.
        CA-24: Por padrão include_notes=False, omitindo qualquer nota interna.
        """
        provisions = Provision.objects.filter(document_id=document_id)
        tree_items = []

        for prov in provisions:
            rev = ProvisionService.get_latest_revision(prov.id)
            if not rev or rev.change_type == 'excluido':
                continue

            item = {
                "id": str(prov.id),
                "kind": prov.kind,
                "revision_number": rev.revision_number,
                "label": rev.label,
                "text": rev.text,
                "theme": rev.theme,
                "position": rev.position,
                "parent_provision_id": str(rev.parent_provision_id) if rev.parent_provision_id else None,
                "etag": rev.etag,
                "change_type": rev.change_type,
            }

            if include_notes:
                notes = InternalNote.objects.filter(provision_id=prov.id).values(
                    'id', 'author_account_id', 'content', 'visibility', 'category', 'created_at'
                )
                item["internal_notes"] = list(notes)

            tree_items.append(sanitize_public_provision_dto(item) if not include_notes else item)

        return sorted(tree_items, key=lambda x: (x.get('position', 0), x.get('label', '')))


class InternalNoteService:
    """Gerencia notas internas com visibilidade restrita (CA-24)."""

    @staticmethod
    def create_note(
        condominium_id: Any,
        provision_id: Any,
        author_account_id: Any,
        content: str,
        visibility: str = 'equipe',
        category: str = 'redacao',
        revision_id: Optional[Any] = None
    ) -> InternalNote:
        return InternalNote.objects.create(
            condominium_id=condominium_id,
            provision_id=provision_id,
            revision_id=revision_id,
            author_account_id=author_account_id,
            content=content.strip(),
            visibility=visibility,
            category=category
        )

    @staticmethod
    def list_notes_for_provision(provision_id: Any, user_role: str) -> List[InternalNote]:
        """CA-24: Apenas papéis administrativos autorizados podem ler notas internas."""
        if user_role not in ('sindico', 'admin', 'juridico', 'comissao'):
            raise PrivateNoteAccessForbiddenError("Usuário sem autorização para visualizar notas internas.")
        return list(InternalNote.objects.filter(provision_id=provision_id).order_by('created_at'))


class SnapshotService:
    """
    CA-41: Congelamento atômico de revisões em snapshots imutáveis e reproduzíveis.
    """

    @staticmethod
    @transaction.atomic
    def create_snapshot(
        document_id: Any,
        condominium_id: Any,
        version_label: str,
        frozen_by_id: Any,
        purpose: str = 'consulta_publica'
    ) -> DocumentSnapshot:
        """
        Cria snapshot imutável congelando o estado exato de cada dispositivo.
        Computa o hash SHA-256 reproduzível.
        """
        provisions = Provision.objects.filter(document_id=document_id)
        items_payload = []
        provision_revision_pairs = []

        for prov in provisions:
            latest_rev = ProvisionService.get_latest_revision(prov.id)
            if not latest_rev or latest_rev.change_type == 'excluido':
                continue

            provision_revision_pairs.append((prov, latest_rev))
            items_payload.append({
                "provision_id": prov.id,
                "revision_id": latest_rev.id,
                "rendered_label": latest_rev.label,
                "position": latest_rev.position,
                "parent_provision_id": latest_rev.parent_provision_id,
                "text": latest_rev.text
            })

        content_hash = calculate_snapshot_hash(document_id, version_label, items_payload)

        snapshot = DocumentSnapshot.objects.create(
            document_id=document_id,
            condominium_id=condominium_id,
            version_label=version_label.strip(),
            purpose=purpose,
            frozen_by_id=frozen_by_id,
            content_hash=content_hash,
            is_immutable=True
        )

        for prov, rev in provision_revision_pairs:
            SnapshotItem.objects.create(
                snapshot=snapshot,
                provision=prov,
                provision_revision=rev,
                rendered_label=rev.label,
                position=rev.position,
                parent_provision_id=rev.parent_provision_id
            )

        return snapshot

    @staticmethod
    def get_snapshot_tree(snapshot_id: Any) -> Dict[str, Any]:
        """Reconstrói a árvore exata congelada a partir do snapshot imutável."""
        snapshot = DocumentSnapshot.objects.get(id=snapshot_id)
        items = SnapshotItem.objects.filter(snapshot=snapshot).select_related('provision_revision')

        tree_items = [
            {
                "provision_id": str(it.provision_id),
                "label": it.rendered_label,
                "text": it.provision_revision.text,
                "position": it.position,
                "parent_provision_id": str(it.parent_provision_id) if it.parent_provision_id else None,
                "revision_number": it.provision_revision.revision_number
            }
            for it in items
        ]

        return {
            "snapshot_id": str(snapshot.id),
            "version_label": snapshot.version_label,
            "purpose": snapshot.purpose,
            "content_hash": snapshot.content_hash,
            "frozen_at": snapshot.frozen_at.isoformat(),
            "is_immutable": snapshot.is_immutable,
            "items": sorted(tree_items, key=lambda x: (x['position'], x['label']))
        }
