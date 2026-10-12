"""
Suíte de Teste de Integração End-to-End: Ciclo de Vida Completo do Regimento Interno Condominial Brasileiro — CONDOC

Simula o ciclo de vida normativo integral de um Regimento Interno brasileiro real:
1. Modelagem normativa robusta:
   - Título I: Do Condomínio e sua Destinação Residencial
   - Capítulo I: Dos Direitos e Deveres Gerais dos Condôminos (Art. 1º a 3º)
   - Capítulo II: Do Sossego e Horário de Silêncio das 22h às 08h (Art. 4º e 5º)
   - Capítulo III: Da Convivência e Trânsito de Animais de Estimação - Pets (Art. 6º e 7º)
   - Capítulo IV: Do Uso das Áreas Comuns - Salão de Festas, Piscina e Churrasqueira (Art. 8º a 11)
   - Capítulo V: Das Penalidades, Advertências e Recursos Administrativos (Art. 12 a 15)

2. Execução das 15 etapas do ciclo de vida:
   - Etapa 1: Criação de Condomínio, Bloco e Unidades com Onboarding e Verificação de Membresias (CA-12, CA-15).
   - Etapa 2: Criação de Projeto Normativo e Documento de Regimento Interno.
   - Etapa 3: Upload do documento original de 1995 e transcrição OCR com conferência humana (CA-17, CA-18).
   - Etapa 4: População da árvore estruturada (15 artigos) e notas internas confidenciais (CA-24).
   - Etapa 5: Teste de controle de concorrência otimista (ETag) em edição normativa (CA-23).
   - Etapa 6: Congelamento do Snapshot Inicial (v1.0-consulta) com cálculo SHA-256 e imutabilidade (CA-41).
   - Etapa 7: Abertura de Campanha de Consulta Pública vinculada ao Snapshot inicial.
   - Etapa 8: Envio de sugestão privada sobre Art. 7º (Pets) gerando protocolo público SUG-2026-XXXXXX (CA-25).
   - Etapa 9: Envio de complemento privado e verificação de regras de submissão (CA-30).
   - Etapa 10: Moderação 4D Completa:
     - Dim 1: Análise Técnica sem exposição de dados pessoais do morador (CA-26).
     - Dim 2: Decisão Editorial 'acolhida' com justificativa compartilhável (CA-27).
     - Dim 3: Mesa de Publicação do Síndico: bloqueio de não-síndico (CA-28) e publicação sanitizada no mural (CA-29).
     - Dim 4: Incorporação atômica da sugestão acolhida gerando nova revisão da minuta (CA-40).
   - Etapa 11: Apoio consultivo (concordância) por morador vizinho (CA-35, CA-36) e blindagem anti-eleitoral (CA-45).
   - Etapa 12: Mapeamento de origens e relatório DePara (mantido, alterado, novo, excluído) (CA-19, CA-20, CA-21).
   - Etapa 13: Renumeração estruturada preservando UUIDs estáveis (CA-22).
   - Etapa 14: Congelamento do Snapshot Final Homologado (v2.0-homologado).
   - Etapa 15: Exportação de pacote oficial limpo (CA-42), manifesto criptográfico SHA-256 e detecção de adulteração.
"""
import uuid
import time
import json
import pytest
from django.utils import timezone

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
    SourceFile,
    SourceTranscription,
    SourceProvision,
    Provision,
    ProvisionRevision,
    InternalNote,
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
    OriginMapping,
    ExportArtifact,
)

from domain.documents.exceptions import (
    ConcurrencyConflictError,
    SnapshotImmutableError,
    PrivateNoteAccessForbiddenError,
)
from domain.documents.invariants import (
    assert_snapshot_immutable,
)
from domain.moderation.exceptions import (
    UnauthorizedPublicationError,
    ComplementWithoutParentError,
)
from domain.agreements.exceptions import (
    AuthorCannotAgreeWithOwnSuggestionError,
    ElectoralVocabularyForbiddenError,
)
from domain.agreements.invariants import (
    assert_no_electoral_terms,
    DISCLAIMER_CONSULTATIVE_AGREEMENT,
)
from domain.comparison.exceptions import (
    FictitiousOriginError,
)
from domain.preservation.exceptions import (
    ManifestIntegrityError,
)
from domain.preservation.invariants import (
    DISCLAIMER_FINAL_PUBLICATION,
    calculate_content_sha256,
)

