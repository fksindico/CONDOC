"""
Invariantes do Núcleo Documental — CONDC (Fase 3)
Garante integridade de árvores hierárquicas, concorrência otimista (CA-23),
imutabilidade de snapshots (CA-41) e privacidade de notas internas (CA-24).
"""
import hashlib
import json
from typing import Optional, Callable, Dict, Any, List

from .exceptions import (
    CircularReferenceError,
    ConcurrencyConflictError,
    SnapshotImmutableError,
    PrivateNoteAccessForbiddenError,
)


def calculate_revision_etag(
    provision_id: Any,
    revision_number: int,
    text: str,
    label: str,
    parent_provision_id: Optional[Any] = None
) -> str:
    """Gera hash SHA-256 determinístico para controle de concorrência otimista (ETag)."""
    raw_payload = f"{str(provision_id)}:{revision_number}:{label.strip()}:{text.strip()}:{str(parent_provision_id or '')}"
    return hashlib.sha256(raw_payload.encode('utf-8')).hexdigest()


def assert_optimistic_concurrency(current_etag: str, provided_etag: Optional[str]) -> None:
    """
    CA-23: Garante que edições concorrentes detectem conflito sem sobrescrita silenciosa.
    Se o ETag fornecido no If-Match for nulo ou diferente do atual, levanta ConcurrencyConflictError.
    """
    if not provided_etag:
        raise ConcurrencyConflictError(
            "Cabeçalho 'If-Match' ou ETag esperado é obrigatório para atualização de dispositivo (controle de concorrência otimista)."
        )

    # Remove aspas se fornecido formato HTTP ETag: W/"..." ou "..."
    clean_provided = provided_etag.strip().strip('"').replace('W/', '')
    clean_current = current_etag.strip().strip('"')

    if clean_provided != clean_current:
        raise ConcurrencyConflictError(
            f"Conflito de edição concorrente detectado: o dispositivo foi modificado por outro usuário (ETag esperado '{clean_provided[:8]}...', atual '{clean_current[:8]}...')."
        )


def assert_no_circular_hierarchy(
    provision_id: Any,
    new_parent_id: Optional[Any],
    get_parent_func: Callable[[Any], Optional[Any]],
    max_depth: int = 50
) -> None:
    """
    Valida que a árvore de dispositivos normativos não contenha ciclos.
    Um dispositivo não pode ser pai de si mesmo nem descender de si mesmo.
    """
    if not new_parent_id:
        return

    prov_str = str(provision_id)
    parent_str = str(new_parent_id)

    if prov_str == parent_str:
        raise CircularReferenceError(
            f"Referência circular detectada: o dispositivo '{prov_str}' não pode ser pai de si mesmo."
        )

    current_id = new_parent_id
    depth = 0
    visited = {prov_str, parent_str}

    while current_id and depth < max_depth:
        ancestor_id = get_parent_func(current_id)
        if not ancestor_id:
            break

        ancestor_str = str(ancestor_id)
        if ancestor_str == prov_str:
            raise CircularReferenceError(
                f"Referência circular detectada: o dispositivo pai '{ancestor_str}' é descendente de '{prov_str}'."
            )

        if ancestor_str in visited:
            raise CircularReferenceError(
                f"Ciclo detectado na hierarquia de dispositivos no nó '{ancestor_str}'."
            )

        visited.add(ancestor_str)
        current_id = ancestor_id
        depth += 1

    if depth >= max_depth:
        raise CircularReferenceError(
            f"Profundidade máxima de hierarquia excedida ({max_depth} níveis). Possível ciclo não detectado."
        )


def calculate_snapshot_hash(document_id: Any, version_label: str, items: List[Dict[str, Any]]) -> str:
    """
    CA-41: Calcula hash SHA-256 reproduzível sobre toda a árvore do snapshot imutável.
    Garante integridade e auditoria de versão de referência.
    """
    sorted_items = sorted(
        items,
        key=lambda x: (x.get('position', 0), str(x.get('provision_id', '')))
    )

    canonical_data = {
        "document_id": str(document_id),
        "version_label": str(version_label).strip(),
        "items": [
            {
                "provision_id": str(it.get('provision_id')),
                "revision_id": str(it.get('revision_id')),
                "rendered_label": str(it.get('rendered_label', '')),
                "position": it.get('position', 0),
                "parent_provision_id": str(it.get('parent_provision_id')) if it.get('parent_provision_id') else None,
                "text_hash": hashlib.sha256(str(it.get('text', '')).encode('utf-8')).hexdigest()
            }
            for it in sorted_items
        ]
    }

    serialized = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def assert_snapshot_immutable(is_immutable: bool) -> None:
    """CA-41: Garante que um snapshot congelado não seja alterado."""
    if is_immutable:
        raise SnapshotImmutableError(
            "Este snapshot documental é estritamente imutável e congelado. Nenhuma modificação é permitida."
        )


def sanitize_public_provision_dto(provision_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    CA-24: Sanitiza DTO público de dispositivo, removendo notas internas,
    tarefas restritas e campos confidenciais de governança administrativa.
    """
    cleaned = dict(provision_dict)
    # Remove terminantemente qualquer menção a notas internas
    cleaned.pop('internal_notes', None)
    cleaned.pop('notes', None)
    cleaned.pop('internal_tasks', None)
    cleaned.pop('legal_opinions', None)
    return cleaned
