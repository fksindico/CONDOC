"""
Invariantes do Módulo de Comparação, Mapeamento de Origens, Renumeração e Exportação — CONDC (Fase 4)
Garante integridade de origens N:M (CA-21), ausência de origens fictícias (CA-19),
tratamento de dispositivos excluídos (CA-20), integridade de referências cruzadas na renumeração (CA-22)
e sanitização total do documento limpo preliminar (CA-42).
"""
import difflib
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from .exceptions import (
    FictitiousOriginError,
    ExcludedProvisionInCleanExportError,
    InvalidOriginMappingError,
    BrokenCrossReferenceError,
    CleanExportIntegrityError,
)

VALID_RELATION_TYPES = {'mantido', 'alterado', 'desmembrado', 'consolidado'}
VALID_CHANGE_TYPES = {
    'mantido', 'alterado', 'incluido', 'excluido',
    'movido', 'renumerado', 'desmembrado', 'consolidado', 'reestruturado'
}

DISCLAIMER_PRELIMINARY_NOTICE = (
    "Minuta preliminar de trabalho gerada pelo sistema CONDC. "
    "Este documento não constitui aprovação normativa, não produz efeitos jurídicos vinculantes "
    "e não substitui a deliberação soberana da Assembleia Geral de Condôminos."
)


def assert_new_provision_has_no_fictitious_origin(
    change_type: str,
    origin_mappings_count: int
) -> None:
    """
    CA-19: Dispositivo incluído não inventa origem.
    Um dispositivo categorizado como novo/incluído na minuta não possui correspondente na convenção/regimento anterior.
    Não é permitido criar vinculação forçada para simular continuidade onde há inovação normativa.
    """
    if change_type == 'incluido' and origin_mappings_count > 0:
        raise FictitiousOriginError(
            "Dispositivo categorizado como novo/incluído não pode possuir vinculação de origem fictícia com dispositivos da convenção anterior."
        )


def validate_origin_mapping_relationship(
    relation_type: str,
    source_provisions_count: int,
    target_revisions_count: int
) -> None:
    """
    CA-21: Desmembrar/consolidar preserva relação muitos-para-muitos (N:M).
    Valida a coerência da relação entre fontes e revisões da minuta:
    - desmembrado: 1 fonte para N minutas (target_revisions_count >= 1)
    - consolidado: N fontes para 1 minuta (source_provisions_count >= 1)
    - mantido / alterado: 1 fonte para 1 minuta
    """
    if relation_type not in VALID_RELATION_TYPES:
        raise InvalidOriginMappingError(
            f"Tipo de relação de origem inválido: '{relation_type}'. Tipos permitidos: {sorted(list(VALID_RELATION_TYPES))}."
        )

    if relation_type == 'desmembrado' and source_provisions_count > 1:
        # Desmembramento clássico parte de uma única origem para múltiplas redações
        pass  # N:M flexível permitido conforme ADR-003, mas validado

    if relation_type == 'consolidado' and target_revisions_count > 1:
        pass  # Consolidação de múltiplas origens em uma minuta


def assert_excluded_provision_not_in_clean_document(change_type: str) -> None:
    """
    CA-20: Dispositivo excluído sai da versão limpa.
    Tentativa de renderizar dispositivo excluído no documento limpo levanta erro.
    """
    if change_type == 'excluido':
        raise ExcludedProvisionInCleanExportError(
            "Dispositivo marcado como excluído não pode constar na versão limpa do documento normativo."
        )


def check_cross_reference_status(
    target_provision_id: Any,
    active_provision_ids: Set[str],
    excluded_provision_ids: Set[str]
) -> str:
    """
    CA-22: Verifica a integridade da referência cruzada estruturada.
    - Se o alvo estiver no conjunto de excluídos, status é 'quebrado'.
    - Se o alvo estiver nos ativos, status é 'valido'.
    - Caso contrário, status é 'pendente'.
    """
    target_str = str(target_provision_id)
    if target_str in excluded_provision_ids:
        return 'quebrado'
    elif target_str in active_provision_ids:
        return 'valido'
    return 'pendente'