from application.identity.services import (
    CondominiumService,
    MembershipVerificationService,
    RoleService,
)
from application.documents.services import (
    ProjectService,
    DocumentService,
    SourceFileService,
    TranscriptionService,
    ProvisionService,
    InternalNoteService,
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
from application.comparison.services import (
    OriginMappingService,
    ComparisonService,
    RenumberingService,
    ExportService,
)
from application.preservation.services import PreservationService


# ==============================================================================
# TEXTO NORMATIVO REAL DO REGIMENTO INTERNO BRASILEIRO (15 ARTIGOS)
# ==============================================================================
REGIMENTO_TEXTS = {
    # Título I & Capítulo I: Direitos e Deveres Gerais
    1: {
        "label": "Art. 1º",
        "text": "O Condomínio Residencial Parque Real destina-se exclusivamente para fins residenciais familiares, sendo terminantemente vedada a exploração comercial, industrial ou profissional com atendimento presencial que desvirtue sua finalidade.",
        "theme": "Destinação Residencial",
    },
    2: {
        "label": "Art. 2º",
        "text": "São direitos dos condôminos e moradores usar, gozar e dispor livremente de suas unidades autônomas, bem como utilizar as áreas comuns de acordo com a sua destinação, desde que respeitadas as normas de segurança, sossego, saúde e boa convivência comunitária.",
        "theme": "Direitos Gerais",
    },
    3: {
        "label": "Art. 3º",
        "text": "São deveres dos condôminos e posseiros: contribuir pontualmente com as despesas ordinárias e extraordinárias; manter inalterada a fachada arquitetônica e a cor das esquadrias; e cumprir rigorosamente as normas da Convenção Condominial e deste Regimento.",
        "theme": "Deveres Gerais",
    },
    # Capítulo II: Sossego e Horário de Silêncio
    4: {
        "label": "Art. 4º",
        "text": "Fica instituído o horário de silêncio no condomínio das 22h00 às 08h00 nos dias úteis, e até às 09h00 aos sábados, domingos e feriados, período no qual é expressamente proibido produzir ruídos, algazarras, música alta ou festas que perturbem o repouso dos vizinhos.",
        "theme": "Horário de Silêncio",
    },
    5: {
        "label": "Art. 5º",
        "text": "Obras, reparos, montagem de móveis e quaisquer reformas ruidosas nas unidades privativas somente são permitidas de segunda a sexta-feira, das 08h00 às 17h00, e aos sábados, das 09h00 às 13h00, sendo estritamente vedadas aos domingos e feriados.",
        "theme": "Obras e Reformas",
    },
    # Capítulo III: Animais de Estimação (Pets)
    6: {
        "label": "Art. 6º",
        "text": "É plenamente assegurado aos moradores o direito de manter animais de estimação (pets) de qualquer porte no interior de suas unidades, desde que não representem ameaça à integridade física, saúde ou sossego dos demais habitantes do condomínio.",
        "theme": "Animais de Estimação - Direito Privativo",
    },
    7: {
        "label": "Art. 7º",
        "text": "O trânsito de animais pelas áreas comuns do condomínio deve ser realizado com coleira e guia curta, sendo obrigatória a limpeza imediata de eventuais dejetos pelo tutor responsável.",
        "theme": "Animais de Estimação - Trânsito e Convivência",
    },
    # Capítulo IV: Áreas Comuns
    8: {
        "label": "Art. 8º",
        "text": "A utilização do Salão de Festas depende de reserva prévia formalizada junto à administração condominial e do recolhimento da respectiva taxa de limpeza e conservação, observando-se a capacidade máxima de 60 pessoas e o horário de encerramento às 02h00.",
        "theme": "Salão de Festas",
    },
    9: {
        "label": "Art. 9º",
        "text": "A área da Piscina é de uso exclusivo dos condôminos e moradores residentes, funcionando de terça a domingo das 07h00 às 22h00, sendo terminantemente proibido o consumo ou porte de garrafas, copos ou recipientes de vidro em todo o seu perímetro.",
        "theme": "Piscina",
    },
    10: {
        "label": "Art. 10",
        "text": "A Churrasqueira comunitária poderá ser reservada para eventos de moradores, cabendo ao requisitante zelar pelo asseio, conservação das grelhas e equipamentos elétricos, e destinação adequada do carvão e resíduos ao término do uso.",
        "theme": "Churrasqueira",
    },
    11: {
        "label": "Art. 11",
        "text": "É expressamente vedada a cessão ou locação de quaisquer áreas comuns do condomínio a terceiros não residentes para eventos com cobrança de ingressos, manifestações político-partidárias ou cultos religiosos públicos.",
        "theme": "Vedação Comercial de Áreas Comuns",
    },
    # Capítulo V: Penalidades, Advertências e Recursos
    12: {
        "label": "Art. 12",
        "text": "A inobservância de qualquer obrigação prevista neste Regimento Interno ensejará notificação e advertência formal por escrito expedida pelo Síndico ou administradora ao condômino infrator.",
        "theme": "Advertência Formal",
    },
    13: {
        "label": "Art. 13",
        "text": "A reincidência na mesma infração no período de 12 (doze) meses acarretará aplicação de multa punitiva no valor de 1 (uma) cota condominial ordinária vigente, dobrando-se o valor nas reincidências subsequentes até o teto legal de 5 (cinco) cotas.",
        "theme": "Multa e Reincidência",
    },
    14: {
        "label": "Art. 14",
        "text": "Das penalidades de multa aplicadas caberá recurso administrativo sem efeito suspensivo ao Conselho Consultivo, no prazo improrrogável de 10 (dez) dias corridos a contar da confirmação do recebimento da notificação de infração.",
        "theme": "Recursos Administrativos",
    },
    15: {
        "label": "Art. 15",
        "text": "Os casos omissos ou situações não contempladas neste Regimento Interno serão resolvidos pelo Síndico em conjunto com o Conselho Consultivo, ad referendum da Assembleia Geral dos Condôminos e nos termos da Lei Federal 10.406/2002 (Código Civil).",
        "theme": "Disposições Finais e Casos Omissos",
    },
}


@pytest.mark.django_db
class TestFullRegimentoInternoLifecycle:
    """Suíte exaustiva de integração testando o ciclo de vida completo do Regimento Interno."""

    def test_complete_regimento_interno_lifecycle(self):
        start_time = time.time()

        # ======================================================================
        # ETAPA 1: CRIAÇÃO DO CONDOMÍNIO, BLOCO, UNIDADES E MEMBRESIAS (CA-12, CA-15)
        # ======================================================================
        print("\n--- ETAPA 1: Estrutura Física, Contas e Membresias ---")
        condo = CondominiumService.create_condominium(
            name="Condomínio Residencial Parque Real 2026",
            cnpj="12.345.678/0001-90"
        )
        assert condo.id is not None
        assert condo.cnpj == "12.345.678/0001-90"

        building = CondominiumService.create_building(
            condominium_id=condo.id,
            code="TORRE_DIAMANTE",
            name="Torre Diamante"
        )
        assert building.condominium_id == condo.id

        unit101 = CondominiumService.create_unit(
            condominium_id=condo.id,
            building_id=building.id,
            code="101",
            ideal_fraction=0.025
        )
        unit102 = CondominiumService.create_unit(
            condominium_id=condo.id,
            building_id=building.id,
            code="102",
            ideal_fraction=0.025
        )
        unit201 = CondominiumService.create_unit(
            condominium_id=condo.id,
            building_id=building.id,
            code="201",
            ideal_fraction=0.025
        )
        unit202 = CondominiumService.create_unit(
            condominium_id=condo.id,
            building_id=building.id,
            code="202",
            ideal_fraction=0.025
        )
        assert Unit.objects.filter(condominium=condo).count() == 4

        # Criação de Contas do Sistema
        sindico_acc = Account.objects.create(
            auth_user_id=uuid.uuid4(),
            email="sindico.parquereal@condoc.com.br",
            full_name="Dr. Fernando Silveira (Síndico Gestor)"
        )
        RoleService.assign_role(
            condominium_id=condo.id,
            account_id=sindico_acc.id,
            role="sindico"
        )

        comissao_acc = Account.objects.create(
            auth_user_id=uuid.uuid4(),
            email="relator.comissao@condoc.com.br",
            full_name="Mariana Alencar (Relatora da Comissão)"
        )
        RoleService.assign_role(
            condominium_id=condo.id,
            account_id=comissao_acc.id,
            role="comissao"
        )

        # Morador 1 (Dra. Helena - Tutora de Pet, Unidade 101)
        helena_acc = Account.objects.create(
            auth_user_id=uuid.uuid4(),
            email="helena.unit101@condoc.com.br",
            full_name="Dra. Helena Martins"
        )
        res_helena = Resident.objects.create(
            condominium=condo,
            account=helena_acc,
            full_name="Dra. Helena Martins",
            phone_e164="+5511999887766"
        )
        mb_helena = UnitMembership.objects.create(
            condominium=condo,
            resident=res_helena,
            unit=unit101,
            category="proprietario_residente",
            verification_status="pendente",
            membership_status="pending"
        )
        # Validação formal de membresia (CA-12, CA-15)
        MembershipVerificationService.verify_membership(
            condominium_id=condo.id,
            membership_id=mb_helena.id,
            new_status="validado",
            method="documento",
            reason="Certidão de matrícula do imóvel no 4º RGI conferida integralmente.",
            actor_account_id=sindico_acc.id
        )
        mb_helena.refresh_from_db()
        assert mb_helena.verification_status == "validado"
        assert mb_helena.membership_status == "active"

        # Morador 2 (Roberto - Unidade 202)
        roberto_acc = Account.objects.create(
            auth_user_id=uuid.uuid4(),
            email="roberto.unit202@condoc.com.br",
            full_name="Roberto Mendes"
        )
        res_roberto = Resident.objects.create(
            condominium=condo,
            account=roberto_acc,
            full_name="Roberto Mendes",
            phone_e164="+5511988776655"
        )
        mb_roberto = UnitMembership.objects.create(
            condominium=condo,
            resident=res_roberto,
            unit=unit202,
            category="inquilino_residente",
            verification_status="pendente",
            membership_status="pending"
        )
        MembershipVerificationService.verify_membership(
            condominium_id=condo.id,
            membership_id=mb_roberto.id,
            new_status="validado",
            method="contrato_locacao",
            reason="Contrato de locação com firmas reconhecidas e autorização do proprietário.",
            actor_account_id=sindico_acc.id
        )
        mb_roberto.refresh_from_db()
        assert mb_roberto.verification_status == "validado"
        assert mb_roberto.membership_status == "active"

        # ======================================================================
        # ETAPA 2: PROJETO NORMATIVO E DOCUMENTO DO REGIMENTO INTERNO
        # ======================================================================
        print("\n--- ETAPA 2: Projeto e Documento Normativo ---")
        project = ProjectService.create_project(
            condominium_id=condo.id,
            name="Revisão Geral do Regimento Interno 2026",
            purpose="Modernização das regras de convivência, trânsito de animais e áreas comuns",
            coordinator_account_id=sindico_acc.id,
            kind="revisao"
        )
        assert project.id is not None
        assert project.coordinator_account_id == sindico_acc.id

        document = DocumentService.create_document(
            project_id=project.id,
            condominium_id=condo.id,
            title="Regimento Interno do Condomínio Parque Real",
            type="regimento_interno",
            numbering_policy="renumeracao_automatica"
        )
        assert document.id is not None
        assert document.editorial_status == "rascunho"

        # ======================================================================
        # ETAPA 3: UPLOAD DO ORIGINAL E TRANSCRIÇÃO OCR COM CONFERÊNCIA HUMANA (CA-17, CA-18)
        # ======================================================================
        print("\n--- ETAPA 3: Upload do Original e Transcrição OCR ---")
        raw_pdf_bytes = b"%PDF-1.4 [DOCUMENTO ORIGINAL REGIMENTO INTERNO 1995: REGRAS GERAIS E CONVIVENCIA]"
        source_file = SourceFileService.register_source_file(
            condominium_id=condo.id,
            uploaded_by_id=sindico_acc.id,
            filename="regimento_original_1995.pdf",
            mime_type="application/pdf",
            size_bytes=len(raw_pdf_bytes),
            file_content=raw_pdf_bytes
        )
        assert len(source_file.file_hash) == 64
        assert source_file.state == "ready"

        # Transcrição OCR inicial
        ocr_text_v1 = "Artigo 7 - E proibido transito de qualquer animal sem focinheira nas areas comuns."
        transcription_v1 = TranscriptionService.create_initial_transcription(
            document_id=document.id,
            condominium_id=condo.id,
            source_file_id=source_file.id,
            raw_text=ocr_text_v1
        )
        assert transcription_v1.version == 1
        assert transcription_v1.status == "under_review"

        # CA-17: Conferência humana realizada pelo síndico
        confirmed_t1 = TranscriptionService.confirm_transcription(
            transcription_id=transcription_v1.id,
            checked_by_id=sindico_acc.id,
            corrected_text="Artigo 7º É proibido o trânsito de qualquer animal sem focinheira nas áreas comuns."
        )
        assert confirmed_t1.status == "confirmed"
        assert confirmed_t1.checked_by_id == sindico_acc.id
        assert confirmed_t1.checked_at is not None

        # CA-18: Correção de OCR posterior gera nova versão (v2) apontando para a v1 (superseded)
        transcription_v2 = TranscriptionService.correct_transcription(
            transcription_id=confirmed_t1.id,
            checked_by_id=sindico_acc.id,
            corrected_text="Art. 7º - É proibido trânsito de qualquer animal sem coleira e focinheira nas áreas comuns."
        )
        assert transcription_v2.version == 2
        assert transcription_v2.status == "confirmed"
        assert transcription_v2.replaces_transcription_id == confirmed_t1.id
        confirmed_t1.refresh_from_db()
        assert confirmed_t1.status == "superseded"

        # ======================================================================
        # ETAPA 4: ESTRUTURAÇÃO DOS DISPOSITIVOS (15 ARTIGOS) E NOTAS INTERNAS (CA-24)
        # ======================================================================
        print("\n--- ETAPA 4: População da Árvore de Dispositivos e Notas Internas ---")
        # Estrutura de Título e Capítulos
        titulo1 = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="titulo",
            label="Título I",
            text="Do Condomínio e sua Destinação Residencial",
            position=1,
            author_account_id=sindico_acc.id
        )

        capitulos = {}
        cap_definitions = [
            (1, "Capítulo I", "Dos Direitos e Deveres Gerais dos Condôminos", 2),
            (2, "Capítulo II", "Do Sossego e Horário de Silêncio das 22h às 08h", 6),
            (3, "Capítulo III", "Da Convivência e Trânsito de Animais de Estimação - Pets", 9),
            (4, "Capítulo IV", "Do Uso das Áreas Comuns - Salão de Festas, Piscina e Churrasqueira", 12),
            (5, "Capítulo V", "Das Penalidades, Advertências e Recursos Administrativos", 17),
        ]
        for c_num, c_label, c_text, c_pos in cap_definitions:
            capitulos[c_num] = ProvisionService.create_provision(
                document_id=document.id,
                condominium_id=condo.id,
                kind="capitulo",
                label=c_label,
                text=c_text,
                parent_provision_id=titulo1.id,
                position=c_pos,
                author_account_id=sindico_acc.id
            )

        # Mapeamento de Artigos para seus Capítulos correspondentes
        art_to_cap = {
            1: 1, 2: 1, 3: 1,
            4: 2, 5: 2,
            6: 3, 7: 3,
            8: 4, 9: 4, 10: 4, 11: 4,
            12: 5, 13: 5, 14: 5, 15: 5,
        }

        created_provisions = {}
        for art_num, art_data in REGIMENTO_TEXTS.items():
            cap_id = capitulos[art_to_cap[art_num]].id
            # Posição sequencial
            pos = art_num + 20
            prov = ProvisionService.create_provision(
                document_id=document.id,
                condominium_id=condo.id,
                kind="artigo",
                label=art_data["label"],
                text=art_data["text"],
                parent_provision_id=cap_id,
                position=pos,
                theme=art_data["theme"],
                change_type="mantido",
                author_account_id=sindico_acc.id
            )
            created_provisions[art_num] = prov

        assert len(created_provisions) == 15
        assert Provision.objects.filter(document=document).count() == 1 + 5 + 15  # 21 nós no total

        # Inserção de Notas Internas Confidenciais (CA-24)
        art7_prov = created_provisions[7]
        InternalNoteService.create_note(
            condominium_id=condo.id,
            provision_id=art7_prov.id,
            author_account_id=comissao_acc.id,
            content="Atenção Jurídico: O STJ pacificou no Resp 1.783.076 que a proibição genérica de animais de estimação é nula. Devemos garantir livre trânsito responsável.",
            visibility="equipe",
            category="juridico"
        )
        InternalNoteService.create_note(
            condominium_id=condo.id,
            provision_id=created_provisions[4].id,
            author_account_id=sindico_acc.id,
            content="Nota operacional: Tivemos 14 reclamações de ruído no último trimestre sobre a torre B.",
            visibility="equipe",
            category="redacao"
        )

        # Verificação do isolamento de notas internas (CA-24)
        tree_clean = ProvisionService.get_document_tree(document.id, include_notes=False)
        assert len(tree_clean) == 21
        for item in tree_clean:
            assert "internal_notes" not in item
            assert "notes" not in item
            assert "legal_opinions" not in item

        with pytest.raises(PrivateNoteAccessForbiddenError):
            InternalNoteService.list_notes_for_provision(art7_prov.id, user_role="morador")

        # ======================================================================
        # ETAPA 5: CONTROLE DE CONCORRÊNCIA OTIMISTA (ETAG) (CA-23)
        # ======================================================================
        print("\n--- ETAPA 5: Concorrência Otimista (ETag) ---")
        art7_rev1 = ProvisionService.get_latest_revision(art7_prov.id)
        current_etag = art7_rev1.etag
        assert current_etag is not None

        # Tentativa com ETag desatualizado / adulterado deve falhar
        with pytest.raises(ConcurrencyConflictError):
            ProvisionService.update_provision(
                provision_id=art7_prov.id,
                expected_etag="etag-obsoleto-ou-invalido-12345",
                text="Tentativa concorrente de alteração sem lock.",
                author_account_id=comissao_acc.id
            )

        # Edição com ETag válido tem sucesso e gera revisão 2
        art7_rev2 = ProvisionService.update_provision(
            provision_id=art7_prov.id,
            expected_etag=current_etag,
            text=art7_rev1.text + " (Observada a exigência de vacinação anual atualizada).",
            label="Art. 7º",
            author_account_id=sindico_acc.id,
            change_type="alterado"
        )
        assert art7_rev2.revision_number == 2
        assert art7_rev2.etag != current_etag

        # ======================================================================
        # ETAPA 6: CONGELAMENTO DO SNAPSHOT INICIAL v1.0-consulta (CA-41)
        # ======================================================================
        print("\n--- ETAPA 6: Snapshot Inicial v1.0-consulta (SHA-256) ---")
        snapshot_v1 = SnapshotService.create_snapshot(
            document_id=document.id,
            condominium_id=condo.id,
            version_label="v1.0-consulta",
            frozen_by_id=sindico_acc.id,
            purpose="consulta_publica"
        )
        assert snapshot_v1.id is not None
        assert snapshot_v1.is_immutable is True
        assert len(snapshot_v1.content_hash) == 64
        assert SnapshotItem.objects.filter(snapshot=snapshot_v1).count() == 21

        # Invariante de imutabilidade estrita (CA-41)
        with pytest.raises(SnapshotImmutableError):
            assert_snapshot_immutable(is_immutable=snapshot_v1.is_immutable)

        # ======================================================================
        # ETAPA 7: CRIAÇÃO E ABERTURA DA CAMPANHA DE CONSULTA PÚBLICA
        # ======================================================================
        print("\n--- ETAPA 7: Campanha de Consulta Pública ---")
        campaign = CampaignService.create_campaign(
            condominium_id=condo.id,
            project_id=project.id,
            snapshot_id=snapshot_v1.id,
            name="Consulta Pública: Regimento Interno 2026",
            description="Participação de todos os moradores para revisão do Regimento e novas diretrizes de convivência.",
            settings={
                "allow_suggestions": True,
                "allow_complements": True,
                "allow_agreements": True,
                "hide_counts": False
            }
        )
        assert campaign.state == "rascunho"

        # Abertura formal da campanha
        campaign = CampaignService.open_campaign(
            campaign_id=campaign.id,
            condominium_id=condo.id
        )
        assert campaign.state == "aberta"
        assert campaign.start_date is not None

        # ======================================================================
        # ETAPA 8: ONBOARDING DO MORADOR E SUGESTÃO PRIVADA (CA-25)
        # ======================================================================
        print("\n--- ETAPA 8: Onboarding e Sugestão Privada com Protocolo SUG-2026-XXXXXX ---")
        part_helena = CampaignService.register_participant(
            condominium_id=condo.id,
            campaign_id=campaign.id,
            resident_id=res_helena.id,
            reference_membership_id=mb_helena.id,
            authorized_by_id=sindico_acc.id
        )
        assert part_helena.status == "habilitado"

        suggestion_text = (
            "Proponho liberar expressamente o uso de elevador social quando o animal estiver no colo ou com guia curta, "
            "e permitir a permanência temporária no gramado externo com guia, eliminando a exigência de focinheira "
            "para cães sociáveis de pequeno e médio porte."
        )
        suggestion_just = (
            "Decisões recentes do STJ garantem que o condomínio não pode impor constrangimentos injustificados aos tutores. "
            "A exigência de apenas elevador de serviço quando este estiver em manutenção isola os moradores idosos com animais."
        )

        sug_helena = SuggestionService.create_suggestion(
            condominium_id=condo.id,
            campaign_id=campaign.id,
            participant_id=part_helena.id,
            target_provision_id=art7_prov.id,
            text=suggestion_text,
            justification=suggestion_just,
            category="redacao",
            author_account_id=helena_acc.id
        )

        assert sug_helena.public_protocol.startswith("SUG-2026-")
        assert sug_helena.publication_status == "nao_publicada"
        assert sug_helena.analysis_status == "pendente"
        assert sug_helena.editorial_decision == "pendente"
        assert sug_helena.incorporation_status == "nao_incorporada"
        assert sug_helena.target_snapshot_revision is not None
        print(f"  -> Sugestão submetida com protocolo: {sug_helena.public_protocol}")

        # ======================================================================
        # ETAPA 9: TESTE DE COMPLEMENTO PRIVADO (CA-30)
        # ======================================================================
        print("\n--- ETAPA 9: Complemento Privado e Validação de Publicação Prévia ---")
        # Tentativa de complemento antes da publicação do pai é barrada
        with pytest.raises(ComplementWithoutParentError):
            SuggestionService.create_complement_suggestion(
                condominium_id=condo.id,
                parent_published_suggestion_id=sug_helena.id,
                participant_id=part_helena.id,
                text="Complemento preliminar antecipado.",
                justification="Teste de rejeição."
            )

        # ======================================================================
        # ETAPA 10: MODERAÇÃO 4D COMPLETA (CA-26, CA-27, CA-28, CA-29, CA-40)
        # ======================================================================
        print("\n--- ETAPA 10: Moderação 4D Completa ---")
        # Dimensão 1: Análise Técnica sem exposição de identidade do morador (CA-26, CA-27)
        queue = ModerationService.list_moderation_queue(
            condominium_id=condo.id,
            campaign_id=campaign.id
        )
        assert len(queue) >= 1
        item_queue = next(q for q in queue if q["id"] == str(sug_helena.id))
        assert "resident_name" not in item_queue
        assert "email" not in item_queue
        assert item_queue["public_protocol"] == sug_helena.public_protocol

        ModerationService.perform_technical_analysis(
            suggestion_id=sug_helena.id,
            condominium_id=condo.id,
            analyst_account_id=comissao_acc.id,
            new_status="analisada"
        )
        sug_helena.refresh_from_db()
        assert sug_helena.analysis_status == "analisada"
        assert sug_helena.publication_status == "nao_publicada"  # Não publica automaticamente!

        # Dimensão 2: Decisão Editorial 'acolhida' (CA-27)
        ModerationService.register_editorial_decision(
            suggestion_id=sug_helena.id,
            condominium_id=condo.id,
            decider_account_id=comissao_acc.id,
            decision="acolhida",
            public_shared_reason="Acolhida integralmente em consonância com a jurisprudência consolidada do Superior Tribunal de Justiça (STJ).",
            internal_note="Parecer jurídico favorável da comissão."
        )
        sug_helena.refresh_from_db()
        assert sug_helena.editorial_decision == "acolhida"
        assert sug_helena.publication_status == "nao_publicada"  # Permanece não publicada!

        # Dimensão 3: Mesa de Publicação do Síndico (CA-28, CA-29)
        # 1. Tentativa de publicação por não-síndico (Membro da comissão) deve falhar
        with pytest.raises(UnauthorizedPublicationError):
            ModerationService.authorize_publication(
                suggestion_id=sug_helena.id,
                condominium_id=condo.id,
                actor_role="comissao",
                authorizer_account_id=comissao_acc.id
            )

        # 2. Síndico sanitiza e autoriza publicação no mural público
        sanitized_text = (
            "Autorização expressa de trânsito de animais nos elevadores com guia curta, e uso de elevador social "
            "quando o de serviço estiver indisponível ou quando o animal estiver no colo."
        )
        sanitized_just = (
            "Adequação ao entendimento consolidado do STJ e promoção da convivência harmônica entre os moradores."
        )

        pub_rev = ModerationService.authorize_publication(
            suggestion_id=sug_helena.id,
            condominium_id=condo.id,
            actor_role="sindico",
            authorizer_account_id=sindico_acc.id,
            sanitized_text=sanitized_text,
            sanitized_justification=sanitized_just
        )
        sug_helena.refresh_from_db()
        assert sug_helena.publication_status == "publicada"
        assert pub_rev.is_active_publication is True
        assert pub_rev.authorized_by_id == sindico_acc.id

        # Agora que o pai está publicado, testa submissão de complemento com sucesso (CA-30)
        complement_sug = SuggestionService.create_complement_suggestion(
            condominium_id=condo.id,
            parent_published_suggestion_id=sug_helena.id,
            participant_id=part_helena.id,
            text="Complemento adicional: Instalar dispenser de saquinhos plásticos biodegradáveis na saída dos blocos.",
            justification="Incentivar a limpeza e descarte correto.",
            author_account_id=helena_acc.id
        )
        assert complement_sug.parent_published_suggestion_id == sug_helena.id
        assert complement_sug.publication_status == "nao_publicada"
        assert complement_sug.analysis_status == "pendente"

        # Dimensão 4: Incorporação Atômica na Minuta Normativa (CA-40)
        new_art7_normative_text = (
            "O trânsito de animais domésticos pelas áreas comuns e elevadores é livre com o uso de coleira e guia curta, "
            "sendo permitido o uso de qualquer elevador quando o animal estiver no colo do tutor, e do elevador social "
            "em caso de inoperância do elevador de serviço, mantida a obrigação de recolhimento imediato de dejetos."
        )
        inc_record = IncorporationService.incorporate_suggestion(
            condominium_id=condo.id,
            suggestion_id=sug_helena.id,
            target_provision_id=art7_prov.id,
            incorporated_by_id=sindico_acc.id,
            new_text=new_art7_normative_text,
            description="Incorporação da sugestão SUG-2026 sobre animais e elevadores."
        )
        assert inc_record.id is not None
        assert inc_record.provision_revision.revision_number == 3
        sug_helena.refresh_from_db()
        assert sug_helena.incorporation_status == "incorporada"

        # ======================================================================
        # ETAPA 11: CONCORDÂNCIA CONSULTIVA E SALVAGUARDAS ANTI-ELEITORAIS (CA-35, CA-36, CA-45)
        # ======================================================================
        print("\n--- ETAPA 11: Concordância Consultiva e Salvaguarda Anti-Eleitoral ---")
        part_roberto = CampaignService.register_participant(
            condominium_id=condo.id,
            campaign_id=campaign.id,
            resident_id=res_roberto.id,
            reference_membership_id=mb_roberto.id,
            authorized_by_id=sindico_acc.id
        )

        # 1. Autor não pode concordar com a própria sugestão (PRD 257)
        with pytest.raises(AuthorCannotAgreeWithOwnSuggestionError):
            AgreementService.register_agreement(
                condominium_id=condo.id,
                campaign_id=campaign.id,
                participant_id=part_helena.id,
                published_suggestion_revision_id=pub_rev.id
            )

        # 2. Morador Roberto acessa o mural e manifesta concordância consultiva (CA-35)
        agr1 = AgreementService.register_agreement(
            condominium_id=condo.id,
            campaign_id=campaign.id,
            participant_id=part_roberto.id,
            published_suggestion_revision_id=pub_rev.id,
            reason="Concordo plenamente. Medida razoável e civilizada."
        )
        assert agr1.active is True
        assert AgreementEvent.objects.filter(agreement=agr1, action="agree").count() == 1

        # Idempotência: cliques múltiplos produzem exatamente 1 registro ativo (CA-35)
        agr_repeat = AgreementService.register_agreement(
            condominium_id=condo.id,
            campaign_id=campaign.id,
            participant_id=part_roberto.id,
            published_suggestion_revision_id=pub_rev.id
        )
        assert agr_repeat.id == agr1.id
        assert ConsultativeAgreement.objects.filter(
            participant=part_roberto,
            published_suggestion_revision=pub_rev
        ).count() == 1

        # 3. Retirada de concordância e histórico de eventos (CA-36)
        withdrawn = AgreementService.withdraw_agreement(
            condominium_id=condo.id,
            campaign_id=campaign.id,
            participant_id=part_roberto.id,
            published_suggestion_revision_id=pub_rev.id,
            reason="Retirada para reflexão."
        )
        assert withdrawn.active is False
        assert AgreementEvent.objects.filter(agreement=agr1, action="withdraw").count() == 1

        # Reafirmação da concordância
        reaffirmed = AgreementService.register_agreement(
            condominium_id=condo.id,
            campaign_id=campaign.id,
            participant_id=part_roberto.id,
            published_suggestion_revision_id=pub_rev.id,
            reason="Reafirmação após leitura do novo texto."
        )
        assert reaffirmed.active is True
        assert AgreementEvent.objects.filter(agreement=agr1, action="reaffirm").count() == 1

        # 4. Salvaguardas anti-eleitorais e ausência de quórum (CA-45)
        for forbidden in ["voto a favor", "quórum de 2/3 atingido", "eleição de síndico", "votação em urna"]:
            with pytest.raises(ElectoralVocabularyForbiddenError):
                assert_no_electoral_terms(forbidden)

        stats = AgreementService.get_revision_agreement_stats(
            condominium_id=condo.id,
            published_suggestion_revision_id=pub_rev.id,
            is_public_viewer=True
        )
        assert stats["concordant_individuals"] == 1
        assert stats["concordant_units"] == 1
        assert stats["is_consultative_only"] is True
        for k in stats.keys():
            assert "voto" not in k
            assert "quorum" not in k
            assert "eleicao" not in k

        # ======================================================================
        # ETAPA 12: RELATÓRIO DEPARA E MAPEAMENTO DE ORIGENS (CA-19, CA-20, CA-21)
        # ======================================================================
        print("\n--- ETAPA 12: Mapeamento de Origens e Relatório DePara ---")
        # Cria dispositivos de origem (1995) para simular correspondência formal
        source_prov_antigo = SourceProvision.objects.create(
            condominium=condo,
            transcription=transcription_v2,
            kind="artigo",
            label="Art. 7º Antigo",
            text="Proibição de animais de qualquer espécie sem autorização do síndico.",
            display_order=7
        )

        # Mapeamento do Artigo 7º alterado -> origem antiga
        art7_latest_rev = ProvisionService.get_latest_revision(art7_prov.id)
        OriginMappingService.create_mapping(
            condominium_id=condo.id,
            revision_id=art7_latest_rev.id,
            source_provision_id=source_prov_antigo.id,
            relation_type="alterado",
            reason="Atualização com base na consulta pública e sugestão SUG-2026 sobre convivência de pets."
        )

        # Criação de um dispositivo novo (Bicicletário) classificado como 'incluido'
        bicicletario_prov = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="artigo",
            label="Art. 16",
            text="O bicicletário coletivo destina-se exclusivamente à guarda de bicicletas ativas dos moradores.",
            position=30,
            theme="Bicicletário",
            change_type="incluido",
            author_account_id=sindico_acc.id
        )
        bici_rev = ProvisionService.get_latest_revision(bicicletario_prov.id)

        # CA-19: Dispositivo novo incluído NÃO pode receber origem fictícia
        with pytest.raises(FictitiousOriginError):
            OriginMappingService.create_mapping(
                condominium_id=condo.id,
                revision_id=bici_rev.id,
                source_provision_id=source_prov_antigo.id,
                relation_type="mantido"
            )

        # Criação de dispositivo a ser excluído para testar CA-20
        art_obsoleto = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="artigo",
            label="Art. 99",
            text="É obrigatório o uso de trajes formais nas reuniões do hall social.",
            position=50,
            theme="Regra Anacrônica",
            change_type="excluido",
            author_account_id=sindico_acc.id
        )

        # Geração do Relatório DePara consolidado
        depara_report = ComparisonService.generate_depara_report(
            condominium_id=condo.id,
            document_id=document.id
        )
        entries = depara_report["entries"]
        assert len(entries) >= 15

        entry_types = {e["entry_type"] for e in entries}
        assert "alterado" in entry_types
        assert "incluido" in entry_types
        assert "excluido" in entry_types

        # CA-20: Dispositivo excluído consta no DePara com histórico
        excl_entry = next(e for e in entries if e["entry_type"] == "excluido")
        assert excl_entry["draft_label"] == "Art. 99"

        # ======================================================================
        # ETAPA 13: RENUMERAÇÃO ESTRUTURADA PRESERVANDO UUIDs (CA-22)
        # ======================================================================
        print("\n--- ETAPA 13: Renumeração Preservando UUIDs Permanentes ---")
        preview = RenumberingService.preview_renumbering(
            condominium_id=condo.id,
            document_id=document.id
        )
        assert preview["total_articles_renumbered"] >= 15
        for item in preview["preview_items"]:
            assert item["uuid_preserved"] is True

        applied = RenumberingService.apply_renumbering(
            condominium_id=condo.id,
            document_id=document.id,
            author_account_id=sindico_acc.id
        )
        assert applied["provisions_renumbered"] >= 1
        assert applied["status"] == "completed"

        # Verifica se os UUIDs originais foram estritamente preservados
        for art_num, prov_obj in created_provisions.items():
            assert Provision.objects.filter(id=prov_obj.id).exists()

        # ======================================================================
        # ETAPA 14: CONGELAMENTO DO SNAPSHOT FINAL HOMOLOGADO v2.0-homologado
        # ======================================================================
        print("\n--- ETAPA 14: Congelamento do Snapshot Final v2.0-homologado ---")
        snapshot_v2 = SnapshotService.create_snapshot(
            document_id=document.id,
            condominium_id=condo.id,
            version_label="v2.0-homologado",
            frozen_by_id=sindico_acc.id,
            purpose="homologacao_final"
        )
        assert snapshot_v2.id is not None
        assert snapshot_v2.is_immutable is True
        assert len(snapshot_v2.content_hash) == 64
        assert snapshot_v2.content_hash != snapshot_v1.content_hash

        # ======================================================================
        # ETAPA 15: PACOTE OFICIAL LIMPO, MANIFESTO SHA-256 E AUDITORIA (CA-42)
        # ======================================================================
        print("\n--- ETAPA 15: Exportação do Pacote Oficial e Manifesto SHA-256 ---")
        package = PreservationService.generate_final_public_package(
            condominium_id=condo.id,
            document_id=document.id,
            generated_by_id=sindico_acc.id
        )

        assert package["manifest_hash"] is not None
        assert len(package["manifest_hash"]) == 64
        assert package["disclaimer"] == DISCLAIMER_FINAL_PUBLICATION

        # Persistência dos arquivos exportados em exports/ para consulta e entrega
        import os
        export_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "exports"))
        os.makedirs(export_dir, exist_ok=True)
        with open(os.path.join(export_dir, "minuta_limpa_final.txt"), "w", encoding="utf-8") as f:
            f.write(package["files_content"]["minuta_limpa_final.txt"])
        with open(os.path.join(export_dir, "minuta_limpa_final.json"), "w", encoding="utf-8") as f:
            json.dump(package["files_content"]["minuta_limpa_final.json"], f, indent=2, ensure_ascii=False)
        with open(os.path.join(export_dir, "relatorio_depara_consolidado.json"), "w", encoding="utf-8") as f:
            json.dump(package["files_content"]["relatorio_depara_consolidado.json"], f, indent=2, ensure_ascii=False)
        manifest_payload = {
            "artifact_id": package["artifact_id"],
            "document_id": package["document_id"],
            "document_title": package["document_title"],
            "manifest_hash": package["manifest_hash"],
            "disclaimer": package["disclaimer"],
            "created_at": package["created_at"],
            "files_manifest": package["files_manifest"]
        }
        with open(os.path.join(export_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest_payload, f, indent=2, ensure_ascii=False)


        # CA-42: Verificação de ausência absoluta de notas internas ou PII
        files_content = package["files_content"]
        clean_json_str = json.dumps(files_content["minuta_limpa_final.json"])
        assert "internal_notes" not in clean_json_str
        assert "Dra. Helena Martins" not in clean_json_str
        assert "helena.unit101@condoc.com.br" not in clean_json_str
        assert "STJ pacificou no Resp" not in clean_json_str  # Nota confidencial não vazou!

        # Verificação da integridade criptográfica
        artifact_id = uuid.UUID(package["artifact_id"])
        verification_payload = {
            "minuta_limpa_final.json": json.dumps(files_content["minuta_limpa_final.json"], sort_keys=True, indent=2, ensure_ascii=False),
            "minuta_limpa_final.txt": files_content["minuta_limpa_final.txt"],
            "relatorio_depara_consolidado.json": json.dumps(files_content["relatorio_depara_consolidado.json"], sort_keys=True, indent=2, ensure_ascii=False)
        }

        integrity_result = PreservationService.verify_manifest_integrity(
            artifact_id=artifact_id,
            condominium_id=condo.id,
            files_content_map=verification_payload
        )
        assert integrity_result["integrity_verified"] is True
        assert len(integrity_result["verified_files"]) == 3

        # Teste de detecção de adulteração (Tamper Detection)
        tampered_payload = dict(verification_payload)
        tampered_payload["minuta_limpa_final.txt"] = tampered_payload["minuta_limpa_final.txt"] + "\n[ADULTERAÇÃO MALICIOSA]"
        with pytest.raises(ManifestIntegrityError):
            PreservationService.verify_manifest_integrity(
                artifact_id=artifact_id,
                condominium_id=condo.id,
                files_content_map=tampered_payload
            )

        # Modo de leitura para assembleia sem módulos de votação (CA-45)
        reading_view = PreservationService.get_assembly_reading_view(
            condominium_id=condo.id,
            document_id=document.id
        )
        assert reading_view["reading_mode"] == "assembleia_somente_leitura"
        assert reading_view["has_voting_module"] is False
        assert "votar" not in reading_view["available_controls"]

        elapsed_time = time.time() - start_time
        print(f"\n>>> SUCESSO TOTAL: Ciclo de vida completo do Regimento Interno executado e validado em {elapsed_time:.2f}s! <<<\n")
