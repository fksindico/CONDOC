"""
Carregador e Instanciador de Templates Normativos OSS — CONDOC (ED-OSS-2.0)
Gerencia esqueletos de Regimento Interno, Convenção de Condomínio e Blocos Normativos.
Garante que na instanciação TODOS os nós recebam UUIDs NOVOS e estáveis (uuid.uuid4()),
preservando estritamente a integridade da hierarquia de parent_id e conformidade com a LC 95/98.
"""
from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .grammar import NormativeNode, validate_normative_tree
from .numbering import renumber_normative_tree


# Diretório canônico de modelos JSON versionados
DEFAULT_MODELOS_DIR = Path(__file__).resolve().parent / "modelos"

REGIMENTO_FILENAME = "Regimento_Esqueleto_OSS.json"
CONVENCAO_FILENAME = "Convencao_Esqueleto_OSS.json"
BLOCOS_FILENAME = "Templates_Blocos_OSS.json"
CATALOGO_FILENAME = "Catalogo_Blocos_OSS.json"
ESTILOS_FILENAME = "Perfil_Estilos_Layout_OSS.json"


class TemplateNotFoundError(FileNotFoundError):
    """Arquivo de template normativo não encontrado no diretório de modelos."""
    pass


class BlockVariantNotFoundError(KeyError):
    """Variante de bloco normativo solicitada não encontrada no catálogo."""
    pass


class DocumentTemplateLoader:
    """
    Carregador e cache de modelos normativos abertos ED-OSS-2.0.
    Garante isolamento sem dependência de SaaS de conversão externa ou @tiptap-pro.
    """

    def __init__(self, modelos_dir: Optional[Path] = None):
        self.modelos_dir = Path(modelos_dir) if modelos_dir else DEFAULT_MODELOS_DIR
        if not self.modelos_dir.exists():
            raise TemplateNotFoundError(f"Diretório de modelos normativos não encontrado: '{self.modelos_dir}'.")
        self._cache: Dict[str, Any] = {}

    def _read_json(self, filename: str) -> Any:
        if filename not in self._cache:
            file_path = self.modelos_dir / filename
            if not file_path.exists():
                raise TemplateNotFoundError(f"Arquivo de template não encontrado: '{file_path}'.")
            with open(file_path, "r", encoding="utf-8") as f:
                self._cache[filename] = json.load(f)
        return copy.deepcopy(self._cache[filename])

    def load_regimento_raw(self) -> Dict[str, Any]:
        """Carrega o esqueleto original do Regimento Interno OSS."""
        return self._read_json(REGIMENTO_FILENAME)

    def load_convencao_raw(self) -> Dict[str, Any]:
        """Carrega o esqueleto original da Convenção de Condomínio OSS."""
        return self._read_json(CONVENCAO_FILENAME)

    @classmethod
    def load_regimento_esqueleto(cls) -> Dict[str, Any]:
        """Carrega o esqueleto do Regimento Interno via instância padrão."""
        return default_loader.load_regimento_raw()

    @classmethod
    def load_convencao_esqueleto(cls) -> Dict[str, Any]:
        """Carrega o esqueleto da Convenção de Condomínio via instância padrão."""
        return default_loader.load_convencao_raw()

    def load_block_templates_raw(self) -> List[Dict[str, Any]]:
        """Carrega o catálogo completo de blocos normativos reutilizáveis."""
        return self._read_json(BLOCOS_FILENAME)

    def list_block_variants(self) -> List[Tuple[str, Optional[str]]]:
        """Lista todas as combinações de (tipo, variante) disponíveis no catálogo de blocos."""
        blocks = self.load_block_templates_raw()
        variants: List[Tuple[str, Optional[str]]] = []
        for b in blocks:
            root = b.get("root", {})
            b_type = root.get("type")
            b_variant = root.get("variant")
            if b_type:
                variants.append((b_type, b_variant))
        return variants

    def get_block_template_raw(self, block_type: str, variant: Optional[str] = None) -> Dict[str, Any]:
        """
        Recupera a definição de um bloco específico pelo tipo e variante.
        Se variante não for especificada, retorna o primeiro correspondente ao tipo.
        """
        blocks = self.load_block_templates_raw()
        for b in blocks:
            root = b.get("root", {})
            if root.get("type") == block_type:
                if variant is None or root.get("variant") == variant:
                    return copy.deepcopy(b)

        variant_desc = f" com variante '{variant}'" if variant else ""
        raise BlockVariantNotFoundError(f"Bloco do tipo '{block_type}'{variant_desc} não encontrado.")


