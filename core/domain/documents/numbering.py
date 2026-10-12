"""
Motor de Numeração Determinística e Renumeração LC 95/98 — CONDOC (ED-OSS-2.0)
Implementa formatação exata conforme a Lei Complementar 95/1998 para Artigos,
Parágrafos (Único e múltiplos), Incisos romanos, Alíneas literais e Itens arábicos,
além de renumeração sequencial completa de árvores e listas de dispositivos.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple, Union

from .grammar import (
    ALINEA,
    ARTICLE,
    CAPUT,
    CHAPTER,
    DOCUMENT_ROOT,
    INCISO,
    ITEM,
    LEGAL_BOOK,
    LEGAL_PARAGRAPH,
    LEGAL_PART,
    LEGAL_SECTION,
    LEGAL_TITLE,
    SUBSECTION,
    NormativeNode,
)


# ---------------------------------------------------------------------------
# Conversores Auxiliares (Romanos e Literais)
# ---------------------------------------------------------------------------

_ROMAN_MAP: List[Tuple[int, str]] = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]

_ROMAN_CHAR_VALUES: Dict[str, int] = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}


def int_to_roman(value: int) -> str:
    """Converte inteiro positivo (1 a 3999) para algarismos romanos maiúsculos."""
    if value <= 0:
        raise ValueError(f"Valor para algarismo romano deve ser estritamente positivo (recebido: {value}).")
    if value > 3999:
        raise ValueError(f"Valor {value} excede o limite máximo suportado para numeração romana (3999).")

    result = []
    remaining = value
    for val, numeral in _ROMAN_MAP:
        while remaining >= val:
            result.append(numeral)
            remaining -= val
    return "".join(result)


def roman_to_int(roman: str) -> int:
    """Converte numeral romano maiúsculo para inteiro."""
    clean = roman.strip().upper()
    if not clean:
        raise ValueError("String romana vazia.")

    total = 0
    prev_val = 0
    for char in reversed(clean):
        val = _ROMAN_CHAR_VALUES.get(char)
        if val is None:
            raise ValueError(f"Caractere romano inválido: '{char}'.")
        if val < prev_val:
            total -= val
        else:
            total += val
        prev_val = val
    return total


def int_to_letter(value: int) -> str:
    """
    Converte inteiro positivo para letras minúsculas:
    1 -> 'a', 2 -> 'b', ..., 26 -> 'z', 27 -> 'aa', 28 -> 'ab', etc.
    """
    if value <= 0:
        raise ValueError(f"Valor para alínea deve ser estritamente positivo (recebido: {value}).")

    result = []
    curr = value
    while curr > 0:
        curr -= 1
        result.append(chr(ord("a") + (curr % 26)))
        curr //= 26
    return "".join(reversed(result))


def letter_to_int(letter_seq: str) -> int:
    """Converte sequência de letras minúsculas de volta para inteiro (1-indexed)."""
    clean = letter_seq.strip().lower()
    if not clean or not clean.isalpha():
        raise ValueError(f"Sequência de letras de alínea inválida: '{letter_seq}'.")

    total = 0
    for ch in clean:
        total = total * 26 + (ord(ch) - ord("a") + 1)
    return total


# ---------------------------------------------------------------------------
# Formatadores Determinísticos Conforme a LC 95/98 (Arts. 10 e 11)
# ---------------------------------------------------------------------------

def format_article_number(value: int, suffix: str = "") -> str:
    """
    LC 95/98, Art. 10, I:
    - 1 a 9: numerais ordinais ('Art. 1º' a 'Art. 9º')
    - 10 em diante: numerais cardinais ('Art. 10', 'Art. 11', etc.)
    Suporta sufixos adicionais (ex.: Art. 10-A, Art. 1º-A).
    """
    if value <= 0:
        raise ValueError(f"Número de artigo deve ser positivo (recebido: {value}).")

    if 1 <= value <= 9:
        base = f"Art. {value}º"
    else:
        base = f"Art. {value}"

    if suffix.strip():
        return f"{base}-{suffix.strip()}"
    return base


def format_paragraph_number(value: int, total_in_article: int = 1, suffix: str = "") -> str:
    """
    LC 95/98, Art. 10, III:
    - Se houver apenas 1 parágrafo no artigo: 'Parágrafo único.'
    - Se houver múltiplos parágrafos:
      - 1 a 9: ordinais com símbolo de parágrafo ('§ 1º' a '§ 9º')
      - 10 em diante: cardinais ('§ 10', '§ 11', etc.)
    """
    if value <= 0:
        raise ValueError(f"Número de parágrafo deve ser positivo (recebido: {value}).")

    clean_suffix = suffix.strip()
    if total_in_article == 1:
        if clean_suffix:
            return f"Parágrafo único-{clean_suffix}."
        return "Parágrafo único."

    if 1 <= value <= 9:
        base = f"§ {value}º"
    else:
        base = f"§ {value}"

    if clean_suffix:
        return f"{base}-{clean_suffix}"
    return base


def format_inciso_number(value: int, suffix: str = "") -> str:
    """
    LC 95/98, Art. 10, II:
    Representados por algarismos romanos maiúsculos seguidos de hífen:
    'I -', 'II -', 'III -', 'X -', etc.
    """
    roman = int_to_roman(value)
    clean_suffix = suffix.strip()
    if clean_suffix:
        return f"{roman}-{clean_suffix} -"
    return f"{roman} -"


def format_alinea_number(value: int, suffix: str = "") -> str:
    """
    LC 95/98, Art. 10, IV:
    Representadas por letras minúsculas seguidas de parêntese fechado:
    'a)', 'b)', 'c)', etc.
    """
    letter = int_to_letter(value)
    clean_suffix = suffix.strip()
    if clean_suffix:
        return f"{letter}-{clean_suffix})"
    return f"{letter})"


def format_item_number(value: int, suffix: str = "") -> str:
    """
    LC 95/98, Art. 10, V:
    Representados por números arábicos seguidos de ponto:
    '1.', '2.', '3.', etc.
    """
    if value <= 0:
        raise ValueError(f"Número de item deve ser positivo (recebido: {value}).")
    clean_suffix = suffix.strip()
    if clean_suffix:
        return f"{value}-{clean_suffix}."
    return f"{value}."


def format_chapter_number(value: int) -> str:
    """LC 95/98: Capítulos identificados por numerais romanos maiúsculos ('CAPÍTULO I')."""
    return f"CAPÍTULO {int_to_roman(value)}"


def format_title_number(value: int) -> str:
    """LC 95/98: Títulos identificados por numerais romanos maiúsculos ('TÍTULO I')."""
    return f"TÍTULO {int_to_roman(value)}"


def format_section_number(value: int) -> str:
    """LC 95/98: Seções identificadas por numerais romanos maiúsculos ('Seção I')."""
    return f"Seção {int_to_roman(value)}"


def format_subsection_number(value: int) -> str:
    """LC 95/98: Subseções identificadas por numerais romanos maiúsculos ('Subseção I')."""
    return f"Subseção {int_to_roman(value)}"


def format_book_number(value: int) -> str:
    """LC 95/98: Livros identificados por numerais romanos maiúsculos ('LIVRO I')."""
    return f"LIVRO {int_to_roman(value)}"


def format_part_number(value: int) -> str:
    """LC 95/98: Partes identificadas por numerais romanos maiúsculos ('PARTE I')."""
    return f"PARTE {int_to_roman(value)}"


# ---------------------------------------------------------------------------
# Motor de Renumeração Sequencial Determinística
# ---------------------------------------------------------------------------

def _get_node_prop(node: Any, prop: str, default: Any = None) -> Any:
    """Obtém propriedade de nó, seja instância de NormativeNode ou dict."""
    if isinstance(node, dict):
        return node.get(prop, default)
    return getattr(node, prop, default)


def _set_node_prop(node: Any, prop: str, value: Any) -> None:
    """Define propriedade de nó, seja instância de NormativeNode ou dict."""
    if isinstance(node, dict):
        node[prop] = value
    else:
        setattr(node, prop, value)


def _get_children(node: Any) -> List[Any]:
    """Retorna lista de filhos do nó."""
    if isinstance(node, dict):
        return node.get("children", [])
    return getattr(node, "children", [])


def renumber_normative_tree(
    target: Union[NormativeNode, Dict[str, Any], List[Union[NormativeNode, Dict[str, Any]]]],
    start_article: int = 1,
    in_place: bool = True,
) -> Union[NormativeNode, Dict[str, Any], List[Union[NormativeNode, Dict[str, Any]]]]:
    """
    Renumera determinística e sequencialmente todos os dispositivos normativos
    conforme a LC 95/98:
    - Artigos: Sequência global contínua (Art. 1º a 9º, Art. 10...)
    - Caput: Herda do artigo, rótulo vazio ""
    - Parágrafos: Se único no artigo -> 'Parágrafo único.'; se múltiplos -> '§ 1º'...'§ 10'
    - Incisos: 'I -', 'II -'...
    - Alíneas: 'a)', 'b)'...
    - Itens: '1.', '2.'...
    - Capítulos e Seções: 'CAPÍTULO I', 'Seção I'...
    """
    if not in_place:
        target = copy.deepcopy(target)

    if isinstance(target, list):
        # Para lista flat com parent_id
        return _renumber_flat_list(target, start_article=start_article)

    # Verifica se dicionário encapsula documento
    root = target["root"] if isinstance(target, dict) and "root" in target and isinstance(target["root"], dict) else target

    # Contexto de numeração sequencial
    article_counter = [start_article]
    chapter_counter = [1]
    title_counter = [1]

    _renumber_node_recursive(root, article_counter, chapter_counter, title_counter)
    return target


def _renumber_node_recursive(
    node: Any,
    article_counter: List[int],
    chapter_counter: List[int],
    title_counter: List[int],
    section_counter: Optional[List[int]] = None,
    subsection_counter: Optional[List[int]] = None,
    book_counter: Optional[List[int]] = None,
    part_counter: Optional[List[int]] = None,
) -> None:
    """Percorre recursivamente a árvore aplicando numeração nos nós e seus filhos."""
    if section_counter is None:
        section_counter = [1]
    if subsection_counter is None:
        subsection_counter = [1]
    if book_counter is None:
        book_counter = [1]
    if part_counter is None:
        part_counter = [1]

    node_type = _get_node_prop(node, "type")

    # Agrupadores
    if node_type == CHAPTER:
        idx = chapter_counter[0]
        chapter_counter[0] += 1
        label = format_chapter_number(idx)
        _set_node_prop(node, "rendered_label", label)
        _set_node_prop(node, "numbering", {"policy": "sequential", "value": idx, "rendered_label": label})

    elif node_type == LEGAL_TITLE:
        idx = title_counter[0]
        title_counter[0] += 1
        label = format_title_number(idx)
        _set_node_prop(node, "rendered_label", label)
        _set_node_prop(node, "numbering", {"policy": "sequential", "value": idx, "rendered_label": label})

    elif node_type == LEGAL_SECTION:
        idx = section_counter[0]
        section_counter[0] += 1
        label = format_section_number(idx)
        _set_node_prop(node, "rendered_label", label)
        _set_node_prop(node, "numbering", {"policy": "sequential", "value": idx, "rendered_label": label})

    elif node_type == SUBSECTION:
        idx = subsection_counter[0]
        subsection_counter[0] += 1
        label = format_subsection_number(idx)
        _set_node_prop(node, "rendered_label", label)
        _set_node_prop(node, "numbering", {"policy": "sequential", "value": idx, "rendered_label": label})

    elif node_type == LEGAL_BOOK:
        idx = book_counter[0]
        book_counter[0] += 1
        label = format_book_number(idx)
        _set_node_prop(node, "rendered_label", label)
        _set_node_prop(node, "numbering", {"policy": "sequential", "value": idx, "rendered_label": label})

    elif node_type == LEGAL_PART:
        idx = part_counter[0]
        part_counter[0] += 1
        label = format_part_number(idx)
        _set_node_prop(node, "rendered_label", label)
        _set_node_prop(node, "numbering", {"policy": "sequential", "value": idx, "rendered_label": label})

    # Dispositivo Artigo
    elif node_type == ARTICLE:
        art_idx = article_counter[0]
        article_counter[0] += 1
        art_label = format_article_number(art_idx)
        _set_node_prop(node, "rendered_label", art_label)
        _set_node_prop(node, "numbering", {"policy": "sequential", "value": art_idx, "rendered_label": art_label})

        # Processamento especializado dos filhos do artigo
        children = _get_children(node)
        _renumber_article_children(children, art_idx)
        return  # Filhos do artigo já foram exaustivamente processados

    # Visita filhos de outros nós (ex.: root, chapter, section)
    children = _get_children(node)
    for child in children:
        _renumber_node_recursive(
            child, article_counter, chapter_counter, title_counter,
            section_counter, subsection_counter, book_counter, part_counter
        )


def _renumber_article_children(children: List[Any], article_number: int) -> None:
    """Renumera a hierarquia interna de um Artigo (Caput, Parágrafos, Incisos, etc.)."""
    paragraphs: List[Any] = []
    direct_incisos: List[Any] = []

    for child in children:
        c_type = _get_node_prop(child, "type")
        if c_type == CAPUT:
            # Caput herda artigo sem rótulo próprio separado
            _set_node_prop(child, "rendered_label", "")
            _set_node_prop(child, "numbering", {"policy": "inherited", "value": article_number, "rendered_label": ""})
        elif c_type == LEGAL_PARAGRAPH:
            paragraphs.append(child)
        elif c_type == INCISO:
            direct_incisos.append(child)

    # Renumera parágrafos
    total_paragraphs = len(paragraphs)
    for p_idx, para in enumerate(paragraphs, start=1):
        p_label = format_paragraph_number(p_idx, total_in_article=total_paragraphs)
        _set_node_prop(para, "rendered_label", p_label)
        _set_node_prop(para, "numbering", {"policy": "sequential", "value": p_idx, "rendered_label": p_label})

        # Incisos deste parágrafo
        para_children = _get_children(para)
        _renumber_incisos(para_children)

    # Renumera incisos diretos do artigo
    if direct_incisos:
        _renumber_incisos(direct_incisos)


def _renumber_incisos(inciso_list: List[Any]) -> None:
    """Renumera incisos sequencialmente e seus desdobramentos em alíneas e itens."""
    for i_idx, inciso in enumerate(inciso_list, start=1):
        if _get_node_prop(inciso, "type") != INCISO:
            continue
        i_label = format_inciso_number(i_idx)
        _set_node_prop(inciso, "rendered_label", i_label)
        _set_node_prop(inciso, "numbering", {"policy": "sequential", "value": i_idx, "rendered_label": i_label})

        # Alíneas deste inciso
        inciso_children = _get_children(inciso)
        _renumber_alineas(inciso_children)


def _renumber_alineas(alinea_list: List[Any]) -> None:
    """Renumera alíneas sequencialmente e seus desdobramentos em itens."""
    for a_idx, alinea in enumerate(alinea_list, start=1):
        if _get_node_prop(alinea, "type") != ALINEA:
            continue
        a_label = format_alinea_number(a_idx)
        _set_node_prop(alinea, "rendered_label", a_label)
        _set_node_prop(alinea, "numbering", {"policy": "sequential", "value": a_idx, "rendered_label": a_label})

        # Itens desta alínea
        alinea_children = _get_children(alinea)
        _renumber_itens(alinea_children)


def _renumber_itens(item_list: List[Any]) -> None:
    """Renumera itens sequencialmente arábicos."""
    for it_idx, item in enumerate(item_list, start=1):
        if _get_node_prop(item, "type") != ITEM:
            continue
        it_label = format_item_number(it_idx)
        _set_node_prop(item, "rendered_label", it_label)
        _set_node_prop(item, "numbering", {"policy": "sequential", "value": it_idx, "rendered_label": it_label})


def _renumber_flat_list(
    nodes: List[Union[NormativeNode, Dict[str, Any]]],
    start_article: int = 1,
) -> List[Union[NormativeNode, Dict[str, Any]]]:
    """Renumera uma lista plana de nós reconstruindo hierarquia temporária."""
    from .grammar import _build_nested_from_flat

    # Agrupa por parent_id
    children_map: Dict[Optional[str], List[Any]] = {}
    for n in nodes:
        pid = _get_node_prop(n, "parent_id")
        children_map.setdefault(pid, []).append(n)

    roots = children_map.get(None, [])
    for root in roots:
        nested_tree = _build_nested_from_flat(root, children_map)
        renumber_normative_tree(nested_tree, start_article=start_article)

        # Copia de volta os rótulos e numerações para os nós originais
        _sync_labels_back_to_flat(nested_tree, {str(_get_node_prop(n, "id")): n for n in nodes})

    return nodes


def _sync_labels_back_to_flat(nested_node: NormativeNode, flat_dict: Dict[str, Any]) -> None:
    """Sincroniza labels e numerações de árvore aninhada de volta para lista plana."""
    flat_node = flat_dict.get(nested_node.id)
    if flat_node:
        _set_node_prop(flat_node, "rendered_label", nested_node.rendered_label)
        _set_node_prop(flat_node, "numbering", nested_node.numbering)
    for c in nested_node.children:
        _sync_labels_back_to_flat(c, flat_dict)


# ---------------------------------------------------------------------------
# Prévia de Renumeração (Diff Auditável — EDOSS-BL-09)
# ---------------------------------------------------------------------------

def preview_renumbering(
    target: Union[NormativeNode, Dict[str, Any], List[Union[NormativeNode, Dict[str, Any]]]],
    start_article: int = 1,
) -> List[Dict[str, Any]]:
    """
    Gera relatório de prévia (diff) de renumeração sem alterar a estrutura original.
    Permite ao operador e ao síndico conferirem o impacto antes de aplicar.
    """
    target_copy = copy.deepcopy(target)
    original_labels: Dict[str, Optional[str]] = {}

    def _collect_original_labels(node: Any) -> None:
        nid = str(_get_node_prop(node, "id"))
        original_labels[nid] = _get_node_prop(node, "rendered_label")
        for c in _get_children(node):
            _collect_original_labels(c)

    if isinstance(target, list):
        for n in target:
            original_labels[str(_get_node_prop(n, "id"))] = _get_node_prop(n, "rendered_label")
    else:
        root = target["root"] if isinstance(target, dict) and "root" in target and isinstance(target["root"], dict) else target
        _collect_original_labels(root)

    # Aplica renumeração na cópia
    renumber_normative_tree(target_copy, start_article=start_article, in_place=True)

    diffs: List[Dict[str, Any]] = []

    def _collect_diffs(node: Any) -> None:
        nid = str(_get_node_prop(node, "id"))
        ntype = _get_node_prop(node, "type")
        old_lbl = original_labels.get(nid)
        new_lbl = _get_node_prop(node, "rendered_label")
        numbering = _get_node_prop(node, "numbering")

        norm_old = (old_lbl or "").strip()
        norm_new = (new_lbl or "").strip()
        if norm_old != norm_new:
            diffs.append({
                "node_id": nid,
                "type": ntype,
                "old_rendered_label": old_lbl,
                "new_rendered_label": new_lbl,
                "numbering": numbering,
            })
        for c in _get_children(node):
            _collect_diffs(c)

    if isinstance(target_copy, list):
        for n in target_copy:
            nid = str(_get_node_prop(n, "id"))
            ntype = _get_node_prop(n, "type")
            old_lbl = original_labels.get(nid)
            new_lbl = _get_node_prop(n, "rendered_label")
            norm_old = (old_lbl or "").strip()
            norm_new = (new_lbl or "").strip()
            if norm_old != norm_new:
                diffs.append({
                    "node_id": nid,
                    "type": ntype,
                    "old_rendered_label": old_lbl,
                    "new_rendered_label": new_lbl,
                    "numbering": _get_node_prop(n, "numbering"),
                })

    else:
        root_copy = target_copy["root"] if isinstance(target_copy, dict) and "root" in target_copy and isinstance(target_copy["root"], dict) else target_copy
        _collect_diffs(root_copy)

    return diffs
