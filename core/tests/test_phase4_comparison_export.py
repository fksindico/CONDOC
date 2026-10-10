"""
Testes Automatizados da Fase 4 — Comparação, Mapeamento de Origens, Renumeração e Exportação Preliminar (CONDC)
Cobre os Critérios de Aceite:
- CA-19: Dispositivo incluído não inventa origem
- CA-20: Excluído sai do limpo e permanece em histórico e DePara
- CA-21: Desmembrar/consolidar preserva relação muitos-para-muitos (N:M)
- CA-22: Renumerar preserva referências, comentários e UUIDs permanentes
- CA-42: Documento limpo sem identidade, notas ou referências antigas indevidas
- UI-12 a UI-18: Operações de comparação, DePara e renumeração sem impacto indevido
"""
import uuid
import pytest
from rest_framework.test import APIClient
from django.utils import timezone

from infrastructure.models import (
    Condominium,
    Account,
    RoleAssignment,
    Project,
    Document,
    SourceFile,
    SourceTranscription,
    SourceProvision,
    Provision,
    ProvisionRevision,
    InternalNote,
    OriginMapping,
    CrossReference,
)
from domain.comparison.exceptions import (
    FictitiousOriginError,
    ExcludedProvisionInCleanExportError,
    InvalidOriginMappingError,
    BrokenCrossReferenceError,
)
from domain.comparison.invariants import (
    assert_new_provision_has_no_fictitious_origin,
    assert_excluded_provision_not_in_clean_document,
    validate_origin_mapping_relationship,
    check_cross_reference_status,
    render_cross_reference_label,
    calculate_text_diff,
    sanitize_clean_export_payload,
)
from application.documents.services import (
    ProjectService,
    DocumentService,
    SourceFileService,
    TranscriptionService,
    ProvisionService,
    InternalNoteService,
)
from application.comparison.services import (
    OriginMappingService,
    ComparisonService,
    CrossReferenceService,
    RenumberingService,
    ExportService,
)


@pytest.fixture
def phase4_setup(db):
    """Cenário base para testes de comparação, origens, renumeração e exportação."""
    condo = Condominium.objects.create(name="Condomínio Residencial Parque dos Pássaros")
    admin_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="sindico.fase4@condc.local",
        full_name="Síndico Revisor Fase 4"
    )
    RoleAssignment.objects.create(
        condominium_id=condo.id,
        account_id=admin_acc.id,
        role="sindico",
        status="active"
    )

    project = ProjectService.create_project(
        condominium_id=condo.id,
        name="Projeto de Revisão da Convenção 2026",
        purpose="Adequação e modernização das normas condominiais",
        coordinator_account_id=admin_acc.id
    )

    document = DocumentService.create_document(
        project_id=project.id,
        condominium_id=condo.id,
        title="Convenção Condominial Minuta Preliminar",
        type="convencao",
        numbering_policy="renumeracao_automatica"
    )

    # Cria arquivo original e transcrição conferida
    source_file = SourceFileService.register_source_file(
        condominium_id=condo.id,
        uploaded_by_id=admin_acc.id,
        filename="convencao_antiga_1998.pdf",
        mime_type="application/pdf",
        size_bytes=10240,
        file_content=b"Texto integral da convencao antiga de 1998"
    )

    transcription = TranscriptionService.create_initial_transcription(
        document_id=document.id,
        condominium_id=condo.id,
        source_file_id=source_file.id,
        raw_text="Artigo 1. Do condomínio. Artigo 2. Das despesas. Artigo 3. Dos animais e garagens."
    )
    TranscriptionService.confirm_transcription(
        transcription_id=transcription.id,
        checked_by_id=admin_acc.id,
        corrected_text=transcription.raw_text
    )

    # Cria dispositivos originais da fonte
    src_p1 = SourceProvision.objects.create(
        transcription=transcription,
        condominium=condo,
        kind="artigo",
        label="Artigo 1º",
        display_order=1,
        text="O condomínio destina-se exclusivamente a fins residenciais."
    )
    src_p2 = SourceProvision.objects.create(
        transcription=transcription,
        condominium=condo,
        kind="artigo",
        label="Artigo 2º",
        display_order=2,
        text="As despesas comuns serão rateadas proporcionalmente entre as unidades."
    )
    src_p3 = SourceProvision.objects.create(
        transcription=transcription,
        condominium=condo,
        kind="artigo",
        label="Artigo 3º",
        display_order=3,
        text="É expressamente proibida a permanência de animais de qualquer porte nas áreas comuns e vagas."
    )
    src_p4 = SourceProvision.objects.create(
        transcription=transcription,
        condominium=condo,
        kind="artigo",
        label="Artigo 4º",
        display_order=4,
        text="As reuniões do conselho serão convocadas exclusivamente por carta registrada com aviso de recebimento."
    )

    return {
        "condo": condo,
        "admin": admin_acc,
        "project": project,
        "document": document,
        "transcription": transcription,
        "source_provisions": [src_p1, src_p2, src_p3, src_p4]
    }


