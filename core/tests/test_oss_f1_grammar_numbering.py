"""
Testes Automatizados para a Fase OSS-F1 — CONDOC (ED-OSS-2.0)
Validação da Gramática Normativa LC 95/98, Numeração Determinística e Instanciação de Templates.
"""
import uuid
import pytest

from domain.documents.exceptions import (
    CircularReferenceError,
    GrammarValidationError,
    MissingCaputError,
    InvalidContainmentError,
    MaxDepthExceededError,
)
from domain.documents.grammar import (
    NormativeNodeType,
    DOCUMENT_ROOT,
    COVER_BLOCK,
    DOCUMENT_HEADING,
    PREAMBLE,
    LEGAL_TITLE,
    CHAPTER,
    LEGAL_SECTION,
    SUBSECTION,
    ARTICLE,
    CAPUT,
    LEGAL_PARAGRAPH,
    INCISO,
    ALINEA,
    ITEM,
    NORMATIVE_TABLE,
    SIGNATURE_GROUP,
    NormativeNode,
    ArticleNode,
    CaputNode,
    LegalParagraphNode,
    IncisoNode,
    AlineaNode,
    ItemNode,
    ChapterNode,
    DocumentRootNode,
    create_normative_node,
    validate_article_caput,
    validate_containment,
    validate_normative_tree,
)
from domain.documents.numbering import (
    format_article_number,
    format_paragraph_number,
    format_inciso_number,
    format_alinea_number,
    format_item_number,
    format_chapter_number,
    format_title_number,
    format_section_number,
    int_to_roman,
    roman_to_int,
    int_to_letter,
    letter_to_int,
    renumber_normative_tree,
    preview_renumbering,
)
from domain.documents.templates import (
    DocumentTemplateLoader,
    instantiate_document_template,
    instantiate_regimento,
    instantiate_convencao,
    instantiate_block_template,
    flatten_document_provisions,
)


# ===========================================================================
# 1. TESTES DA GRAMÁTICA NORMATIVA LC 95/98 (grammar.py)
# ===========================================================================

class TestNormativeGrammarConstantsAndNodes:
    """Verifica constantes, tipos canônicos e classes de nós."""

    def test_all_16_mandatory_node_types_defined(self):
        """Garante que os 16 nós normativos obrigatórios existam no Enum e constantes."""
        expected_types = [
            DOCUMENT_ROOT,
            COVER_BLOCK,
            DOCUMENT_HEADING,
            PREAMBLE,
            LEGAL_TITLE,
            CHAPTER,
            LEGAL_SECTION,
            SUBSECTION,
            ARTICLE,
            CAPUT,
            LEGAL_PARAGRAPH,
            INCISO,
            ALINEA,
            ITEM,
            NORMATIVE_TABLE,
            SIGNATURE_GROUP,
        ]
        for t in expected_types:
            assert isinstance(t, str)
            assert NormativeNodeType(t) is not None

    def test_node_factory_and_typed_instances(self):
        """Garante que o factory create_normative_node instancia a classe tipada correta."""
        art = create_normative_node(ARTICLE, heading="Artigo de Teste")
        assert isinstance(art, ArticleNode)
        assert art.type == ARTICLE
        assert art.heading == "Artigo de Teste"
        assert uuid.UUID(art.id)  # UUID válido

        cap = create_normative_node(CAPUT)
        assert isinstance(cap, CaputNode)
        assert cap.type == CAPUT

        art.add_child(cap)
        assert len(art.children) == 1
        assert cap.parent_id == art.id

    def test_node_dict_serialization_roundtrip(self):
        """Garante que a serialização to_dict e desserialização from_dict preserve dados e hierarquia."""
        root = DocumentRootNode()
        chap = root.add_child(ChapterNode(heading="Capítulo I"))
        art = chap.add_child(ArticleNode())
        cap = art.add_child(CaputNode(body=[{"type": "paragraph", "text": "Texto do caput"}]))

        serialized = root.to_dict()
        assert serialized["type"] == DOCUMENT_ROOT
        assert len(serialized["children"]) == 1

        deserialized = NormativeNode.from_dict(serialized)
        assert isinstance(deserialized, DocumentRootNode)
        assert deserialized.children[0].heading == "Capítulo I"
        assert deserialized.children[0].children[0].children[0].type == CAPUT
        assert deserialized.children[0].children[0].children[0].parent_id == deserialized.children[0].children[0].id


