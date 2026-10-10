"""
Testes Automatizados para a Fase 5 — Consulta Pública, Participação e Moderação Editorial — CONDOC
Cobre integralmente os critérios de aceite:
- CA-25: Sugestão privada recebe protocolo e versão consultada
- CA-26: Conselho/revisor analisa conteúdo sem identidade (sanitização de DTO)
- CA-27: Análise técnica e decisão editorial não publicam automaticamente (4 dimensões independentes)
- CA-28: Admin sem papel de síndico não pode autorizar publicação (exclusivo síndico ativo)
- CA-29: Portal público exibe apenas versões autorizadas pelo síndico
- CA-30: Complemento nasce privado e é moderado independentemente
- CA-31: Edição de sugestão publicada gera nova versão pendente de nova moderação
- CA-32: Ocultação pelo síndico bloqueia imediatamente API, link, busca e interações
- CA-33: Acesso à identidade exige autorização e justificativa auditada (IdentityAccessEvent)
- CA-34: Anexos nascem privados e não publicam automaticamente
- Isolamento multi-tenancy entre condomínios
"""
import uuid
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    Resident,
    UnitMembership,
    RoleAssignment,
    Project,
    Document,
    Provision,
    ProvisionRevision,
    DocumentSnapshot,
    SnapshotItem,
    SourceFile,
    ConsultationCampaign,
    CampaignParticipant,
    Suggestion,
    SuggestionRevision,
    PublishedSuggestionRevision,
    SuggestionEditorialDecision,
    IdentityAccessEvent,
    SuggestionAttachment,
)
from application.documents.services import (
    ProjectService,
    DocumentService,
    ProvisionService,
    SnapshotService,
    SourceFileService,
)
from application.moderation.services import (
    CampaignService,
    SuggestionService,
    ModerationService,
)
from domain.moderation.exceptions import (
    CampaignNotOpenError,
    ParticipantNotEligibleError,
    UnauthorizedPublicationError,
    AutoPublicationForbiddenError,
    HiddenSuggestionAccessError,
    IdentityAccessWithoutJustificationError,
    ComplementWithoutParentError,
)
from domain.moderation.invariants import (
    assert_can_publish_suggestion,
    assert_analysis_does_not_auto_publish,
    assert_identity_access_authorized,
    assert_suggestion_not_hidden,
    sanitize_public_suggestion_dto,
    sanitize_author_suggestion_dto,
)


@pytest.fixture
def phase5_setup(db):
    """Cenário de teste para a Fase 5 com condomínio, síndico, morador, projeto, documento e snapshot."""
    condo = Condominium.objects.create(name="Condomínio Bosque dos Ipês")
    building = Building.objects.create(condominium=condo, code="BL-A", name="Bloco A")
    unit = Unit.objects.create(condominium=condo, building=building, code="101")

    # Contas: Síndico e Admin Comum (ambos com RoleAssignment)
    sindico = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="sindico.ipês@condoc.com.br",
        full_name="Dr. Síndico Geral"
    )
    RoleAssignment.objects.create(
        condominium=condo,
        account=sindico,
        role="sindico",
        status="active"
    )

    admin_comum = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="admin.auxiliar@condoc.com.br",
        full_name="Carlos Operador Admin"
    )
    RoleAssignment.objects.create(
        condominium=condo,
        account=admin_comum,
        role="admin",
        status="active"
    )

    # Morador e Vínculo Ativo
    morador_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="mariana.101@gmail.com",
        full_name="Mariana Moradora"
    )
    resident = Resident.objects.create(
        condominium=condo,
        account=morador_acc,
        full_name=morador_acc.full_name,
        phone_e164="+5511988887777"
    )
    membership = UnitMembership.objects.create(
        condominium=condo,
        resident=resident,
        unit=unit,
        category="proprietario_residente",
        verification_status="validado",
        membership_status="active"
    )

    # Projeto e Documento
    proj = ProjectService.create_project(
        condominium_id=condo.id,
        name="Revisão Regimento 2026",
        coordinator_account_id=sindico.id
    )
    doc = DocumentService.create_document(
        project_id=proj.id,
        condominium_id=condo.id,
        title="Minuta do Regimento Interno 2026",
        type="regimento_interno"
    )

    # Dispositivo normativo na minuta
    p1 = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 10",
        text="O horário de silêncio inicia-se rigorosamente às 22h00.",
        author_account_id=sindico.id
    )

    # Cria snapshot congelado (CA-41)
    snapshot = SnapshotService.create_snapshot(
        document_id=doc.id,
        condominium_id=condo.id,
        version_label="Snapshot Consulta Pública v1.0",
        frozen_by_id=sindico.id,
        purpose="consulta_publica"
    )

    # Cria campanha vinculada ao snapshot e abre a campanha
    campaign = CampaignService.create_campaign(
        condominium_id=condo.id,
        project_id=proj.id,
        snapshot_id=snapshot.id,
        name="Consulta Pública - Regimento 2026"
    )
    CampaignService.open_campaign(campaign.id, condo.id)

    # Habilita o morador na campanha
    participant = CampaignService.register_participant(
        condominium_id=condo.id,
        campaign_id=campaign.id,
        resident_id=resident.id,
        reference_membership_id=membership.id,
        authorized_by_id=sindico.id
    )

    return {
        "condo": condo,
        "sindico": sindico,
        "admin_comum": admin_comum,
        "resident": resident,
        "membership": membership,
        "document": doc,
        "provision_1": p1,
        "snapshot": snapshot,
        "campaign": campaign,
        "participant": participant,
    }