# ============================================================================
# CA-19: DISPOSITIVO INCLUÍDO NÃO INVENTA ORIGEM
# ============================================================================

def test_ca_19_dispositivo_incluido_nao_inventa_origem(phase4_setup):
    """
    CA-19: Dispositivo incluído como novo na minuta sem correspondente na convenção anterior
    não pode receber vinculação forçada ou fictícia a dispositivo antigo.
    """
    ctx = phase4_setup
    condo = ctx['condo']
    admin = ctx['admin']
    doc = ctx['document']
    src_p1 = ctx['source_provisions'][0]

    # Cria dispositivo estritamente novo na minuta
    new_prov = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. Novo",
        text="Fica autorizada a instalação de pontos de recarga veicular nas garagens individuais.",
        author_account_id=admin.id
    )
    # Define como 'incluido'
    rev = ProvisionService.get_latest_revision(new_prov.id)
    rev.change_type = 'incluido'
    rev.save()

    # Tentativa de criar mapeamento de origem para dispositivo 'incluido' deve falhar
    with pytest.raises(FictitiousOriginError) as exc_info:
        OriginMappingService.create_mapping(
            condominium_id=condo.id,
            revision_id=rev.id,
            source_provision_id=src_p1.id,
            relation_type='mantido'
        )
    assert "não pode ter vinculação de origem" in str(exc_info.value)

    # API REST também rejeita com HTTP 400
    client = APIClient()
    url = f"/api/v1/condominiums/{condo.id}/provisions/{new_prov.id}/origin-mappings"
    response = client.post(url, {
        "source_provision_id": str(src_p1.id),
        "relation_type": "mantido"
    }, format="json")
    assert response.status_code == 400
    assert response.data.get("code") == "FICTITIOUS_ORIGIN_PROHIBITED"

    # No relatório DePara, dispositivo novo consta sem origens fictícias
    report = ComparisonService.generate_depara_report(condo.id, doc.id)
    item = next(e for e in report['entries'] if e['draft_provision_id'] == str(new_prov.id))
    assert item['entry_type'] == 'incluido'
    assert item['has_fictitious_origin'] is False
    assert len(item['sources']) == 0


# ============================================================================
# CA-20: EXCLUÍDO SAI DO LIMPO E PERMANECE EM HISTÓRICO E DEPARA
# ============================================================================

def test_ca_20_dispositivo_excluido_sai_do_limpo_e_permanece_em_historico_e_depara(phase4_setup):
    """
    CA-20: Dispositivo marcado como excluído na minuta não consta no documento limpo exportado,
    mas permanece registrado com integridade histórica e no relatório DePara.
    """
    ctx = phase4_setup
    condo = ctx['condo']
    admin = ctx['admin']
    doc = ctx['document']
    src_p4 = ctx['source_provisions'][3]

    # Cria dispositivo na minuta representando o antigo Art. 4º (convocação por carta registrada)
    prov_carta = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 4º",
        text=src_p4.text,
        author_account_id=admin.id
    )
    rev = ProvisionService.get_latest_revision(prov_carta.id)

    # Cria mapeamento de origem
    OriginMappingService.create_mapping(
        condominium_id=condo.id,
        revision_id=rev.id,
        source_provision_id=src_p4.id,
        relation_type='mantido',
        reason="Dispositivo obsoleto diante da comunicação digital"
    )

    # Marca dispositivo como excluído na minuta
    ProvisionService.update_provision(
        provision_id=prov_carta.id,
        expected_etag=rev.etag,
        text="[REVOGADO / EXCLUÍDO DA MINUTA]",
        label="Art. 4º (Excluído)",
        change_type="excluido",
        author_account_id=admin.id
    )

    # 1. Valida que o histórico de revisões preserva a revisão
    all_revs = ProvisionRevision.objects.filter(provision=prov_carta)
    assert all_revs.count() == 2
    assert all_revs.latest('revision_number').change_type == 'excluido'

    # 2. Valida que a exportação limpa preliminar NÃO contém o dispositivo excluído
    clean_doc = ExportService.export_clean_document(condo.id, doc.id)
    clean_prov_ids = [p['provision_id'] for p in clean_doc['provisions']]
    assert str(prov_carta.id) not in clean_prov_ids

    # 3. Valida que a invariante de documento limpo rejeita item excluído
    with pytest.raises(ExcludedProvisionInCleanExportError):
        assert_excluded_provision_not_in_clean_document('excluido')

    # 4. Valida que o relatório DePara registra o dispositivo excluído com suas origens e justificativa
    report = ComparisonService.generate_depara_report(condo.id, doc.id)
    entry = next(e for e in report['entries'] if e['draft_provision_id'] == str(prov_carta.id))
    assert entry['entry_type'] == 'excluido'
    assert len(entry['sources']) == 1
    assert entry['sources'][0]['source_label'] == src_p4.label