class TestGrammarValidationRules:
    """Testa regras de validação estritas da LC 95 (Caput obrigatório, contenção, ciclos e profundidade)."""

    def test_article_without_children_fails(self):
        """Artigo sem filhos viola regra do caput inicial obrigatório."""
        art = ArticleNode()
        with pytest.raises(MissingCaputError, match="caput inicial como primeiro filho"):
            validate_article_caput(art)

    def test_article_with_first_child_not_caput_fails(self):
        """Artigo cujo primeiro filho é um inciso ou parágrafo viola a regra."""
        art = ArticleNode()
        art.add_child(IncisoNode())  # Inciso direto antes do caput
        with pytest.raises(MissingCaputError, match="primeiro filho deve ser obrigatoriamente do tipo 'caput'"):
            validate_article_caput(art)

    def test_article_with_multiple_caputs_fails(self):
        """Artigo não pode ter mais de um caput."""
        art = ArticleNode()
        art.add_child(CaputNode())
        art.add_child(LegalParagraphNode())
        art.add_child(CaputNode())  # Segundo caput inválido
        with pytest.raises(GrammarValidationError, match="possui caput adicional"):
            validate_article_caput(art)

    def test_valid_article_passes_validation(self):
        """Artigo com caput primeiro seguido de parágrafo e incisos é plenamente válido."""
        art = ArticleNode()
        art.add_child(CaputNode())
        art.add_child(LegalParagraphNode())
        validate_article_caput(art)  # Não lança exceção

    def test_strict_containment_alinea_must_be_child_of_inciso(self):
        """Alínea só pode ser filha de inciso. Inserção em artigo ou parágrafo é rejeitada."""
        # Alínea sob artigo -> Erro
        with pytest.raises(InvalidContainmentError, match="não pode ser filho de 'article'"):
            validate_containment(ARTICLE, ALINEA, "art-1", "ali-1")

        # Alínea sob parágrafo -> Erro
        with pytest.raises(InvalidContainmentError, match="não pode ser filho de 'legal_paragraph'"):
            validate_containment(LEGAL_PARAGRAPH, ALINEA, "p-1", "ali-1")

        # Alínea sob inciso -> Válido
        validate_containment(INCISO, ALINEA, "inc-1", "ali-1")

    def test_strict_containment_item_must_be_child_of_alinea(self):
        """Item só pode ser filho de alínea."""
        with pytest.raises(InvalidContainmentError, match="não pode ser filho de 'inciso'"):
            validate_containment(INCISO, ITEM, "inc-1", "item-1")

        validate_containment(ALINEA, ITEM, "ali-1", "item-1")

    def test_strict_containment_caput_must_be_child_of_article(self):
        """Caput só pode ser filho de artigo."""
        with pytest.raises(InvalidContainmentError, match="não pode ser filho de 'chapter'"):
            validate_containment(CHAPTER, CAPUT, "chap-1", "cap-1")

        validate_containment(ARTICLE, CAPUT, "art-1", "cap-1")

    def test_detect_direct_and_indirect_cycles(self):
        """Detecção de referência circular na hierarquia."""
        node_a = DocumentRootNode(id="node-a")
        node_b = node_a.add_child(ChapterNode(id="node-b"))
        node_c = node_b.add_child(ArticleNode(id="node-c"))
        node_c.add_child(CaputNode(id="cap-1"))

        # Cria ciclo indireto: node_c aponta para node_a como filho
        node_c.children.append(node_a)

        with pytest.raises(CircularReferenceError, match="Referência circular detectada"):
            validate_normative_tree(node_a)

    def test_max_depth_exceeded(self):
        """Garante que limite de profundidade dispare MaxDepthExceededError."""
        # Cria uma cadeia válida: root -> legal_part -> legal_book -> legal_title -> chapter -> legal_section
        root = DocumentRootNode(id="root")
        p = root.add_child(create_normative_node(NormativeNodeType.LEGAL_PART.value, id="part-1"))
        b = p.add_child(create_normative_node(NormativeNodeType.LEGAL_BOOK.value, id="book-1"))
        t = b.add_child(create_normative_node(NormativeNodeType.LEGAL_TITLE.value, id="title-1"))
        c = t.add_child(create_normative_node(NormativeNodeType.CHAPTER.value, id="chap-1"))
        s = c.add_child(create_normative_node(NormativeNodeType.LEGAL_SECTION.value, id="sec-1"))

        with pytest.raises(MaxDepthExceededError, match="Profundidade máxima da hierarquia"):
            validate_normative_tree(root, max_depth=3)