def test_ca_25_sugestao_privada_recebe_protocolo_e_versao_consultada(phase5_setup):
    """
    CA-25 / V21-26: Sugestão privada recebe protocolo e versão consultada.
    Toda sugestão enviada nasce privada, com protocolo único e registro da versão consultada.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    p1 = ctx['provision_1']

    # Morador submete sugestão sobre o Art. 10
    suggestion = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="O horário de silêncio deve iniciar às 23h00 nas sextas-feiras e sábados.",
        justification="Permitir confraternizações moderadas nos finais de semana.",
        category="redacao",
        target_provision_id=p1.id
    )

    # Validações estruturais do CA-25
    assert suggestion.public_protocol.startswith("SUG-2026-")
    assert suggestion.publication_status == 'nao_publicada'
    assert suggestion.analysis_status == 'pendente'
    assert suggestion.editorial_decision == 'pendente'
    assert suggestion.incorporation_status == 'nao_incorporada'
    assert suggestion.target_provision_id == p1.id
    assert suggestion.target_snapshot_revision is not None

    # Valida que foi criada a revisão v1 da sugestão
    rev = SuggestionRevision.objects.get(suggestion=suggestion, version_number=1)
    assert rev.text == "O horário de silêncio deve iniciar às 23h00 nas sextas-feiras e sábados."
    assert rev.justification == "Permitir confraternizações moderadas nos finais de semana."


def test_ca_26_revisor_analisa_conteudo_sem_identidade(phase5_setup):
    """
    CA-26 / UI-25 / V21-02: Conselho/revisores analisam conteúdo sem identidade.
    O DTO público e de moderação não inclui dados do autor (nome, email, telefone, unidade).
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    p1 = ctx['provision_1']

    sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Proponho inclusão de regras para veículos elétricos na garagem.",
        justification="Aumento de moradores com carros elétricos.",
        category="adicao",
        target_provision_id=p1.id
    )

    # 1. Fila de moderação para a equipe
    queue = ModerationService.list_moderation_queue(condo.id, camp.id)
    assert len(queue) == 1
    queue_item = queue[0]
    # Nenhum campo pessoal presente
    assert 'resident_name' not in queue_item
    assert 'email' not in queue_item
    assert 'unit_code' not in queue_item
    assert 'phone' not in queue_item
    assert queue_item['public_protocol'] == sug.public_protocol

    # 2. Invariante de sanitização de DTO público
    raw_payload = {
        "id": str(sug.id),
        "public_protocol": sug.public_protocol,
        "author_name": "Mariana Moradora",
        "email": "mariana@gmail.com",
        "unit": "101",
        "sanitized_public_text": "Texto público",
        "sanitized_justification": "Justificativa pública",
        "internal_note": "Nota jurídica confidencial"
    }
    sanitized = sanitize_public_suggestion_dto(raw_payload)
    assert 'author_name' not in sanitized
    assert 'email' not in sanitized
    assert 'unit' not in sanitized
    assert 'internal_note' not in sanitized
    assert sanitized['public_protocol'] == sug.public_protocol