# ============================================================================
# CA-21: DESMEMBRAR E CONSOLIDAR PRESERVAM RELAÇÃO MUITOS-PARA-MUITOS (N:M)
# ============================================================================

def test_ca_21_desmembrar_e_consolidar_preservam_relacao_muitos_para_muitos(phase4_setup):
    """
    CA-21: Desmembramento (1 origem -> N destinos) e consolidação (N origens -> 1 destino)
    são suportados por mapeamentos de origens N:M com integridade referencial.
    """
    ctx = phase4_setup
    condo = ctx['condo']
    admin = ctx['admin']
    doc = ctx['document']
    src_p1 = ctx['source_provisions'][0]
    src_p2 = ctx['source_provisions'][1]
    src_p3 = ctx['source_provisions'][2]  # "Animais e garagens"

    # --- CENÁRIO A: Desmembramento de src_p3 em dois novos artigos na minuta (1:N) ---
    prov_animais = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 10",
        text="A permanência de animais domésticos é permitida, desde que respeitadas as normas de higiene e sossego.",
        author_account_id=admin.id
    )
    prov_garagem = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 11",
        text="As vagas de garagem destinam-se exclusivamente a guarda de veículos automotores e motocicletas.",
        author_account_id=admin.id
    )

    rev_animais = ProvisionService.get_latest_revision(prov_animais.id)
    rev_garagem = ProvisionService.get_latest_revision(prov_garagem.id)

    # Mapeia ambos para a mesma origem src_p3 com relation_type='desmembrado'
    m_desm_1 = OriginMappingService.create_mapping(
        condominium_id=condo.id,
        revision_id=rev_animais.id,
        source_provision_id=src_p3.id,
        relation_type='desmembrado',
        reason="Desmembramento do antigo Art. 3º: regra de animais isolada"
    )
    m_desm_2 = OriginMappingService.create_mapping(
        condominium_id=condo.id,
        revision_id=rev_garagem.id,
        source_provision_id=src_p3.id,
        relation_type='desmembrado',
        reason="Desmembramento do antigo Art. 3º: regra de garagem isolada"
    )

    # Verifica que 1 fonte aponta para 2 destinos
    mappings_from_src3 = OriginMappingService.list_mappings_for_source(condo.id, src_p3.id)
    assert len(mappings_from_src3) == 2
    assert {m.revision_id for m in mappings_from_src3} == {rev_animais.id, rev_garagem.id}

    # --- CENÁRIO B: Consolidação de src_p1 e src_p2 em um único artigo na minuta (N:1) ---
    prov_consolidado = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 1º",
        text="O condomínio é residencial, competindo aos coproprietários o custeio proporcional das despesas comuns.",
        author_account_id=admin.id
    )
    rev_consol = ProvisionService.get_latest_revision(prov_consolidado.id)

    # Mapeia duas origens para a mesma revisão da minuta com relation_type='consolidado'
    OriginMappingService.create_mapping(
        condominium_id=condo.id,
        revision_id=rev_consol.id,
        source_provision_id=src_p1.id,
        relation_type='consolidado',
        reason="Consolidação: união de destinação residencial e rateio"
    )
    OriginMappingService.create_mapping(
        condominium_id=condo.id,
        revision_id=rev_consol.id,
        source_provision_id=src_p2.id,
        relation_type='consolidado',
        reason="Consolidação: união de destinação residencial e rateio"
    )

    # Verifica que 1 destino aponta para 2 fontes
    mappings_to_consol = OriginMappingService.list_mappings_for_revision(condo.id, rev_consol.id)
    assert len(mappings_to_consol) == 2
    assert {m.source_provision_id for m in mappings_to_consol} == {src_p1.id, src_p2.id}