# ===========================================================================
# 2. TESTES DE NUMERAÇÃO DETERMINÍSTICA LC 95/98 (numbering.py)
# ===========================================================================

class TestLC95NumberingFormatters:
    """Valida formatadores determinísticos conforme a Lei Complementar 95/98."""

    def test_article_numbering_ordinal_1_to_9(self):
        """LC 95 Art. 10, I: Artigos 1 a 9 devem ser ordinais 'Art. 1º' a 'Art. 9º'."""
        assert format_article_number(1) == "Art. 1º"
        assert format_article_number(2) == "Art. 2º"
        assert format_article_number(5) == "Art. 5º"
        assert format_article_number(9) == "Art. 9º"

    def test_article_numbering_cardinal_from_10(self):
        """LC 95 Art. 10, I: Artigos a partir de 10 devem ser cardinais 'Art. 10', 'Art. 11', etc."""
        assert format_article_number(10) == "Art. 10"
        assert format_article_number(11) == "Art. 11"
        assert format_article_number(42) == "Art. 42"
        assert format_article_number(100) == "Art. 100"

    def test_article_numbering_with_suffix(self):
        """LC 95: Artigos com sufixo (ex.: Art. 1º-A, Art. 10-A)."""
        assert format_article_number(1, suffix="A") == "Art. 1º-A"
        assert format_article_number(10, suffix="B") == "Art. 10-B"

    def test_paragraph_numbering_single(self):
        """LC 95 Art. 10, III: Se houver apenas 1 parágrafo -> 'Parágrafo único.'."""
        assert format_paragraph_number(1, total_in_article=1) == "Parágrafo único."

    def test_paragraph_numbering_multiple_1_to_9_and_10(self):
        """LC 95 Art. 10, III: Se houver múltiplos parágrafos -> '§ 1º' a '§ 9º' e '§ 10' em diante."""
        assert format_paragraph_number(1, total_in_article=3) == "§ 1º"
        assert format_paragraph_number(2, total_in_article=3) == "§ 2º"
        assert format_paragraph_number(9, total_in_article=12) == "§ 9º"
        assert format_paragraph_number(10, total_in_article=12) == "§ 10"
        assert format_paragraph_number(12, total_in_article=12) == "§ 12"

    def test_inciso_numbering_roman(self):
        """LC 95 Art. 10, II: Incisos representados por numerais romanos maiúsculos 'I -', 'II -'."""
        assert format_inciso_number(1) == "I -"
        assert format_inciso_number(2) == "II -"
        assert format_inciso_number(3) == "III -"
        assert format_inciso_number(4) == "IV -"
        assert format_inciso_number(9) == "IX -"
        assert format_inciso_number(10) == "X -"
        assert format_inciso_number(14) == "XIV -"
        assert format_inciso_number(20) == "XX -"

    def test_alinea_numbering_letters(self):
        """LC 95 Art. 10, IV: Alíneas representadas por letras minúsculas 'a)', 'b)', etc."""
        assert format_alinea_number(1) == "a)"
        assert format_alinea_number(2) == "b)"
        assert format_alinea_number(3) == "c)"
        assert format_alinea_number(26) == "z)"
        assert format_alinea_number(27) == "aa)"

    def test_item_numbering_arabic(self):
        """LC 95 Art. 10, V: Itens representados por arábicos seguidos de ponto '1.', '2.'."""
        assert format_item_number(1) == "1."
        assert format_item_number(2) == "2."
        assert format_item_number(10) == "10."

    def test_grouping_formatters(self):
        """Valida formatação de Capítulos e Seções."""
        assert format_chapter_number(1) == "CAPÍTULO I"
        assert format_chapter_number(4) == "CAPÍTULO IV"
        assert format_section_number(2) == "Seção II"
        assert format_title_number(3) == "TÍTULO III"

    def test_roman_and_letter_converters_roundtrip(self):
        """Verifica integridade bidirecional dos conversores."""
        for val in [1, 4, 9, 14, 49, 99, 400, 999, 2026]:
            roman = int_to_roman(val)
            assert roman_to_int(roman) == val

        for val in [1, 2, 26, 27, 28, 52, 53]:
            letter = int_to_letter(val)
            assert letter_to_int(letter) == val