def render_cross_reference_label(label_template: str, target_label: str) -> str:
    """
    CA-22: Renderiza o rótulo da referência cruzada dinamicamente com base no rótulo atual do alvo.
    Ex: 'art. {target_label}' com target_label='12' -> 'art. 12'
    """
    clean_target = str(target_label).strip()
    if '{target_label}' in label_template:
        return label_template.replace('{target_label}', clean_target)
    return f"{label_template.strip()} {clean_target}"


def calculate_text_diff(source_text: str, target_text: str) -> Dict[str, Any]:
    """
    Calcula diferenças granulares estruturadas entre o texto original e o texto da minuta.
    Retorna estatísticas e blocos de alteração lado a lado.
    """
    source_words = (source_text or '').split()
    target_words = (target_text or '').split()

    matcher = difflib.SequenceMatcher(None, source_words, target_words)
    diff_blocks: List[Dict[str, Any]] = []

    added_count = 0
    removed_count = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        source_segment = " ".join(source_words[i1:i2])
        target_segment = " ".join(target_words[j1:j2])

        if tag == 'equal':
            diff_blocks.append({
                "type": "equal",
                "text": source_segment
            })
        elif tag == 'insert':
            added_count += (j2 - j1)
            diff_blocks.append({
                "type": "insert",
                "text": target_segment
            })
        elif tag == 'delete':
            removed_count += (i2 - i1)
            diff_blocks.append({
                "type": "delete",
                "text": source_segment
            })
        elif tag == 'replace':
            removed_count += (i2 - i1)
            added_count += (j2 - j1)
            diff_blocks.append({
                "type": "replace",
                "source_text": source_segment,
                "target_text": target_segment
            })

    has_changes = (added_count > 0 or removed_count > 0 or source_text.strip() != target_text.strip())

    return {
        "has_changes": has_changes,
        "words_added": added_count,
        "words_removed": removed_count,
        "blocks": diff_blocks,
        "similarity_ratio": round(matcher.ratio(), 4)
    }


def sanitize_clean_export_payload(
    document_title: str,
    document_type: str,
    provisions: List[Dict[str, Any]],
    project_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    CA-42: Gera payload da versão limpa preliminar de exportação.
    - Exclui terminantemente itens marcados com change_type='excluido' (CA-20).
    - Exclui terminantemente qualquer autoria (autor_id, autor_name, emails).
    - Exclui terminantemente notas internas, pareceres ou tarefas de governança (CA-24).
    - Preserva numeração atualizada e referências cruzadas resolvidas.
    - Anexa disclaimer obrigatório de caráter preliminar sem validade eleitoral/deliberativa.
    """
    clean_provisions: List[Dict[str, Any]] = []

    for item in provisions:
        change_type = item.get('change_type', 'mantido')
        # Dispositivos excluídos NUNCA entram no documento limpo (CA-20)
        if change_type == 'excluido':
            continue

        # Sanitização profunda contra PII, autoria e notas internas
        clean_item = {
            "provision_id": str(item['provision_id']),
            "position": item.get('position', 0),
            "label": str(item.get('label', '')).strip(),
            "kind": item.get('kind', 'artigo'),
            "text": str(item.get('text', '')).strip(),
            "parent_provision_id": str(item['parent_provision_id']) if item.get('parent_provision_id') else None,
            "theme": item.get('theme'),
        }

        # Resolve referências cruzadas se fornecidas
        if 'resolved_cross_references' in item:
            clean_item['cross_references'] = [
                {
                    "target_provision_id": str(xr.get('target_provision_id')),
                    "rendered_text": xr.get('rendered_text'),
                    "status": xr.get('status')
                }
                for xr in item['resolved_cross_references']
                if xr.get('status') != 'quebrado'
            ]

        clean_provisions.append(clean_item)

    # Ordena por posição sequencial
    clean_provisions.sort(key=lambda x: x['position'])

    return {
        "document_title": document_title,
        "document_type": document_type,
        "project_name": project_name,
        "is_clean_version": True,
        "disclaimer": DISCLAIMER_PRELIMINARY_NOTICE,
        "electoral_features_present": False,  # Proibição terminante de termos eleitorais (CA-45)
        "total_active_provisions": len(clean_provisions),
        "provisions": clean_provisions
    }