# ============================================================================
# CA-22: RENUMERAR PRESERVA REFERÊNCIAS, COMENTÁRIOS E UUIDS PERMANENTES
# ============================================================================

def test_ca_22_renumerar_preserva_referencias_comentarios_e_uuids(phase4_setup):
    """
    CA-22: Renumeração de dispositivos atualiza labels e posições sem alterar os UUIDs permanentes,
    preservando notas internas associadas e atualizando referências cruzadas dinamicamente.
    """
    ctx = phase4_setup
    condo = ctx['condo']
    admin = ctx['admin']
    doc = ctx['document']

    # Cria Art. 1 e Art. 2
    p1 = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. Antigo 1",
        text="São deveres dos condôminos respeitar o regimento.",
        position=1,
        author_account_id=admin.id
    )
    p2 = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. Antigo 2",
        text="Aplica-se advertência e multa pelo descumprimento das regras.",
        position=2,
        author_account_id=admin.id
    )

    original_p1_uuid = p1.id
    original_p2_uuid = p2.id

    # Adiciona nota interna ao dispositivo p2
    note = InternalNoteService.create_note(
        condominium_id=condo.id,
        provision_id=p2.id,
        author_account_id=admin.id,
        content="Verificar se o valor da multa máxima respeita o Código Civil (5 vezes a cota).",
        category="juridico"
    )

    rev_p1 = ProvisionService.get_latest_revision(p1.id)
    # Cria referência cruzada de p1 apontando para o UUID permanente de p2
    xref = CrossReferenceService.create_cross_reference(
        condominium_id=condo.id,
        revision_id=rev_p1.id,
        target_provision_id=p2.id,
        label_template="nos termos do art. {target_label}"
    )

    # 1. Executa prévia da renumeração
    preview = RenumberingService.preview_renumbering(condo.id, doc.id)
    assert preview['total_articles_renumbered'] >= 2
    for item in preview['preview_items']:
        assert item['uuid_preserved'] is True

    # 2. Aplica renumeração automática
    apply_res = RenumberingService.apply_renumbering(
        condominium_id=condo.id,
        document_id=doc.id,
        author_account_id=admin.id
    )
    assert apply_res['status'] == 'completed'

    # 3. Verifica que os UUIDs dos dispositivos permaneceram exatamente os mesmos
    p1_reloaded = Provision.objects.get(id=original_p1_uuid)
    p2_reloaded = Provision.objects.get(id=original_p2_uuid)
    assert p1_reloaded.id == original_p1_uuid
    assert p2_reloaded.id == original_p2_uuid

    # 4. Verifica que as notas internas continuam vinculadas perfeitamente ao p2
    notes_p2 = InternalNoteService.list_notes_for_provision(p2.id, user_role="juridico")
    assert len(notes_p2) == 1
    assert notes_p2[0].id == note.id

    # 5. Verifica que a referência cruzada resolveu para a nova numeração do alvo
    rev_p1_nova = ProvisionService.get_latest_revision(p1.id)
    resolved_xrs = CrossReferenceService.resolve_references_for_revision(condo.id, rev_p1_nova.id)
    assert len(resolved_xrs) == 1
    # p2 foi renumerado para Art. 2º
    assert "art. Art. 2º" in resolved_xrs[0]['rendered_text']
    assert resolved_xrs[0]['status'] == 'valido'

    # 6. Se o alvo for excluído, a referência cruzada passa para status 'quebrado'
    rev_p2_atual = ProvisionService.get_latest_revision(p2.id)
    ProvisionService.update_provision(
        provision_id=p2.id,
        expected_etag=rev_p2_atual.etag,
        text="[REVOGADO]",
        change_type="excluido",
        author_account_id=admin.id
    )
    # Reexecuta atualização de status de referências
    RenumberingService.apply_renumbering(condo.id, doc.id, author_account_id=admin.id)
    resolved_after_exclusion = CrossReferenceService.resolve_references_for_revision(condo.id, rev_p1_nova.id)
    assert resolved_after_exclusion[0]['status'] == 'quebrado'


# ============================================================================
# CA-42: DOCUMENTO LIMPO SEM IDENTIDADE, NOTAS OU REFERÊNCIA ANTIGA INDEVIDA
# ============================================================================