def test_ca_27_analise_e_decisao_nao_publicam_automaticamente(phase5_setup):
    """
    CA-27: Conclusão de análise técnica e acolhimento editorial NÃO publicam automaticamente.
    A publicação exige autorização explícita e separada na mesa de publicação do síndico.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    admin = ctx['admin_comum']

    sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Proponho tolerância de 15 minutos para carga e descarga.",
        justification="Facilitar entregas de supermercado.",
        category="redacao"
    )

    # 1. Operador/analista executa análise técnica concluída
    ModerationService.perform_technical_analysis(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        analyst_account_id=admin.id,
        new_status="concluida"
    )
    sug.refresh_from_db()
    assert sug.analysis_status == 'concluida'
    # NÃO publica automaticamente!
    assert sug.publication_status == 'nao_publicada'

    # 2. Comissão/conselho acolhe a sugestão editorialmente
    ModerationService.register_editorial_decision(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        decider_account_id=admin.id,
        decision="acolhida",
        public_shared_reason="Acolhida para aperfeiçoamento da redação normativa da minuta.",
        internal_note="Parecer jurídico prévio favorável à tolerância de 15 minutos."
    )
    sug.refresh_from_db()
    assert sug.editorial_decision == 'acolhida'
    # Permanece estritamente não publicada até decisão expressa do síndico!
    assert sug.publication_status == 'nao_publicada'

    # 3. Invariante rejeita publicação automática
    with pytest.raises(AutoPublicationForbiddenError):
        assert_analysis_does_not_auto_publish('concluida', 'acolhida', 'publicada')


def test_ca_28_admin_sem_papel_de_sindico_nao_publica(phase5_setup):
    """
    CA-28 / V21-03 / V21-04: Admin sem papel de síndico não pode autorizar publicação.
    A autorização de publicação é prerrogativa pessoal e exclusiva do síndico ativo.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    admin = ctx['admin_comum']
    sindico = ctx['sindico']

    sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Adequar horário do salão de festas.",
        justification="Minimizar barulho no condomínio."
    )

    # 1. Admin comum tenta autorizar publicação -> DEVE FALHAR (UnauthorizedPublicationError)
    with pytest.raises(UnauthorizedPublicationError):
        ModerationService.authorize_publication(
            suggestion_id=sug.id,
            condominium_id=condo.id,
            actor_role="admin",  # Não é síndico!
            authorizer_account_id=admin.id
        )

    sug.refresh_from_db()
    assert sug.publication_status == 'nao_publicada'

    # 2. Conselho ou comissão também são recusados
    with pytest.raises(UnauthorizedPublicationError):
        assert_can_publish_suggestion("conselho")
    with pytest.raises(UnauthorizedPublicationError):
        assert_can_publish_suggestion("comissao")

    # 3. Síndico ativo autoriza publicação sanitizada com sucesso
    pub_rev = ModerationService.authorize_publication(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico.id,
        sanitized_text="Adequar horário de funcionamento do salão de festas.",
        sanitized_justification="Minimizar barulho no condomínio."
    )
    sug.refresh_from_db()
    assert sug.publication_status == 'publicada'
    assert pub_rev.is_active_publication is True
    assert pub_rev.authorized_by_id == sindico.id