# Instância singleton padrão do loader
default_loader = DocumentTemplateLoader()


# ---------------------------------------------------------------------------
# Instanciação Recursiva com Geração Determinística de Novos UUIDs
# ---------------------------------------------------------------------------

def instantiate_node_tree(
    node_data: Dict[str, Any],
    parent_id: Optional[str] = None,
    id_mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Cria uma nova instância profunda de um nó e toda sua subárvore:
    - Atribui um NOVO UUID estável gerado via uuid.uuid4().
    - Atualiza explicitamente o parent_id para apontar para o novo UUID do nó pai.
    - Registra a equivalência no dicionário id_mapping (old_id -> new_id).
    - Preserva intactos o corpo, formatações, placeholders e propriedades jurídicas.
    """
    node = copy.deepcopy(node_data)
    old_id = str(node.get("id", ""))
    new_id = str(uuid.uuid4())

    if id_mapping is not None and old_id:
        id_mapping[old_id] = new_id

    node["id"] = new_id
    node["parent_id"] = parent_id

    # Instancia recursivamente os filhos preservando a hierarquia
    original_children = node.get("children", [])
    new_children: List[Dict[str, Any]] = []
    for child in original_children:
        instantiated_child = instantiate_node_tree(
            child,
            parent_id=new_id,
            id_mapping=id_mapping,
        )
        new_children.append(instantiated_child)

    if original_children or "children" in node:
        node["children"] = new_children

    return node


def instantiate_document_template(
    template_data: Dict[str, Any],
    condominium_id: Optional[Union[str, uuid.UUID]] = None,
    title: Optional[str] = None,
    validate: bool = True,
    renumber: bool = True,
) -> Dict[str, Any]:
    """
    Instancia um documento normativo completo a partir de um esqueleto JSON:
    1. Regenera novos UUIDs para todos os nós, preservando a hierarquia de parent_id.
    2. Aplica numeração determinística LC 95 (se renumber=True).
    3. Valida conformidade estrita da árvore com a gramática LC 95 (se validate=True).
    4. Anexa metadados de auditoria e contexto condominial.
    """
    doc = copy.deepcopy(template_data)
    id_mapping: Dict[str, str] = {}

    raw_root = doc.get("root")
    if not raw_root:
        raise ValueError("O template fornecido não possui o nó obrigatório 'root'.")

    # Instancia a árvore completa de nós a partir da raiz
    new_root = instantiate_node_tree(raw_root, parent_id=None, id_mapping=id_mapping)
    doc["root"] = new_root

    # Atualiza metadados do documento instanciado
    doc["id"] = str(uuid.uuid4())
    doc["editorial_status"] = "draft"
    doc["legal_status"] = "not_validated"
    doc["condominium_id"] = str(condominium_id) if condominium_id else None
    doc["template_instantiated_at"] = datetime.now(timezone.utc).isoformat()
    doc["instantiated_node_count"] = len(id_mapping)
    doc["id_mapping"] = id_mapping

    if title:
        doc["title"] = title

    # Renumeração determinística sequencial conforme LC 95
    if renumber:
        renumber_normative_tree(doc["root"], in_place=True)

    # Validação da integridade gramatical
    if validate:
        validate_normative_tree(doc["root"])

    return doc


def instantiate_regimento(
    condominium_id: Optional[Union[str, uuid.UUID]] = None,
    title: Optional[str] = "Regimento Interno",
    loader: Optional[DocumentTemplateLoader] = None,
    validate: bool = True,
    renumber: bool = True,
) -> Dict[str, Any]:
    """Gera uma nova instância isolada do Regimento Interno a partir do modelo OSS."""
    active_loader = loader or default_loader
    raw_template = active_loader.load_regimento_raw()
    return instantiate_document_template(
        raw_template,
        condominium_id=condominium_id,
        title=title,
        validate=validate,
        renumber=renumber,
    )


def instantiate_convencao(
    condominium_id: Optional[Union[str, uuid.UUID]] = None,
    title: Optional[str] = "Convenção de Condomínio",
    loader: Optional[DocumentTemplateLoader] = None,
    validate: bool = True,
    renumber: bool = True,
) -> Dict[str, Any]:
    """Gera uma nova instância isolada da Convenção de Condomínio a partir do modelo OSS."""
    active_loader = loader or default_loader
    raw_template = active_loader.load_convencao_raw()
    return instantiate_document_template(
        raw_template,
        condominium_id=condominium_id,
        title=title,
        validate=validate,
        renumber=renumber,
    )


def instantiate_block_template(
    block_type: str,
    variant: Optional[str] = None,
    parent_id: Optional[Union[str, uuid.UUID]] = None,
    loader: Optional[DocumentTemplateLoader] = None,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Instancia um bloco normativo reutilizável (ex.: artigo com parágrafos, inciso com alíneas):
    Garante novos UUIDs para o bloco raiz e todos os seus filhos, configurando o parent_id informado.
    """
    active_loader = loader or default_loader
    raw_block = active_loader.get_block_template_raw(block_type, variant=variant)

    id_mapping: Dict[str, str] = {}
    parent_id_str = str(parent_id) if parent_id else None

    instantiated_root = instantiate_node_tree(
        raw_block["root"],
        parent_id=parent_id_str,
        id_mapping=id_mapping,
    )

    if validate and block_type == "article":
        # Se for um artigo completo, valida a regra de caput
        from .grammar import validate_article_caput
        validate_article_caput(instantiated_root)

    return {
        "template_version": raw_block.get("template_version", "ED-OSS-2.0"),
        "root": instantiated_root,
        "id_mapping": id_mapping,
    }


# ---------------------------------------------------------------------------
# Utilitário de Exportação Plana (Compatibilidade com Banco de Dados / Provision)
# ---------------------------------------------------------------------------

def flatten_document_provisions(
    doc_or_root: Union[Dict[str, Any], NormativeNode],
) -> List[Dict[str, Any]]:
    """
    Converte a árvore de nós instanciada em uma lista sequencial de dispositivos planos,
    adequada para persistência na tabela app.provisions / ProvisionRevision.
    Preserva estritamente: id, parent_id, kind/type, position, rendered_label, body.
    """
    root = doc_or_root
    if isinstance(doc_or_root, dict) and "root" in doc_or_root:
        root = doc_or_root["root"]

    items: List[Dict[str, Any]] = []
    global_seq = 0

    def _traverse(node: Any, parent_id: Optional[str], child_pos: int) -> None:
        nonlocal global_seq
        current_pos = global_seq
        global_seq += 1

        nid = str(node.get("id") if isinstance(node, dict) else node.id)
        ntype = node.get("type") if isinstance(node, dict) else node.type
        heading = node.get("heading") if isinstance(node, dict) else getattr(node, "heading", None)
        body = node.get("body") if isinstance(node, dict) else getattr(node, "body", None)
        numbering = node.get("numbering") if isinstance(node, dict) else getattr(node, "numbering", None)
        rendered_label = node.get("rendered_label") if isinstance(node, dict) else getattr(node, "rendered_label", None)
        metadata = node.get("metadata") if isinstance(node, dict) else getattr(node, "metadata", None)

        item_dto: Dict[str, Any] = {
            "id": nid,
            "parent_id": parent_id,
            "kind": ntype,
            "position": current_pos,
            "sibling_position": child_pos,
            "rendered_label": rendered_label or "",
            "heading": heading,
            "body": body,
            "numbering": numbering,
            "metadata": metadata,
        }
        items.append(item_dto)

        children = node.get("children", []) if isinstance(node, dict) else getattr(node, "children", [])
        for idx, child in enumerate(children):
            _traverse(child, parent_id=nid, child_pos=idx)

    _traverse(root, parent_id=None, child_pos=0)
    return items


# ---------------------------------------------------------------------------
# Aliases de Compatibilidade
# ---------------------------------------------------------------------------

NormativeTemplateLoader = DocumentTemplateLoader


class NormativeTemplateInstantiator:
    """Fachada estática para instanciação de templates com novos UUIDs."""

    @staticmethod
    def instantiate_tree(skeleton_data: Dict[str, Any], renumber: bool = True) -> Dict[str, Any]:
        return instantiate_document_template(skeleton_data, renumber=renumber)

    @staticmethod
    def instantiate_regimento(loader: Optional[DocumentTemplateLoader] = None, renumber: bool = True) -> Dict[str, Any]:
        return instantiate_regimento(loader=loader, renumber=renumber)

    @staticmethod
    def instantiate_convencao(loader: Optional[DocumentTemplateLoader] = None, renumber: bool = True) -> Dict[str, Any]:
        return instantiate_convencao(loader=loader, renumber=renumber)