def test_ca_42_documento_limpo_sem_identidade_notas_ou_referencia_antiga(phase4_setup):
    """
    CA-42: A versão limpa preliminar de exportação omite dados de autoria,
    omite notas internas, exclui dispositivos revogados e inclui aviso legal obrigatório.
    """
    ctx = phase4_setup
    condo = ctx['condo']
    admin = ctx['admin']
    doc = ctx['document']

    # Cria dispositivo ativo com nota interna
    p_ativo = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 1º",
        text="O condomínio é constituído por 50 unidades autônomas.",
        author_account_id=admin.id
    )
    InternalNoteService.create_note(
        condominium_id=condo.id,
        provision_id=p_ativo.id,
        author_account_id=admin.id,
        content="Nota altamente confidencial sobre a construtora.",
        category="juridico",
        visibility="gestao"
    )

    # Cria dispositivo excluído
    p_excluido = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 2º",
        text="Dispositivo que foi revogado pela comissão.",
        author_account_id=admin.id
    )
    rev_excluido = ProvisionService.get_latest_revision(p_excluido.id)
    rev_excluido.change_type = 'excluido'
    rev_excluido.save()

    # Gera export limpo preliminar
    clean_data = ExportService.export_clean_document(condo.id, doc.id)

    # 1. Verifica presença de disclaimer preliminar obrigatório
    assert "Minuta preliminar" in clean_data['disclaimer']
    assert clean_data['electoral_features_present'] is False

    # 2. Verifica que p_excluido NÃO está no documento limpo
    ids_no_limpo = [p['provision_id'] for p in clean_data['provisions']]
    assert str(p_ativo.id) in ids_no_limpo
    assert str(p_excluido.id) not in ids_no_limpo

    # 3. Verifica sanitização de autoria e notas internas
    for item in clean_data['provisions']:
        assert 'author_account_id' not in item
        assert 'internal_notes' not in item
        assert 'notes' not in item
        assert 'legal_opinions' not in item

    # 4. Export em texto corrido também omite notas e excluídos
    clean_text = ExportService.export_clean_text(condo.id, doc.id)
    assert "Nota altamente confidencial" not in clean_text
    assert "Dispositivo que foi revogado" not in clean_text
    assert "Art. 1º O condomínio é constituído por 50 unidades autônomas." in clean_text


# ============================================================================
# COMPARAÇÃO LADO A LADO E DIFF GRANULAR
# ============================================================================

def test_comparacao_lado_a_lado_diff_granular(phase4_setup):
    """
    Testa o motor de comparação lado a lado entre original e minuta com cálculo de diff.
    """
    ctx = phase4_setup
    condo = ctx['condo']
    admin = ctx['admin']
    doc = ctx['document']
    src_p1 = ctx['source_provisions'][0]

    # Cria revisão alterada na minuta
    prov = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 1º",
        text="O condomínio destina-se exclusivamente a fins residenciais e unifamiliares.",
        author_account_id=admin.id
    )
    rev = ProvisionService.get_latest_revision(prov.id)
    rev.change_type = 'alterado'
    rev.save()

    # Mapeia origem
    OriginMappingService.create_mapping(
        condominium_id=condo.id,
        revision_id=rev.id,
        source_provision_id=src_p1.id,
        relation_type='alterado'
    )

    # Executa comparação
    comp = ComparisonService.compare_revision_with_source(condo.id, rev.id)
    assert comp['change_type'] == 'alterado'
    assert comp['diff']['has_changes'] is True
    assert comp['diff']['words_added'] > 0
    # Verifica que identificou a inserção de 'e unifamiliares.'
    blocks = comp['diff']['blocks']
    assert any(b['type'] in ('insert', 'replace') for b in blocks)


# ============================================================================
# ISOLAMENTO MULTI-TENANT NA FASE 4
# ============================================================================

def test_isolamento_tenant_fase4(phase4_setup):
    """
    Garante que mapeamentos de origens e documentos de um condomínio
    não sejam expostos ou manipulados por outro condomínio.
    """
    ctx = phase4_setup
    condo1 = ctx['condo']
    doc1 = ctx['document']

    # Cria segundo condomínio independente
    condo2 = Condominium.objects.create(name="Condomínio Outro Lado Tenancy")

    client = APIClient()

    # Tentativa de obter relatório DePara do condomínio 1 passando o id do condomínio 2
    url_cross = f"/api/v1/condominiums/{condo2.id}/documents/{doc1.id}/depara"
    response = client.get(url_cross)
    assert response.status_code == 404