def test_ca_29_portal_mostra_apenas_versoes_autorizadas(phase5_setup):
    """
    CA-29 / UI-25: Portal público exibe apenas versões autorizadas pelo síndico.
    Sugestões não publicadas ou em análise não vazam para consultas públicas.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    sindico = ctx['sindico']

    # Sugestão 1: Não autorizada (privada/em análise)
    sug1 = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Sugestão privada 1 ainda em análise.",
        justification="Privada."
    )

    # Sugestão 2: Autorizada e publicada pelo síndico
    sug2 = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Sugestão pública 2 autorizada.",
        justification="Justificativa da sugestão 2."
    )
    ModerationService.authorize_publication(
        suggestion_id=sug2.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico.id
    )

    # Listagem pública da campanha
    public_sugs = SuggestionService.list_public_suggestions(condo.id, camp.id)

    # Apenas a sugestão 2 consta no retorno público!
    assert len(public_sugs) == 1
    assert public_sugs[0]['id'] == str(sug2.id)
    assert public_sugs[0]['public_protocol'] == sug2.public_protocol


def test_ca_30_complemento_privado_e_moderado_independentemente(phase5_setup):
    """
    CA-30 / V21-27: Complemento nasce privado e é moderado independentemente.
    Um complemento sobre sugestão pública passa por novo ciclo completo de moderação.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    sindico = ctx['sindico']

    # 1. Sugestão original publicada
    parent_sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Definição de regras para uso da piscina.",
        justification="Evitar conflitos de horário."
    )
    ModerationService.authorize_publication(
        suggestion_id=parent_sug.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico.id
    )

    # 2. Outro envio representando complemento da sugestão pública
    complement = SuggestionService.create_complement_suggestion(
        condominium_id=condo.id,
        parent_published_suggestion_id=parent_sug.id,
        participant_id=part.id,
        text="Complemento: Exigir exame médico para acesso à piscina.",
        justification="Proteção da saúde coletiva."
    )

    # O complemento nasce como privada e com status de moderação independentes!
    assert complement.parent_published_suggestion_id == parent_sug.id
    assert complement.publication_status == 'nao_publicada'
    assert complement.analysis_status == 'pendente'
    assert complement.editorial_decision == 'pendente'
    assert complement.public_protocol != parent_sug.public_protocol


def test_ca_31_edicao_publicada_cria_versao_pendente(phase5_setup):
    """
    CA-31 / V21-28: Edição de sugestão publicada gera nova versão pendente de nova moderação.
    A nova revisão não entra no ar automaticamente e não sobrescreve a versão publicada anterior.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    sindico = ctx['sindico']

    sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Instalação de bicicletário no subsolo.",
        justification="Incentivo à mobilidade sustentável."
    )
    pub_v1 = ModerationService.authorize_publication(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico.id
    )

    # Morador edita sua sugestão publicada gerando revisão v2
    new_rev = SuggestionService.update_suggestion(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        author_account_id=sindico.id,
        new_text="Instalação de bicicletário no subsolo com tomada para bikes elétricas.",
        new_justification="Atualização tecnológica necessária."
    )

    assert new_rev.version_number == 2
    sug.refresh_from_db()

    # O status editorial volta para pendente de re-análise
    assert sug.analysis_status == 'pendente'
    assert sug.editorial_decision == 'pendente'

    # A publicação ativa no portal continua exibindo o texto v1 aprovado pelo síndico!
    public_detail = SuggestionService.get_public_suggestion(condo.id, sug.id)
    assert public_detail['sanitized_public_text'] == "Instalação de bicicletário no subsolo."


def test_ca_32_ocultacao_bloqueia_api_link_busca_e_interacao(phase5_setup):
    """
    CA-32 / V21-36: Ocultação pelo síndico bloqueia imediatamente API, link, busca e interações.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    sindico = ctx['sindico']

    sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Sugestão que será ocultada.",
        justification="Justificativa."
    )
    ModerationService.authorize_publication(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico.id
    )

    # 1. Antes da ocultação: acessível publicamente
    assert len(SuggestionService.list_public_suggestions(condo.id, camp.id)) == 1

    # 2. Síndico oculta a publicação
    ModerationService.hide_published_suggestion(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        actor_role="sindico",
        actor_account_id=sindico.id,
        reason="Conteúdo ofensivo ou em desacordo com as regras de convivência."
    )

    # 3. Listagem pública não exibe a sugestão
    assert len(SuggestionService.list_public_suggestions(condo.id, camp.id)) == 0

    # 4. Acesso por link direto lança HiddenSuggestionAccessError
    with pytest.raises(HiddenSuggestionAccessError):
        SuggestionService.get_public_suggestion(condo.id, sug.id)

    # 5. Invariante valida rejeição
    with pytest.raises(HiddenSuggestionAccessError):
        assert_suggestion_not_hidden(timezone.now(), "oculta")