class TestSequentialRenumbering:
    """Valida a renumeração sequencial completa da árvore normativa e prévia de diff."""

    def test_renumber_full_normative_tree(self):
        """
        Cria uma árvore com:
        - 2 capítulos
        - No capítulo 1: Artigo 1 com Caput e 1 Parágrafo (deve virar 'Parágrafo único.')
        - No capítulo 2: Artigo 2 com Caput e 2 Parágrafos (devem virar '§ 1º' e '§ 2º')
        - No § 1º: 2 Incisos ('I -', 'II -')
        - No Inciso I: 2 Alíneas ('a)', 'b)')
        - Na Alínea a: 2 Itens ('1.', '2.')
        """
        root = DocumentRootNode()
        c1 = root.add_child(ChapterNode())
        art1 = c1.add_child(ArticleNode())
        art1.add_child(CaputNode())
        p_single = art1.add_child(LegalParagraphNode())

        c2 = root.add_child(ChapterNode())
        art2 = c2.add_child(ArticleNode())
        art2.add_child(CaputNode())
        p1 = art2.add_child(LegalParagraphNode())
        p2 = art2.add_child(LegalParagraphNode())

        inc1 = p1.add_child(IncisoNode())
        inc2 = p1.add_child(IncisoNode())

        ali1 = inc1.add_child(AlineaNode())
        ali2 = inc1.add_child(AlineaNode())

        it1 = ali1.add_child(ItemNode())
        it2 = ali1.add_child(ItemNode())

        # Executa renumeração
        renumber_normative_tree(root)

        # Verificações dos Capítulos
        assert c1.rendered_label == "CAPÍTULO I"
        assert c2.rendered_label == "CAPÍTULO II"

        # Verificações dos Artigos
        assert art1.rendered_label == "Art. 1º"
        assert art1.numbering["value"] == 1
        assert art2.rendered_label == "Art. 2º"
        assert art2.numbering["value"] == 2

        # Verificações dos Parágrafos
        assert p_single.rendered_label == "Parágrafo único."
        assert p1.rendered_label == "§ 1º"
        assert p2.rendered_label == "§ 2º"

        # Verificações dos Incisos
        assert inc1.rendered_label == "I -"
        assert inc2.rendered_label == "II -"

        # Verificações das Alíneas
        assert ali1.rendered_label == "a)"
        assert ali2.rendered_label == "b)"

        # Verificações dos Itens
        assert it1.rendered_label == "1."
        assert it2.rendered_label == "2."

    def test_renumber_flat_list_representation(self):
        """Valida que uma lista plana de nós com parent_id seja renumerada com precisão."""
        art_id = "art-flat-1"
        cap_id = "cap-flat-1"
        p_id = "p-flat-1"

        flat_nodes = [
            {"id": art_id, "parent_id": None, "type": ARTICLE, "children": []},
            {"id": cap_id, "parent_id": art_id, "type": CAPUT, "children": []},
            {"id": p_id, "parent_id": art_id, "type": LEGAL_PARAGRAPH, "children": []},
        ]

        renumber_normative_tree(flat_nodes)

        assert flat_nodes[0]["rendered_label"] == "Art. 1º"
        assert flat_nodes[1]["rendered_label"] == ""  # Caput herda sem label
        assert flat_nodes[2]["rendered_label"] == "Parágrafo único."

    def test_preview_renumbering_generates_auditable_diff(self):
        """Garante que a prévia de renumeração reporte apenas as alterações sem modificar a origem."""
        art = ArticleNode(rendered_label="Art. 99 (antigo)")
        art.add_child(CaputNode())
        p = art.add_child(LegalParagraphNode(rendered_label="Parágrafo Velho"))

        diffs = preview_renumbering(art, start_article=1)

        # O artigo original não foi modificado
        assert art.rendered_label == "Art. 99 (antigo)"

        # O diff capturou as mudanças esperadas
        assert len(diffs) == 2
        art_diff = next(d for d in diffs if d["node_id"] == art.id)
        assert art_diff["old_rendered_label"] == "Art. 99 (antigo)"
        assert art_diff["new_rendered_label"] == "Art. 1º"

        para_diff = next(d for d in diffs if d["node_id"] == p.id)
        assert para_diff["old_rendered_label"] == "Parágrafo Velho"
        assert para_diff["new_rendered_label"] == "Parágrafo único."


