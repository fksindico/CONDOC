"""
Gramática Normativa e Estrutura Hierárquica LC 95/98 — CONDOC (ED-OSS-2.0)
Define os tipos de nós, classes de dispositivos, regras estritas de contenção,
validação de Caput obrigatório e salvaguardas contra ciclos e profundidade excessiva.
Em estrita conformidade com a Lei Complementar nº 95/1998 e PRD Complementar ED-OSS-2.0.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from .exceptions import (
    CircularReferenceError,
    DocumentDomainError,
    GrammarValidationError,
    MissingCaputError,
    InvalidContainmentError,
    MaxDepthExceededError,
)


# ---------------------------------------------------------------------------
# Constantes e Enum dos Nós Normativos (Catálogo ED-OSS-2.0 / LC 95)
# ---------------------------------------------------------------------------

class NormativeNodeType(str, Enum):
    """Tipos semânticos canônicos de dispositivos e agrupadores normativos."""
    # Raiz e Metadados do Documento
    DOCUMENT_ROOT = "document_root"
    COVER_BLOCK = "cover_block"
    DOCUMENT_HEADING = "document_heading"
    PREAMBLE = "preamble"
    SCOPE_BLOCK = "scope_block"
    TOC_BLOCK = "toc_block"

    # Agrupadores Normativos Maiores
    LEGAL_PART = "legal_part"
    LEGAL_BOOK = "legal_book"
    LEGAL_TITLE = "legal_title"
    CHAPTER = "chapter"
    LEGAL_SECTION = "legal_section"
    SUBSECTION = "subsection"

    # Dispositivos Normativos Nucleares (LC 95/98)
    ARTICLE = "article"
    CAPUT = "caput"
    LEGAL_PARAGRAPH = "legal_paragraph"
    INCISO = "inciso"
    ALINEA = "alinea"
    ITEM = "item"

    # Elementos Complementares e Documentais
    LEGACY_CLAUSE = "legacy_clause"
    NARRATIVE_BLOCK = "narrative_block"
    NORMATIVE_TABLE = "normative_table"
    FIGURE = "figure"
    ANNEX = "annex"
    SIGNATURE_GROUP = "signature_group"
    UNSUPPORTED_PRESERVED = "unsupported_preserved"


# Constantes exportadas diretamente para conveniência
DOCUMENT_ROOT = NormativeNodeType.DOCUMENT_ROOT.value
COVER_BLOCK = NormativeNodeType.COVER_BLOCK.value
DOCUMENT_HEADING = NormativeNodeType.DOCUMENT_HEADING.value
PREAMBLE = NormativeNodeType.PREAMBLE.value
SCOPE_BLOCK = NormativeNodeType.SCOPE_BLOCK.value
TOC_BLOCK = NormativeNodeType.TOC_BLOCK.value

LEGAL_PART = NormativeNodeType.LEGAL_PART.value
LEGAL_BOOK = NormativeNodeType.LEGAL_BOOK.value
LEGAL_TITLE = NormativeNodeType.LEGAL_TITLE.value
CHAPTER = NormativeNodeType.CHAPTER.value
LEGAL_SECTION = NormativeNodeType.LEGAL_SECTION.value
SUBSECTION = NormativeNodeType.SUBSECTION.value

ARTICLE = NormativeNodeType.ARTICLE.value
CAPUT = NormativeNodeType.CAPUT.value
LEGAL_PARAGRAPH = NormativeNodeType.LEGAL_PARAGRAPH.value
INCISO = NormativeNodeType.INCISO.value
ALINEA = NormativeNodeType.ALINEA.value
ITEM = NormativeNodeType.ITEM.value

LEGACY_CLAUSE = NormativeNodeType.LEGACY_CLAUSE.value
NARRATIVE_BLOCK = NormativeNodeType.NARRATIVE_BLOCK.value
NORMATIVE_TABLE = NormativeNodeType.NORMATIVE_TABLE.value
FIGURE = NormativeNodeType.FIGURE.value
ANNEX = NormativeNodeType.ANNEX.value
SIGNATURE_GROUP = NormativeNodeType.SIGNATURE_GROUP.value
UNSUPPORTED_PRESERVED = NormativeNodeType.UNSUPPORTED_PRESERVED.value

MAX_TREE_DEPTH = 30


# ---------------------------------------------------------------------------
# Mapeamento de termos em português (legado/ORM) para o padrão canônico ED-OSS-2.0
# ---------------------------------------------------------------------------

PORTUGUESE_TYPE_MAPPING: Dict[str, str] = {
    "artigo": ARTICLE,
    "caput": CAPUT,
    "paragrafo": LEGAL_PARAGRAPH,
    "inciso": INCISO,
    "alinea": ALINEA,
    "item": ITEM,
    "capitulo": CHAPTER,
    "secao": LEGAL_SECTION,
    "subsecao": SUBSECTION,
    "titulo": LEGAL_TITLE,
    "preambulo": PREAMBLE,
    "anexo": ANNEX,
    "tabela": NORMATIVE_TABLE,
    "assinaturas": SIGNATURE_GROUP,
    "livro": LEGAL_BOOK,
    "parte": LEGAL_PART,
    "figura": FIGURE,
    "escopo": SCOPE_BLOCK,
    "sumario": TOC_BLOCK,
    "indice": TOC_BLOCK,
    "cabecalho": DOCUMENT_HEADING,
    "capa": COVER_BLOCK,
    "clausula": LEGACY_CLAUSE,
    "narrativa": NARRATIVE_BLOCK,
}


def normalize_node_type(raw_type: str) -> str:
    """Normaliza o tipo do nó, aceitando tanto a nomenclatura em inglês quanto português."""
    cleaned = raw_type.lower().strip()
    return PORTUGUESE_TYPE_MAPPING.get(cleaned, cleaned)


# ---------------------------------------------------------------------------
# Regras de Contenção Estrita (Allowed Children e Allowed Parents)
# ---------------------------------------------------------------------------

ALLOWED_CHILDREN: Dict[str, Set[str]] = {
    DOCUMENT_ROOT: {
        COVER_BLOCK,
        DOCUMENT_HEADING,
        PREAMBLE,
        SCOPE_BLOCK,
        TOC_BLOCK,
        LEGAL_PART,
        LEGAL_BOOK,
        LEGAL_TITLE,
        CHAPTER,
        LEGAL_SECTION,
        SUBSECTION,
        ARTICLE,
        LEGACY_CLAUSE,
        NARRATIVE_BLOCK,
        NORMATIVE_TABLE,
        ANNEX,
        SIGNATURE_GROUP,
        UNSUPPORTED_PRESERVED,
    },
    COVER_BLOCK: set(),
    DOCUMENT_HEADING: set(),
    PREAMBLE: set(),
    SCOPE_BLOCK: set(),
    TOC_BLOCK: set(),
    LEGAL_PART: {
        LEGAL_BOOK,
        LEGAL_TITLE,
        CHAPTER,
        LEGAL_SECTION,
        SUBSECTION,
        ARTICLE,
        LEGACY_CLAUSE,
        NARRATIVE_BLOCK,
        NORMATIVE_TABLE,
        FIGURE,
    },
    LEGAL_BOOK: {
        LEGAL_TITLE,
        CHAPTER,
        LEGAL_SECTION,
        SUBSECTION,
        ARTICLE,
        LEGACY_CLAUSE,
        NARRATIVE_BLOCK,
        NORMATIVE_TABLE,
        FIGURE,
    },
    LEGAL_TITLE: {
        CHAPTER,
        LEGAL_SECTION,
        SUBSECTION,
        ARTICLE,
        LEGACY_CLAUSE,
        NARRATIVE_BLOCK,
        NORMATIVE_TABLE,
        FIGURE,
    },
    CHAPTER: {
        LEGAL_SECTION,
        SUBSECTION,
        ARTICLE,
        LEGACY_CLAUSE,
        NARRATIVE_BLOCK,
        NORMATIVE_TABLE,
        FIGURE,
        UNSUPPORTED_PRESERVED,
    },
    LEGAL_SECTION: {
        SUBSECTION,
        ARTICLE,
        LEGACY_CLAUSE,
        NARRATIVE_BLOCK,
        NORMATIVE_TABLE,
        FIGURE,
        UNSUPPORTED_PRESERVED,
    },
    SUBSECTION: {
        ARTICLE,
        LEGACY_CLAUSE,
        NARRATIVE_BLOCK,
        NORMATIVE_TABLE,
        FIGURE,
    },
    ARTICLE: {
        CAPUT,
        LEGAL_PARAGRAPH,
        INCISO,
        NORMATIVE_TABLE,
        FIGURE,
    },
    CAPUT: {
        INCISO,
    },
    LEGAL_PARAGRAPH: {
        INCISO,
        NORMATIVE_TABLE,
        FIGURE,
    },
    INCISO: {
        ALINEA,
    },
    ALINEA: {
        ITEM,
    },
    ITEM: set(),
    LEGACY_CLAUSE: set(),
    NARRATIVE_BLOCK: set(),
    NORMATIVE_TABLE: set(),
    FIGURE: set(),
    ANNEX: {
        CHAPTER,
        LEGAL_SECTION,
        SUBSECTION,
        ARTICLE,
        LEGACY_CLAUSE,
        NARRATIVE_BLOCK,
        NORMATIVE_TABLE,
        FIGURE,
        SIGNATURE_GROUP,
        UNSUPPORTED_PRESERVED,
    },
    SIGNATURE_GROUP: set(),
    UNSUPPORTED_PRESERVED: set(),
}

# Mapa invertido: para cada tipo filho, quais pais são permitidos
ALLOWED_PARENTS: Dict[str, Set[str]] = {}
for _parent, _children in ALLOWED_CHILDREN.items():
    for _child in _children:
        if _child not in ALLOWED_PARENTS:
            ALLOWED_PARENTS[_child] = set()
        ALLOWED_PARENTS[_child].add(_parent)


# ---------------------------------------------------------------------------
# Classes do Modelo de Objetos de Dispositivos Normativos
# ---------------------------------------------------------------------------

@dataclass
class NormativeNode:
    """Classe base para nós da árvore normativa com identidade estável (UUID)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = DOCUMENT_ROOT
    parent_id: Optional[str] = None
    children: List[NormativeNode] = field(default_factory=list)
    heading: Optional[str] = None
    body: Optional[Any] = None
    label: Optional[str] = None
    numbering: Optional[Dict[str, Any]] = None
    rendered_label: Optional[str] = None
    variant: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def add_child(self, child: NormativeNode) -> NormativeNode:
        """Adiciona um nó filho configurando o parent_id correspondente."""
        child.parent_id = self.id
        self.children.append(child)
        return child

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Converte a estrutura hierárquica em dicionário serializável JSON."""
        data: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
        }
        if self.parent_id:
            data["parent_id"] = self.parent_id
        if self.heading is not None:
            data["heading"] = self.heading
        if self.label is not None:
            data["label"] = self.label
        if self.variant is not None:
            data["variant"] = self.variant
        if self.rendered_label is not None:
            data["rendered_label"] = self.rendered_label
        if self.numbering is not None:
            data["numbering"] = self.numbering
        if self.body is not None:
            data["body"] = self.body
        if self.metadata is not None:
            data["metadata"] = self.metadata
        if self.children:
            data["children"] = [child.to_dict() for child in self.children]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NormativeNode:
        """Instancia a classe concreta apropriada a partir de um dicionário."""
        raw_type = data.get("type") or data.get("kind", DOCUMENT_ROOT)
        node_type = normalize_node_type(raw_type)
        node_class = NODE_CLASS_REGISTRY.get(node_type, NormativeNode)

        node = node_class(
            id=str(data.get("id") or uuid.uuid4()),
            type=node_type,
            parent_id=str(data["parent_id"]) if data.get("parent_id") else None,
            heading=data.get("heading"),
            body=data.get("body"),
            label=data.get("label"),
            numbering=data.get("numbering"),
            rendered_label=data.get("rendered_label"),
            variant=data.get("variant"),
            metadata=data.get("metadata"),
        )
        if "children" in data and isinstance(data["children"], list):
            node.children = [cls.from_dict(c) for c in data["children"]]
            for c in node.children:
                if not c.parent_id:
                    c.parent_id = node.id
        return node


@dataclass
class DocumentRootNode(NormativeNode):
    type: str = DOCUMENT_ROOT


@dataclass
class CoverBlockNode(NormativeNode):
    type: str = COVER_BLOCK


@dataclass
class DocumentHeadingNode(NormativeNode):
    type: str = DOCUMENT_HEADING


@dataclass
class PreambleNode(NormativeNode):
    type: str = PREAMBLE


@dataclass
class LegalTitleNode(NormativeNode):
    type: str = LEGAL_TITLE


@dataclass
class ChapterNode(NormativeNode):
    type: str = CHAPTER


@dataclass
class LegalSectionNode(NormativeNode):
    type: str = LEGAL_SECTION


@dataclass
class SubsectionNode(NormativeNode):
    type: str = SUBSECTION


@dataclass
class ArticleNode(NormativeNode):
    type: str = ARTICLE


@dataclass
class CaputNode(NormativeNode):
    type: str = CAPUT


@dataclass
class LegalParagraphNode(NormativeNode):
    type: str = LEGAL_PARAGRAPH


@dataclass
class IncisoNode(NormativeNode):
    type: str = INCISO


@dataclass
class AlineaNode(NormativeNode):
    type: str = ALINEA


@dataclass
class ItemNode(NormativeNode):
    type: str = ITEM


@dataclass
class NormativeTableNode(NormativeNode):
    type: str = NORMATIVE_TABLE


@dataclass
class SignatureGroupNode(NormativeNode):
    type: str = SIGNATURE_GROUP


@dataclass
class LegalPartNode(NormativeNode):
    type: str = LEGAL_PART


@dataclass
class LegalBookNode(NormativeNode):
    type: str = LEGAL_BOOK


@dataclass
class ScopeBlockNode(NormativeNode):
    type: str = SCOPE_BLOCK


@dataclass
class TocBlockNode(NormativeNode):
    type: str = TOC_BLOCK


@dataclass
class LegacyClauseNode(NormativeNode):
    type: str = LEGACY_CLAUSE


@dataclass
class NarrativeBlockNode(NormativeNode):
    type: str = NARRATIVE_BLOCK


@dataclass
class FigureNode(NormativeNode):
    type: str = FIGURE


@dataclass
class AnnexNode(NormativeNode):
    type: str = ANNEX


@dataclass
class UnsupportedPreservedNode(NormativeNode):
    type: str = UNSUPPORTED_PRESERVED


NODE_CLASS_REGISTRY: Dict[str, type[NormativeNode]] = {
    DOCUMENT_ROOT: DocumentRootNode,
    COVER_BLOCK: CoverBlockNode,
    DOCUMENT_HEADING: DocumentHeadingNode,
    PREAMBLE: PreambleNode,
    LEGAL_TITLE: LegalTitleNode,
    CHAPTER: ChapterNode,
    LEGAL_SECTION: LegalSectionNode,
    SUBSECTION: SubsectionNode,
    ARTICLE: ArticleNode,
    CAPUT: CaputNode,
    LEGAL_PARAGRAPH: LegalParagraphNode,
    INCISO: IncisoNode,
    ALINEA: AlineaNode,
    ITEM: ItemNode,
    NORMATIVE_TABLE: NormativeTableNode,
    SIGNATURE_GROUP: SignatureGroupNode,
    LEGAL_PART: LegalPartNode,
    LEGAL_BOOK: LegalBookNode,
    SCOPE_BLOCK: ScopeBlockNode,
    TOC_BLOCK: TocBlockNode,
    LEGACY_CLAUSE: LegacyClauseNode,
    NARRATIVE_BLOCK: NarrativeBlockNode,
    FIGURE: FigureNode,
    ANNEX: AnnexNode,
    UNSUPPORTED_PRESERVED: UnsupportedPreservedNode,
}


def create_normative_node(node_type: str, **kwargs: Any) -> NormativeNode:
    """Fábrica para instanciar nós normativos fortemente tipados."""
    norm_type = normalize_node_type(node_type)
    node_cls = NODE_CLASS_REGISTRY.get(norm_type, NormativeNode)
    return node_cls(type=norm_type, **kwargs)


# ---------------------------------------------------------------------------
# Validações da Gramática Normativa (LC 95/98)
# ---------------------------------------------------------------------------

def validate_article_caput(node: Union[NormativeNode, Dict[str, Any]]) -> None:
    """
    Valida regra basilar LC 95: Todo artigo deve possuir obrigatoriamente
    um único caput inicial como primeiro filho (children[0]).
    """
    children = node.children if isinstance(node, NormativeNode) else node.get("children", [])
    art_id = node.id if isinstance(node, NormativeNode) else node.get("id", "desconhecido")

    if not children:
        raise MissingCaputError(
            f"Artigo '{art_id}' inválido: todo artigo deve possuir obrigatoriamente um caput inicial como primeiro filho."
        )

    first_child = children[0]
    raw_first_type = first_child.type if isinstance(first_child, NormativeNode) else (first_child.get("type") or first_child.get("kind", ""))
    first_type = normalize_node_type(raw_first_type)

    if first_type != CAPUT:
        raise MissingCaputError(
            f"Artigo '{art_id}' inválido: o primeiro filho deve ser obrigatoriamente do tipo 'caput' (encontrado: '{first_type}')."
        )

    # Verifica se há caputs duplicados posteriores
    for idx, c in enumerate(children[1:], start=1):
        raw_c_type = c.type if isinstance(c, NormativeNode) else (c.get("type") or c.get("kind", ""))
        c_type = normalize_node_type(raw_c_type)
        if c_type == CAPUT:
            raise GrammarValidationError(
                f"Artigo '{art_id}' inválido: possui caput adicional na posição {idx}. É permitido apenas um caput inicial por artigo."
            )


def validate_containment(
    parent_type: str,
    child_type: str,
    parent_id: Optional[str] = None,
    child_id: Optional[str] = None,
) -> None:
    """
    Valida a hierarquia de contenção estrita entre pai e filho.
    Exemplos: alinea só pode ser filha de inciso; item só de alinea.
    """
    norm_parent = normalize_node_type(parent_type)
    norm_child = normalize_node_type(child_type)

    allowed_children = ALLOWED_CHILDREN.get(norm_parent)
    if allowed_children is None:
        raise InvalidContainmentError(
            f"Tipo de nó pai desconhecido: '{parent_type}' (normalizado: '{norm_parent}')."
        )

    if norm_child not in allowed_children:
        allowed_parents = ALLOWED_PARENTS.get(norm_child, set())
        parents_str = ", ".join(sorted(allowed_parents)) if allowed_parents else "nenhum"
        p_desc = f" (id: '{parent_id}')" if parent_id else ""
        c_desc = f" (id: '{child_id}')" if child_id else ""
        raise InvalidContainmentError(
            f"Hierarquia inválida: nó '{child_type}'{c_desc} não pode ser filho de '{parent_type}'{p_desc}. "
            f"Pais permitidos para '{child_type}': [{parents_str}]."
        )


def validate_normative_tree(
    target: Union[NormativeNode, Dict[str, Any], List[Union[NormativeNode, Dict[str, Any]]]],
    max_depth: int = MAX_TREE_DEPTH,
) -> None:
    """
    Validador completo da árvore ou floresta normativa.
    Verifica:
    1. Tipos de nós conhecidos.
    2. Regra de caput inicial obrigatório para todos os artigos.
    3. Hierarquia de contenção estrita.
    4. Detecção de ciclos e ancestralidade circular.
    5. Limite máximo de profundidade.
    """
    if isinstance(target, list):
        _validate_flat_node_list(target, max_depth=max_depth)
        return

    if isinstance(target, dict) and "root" in target and isinstance(target["root"], dict):
        root = target["root"]
    else:
        root = target

    visited_path: List[str] = []
    _traverse_and_validate(root, parent_type=None, parent_id=None, current_depth=0, visited_path=visited_path, max_depth=max_depth)


def _traverse_and_validate(
    node: Union[NormativeNode, Dict[str, Any]],
    parent_type: Optional[str],
    parent_id: Optional[str],
    current_depth: int,
    visited_path: List[str],
    max_depth: int,
) -> None:
    """Percorre recursivamente a árvore validando integridade em profundidade."""
    if current_depth > max_depth:
        raise MaxDepthExceededError(
            f"Profundidade máxima da hierarquia normativa excedida ({current_depth} > {max_depth}). Possível ciclo não detectado."
        )

    node_id = str(node.id if isinstance(node, NormativeNode) else node.get("id", ""))
    raw_node_type = node.type if isinstance(node, NormativeNode) else (node.get("type") or node.get("kind", ""))
    node_type = normalize_node_type(raw_node_type)

    if not node_id:
        raise GrammarValidationError("Nó normativo sem UUID estável ('id').")

    if not node_type or node_type not in ALLOWED_CHILDREN:
        raise GrammarValidationError(f"Tipo normativo inválido ou desconhecido: '{raw_node_type}'.")

    # Detecção de ciclos na cadeia de ancestrais
    if node_id in visited_path:
        cycle_chain = " -> ".join(visited_path + [node_id])
        raise CircularReferenceError(
            f"Referência circular detectada na hierarquia normativa: ciclo [{cycle_chain}]."
        )

    # Validação de contenção se houver pai
    if parent_type is not None and parent_id is not None:
        validate_containment(parent_type, node_type, parent_id, node_id)

    # Validação da regra do artigo
    if node_type == ARTICLE:
        validate_article_caput(node)

    # Visita filhos
    children = node.children if isinstance(node, NormativeNode) else node.get("children", [])
    if children:
        visited_path.append(node_id)
        for child in children:
            _traverse_and_validate(
                child,
                parent_type=node_type,
                parent_id=node_id,
                current_depth=current_depth + 1,
                visited_path=visited_path,
                max_depth=max_depth,
            )
        visited_path.pop()


def _validate_flat_node_list(
    nodes: List[Union[NormativeNode, Dict[str, Any]]],
    max_depth: int,
) -> None:
    """Valida integridade de uma lista plana de nós vinculados por parent_id."""
    nodes_by_id: Dict[str, Union[NormativeNode, Dict[str, Any]]] = {}
    children_by_parent: Dict[Optional[str], List[Union[NormativeNode, Dict[str, Any]]]] = {}

    for n in nodes:
        nid = str(n.id if isinstance(n, NormativeNode) else n.get("id", ""))
        pid = str(n.parent_id if isinstance(n, NormativeNode) else n.get("parent_id")) if (n.parent_id if isinstance(n, NormativeNode) else n.get("parent_id")) else None
        if not nid:
            raise GrammarValidationError("Nó em lista plana sem 'id' definido.")
        if nid in nodes_by_id:
            raise GrammarValidationError(f"Identificador UUID duplicado na lista: '{nid}'.")
        nodes_by_id[nid] = n
        children_by_parent.setdefault(pid, []).append(n)

    roots = children_by_parent.get(None, [])
    if not roots:
        if nodes:
            raise CircularReferenceError("Referência circular detectada: nenhum nó raiz (parent_id=None) encontrado na lista.")

    for r in roots:
        nested_root = _build_nested_from_flat(r, children_by_parent)
        validate_normative_tree(nested_root, max_depth=max_depth)


def _build_nested_from_flat(
    curr_node: Union[NormativeNode, Dict[str, Any]],
    children_map: Dict[Optional[str], List[Union[NormativeNode, Dict[str, Any]]]],
) -> NormativeNode:
    """Reconstrói árvore hierárquica recursivamente a partir do mapa de parent_id."""
    if isinstance(curr_node, NormativeNode):
        nid = curr_node.id
        node_copy = NormativeNode.from_dict(curr_node.to_dict())
    else:
        nid = str(curr_node.get("id", ""))
        node_copy = NormativeNode.from_dict(curr_node)

    child_nodes = children_map.get(nid, [])
    node_copy.children = [_build_nested_from_flat(c, children_map) for c in child_nodes]
    for c in node_copy.children:
        c.parent_id = node_copy.id
    return node_copy


# ---------------------------------------------------------------------------
# Classe Fachada NormativeGrammar
# ---------------------------------------------------------------------------

class NormativeGrammar:
    """Fachada estática para validações normativas conforme a LC 95/98."""

    @classmethod
    def validate_containment(cls, parent_type: str, child_type: str) -> None:
        validate_containment(parent_type, child_type)

    @classmethod
    def validate_article(cls, article_node: Union[NormativeNode, Dict[str, Any]]) -> None:
        validate_article_caput(article_node)

    @classmethod
    def validate_tree(cls, root_node: Union[NormativeNode, Dict[str, Any]], max_depth: int = MAX_TREE_DEPTH) -> None:
        validate_normative_tree(root_node, max_depth=max_depth)