def test_ca_33_acesso_a_identidade_exige_autorizacao_e_justificativa_auditada(phase5_setup):
    """
    CA-33 / V21-33: Acesso à identidade exige autorização e justificativa auditada.
    Registra evento em app.identity_access_events com motivo obrigatório.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    sindico = ctx['sindico']

    sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Sugestão para auditoria de identidade.",
        justification="Justificativa."
    )

    # 1. Sem justificativa ou justificativa curta -> DEVE FALHAR
    with pytest.raises(IdentityAccessWithoutJustificationError):
        ModerationService.access_suggestion_identity(
            suggestion_id=sug.id,
            condominium_id=condo.id,
            actor_role="sindico",
            actor_account_id=sindico.id,
            justification="123"  # Menos de 5 caracteres
        )

    # 2. Papel não administrativo -> DEVE FALHAR
    with pytest.raises(IdentityAccessWithoutJustificationError):
        assert_identity_access_authorized("morador", "Verificação necessária")

    # 3. Consulta fundamentada pelo síndico
    initial_audit_count = IdentityAccessEvent.objects.filter(condominium_id=condo.id).count()
    identity = ModerationService.access_suggestion_identity(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        actor_role="sindico",
        actor_account_id=sindico.id,
        justification="Verificação de unidade para dirimir dúvida sobre vaga de garagem."
    )

    # Verifica os dados retornados
    assert identity['full_name'] == "Mariana Moradora"
    assert identity['email'] == "mariana.101@gmail.com"
    assert identity['unit_code'] == "101"

    # Verifica registro da auditoria
    assert IdentityAccessEvent.objects.filter(condominium_id=condo.id).count() == initial_audit_count + 1
    audit = IdentityAccessEvent.objects.filter(condominium_id=condo.id).latest('created_at')
    assert audit.target_id == sug.id
    assert "Verificação de unidade" in audit.purpose


def test_ca_34_anexos_nascem_privados_e_nao_publicam_automaticamente(phase5_setup):
    """
    CA-34: Anexos nascem privados e não publicam automaticamente.
    A publicação do texto da sugestão não torna os anexos públicos sem autorização expressa.
    """
    ctx = phase5_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part = ctx['participant']
    sindico = ctx['sindico']

    sug = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part.id,
        text="Sugestão com foto de vazamento.",
        justification="Anexo demonstra necessidade de obra urgente."
    )

    # Registra arquivo fonte
    source_file = SourceFileService.register_source_file(
        condominium_id=condo.id,
        uploaded_by_id=sindico.id,
        filename="foto_vazamento.jpg",
        mime_type="image/jpeg",
        size_bytes=2048,
        file_content=b"foto-bytes-vazamento"
    )

    # Vincula anexo à sugestão
    attachment = SuggestionService.add_attachment(
        condominium_id=condo.id,
        suggestion_id=sug.id,
        source_file_id=source_file.id
    )

    # Anexo nasce NÃO aprovado para publicação pública
    assert attachment.is_publicly_approved is False

    # Síndico publica a sugestão
    ModerationService.authorize_publication(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico.id
    )

    # O anexo CONTINUA privado (is_publicly_approved = False)!
    attachment.refresh_from_db()
    assert attachment.is_publicly_approved is False

    # Apenas com aprovação explícita do síndico o anexo torna-se público
    ModerationService.approve_attachment_publication(
        attachment_id=attachment.id,
        condominium_id=condo.id,
        actor_role="sindico",
        actor_account_id=sindico.id
    )
    attachment.refresh_from_db()
    assert attachment.is_publicly_approved is True


def test_isolamento_tenant_fase5(phase5_setup):
    """Isolamento estrito multi-tenancy: um condomínio não acessa campanhas nem sugestões de outro."""
    ctx = phase5_setup
    condo1 = ctx['condo']
    camp1 = ctx['campaign']
    part1 = ctx['participant']

    # Condomínio 2 independente
    condo2 = Condominium.objects.create(name="Condomínio Solar das Flores")

    sug1 = SuggestionService.create_suggestion(
        condominium_id=condo1.id,
        campaign_id=camp1.id,
        participant_id=part1.id,
        text="Sugestão exclusiva do condomínio 1.",
        justification="Justificativa."
    )

    # Tentativa de listar campanhas ou moderação no condomínio 2 não retorna nada do condomínio 1
    queue_condo2 = ModerationService.list_moderation_queue(condominium_id=condo2.id)
    assert len(queue_condo2) == 0

    # Tentativa de acesso à sugestão do condomínio 1 com tenant do condomínio 2 falha
    with pytest.raises(Suggestion.DoesNotExist):
        Suggestion.objects.get(id=sug1.id, condominium_id=condo2.id)


def test_fluxo_completo_api_campanhas_sugestoes_e_moderacao(phase5_setup):
    """
    Testa o fluxo REST completo da Fase 5 via APIClient:
    Campanha -> Participante -> Sugestão Privada -> Moderação em 4 dimensões -> Mesa do Síndico -> Acesso Auditado -> Ocultação.
    """
    client = APIClient()
    ctx = phase5_setup
    condo = ctx['condo']
    sindico = ctx['sindico']
    admin = ctx['admin_comum']
    part = ctx['participant']
    p1 = ctx['provision_1']
    snap = ctx['snapshot']
    proj = Project.objects.filter(condominium_id=condo.id).first()

    # 1. Cria nova campanha via API
    resp_camp = client.post(
        f"/api/v1/condominiums/{condo.id}/campaigns",
        data={
            "project_id": str(proj.id),
            "snapshot_id": str(snap.id),
            "name": "Consulta Regimento via API",
            "description": "Teste end-to-end de API"
        },
        format="json"
    )
    assert resp_camp.status_code == 201
    camp_id = resp_camp.data['id']

    # 2. Abre a campanha via API
    resp_open = client.post(
        f"/api/v1/condominiums/{condo.id}/campaigns/{camp_id}/open"
    )
    assert resp_open.status_code == 200
    assert resp_open.data['state'] == 'aberta'

    # 3. Morador submete sugestão privada na campanha aberta
    resp_sug = client.post(
        f"/api/v1/condominiums/{condo.id}/campaigns/{camp_id}/suggestions",
        data={
            "participant_id": str(part.id),
            "target_provision_id": str(p1.id),
            "text": "Sugestão submetida via REST API.",
            "justification": "Justificativa detalhada enviada pelo morador.",
            "category": "redacao"
        },
        format="json"
    )
    assert resp_sug.status_code == 201
    sug_id = resp_sug.data['id']
    protocol = resp_sug.data['public_protocol']
    assert protocol.startswith("SUG-2026-")
    assert resp_sug.data['publication_status'] == 'nao_publicada'

    # 4. Consulta pública na campanha não exibe a sugestão (pois é privada/não autorizada)
    resp_public_list = client.get(
        f"/api/v1/condominiums/{condo.id}/campaigns/{camp_id}/suggestions"
    )
    assert resp_public_list.status_code == 200
    assert len(resp_public_list.data) == 0

    # 5. Equipe visualiza fila de moderação com 4 dimensões (S16, CA-26: sem PII)
    resp_queue = client.get(
        f"/api/v1/condominiums/{condo.id}/moderation/queue?campaign_id={camp_id}"
    )
    assert resp_queue.status_code == 200
    assert len(resp_queue.data) == 1
    queue_item = resp_queue.data[0]
    assert queue_item['public_protocol'] == protocol
    assert 'resident_name' not in queue_item
    assert 'email' not in queue_item

    # 6. Analista conclui análise técnica via API (CA-27: não publica)
    resp_analysis = client.post(
        f"/api/v1/condominiums/{condo.id}/moderation/suggestions/{sug_id}/analysis",
        data={"new_status": "concluida"},
        format="json"
    )
    assert resp_analysis.status_code == 200
    assert resp_analysis.data['analysis_status'] == 'concluida'
    assert resp_analysis.data['publication_status'] == 'nao_publicada'

    # 7. Comissão registra decisão editorial acolhida via API (CA-27: não publica)
    resp_dec = client.post(
        f"/api/v1/condominiums/{condo.id}/moderation/suggestions/{sug_id}/decision",
        data={
            "decision": "acolhida",
            "public_shared_reason": "Sugestão acolhida pela comissão para aprimorar o texto.",
            "internal_note": "Anotação interna da comissão."
        },
        format="json"
    )
    assert resp_dec.status_code == 200
    assert resp_dec.data['decision'] == 'acolhida'

    # 8. Admin sem papel de síndico tenta publicar -> HTTP 403 (CA-28)
    resp_pub_denied = client.post(
        f"/api/v1/condominiums/{condo.id}/moderation/suggestions/{sug_id}/publish?role=admin",
        data={"sanitized_text": "Texto sanitizado"},
        format="json"
    )
    assert resp_pub_denied.status_code == 403
    assert resp_pub_denied.data['code'] == 'UNAUTHORIZED_PUBLICATION_SINDICO_ONLY'

    # 9. Síndico ativo autoriza publicação na mesa de publicação (CA-28, S18)
    resp_pub_ok = client.post(
        f"/api/v1/condominiums/{condo.id}/moderation/suggestions/{sug_id}/publish?role=sindico",
        data={
            "sanitized_text": "Texto normativo sanitizado aprovado pelo síndico.",
            "sanitized_justification": "Justificativa pública sanitizada."
        },
        format="json"
    )
    assert resp_pub_ok.status_code == 200
    assert resp_pub_ok.data['status'] == 'publicada'

    # 10. Agora a listagem pública da campanha exibe a sugestão sanitizada (CA-29)
    resp_public_list_after = client.get(
        f"/api/v1/condominiums/{condo.id}/campaigns/{camp_id}/suggestions"
    )
    assert resp_public_list_after.status_code == 200
    assert len(resp_public_list_after.data) == 1
    assert resp_public_list_after.data[0]['sanitized_public_text'] == "Texto normativo sanitizado aprovado pelo síndico."
    assert 'author_account_id' not in resp_public_list_after.data[0]

    # 11. Consulta justificada de autoria/identidade com auditoria (CA-33)
    resp_identity = client.post(
        f"/api/v1/condominiums/{condo.id}/moderation/suggestions/{sug_id}/identity?role=sindico",
        data={"justification": "Diligência administrativa para conferir legitimidade."},
        format="json"
    )
    assert resp_identity.status_code == 200
    assert resp_identity.data['full_name'] == "Mariana Moradora"
    assert resp_identity.data['unit_code'] == "101"

    # 12. Síndico oculta a publicação (CA-32)
    resp_hide = client.post(
        f"/api/v1/condominiums/{condo.id}/moderation/suggestions/{sug_id}/hide?role=sindico",
        data={"reason": "Ocultação temporária para reavaliação."},
        format="json"
    )
    assert resp_hide.status_code == 200
    assert resp_hide.data['status'] == 'oculta'

    # 13. Acesso à sugestão oculta retorna HTTP 404 (CA-32)
    resp_get_hidden = client.get(
        f"/api/v1/condominiums/{condo.id}/suggestions/{sug_id}"
    )
    assert resp_get_hidden.status_code == 404
    assert resp_get_hidden.data['code'] == 'SUGGESTION_HIDDEN'