# ===========================================================================
# 3. TESTES DOS TEMPLATES NORMATIVOS OSS (templates.py)
# ===========================================================================

class TestDocumentTemplateLoadingAndInstantiation:
    """Valida carregamento dos modelos OSS e instanciação estrita com novos UUIDs e parent_id."""

    @pytest.fixture
    def loader(self):
        return DocumentTemplateLoader()

    def test_loader_loads_raw_skeletons_and_blocks(self, loader):
        """Verifica se os arquivos JSON em modelos/ são carregados corretamente."""
        reg = loader.load_regimento_raw()
        assert reg["version"] == "ED-OSS-2.0"
        assert reg["document_kind"] == "regimento"
        assert "root" in reg

        conv = loader.load_convencao_raw()
        assert conv["version"] == "ED-OSS-2.0"
        assert conv["document_kind"] == "convencao"
        assert "root" in conv

        blocks = loader.load_block_templates_raw()
        assert isinstance(blocks, list)
        assert len(blocks) >= 10

    def test_instantiate_regimento_generates_new_uuids_and_preserves_hierarchy(self):
        """
        Garante que ao instanciar o Regimento Interno:
        1. Todos os 43 nós recebam UUIDs NOVOS (nenhum repete o ID original).
        2. A hierarquia de parent_id seja 100% preservada e aponte para os novos UUIDs.
        3. A árvore instanciada seja estritamente válida na gramática LC 95.
        """
        raw_regimento = DocumentTemplateLoader().load_regimento_raw()
        raw_root_id = raw_regimento["root"]["id"]

        instantiated = instantiate_regimento(condominium_id=uuid.uuid4(), title="Regimento Residencial Aurora")

        assert instantiated["title"] == "Regimento Residencial Aurora"
        assert instantiated["root"]["id"] != raw_root_id
        assert len(instantiated["id_mapping"]) == 43

        # Nenhum novo UUID coincide com qualquer ID antigo
        old_ids = set(instantiated["id_mapping"].keys())
        new_ids = set(instantiated["id_mapping"].values())
        assert len(old_ids.intersection(new_ids)) == 0

        # Verifica consistência de parent_id em toda a árvore instanciada
        def _check_hierarchy(node, expected_parent_id):
            assert node["parent_id"] == expected_parent_id
            for child in node.get("children", []):
                _check_hierarchy(child, expected_parent_id=node["id"])

        _check_hierarchy(instantiated["root"], expected_parent_id=None)

        # Validação formal da árvore gerada
        validate_normative_tree(instantiated["root"])

    def test_instantiate_convencao_generates_new_uuids_and_preserves_hierarchy(self):
        """Garante nova identidade e integridade de parent_id na Convenção de Condomínio."""
        raw_convencao = DocumentTemplateLoader().load_convencao_raw()
        raw_root_id = raw_convencao["root"]["id"]

        instantiated = instantiate_convencao(condominium_id=uuid.uuid4(), title="Convenção Condominial Parque dos Ipês")

        assert instantiated["root"]["id"] != raw_root_id
        assert len(instantiated["id_mapping"]) == 43
        validate_normative_tree(instantiated["root"])

    def test_instantiate_block_template_variants(self):
        """Instancia blocos reutilizáveis do catálogo de templates com parent_id."""
        parent_id = str(uuid.uuid4())

        # 1. Artigo simples
        art_simple = instantiate_block_template("article", variant="simple", parent_id=parent_id)
        assert art_simple["root"]["type"] == ARTICLE
        assert art_simple["root"]["parent_id"] == parent_id
        assert len(art_simple["root"]["children"]) == 1
        assert art_simple["root"]["children"][0]["type"] == CAPUT
        assert art_simple["root"]["children"][0]["parent_id"] == art_simple["root"]["id"]

        # 2. Artigo com múltiplos parágrafos
        art_multi = instantiate_block_template("article", variant="with_multiple_paragraphs", parent_id=parent_id)
        assert art_multi["root"]["children"][0]["type"] == CAPUT
        assert art_multi["root"]["children"][1]["type"] == LEGAL_PARAGRAPH
        assert art_multi["root"]["children"][2]["type"] == LEGAL_PARAGRAPH

        # 3. Inciso com alíneas
        inc_ali = instantiate_block_template("inciso", variant="inciso_with_alineas", parent_id=parent_id)
        assert inc_ali["root"]["type"] == INCISO
        assert inc_ali["root"]["children"][0]["type"] == ALINEA
        assert inc_ali["root"]["children"][0]["parent_id"] == inc_ali["root"]["id"]

    def test_flatten_document_provisions_export(self):
        """
        Garante que a exportação plana do documento gere uma sequência de DTOs
        perfeita para persistência na tabela app.provisions do Supabase / Django ORM.
        """
        doc = instantiate_regimento()
        flat_list = flatten_document_provisions(doc)

        assert len(flat_list) == 43

        # Raiz tem parent_id nulo e position 0
        root_item = flat_list[0]
        assert root_item["kind"] == DOCUMENT_ROOT
        assert root_item["parent_id"] is None
        assert root_item["position"] == 0

        # Dispositivos subsequentes têm parent_id e posição válidos
        for item in flat_list[1:]:
            assert item["id"] is not None
            assert item["parent_id"] is not None
            assert isinstance(item["position"], int)
            assert item["kind"] is not None

        # Posições globais pré-ordem são estritamente contínuas (0 a N-1)
        positions = [item["position"] for item in flat_list]
        assert positions == list(range(len(flat_list)))

    def test_renumbering_supports_sections_subsections_books_and_parts(self):
        """Garante suporte e formatação determinística para Seção, Subseção, Livro e Parte."""
        from domain.documents.grammar import LEGAL_BOOK, LEGAL_PART, LEGAL_SECTION, SUBSECTION

        tree = {
            "id": str(uuid.uuid4()),
            "type": DOCUMENT_ROOT,
            "children": [
                {
                    "id": str(uuid.uuid4()),
                    "type": LEGAL_BOOK,
                    "label": "Livro Antigo",
                    "children": []
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": LEGAL_PART,
                    "label": "Parte Antiga",
                    "children": []
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": LEGAL_SECTION,
                    "label": "Seção Antiga",
                    "children": [
                        {
                            "id": str(uuid.uuid4()),
                            "type": SUBSECTION,
                            "label": "Subseção Antiga",
                            "children": []
                        }
                    ]
                }
            ]
        }

        renumbered = renumber_normative_tree(tree)
        assert renumbered["children"][0]["rendered_label"] == "LIVRO I"
        assert renumbered["children"][1]["rendered_label"] == "PARTE I"
        assert renumbered["children"][2]["rendered_label"] == "Seção I"
        assert renumbered["children"][2]["children"][0]["rendered_label"] == "Subseção I"

