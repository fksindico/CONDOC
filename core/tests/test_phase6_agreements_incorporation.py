"""
Testes Automatizados para a Fase 6 — Concordâncias Consultivas e Consolidação na Minuta — CONDOC
Cobre integralmente os critérios de aceite:
- CA-35: Cliques repetidos produzem exatamente uma concordância ativa (idempotência)
- CA-36: Retirada de concordância atualiza agregado e preserva evento no histórico
- CA-37: Mudança substancial não transfere concordâncias entre versões
- CA-38: Contagem oculta ausente no payload público para moradores
- CA-39: Estatística explicita texto, versão, segregação pessoa vs unidade, denominador e ressalva
- CA-40: Incorporação liga revisão da minuta e contribuição de forma transacional e atômica
- CA-45: Proibição terminante de votações, cálculo de quórum ou termos eleitorais
- PRD 257: Autor não pode concordar com a própria contribuição
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
    ConsultationCampaign,
    CampaignParticipant,
    Suggestion,
    SuggestionRevision,
    PublishedSuggestionRevision,
    SuggestionEditorialDecision,
    ConsultativeAgreement,
    AgreementEvent,
    SuggestionIncorporation,
    ConsultationSnapshot,
)
from application.documents.services import (
    ProjectService,
    DocumentService,
    ProvisionService,
    SnapshotService,
)
from application.moderation.services import (
    CampaignService,
    SuggestionService,
    ModerationService,
)
from application.agreements.services import (
    AgreementService,
    IncorporationService,
)
from domain.agreements.invariants import (
    DISCLAIMER_CONSULTATIVE_AGREEMENT,
    assert_no_electoral_terms,
    calculate_agreement_metrics,
    sanitize_public_metrics_payload,
)
from domain.agreements.exceptions import (
    CampaignClosedForAgreementsError,
    AuthorCannotAgreeWithOwnSuggestionError,
    ElectoralVocabularyForbiddenError,
    IncorporationIntegrityError,
)


@pytest.fixture
def phase6_setup(db):
    """Cenário completo para testes da Fase 6: condomínio, síndico, múltiplos moradores com unidades, campanha aberta."""
    condo = Condominium.objects.create(name="Condomínio Residencial das Palmeiras")
    building = Building.objects.create(condominium=condo, code="BL-A", name="Bloco A")
    unit_101 = Unit.objects.create(condominium=condo, building=building, code="101")
    unit_102 = Unit.objects.create(condominium=condo, building=building, code="102")
    unit_201 = Unit.objects.create(condominium=condo, building=building, code="201")

    # Síndico ativo
    sindico_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="sindico.palmeiras@condoc.com.br",
        full_name="Dr. Síndico Palmeiras"
    )
    RoleAssignment.objects.create(
        condominium=condo,
        account=sindico_acc,
        role="sindico",
        status="active"
    )

    # Morador 1 (Mariana - Unidade 101)
    acc_mariana = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="mariana.101@palmeiras.com.br",
        full_name="Mariana Moradora"
    )
    res_mariana = Resident.objects.create(
        condominium=condo,
        account=acc_mariana,
        full_name=acc_mariana.full_name
    )
    mb_mariana = UnitMembership.objects.create(
        condominium=condo,
        resident=res_mariana,
        unit=unit_101,
        category="proprietario_residente",
        verification_status="validado",
        membership_status="active"
    )

    # Morador 2 (Carlos Investidor - possui 2 unidades: 102 e 201)
    acc_carlos = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="carlos.investidor@palmeiras.com.br",
        full_name="Carlos Investidor"
    )
    res_carlos = Resident.objects.create(
        condominium=condo,
        account=acc_carlos,
        full_name=acc_carlos.full_name
    )
    mb_carlos_102 = UnitMembership.objects.create(
        condominium=condo,
        resident=res_carlos,
        unit=unit_102,
        category="proprietario_nao_residente",
        verification_status="validado",
        membership_status="active"
    )
    mb_carlos_201 = UnitMembership.objects.create(
        condominium=condo,
        resident=res_carlos,
        unit=unit_201,
        category="proprietario_nao_residente",
        verification_status="validado",
        membership_status="active"
    )

    # Morador 3 (Beatriz - inquilina na 102)
    acc_beatriz = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="beatriz.102@palmeiras.com.br",
        full_name="Beatriz Inquilina"
    )
    res_beatriz = Resident.objects.create(
        condominium=condo,
        account=acc_beatriz,
        full_name=acc_beatriz.full_name
    )
    mb_beatriz = UnitMembership.objects.create(
        condominium=condo,
        resident=res_beatriz,
        unit=unit_102,
        category="inquilino",
        verification_status="validado",
        membership_status="active"
    )

    # Projeto, Documento e Dispositivo
    proj = ProjectService.create_project(condominium_id=condo.id, name="Revisão Regimento 2026", coordinator_account_id=sindico_acc.id)
    doc = DocumentService.create_document(project_id=proj.id, condominium_id=condo.id, title="Regimento Interno", type="regimento_interno")
    p1 = ProvisionService.create_provision(
        document_id=doc.id,
        condominium_id=condo.id,
        kind="artigo",
        label="Art. 15",
        text="O uso da academia de ginástica é restrito aos moradores cadastrados.",
        author_account_id=sindico_acc.id
    )

    # Snapshot imutável
    snapshot = SnapshotService.create_snapshot(
        document_id=doc.id,
        condominium_id=condo.id,
        version_label="Snapshot v1.0",
        frozen_by_id=sindico_acc.id
    )

    # Campanha de Consulta Pública aberta
    campaign = CampaignService.create_campaign(
        condominium_id=condo.id,
        project_id=proj.id,
        snapshot_id=snapshot.id,
        name="Consulta Regimento Palmeiras",
        settings={"allow_suggestions": True, "allow_agreements": True, "hide_counts": False}
    )
    CampaignService.open_campaign(campaign.id, condo.id)

    # Habilita participantes
    part_mariana = CampaignService.register_participant(
        condominium_id=condo.id, campaign_id=campaign.id, resident_id=res_mariana.id, reference_membership_id=mb_mariana.id
    )
    part_carlos = CampaignService.register_participant(
        condominium_id=condo.id, campaign_id=campaign.id, resident_id=res_carlos.id, reference_membership_id=mb_carlos_102.id
    )
    part_beatriz = CampaignService.register_participant(
        condominium_id=condo.id, campaign_id=campaign.id, resident_id=res_beatriz.id, reference_membership_id=mb_beatriz.id
    )

    # Mariana envia sugestão privada
    suggestion = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=campaign.id,
        participant_id=part_mariana.id,
        text="Permitir convidados na academia nos sábados e domingos das 10h às 14h.",
        justification="Estimular atividades físicas compartilhadas com parentes.",
        target_provision_id=p1.id,
        author_account_id=acc_mariana.id
    )

    # Síndico acolhe e publica a versão 1 da sugestão
    ModerationService.perform_technical_analysis(suggestion.id, condo.id, sindico_acc.id, "concluida")
    ModerationService.register_editorial_decision(
        suggestion.id, condo.id, sindico_acc.id, "acolhida", "Acolhida para avaliação coletiva dos horários."
    )
    pub_v1 = ModerationService.authorize_publication(
        suggestion_id=suggestion.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico_acc.id,
        sanitized_text="Permitir acesso de até 1 convidado por unidade na academia aos finais de semana das 10h às 14h.",
        sanitized_justification="Estimular atividades físicas compartilhadas."
    )

    return {
        "condo": condo,
        "sindico": sindico_acc,
        "acc_mariana": acc_mariana,
        "acc_carlos": acc_carlos,
        "acc_beatriz": acc_beatriz,
        "res_mariana": res_mariana,
        "res_carlos": res_carlos,
        "res_beatriz": res_beatriz,
        "mb_mariana": mb_mariana,
        "mb_carlos_102": mb_carlos_102,
        "mb_carlos_201": mb_carlos_201,
        "mb_beatriz": mb_beatriz,
        "document": doc,
        "provision_1": p1,
        "campaign": campaign,
        "part_mariana": part_mariana,
        "part_carlos": part_carlos,
        "part_beatriz": part_beatriz,
        "suggestion": suggestion,
        "pub_v1": pub_v1,
    }


def test_ca_35_cliques_repetidos_produzem_uma_concordancia_ativa(phase6_setup):
    """
    CA-35: Cliques repetidos produzem exatamente uma concordância ativa (idempotência).
    Múltiplas requisições do mesmo participante para a mesma versão publicada não duplicam registros.
    """
    ctx = phase6_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part_carlos = ctx['part_carlos']
    pub_v1 = ctx['pub_v1']

    # 1. Primeiro clique em "Concordo"
    agr1 = AgreementService.register_agreement(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part_carlos.id,
        published_suggestion_revision_id=pub_v1.id
    )
    assert agr1.active is True

    # 2. Segundo clique consecutivo (mesmo participante, mesma versão)
    agr2 = AgreementService.register_agreement(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part_carlos.id,
        published_suggestion_revision_id=pub_v1.id
    )
    assert agr2.id == agr1.id
    assert agr2.active is True

    # 3. Terceiro clique consecutivo
    agr3 = AgreementService.register_agreement(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part_carlos.id,
        published_suggestion_revision_id=pub_v1.id
    )
    assert agr3.id == agr1.id

    # Valida no banco: existe rigorosamente 1 registro e 1 evento inicial
    agrs = ConsultativeAgreement.objects.filter(
        participant=part_carlos,
        published_suggestion_revision=pub_v1
    )
    assert agrs.count() == 1
    assert agrs.first().active is True


def test_ca_36_retirada_atualiza_agregado_e_preserva_evento(phase6_setup):
    """
    CA-36: Retirada atualiza agregado e preserva evento no histórico.
    A retirada coloca active=False, decrementa as estatísticas e registra evento histórico imutável.
    """
    ctx = phase6_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part_carlos = ctx['part_carlos']
    pub_v1 = ctx['pub_v1']

    # 1. Carlos concorda com a proposta
    agr = AgreementService.register_agreement(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part_carlos.id,
        published_suggestion_revision_id=pub_v1.id
    )
    assert agr.active is True

    # Estatística mostra 1 indivíduo concordante
    stats_before = AgreementService.get_revision_agreement_stats(condo.id, pub_v1.id)
    assert stats_before['concordant_individuals'] == 1

    # 2. Carlos retira sua concordância
    AgreementService.withdraw_agreement(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part_carlos.id,
        published_suggestion_revision_id=pub_v1.id,
        reason="Mudei de ideia sobre a lotação da academia."
    )

    # 3. Valida que o agregado atualizou para 0
    stats_after = AgreementService.get_revision_agreement_stats(condo.id, pub_v1.id)
    assert stats_after['concordant_individuals'] == 0
    assert stats_after['concordant_units'] == 0

    # 4. Valida que o evento histórico de retirada foi registrado imutavelmente
    events = AgreementEvent.objects.filter(agreement=agr).order_by('created_at')
    assert events.count() == 2
    assert events[0].action == 'agree'
    assert events[1].action == 'withdraw'
    assert "Mudei de ideia" in events[1].reason

    # 5. Se Carlos concordar novamente, reativa e grava 'reaffirm'
    agr_reativado = AgreementService.register_agreement(
        condominium_id=condo.id,
        campaign_id=camp.id,
        participant_id=part_carlos.id,
        published_suggestion_revision_id=pub_v1.id
    )
    assert agr_reativado.active is True
    assert AgreementEvent.objects.filter(agreement=agr).latest('created_at').action == 'reaffirm'


def test_ca_37_mudanca_substancial_nao_transfere_concordancias(phase6_setup):
    """
    CA-37 / V21-29 / PRD 56: Mudança substancial não transfere concordâncias.
    Concordâncias pertencem estritamente à versão avaliada. A publicação de uma nova versão
    inicia com 0 apoios, exigindo novas manifestações.
    """
    ctx = phase6_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part_carlos = ctx['part_carlos']
    part_beatriz = ctx['part_beatriz']
    sug = ctx['suggestion']
    pub_v1 = ctx['pub_v1']
    sindico = ctx['sindico']

    # 1. Carlos e Beatriz concordam com a Versão 1
    AgreementService.register_agreement(condo.id, camp.id, part_carlos.id, pub_v1.id)
    AgreementService.register_agreement(condo.id, camp.id, part_beatriz.id, pub_v1.id)

    stats_v1 = AgreementService.get_revision_agreement_stats(condo.id, pub_v1.id)
    assert stats_v1['concordant_individuals'] == 2

    # 2. Ocorre alteração substancial no horário/condição da proposta gerando Versão 2
    pub_v2 = ModerationService.authorize_publication(
        suggestion_id=sug.id,
        condominium_id=condo.id,
        actor_role="sindico",
        authorizer_account_id=sindico.id,
        sanitized_text="Permitir convidados na academia apenas de terça a quinta com taxa extra de R$ 30.",
        sanitized_justification="Mudança substancial de condições e cobrança de taxa."
    )

    # 3. Valida que a nova versão (pub_v2) NÃO herdou os apoios da versão anterior!
    stats_v2 = AgreementService.get_revision_agreement_stats(condo.id, pub_v2.id)
    assert stats_v2['concordant_individuals'] == 0
    assert stats_v2['concordant_units'] == 0

    # 4. A versão anterior (v1) mantém seu registro histórico intacto
    agrs_v1 = ConsultativeAgreement.objects.filter(published_suggestion_revision=pub_v1, active=True)
    assert agrs_v1.count() == 2


def test_ca_38_contagem_oculta_ausente_no_payload(phase6_setup):
    """
    CA-38 / V21-31 / UI-30: Contagem oculta ausente no payload público.
    Se a campanha define hide_counts=True, consultas públicas não recebem números ou percentuais.
    """
    ctx = phase6_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part_carlos = ctx['part_carlos']
    pub_v1 = ctx['pub_v1']

    # Registra concordância
    AgreementService.register_agreement(condo.id, camp.id, part_carlos.id, pub_v1.id)

    # 1. Ativa contagens ocultas na campanha
    camp.settings['hide_counts'] = True
    camp.save(update_fields=['settings'])

    # 2. Consulta pública para moradores (is_public_viewer=True)
    public_stats = AgreementService.get_revision_agreement_stats(
        condominium_id=condo.id,
        published_suggestion_revision_id=pub_v1.id,
        is_public_viewer=True
    )

    # Contagens numéricas e percentuais NÃO estão presentes no payload público!
    assert 'concordant_individuals' not in public_stats
    assert 'concordant_units' not in public_stats
    assert 'percentage_individuals' not in public_stats
    assert 'percentage_units' not in public_stats
    assert public_stats['hide_counts'] is True
    assert public_stats['status'] == 'contagens_ocultas'
    assert public_stats['disclaimer'] == DISCLAIMER_CONSULTATIVE_AGREEMENT

    # 3. Consulta administrativa interna pelo síndico (is_public_viewer=False) continua recebendo os dados
    admin_stats = AgreementService.get_revision_agreement_stats(
        condominium_id=condo.id,
        published_suggestion_revision_id=pub_v1.id,
        is_public_viewer=False
    )
    assert admin_stats['concordant_individuals'] == 1


def test_ca_39_estatistica_explicita_individuo_unidade_corte_e_ressalva(phase6_setup):
    """
    CA-39 / V21-30 / V21-34 / UI-31 / S19:
    Estatística explicita texto, versão, segregação pessoa vs unidade, denominador e ressalva.
    V21-30: Várias unidades da mesma pessoa NÃO multiplicam apoio individual (1 pessoa = 1 apoio).
    """
    ctx = phase6_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    pub_v1 = ctx['pub_v1']
    part_carlos = ctx['part_carlos']
    part_beatriz = ctx['part_beatriz']

    # Carlos (proprietário das unidades 102 e 201) registra concordância
    AgreementService.register_agreement(condo.id, camp.id, part_carlos.id, pub_v1.id)

    # Beatriz (inquilina na unidade 102) também registra concordância
    AgreementService.register_agreement(condo.id, camp.id, part_beatriz.id, pub_v1.id)

    stats = AgreementService.get_revision_agreement_stats(condo.id, pub_v1.id, is_public_viewer=False)

    # Indivíduos únicos: Carlos e Beatriz = 2 pessoas
    assert stats['concordant_individuals'] == 2
    # Unidades únicas representadas: 102 = 1 unidade
    assert stats['concordant_units'] == 1

    # Denominadores explícitos presentes
    assert stats['eligible_individuals_denominator'] == 3  # Mariana, Carlos, Beatriz
    assert stats['eligible_units_denominator'] == 2        # Unidade 101 e 102

    # Aviso permanente obrigatório de caráter estritamente consultivo presente
    assert stats['disclaimer'] == DISCLAIMER_CONSULTATIVE_AGREEMENT

    # Gera fotografia estatística (snapshot de consulta)
    cut = AgreementService.create_consultation_snapshot(condo.id, camp.id, created_by_id=ctx['sindico'].id)
    assert cut.total_eligible_participants == 3
    assert cut.total_eligible_units == 2
    assert cut.disclaimer == DISCLAIMER_CONSULTATIVE_AGREEMENT
    assert str(pub_v1.suggestion_id) in cut.stats_payload


def test_ca_40_incorporacao_liga_revisao_e_contribuicao_atomicamente(phase6_setup):
    """
    CA-40 / V21-37 / S17 / S18: Incorporação liga revisão e contribuição atomicamente.
    A consolidação da sugestão acolhida cria nova revisão da minuta e transiciona
    a sugestão para 'incorporada' em transação atômica.
    """
    ctx = phase6_setup
    condo = ctx['condo']
    sindico = ctx['sindico']
    sug = ctx['suggestion']
    p1 = ctx['provision_1']

    # 1. Sugestão acolhida é incorporada à minuta pelo síndico
    inc = IncorporationService.incorporate_suggestion(
        condominium_id=condo.id,
        suggestion_id=sug.id,
        target_provision_id=p1.id,
        incorporated_by_id=sindico.id,
        new_text="O uso da academia é permitido a moradores e convidados conforme regulamento de horários.",
        description=f"Acolhimento da sugestão {sug.public_protocol} dos moradores."
    )

    # Validações atômicas
    assert inc.suggestion_id == sug.id
    assert inc.provision_revision is not None
    assert inc.provision_revision.text == "O uso da academia é permitido a moradores e convidados conforme regulamento de horários."
    assert inc.provision_revision.change_type == 'alterado'

    # A sugestão transicionou para 'incorporada'
    sug.refresh_from_db()
    assert sug.incorporation_status == 'incorporada'

    # 2. Sugestão NÃO acolhida é recusada com erro transacional
    sug_rejeitada = SuggestionService.create_suggestion(
        condominium_id=condo.id,
        campaign_id=ctx['campaign'].id,
        participant_id=ctx['part_carlos'].id,
        text="Proposta que será rejeitada.",
        justification="Sem amparo legal."
    )
    ModerationService.register_editorial_decision(
        sug_rejeitada.id, condo.id, sindico.id, "rejeitada", "Incompatível com a convenção."
    )

    with pytest.raises(IncorporationIntegrityError):
        IncorporationService.incorporate_suggestion(
            condominium_id=condo.id,
            suggestion_id=sug_rejeitada.id,
            target_provision_id=p1.id,
            incorporated_by_id=sindico.id,
            new_text="Texto indevido."
        )

    sug_rejeitada.refresh_from_db()
    assert sug_rejeitada.incorporation_status == 'nao_incorporada'


def test_ca_45_proibicao_terminante_de_recursos_e_termos_eleitorais():
    """
    CA-45: Proibição terminante de termos como 'voto', 'eleição', 'quórum de assembleia' ou 'apuração'.
    """
    with pytest.raises(ElectoralVocabularyForbiddenError):
        assert_no_electoral_terms("Esta proposta obteve 10 votos a favor.")

    with pytest.raises(ElectoralVocabularyForbiddenError):
        assert_no_electoral_terms("Apuração de votos do quórum de assembleia.")

    with pytest.raises(ElectoralVocabularyForbiddenError):
        assert_no_electoral_terms("Eleição do novo síndico com peso por fração ideal.")

    # Termo seguro não dispara exceção
    assert_no_electoral_terms("Manifestação consultiva sobre esta redação normativa.")


def test_autor_nao_concorda_com_propria_sugestao(phase6_setup):
    """
    PRD 257: Autor não pode acrescentar concordância à própria contribuição.
    """
    ctx = phase6_setup
    condo = ctx['condo']
    camp = ctx['campaign']
    part_mariana = ctx['part_mariana']  # Mariana é a autora de pub_v1!
    pub_v1 = ctx['pub_v1']

    with pytest.raises(AuthorCannotAgreeWithOwnSuggestionError):
        AgreementService.register_agreement(
            condominium_id=condo.id,
            campaign_id=camp.id,
            participant_id=part_mariana.id,
            published_suggestion_revision_id=pub_v1.id
        )


def test_isolamento_tenant_fase6(phase6_setup):
    """Isolamento estrito multi-tenancy: acordos de um condomínio não afetam outro."""
    ctx = phase6_setup
    condo1 = ctx['condo']
    camp1 = ctx['campaign']
    part1 = ctx['part_carlos']
    pub_v1 = ctx['pub_v1']

    condo2 = Condominium.objects.create(name="Condomínio Outro")

    # Registra no condomínio 1
    AgreementService.register_agreement(condo1.id, camp1.id, part1.id, pub_v1.id)

    # Consulta no condomínio 2 não encontra nenhum acordo
    assert ConsultativeAgreement.objects.filter(condominium=condo2).count() == 0


def test_fluxo_completo_api_concordancias_e_incorporacao(phase6_setup):
    """
    Testa o fluxo REST completo da Fase 6 via APIClient:
    - Morador concorda -> Retira -> Reafirma
    - Consulta estatísticas públicas com aviso legal
    - Incorporação atômica da sugestão na minuta de trabalho
    """
    client = APIClient()
    ctx = phase6_setup
    condo = ctx['condo']
    part_carlos = ctx['part_carlos']
    pub_v1 = ctx['pub_v1']
    sug = ctx['suggestion']
    p1 = ctx['provision_1']

    # 1. Morador registra concordância via POST
    resp_agree = client.post(
        f"/api/v1/condominiums/{condo.id}/suggestions/{sug.id}/agreements",
        data={
            "participant_id": str(part_carlos.id),
            "published_suggestion_revision_id": str(pub_v1.id),
            "reason": "Concordo com a proposta."
        },
        format="json"
    )
    assert resp_agree.status_code == 200
    assert resp_agree.data['active'] is True

    # 2. Consulta estatísticas da sugestão via GET
    resp_stats = client.get(
        f"/api/v1/condominiums/{condo.id}/suggestions/{sug.id}/stats?viewer=public"
    )
    assert resp_stats.status_code == 200
    assert resp_stats.data['concordant_individuals'] == 1
    assert "Manifestação consultiva" in resp_stats.data['disclaimer']

    # 3. Morador consulta suas próprias concordâncias ativas (M11)
    resp_my = client.get(
        f"/api/v1/condominiums/{condo.id}/my-agreements?participant_id={part_carlos.id}"
    )
    assert resp_my.status_code == 200
    assert len(resp_my.data) == 1
    assert resp_my.data[0]['active'] is True

    # 4. Morador retira sua concordância via DELETE
    resp_withdraw = client.delete(
        f"/api/v1/condominiums/{condo.id}/suggestions/{sug.id}/agreements",
        data={
            "participant_id": str(part_carlos.id),
            "published_suggestion_revision_id": str(pub_v1.id)
        },
        format="json"
    )
    assert resp_withdraw.status_code == 200
    assert resp_withdraw.data['active'] is False

    # 5. Incorporação atômica da sugestão na minuta normativa (CA-40)
    resp_inc = client.post(
        f"/api/v1/condominiums/{condo.id}/suggestions/{sug.id}/incorporate",
        data={
            "target_provision_id": str(p1.id),
            "new_text": "Texto incorporado via API REST.",
            "description": "Incorporação final aprovada."
        },
        format="json"
    )
    assert resp_inc.status_code == 201
    assert str(resp_inc.data['suggestion_id']) == str(sug.id)
    assert resp_inc.data['public_protocol'] == sug.public_protocol

    # 6. Gera fotografia estatística da campanha
    resp_snap = client.post(
        f"/api/v1/condominiums/{condo.id}/campaigns/{ctx['campaign'].id}/snapshots"
    )
    assert resp_snap.status_code == 201, f"Erro: {resp_snap.data}"
    assert str(resp_snap.data['campaign_id']) == str(ctx['campaign'].id)
    assert "Manifestação consultiva" in resp_snap.data['disclaimer']
