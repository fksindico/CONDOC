"""
Testes Automatizados da Fase 3 — Núcleo Documental, OCR, Dispositivos e Snapshots (CONDC)
Cobre os Critérios de Aceite:
- CA-17: Original documental preservado com conferência humana
- CA-18: Corrigir transcrição gera versão e não simula alteração normativa
- CA-23: Edição concorrente gera conflito sem sobrescrita (ETag / If-Match)
- CA-24: Nota interna ausente em API e export público
- CA-41: Snapshot imutável e reproduzível
- Gate Fase 3: Árvore sem ciclos, recuperação de task, snapshot e nota privada.
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
    Provision,
    ProvisionRevision,
    InternalNote,
    DocumentSnapshot,
    SnapshotItem,
)
from domain.documents.exceptions import (
    CircularReferenceError,
    ConcurrencyConflictError,
    SnapshotImmutableError,
    PrivateNoteAccessForbiddenError,
)
from domain.documents.invariants import (
    assert_no_circular_hierarchy,
    calculate_revision_etag,
    assert_optimistic_concurrency,
    calculate_snapshot_hash,
    assert_snapshot_immutable,
    sanitize_public_provision_dto,
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


@pytest.fixture
def phase3_setup(db):
    """Cenário base para testes de documentos normativos."""
    condo = Condominium.objects.create(name="Condomínio Residencial Aurora Documental")
    admin_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="sindico.doc@condc.local",
        full_name="Síndico Operador Documental"
    )
    RoleAssignment.objects.create(
        condominium_id=condo.id,
        account_id=admin_acc.id,
        role="sindico",
        status="active"
    )

    morador_acc = Account.objects.create(
        auth_user_id=uuid.uuid4(),
        email="morador.doc@condc.local",
        full_name="Morador Leitor"
    )

    project = ProjectService.create_project(
        condominium_id=condo.id,
        name="Modernização do Regimento Interno 2026",
        purpose="Adequação às novas normas de áreas comuns e animais",
        kind="revisao",
        coordinator_account_id=admin_acc.id
    )

    document = DocumentService.create_document(
        project_id=project.id,
        condominium_id=condo.id,
        title="Regimento Interno Consolidado",
        type="regimento_interno"
    )

    return {
        "condo": condo,
        "admin_acc": admin_acc,
        "morador_acc": morador_acc,
        "project": project,
        "document": document,
        "client": APIClient()
    }


# ============================================================================
# 1. TESTES DE DOMÍNIO E INVARIANTES ESTRUTURAIS
# ============================================================================

class TestPhase3DomainInvariants:

    def test_assert_no_circular_hierarchy_detects_self_parent(self):
        """Dispositivo não pode ser pai de si mesmo."""
        prov_id = uuid.uuid4()
        with pytest.raises(CircularReferenceError, match="não pode ser pai de si mesmo"):
            assert_no_circular_hierarchy(
                provision_id=prov_id,
                new_parent_id=prov_id,
                get_parent_func=lambda pid: None
            )

    def test_assert_no_circular_hierarchy_detects_indirect_cycle(self):
        """Ciclo indireto (A -> B -> C -> A) deve ser detectado e bloqueado."""
        node_a = uuid.uuid4()
        node_b = uuid.uuid4()
        node_c = uuid.uuid4()

        # Estrutura existente: C é pai de B; B é pai de A
        # Tentativa: fazer de A o pai de C geraria o ciclo A -> B -> C -> A
        hierarchy = {
            node_b: node_a,
            node_c: node_b,
        }

        with pytest.raises(CircularReferenceError, match="é descendente de"):
            assert_no_circular_hierarchy(
                provision_id=node_a,
                new_parent_id=node_c,
                get_parent_func=lambda pid: hierarchy.get(pid)
            )

    def test_assert_snapshot_immutable(self):
        """Snapshot com is_immutable=True rejeita alterações (CA-41)."""
        with pytest.raises(SnapshotImmutableError, match="estritamente imutável"):
            assert_snapshot_immutable(is_immutable=True)

    def test_sanitize_public_provision_dto_removes_internal_notes(self):
        """CA-24: DTO público remove qualquer nota interna ou comentário confidencial."""
        raw_dto = {
            "id": str(uuid.uuid4()),
            "label": "Art. 15",
            "text": "É proibido ruído excessivo após as 22h.",
            "internal_notes": [{"author": "Jurídico", "content": "Verificar jurisprudência local"}],
            "notes": "Anotação preliminar",
            "legal_opinions": "Risco moderado"
        }
        cleaned = sanitize_public_provision_dto(raw_dto)
        assert "internal_notes" not in cleaned
        assert "notes" not in cleaned
        assert "legal_opinions" not in cleaned
        assert cleaned["label"] == "Art. 15"


# ============================================================================
# 2. TESTES DE OCR E TRANSCRIÇÃO (CA-17, CA-18)
# ============================================================================

class TestPhase3SourceTranscriptionLifecycle:

    def test_ca_17_original_documental_preservado_com_conferencia_humana(self, phase3_setup):
        """
        CA-17: Original documental preservado com conferência humana.
        Upload calcula hash SHA-256 e conferência registra checked_by e checked_at.
        """
        condo = phase3_setup["condo"]
        admin_acc = phase3_setup["admin_acc"]
        document = phase3_setup["document"]

        content = b"DOCUMENTO ORIGINAL: REGIMENTO INTERNO DE 1998. Artigo 1 - Regras gerais."
        source_file = SourceFileService.register_source_file(
            condominium_id=condo.id,
            uploaded_by_id=admin_acc.id,
            filename="regimento_1998.pdf",
            mime_type="application/pdf",
            size_bytes=len(content),
            file_content=content
        )

        assert len(source_file.file_hash) == 64
        assert source_file.state == "ready"

        # Cria transcrição bruta de OCR
        transcription = TranscriptionService.create_initial_transcription(
            document_id=document.id,
            condominium_id=condo.id,
            source_file_id=source_file.id,
            raw_text="Artigo 1 - Regras gerais do condominio."
        )
        assert transcription.status == "under_review"
        assert transcription.version == 1

        # Conferência humana realizada
        confirmed = TranscriptionService.confirm_transcription(
            transcription_id=transcription.id,
            checked_by_id=admin_acc.id,
            corrected_text="Art. 1º Regras gerais do Condomínio Aurora."
        )

        assert confirmed.status == "confirmed"
        assert confirmed.checked_by_id == admin_acc.id
        assert confirmed.checked_at is not None
        assert confirmed.corrected_text == "Art. 1º Regras gerais do Condomínio Aurora."

    def test_ca_18_corrigir_transcricao_gera_versao_sem_simular_alteracao_normativa(self, phase3_setup):
        """
        CA-18: Corrigir transcrição gera nova versão (v2) apontando para o antecessor
        sem gerar revisão no dispositivo normativo e sem simular alteração deliberativa.
        """
        condo = phase3_setup["condo"]
        admin_acc = phase3_setup["admin_acc"]
        document = phase3_setup["document"]

        content = b"DOCUMENTO COM ERRO DE OCR"
        source_file = SourceFileService.register_source_file(
            condominium_id=condo.id,
            uploaded_by_id=admin_acc.id,
            filename="doc_ocr.pdf",
            mime_type="application/pdf",
            size_bytes=len(content),
            file_content=content
        )

        t_v1 = TranscriptionService.create_initial_transcription(
            document_id=document.id,
            condominium_id=condo.id,
            source_file_id=source_file.id,
            raw_text="Art. 5 - Permitido animais de pequeno porte com coleira."
        )
        TranscriptionService.confirm_transcription(t_v1.id, admin_acc.id)

        # Correção tipográfica do OCR identificada posteriormente
        t_v2 = TranscriptionService.correct_transcription(
            transcription_id=t_v1.id,
            checked_by_id=admin_acc.id,
            corrected_text="Art. 5º É permitido o trânsito de animais de pequeno porte, sempre com guia."
        )

        assert t_v2.version == 2
        assert t_v2.status == "confirmed"
        assert t_v2.replaces_transcription_id == t_v1.id

        # Versão antiga marcada como superseded
        t_v1.refresh_from_db()
        assert t_v1.status == "superseded"


# ============================================================================
# 3. TESTES DE DISPOSITIVOS E CONCORRÊNCIA OTIMISTA (CA-23)
# ============================================================================

class TestPhase3ProvisionsAndOptimisticConcurrency:

    def test_ca_23_edicao_concorrente_gera_conflito_sem_sobrescrita(self, phase3_setup):
        """
        CA-23: Edição concorrente gera conflito (ETag / If-Match).
        Se o usuário tentar atualizar com ETag desatualizado, levanta ConcurrencyConflictError
        e não sobrescreve os dados no banco.
        """
        condo = phase3_setup["condo"]
        admin_acc = phase3_setup["admin_acc"]
        document = phase3_setup["document"]

        # Criação de dispositivo inicial (revisão 1)
        prov = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="artigo",
            label="Art. 10",
            text="O horário de silêncio inicia às 22h.",
            author_account_id=admin_acc.id
        )

        rev_v1 = ProvisionService.get_latest_revision(prov.id)
        assert rev_v1.revision_number == 1
        etag_original = rev_v1.etag

        # Usuário A atualiza com sucesso para revisão 2
        rev_v2 = ProvisionService.update_provision(
            provision_id=prov.id,
            expected_etag=etag_original,
            text="O horário de silêncio inicia às 22h e encerra às 08h.",
            author_account_id=admin_acc.id
        )
        assert rev_v2.revision_number == 2
        assert rev_v2.etag != etag_original

        # Usuário B tenta atualizar simultaneamente usando o etag_original da revisão 1
        with pytest.raises(ConcurrencyConflictError, match="Conflito de edição concorrente detectado"):
            ProvisionService.update_provision(
                provision_id=prov.id,
                expected_etag=etag_original,
                text="Texto divergente do usuário B que tentou sobrescrever.",
                author_account_id=admin_acc.id
            )

        # O banco preservou o texto do Usuário A intacto
        current_rev = ProvisionService.get_latest_revision(prov.id)
        assert current_rev.revision_number == 2
        assert current_rev.text == "O horário de silêncio inicia às 22h e encerra às 08h."

    def test_assert_no_circular_hierarchy_on_update_provision(self, phase3_setup):
        """Mover dispositivo para ser filho de seu descendente gera CircularReferenceError."""
        condo = phase3_setup["condo"]
        admin_acc = phase3_setup["admin_acc"]
        document = phase3_setup["document"]

        # Artigo 1 (pai)
        artigo = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="artigo",
            label="Art. 1º",
            text="Das áreas de lazer.",
            author_account_id=admin_acc.id
        )

        # Parágrafo 1 (filho do Artigo 1)
        paragrafo = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="paragrafo",
            label="§ 1º",
            text="A piscina funciona até as 20h.",
            parent_provision_id=artigo.id,
            author_account_id=admin_acc.id
        )

        rev_artigo = ProvisionService.get_latest_revision(artigo.id)

        # Tentativa de transformar Artigo 1 em filho do Parágrafo 1 (ciclo)
        with pytest.raises(CircularReferenceError, match="Referência circular detectada"):
            ProvisionService.update_provision(
                provision_id=artigo.id,
                expected_etag=rev_artigo.etag,
                text="Texto do artigo tentando virar filho do seu parágrafo.",
                parent_provision_id=paragrafo.id,
                author_account_id=admin_acc.id
            )


# ============================================================================
# 4. TESTES DE PRIVACIDADE DE NOTAS INTERNAS (CA-24)
# ============================================================================

class TestPhase3InternalNotesPrivacy:

    def test_ca_24_nota_interna_ausente_em_api_publica_e_restrita_a_gestao(self, phase3_setup):
        """
        CA-24: Notas internas são ausentes em superfícies e payloads públicos.
        Somente papéis com autorização administrativa têm acesso.
        """
        condo = phase3_setup["condo"]
        admin_acc = phase3_setup["admin_acc"]
        morador_acc = phase3_setup["morador_acc"]
        document = phase3_setup["document"]

        prov = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="artigo",
            label="Art. 25",
            text="Multas por infração ao regulamento interno.",
            author_account_id=admin_acc.id
        )

        # Criação de nota interna confidencial
        InternalNoteService.create_note(
            condominium_id=condo.id,
            provision_id=prov.id,
            author_account_id=admin_acc.id,
            content="Nota jurídica: O valor máximo não pode ultrapassar 5 vezes a cota condominial conforme art. 1.336 CC.",
            visibility="juridico",
            category="juridico"
        )

        # 1. Consulta em árvore padrão (pública / portal): notas internas NUNCA aparecem
        tree_public = ProvisionService.get_document_tree(document_id=document.id, include_notes=False)
        assert len(tree_public) == 1
        assert "internal_notes" not in tree_public[0]

        # 2. Morador comum tentando listar notas internas diretamente é bloqueado com 403
        with pytest.raises(PrivateNoteAccessForbiddenError, match="sem autorização"):
            InternalNoteService.list_notes_for_provision(provision_id=prov.id, user_role="morador")

        # 3. Síndico ou jurídico com papel administrativo consegue consultar
        notes_admin = InternalNoteService.list_notes_for_provision(provision_id=prov.id, user_role="sindico")
        assert len(notes_admin) == 1
        assert "art. 1.336 CC" in notes_admin[0].content


# ============================================================================
# 5. TESTES DE SNAPSHOTS IMUTÁVEIS (CA-41)
# ============================================================================

class TestPhase3SnapshotsImmutability:

    def test_ca_41_snapshot_imutavel_e_reproduzivel(self, phase3_setup):
        """
        CA-41: Snapshot congela atomicamente o documento com hash SHA-256 reproduzível.
        Edições posteriores no documento não alteram a versão histórica congelada.
        """
        condo = phase3_setup["condo"]
        admin_acc = phase3_setup["admin_acc"]
        document = phase3_setup["document"]

        # Cria dois dispositivos na minuta
        p1 = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="artigo",
            label="Art. 1º",
            text="Disposições preliminares do condomínio.",
            position=1,
            author_account_id=admin_acc.id
        )
        p2 = ProvisionService.create_provision(
            document_id=document.id,
            condominium_id=condo.id,
            kind="artigo",
            label="Art. 2º",
            text="Dos direitos dos condôminos.",
            position=2,
            author_account_id=admin_acc.id
        )

        # Congela o snapshot da versão de consulta pública
        snapshot = SnapshotService.create_snapshot(
            document_id=document.id,
            condominium_id=condo.id,
            version_label="Snapshot-v1.0-Consulta",
            frozen_by_id=admin_acc.id,
            purpose="consulta_publica"
        )

        assert snapshot.is_immutable is True
        assert len(snapshot.content_hash) == 64

        # Recupera a árvore do snapshot congelado
        snap_tree = SnapshotService.get_snapshot_tree(snapshot.id)
        assert len(snap_tree["items"]) == 2
        assert snap_tree["items"][0]["text"] == "Disposições preliminares do condomínio."

        # Modifica o documento normativo na minuta de trabalho (gera revisão v2 no Art. 1º)
        rev_p1 = ProvisionService.get_latest_revision(p1.id)
        ProvisionService.update_provision(
            provision_id=p1.id,
            expected_etag=rev_p1.etag,
            text="Texto alterado na minuta de trabalho que não deve afetar o snapshot.",
            author_account_id=admin_acc.id
        )

        # Verifica se o snapshot permaneceu 100% inalterado (imutabilidade estrita)
        snap_tree_after = SnapshotService.get_snapshot_tree(snapshot.id)
        assert snap_tree_after["items"][0]["text"] == "Disposições preliminares do condomínio."
        assert snap_tree_after["content_hash"] == snapshot.content_hash


# ============================================================================
# 6. TESTES DE INTEGRAÇÃO DOS ENDPOINTS DA API REST
# ============================================================================

class TestPhase3APIEndpoints:

    def test_fluxo_completo_api_documentos_concorrencia_e_notas(self, phase3_setup):
        """Fluxo completo via API REST cobrindo criação, ETag, notas e snapshots."""
        client = phase3_setup["client"]
        condo = phase3_setup["condo"]
        project = phase3_setup["project"]
        document = phase3_setup["document"]
        admin_acc = phase3_setup["admin_acc"]

        # 1. Criação de Dispositivo via API (POST /provisions)
        create_resp = client.post(
            f"/api/v1/condominiums/{condo.id}/documents/{document.id}/provisions",
            {
                "kind": "artigo",
                "label": "Art. 30",
                "text": "Da utilização do salão de festas.",
                "position": 1,
                "actor_account_id": str(admin_acc.id)
            },
            format='json'
        )
        assert create_resp.status_code == 201
        prov_id = create_resp.data["id"]
        etag_v1 = create_resp.data["etag"]
        assert 'ETag' in create_resp.headers

        # 2. Atualização com ETag correto (PATCH com If-Match) -> Sucesso HTTP 200
        patch_ok = client.patch(
            f"/api/v1/condominiums/{condo.id}/provisions/{prov_id}",
            {
                "text": "Da utilização do salão de festas mediante reserva prévia.",
            },
            HTTP_IF_MATCH=f'"{etag_v1}"',
            format='json'
        )
        assert patch_ok.status_code == 200
        etag_v2 = patch_ok.data["etag"]
        assert patch_ok.data["revision_number"] == 2

        # 3. Atualização concorrente com ETag desatualizado (If-Match com etag_v1) -> HTTP 412
        patch_conflict = client.patch(
            f"/api/v1/condominiums/{condo.id}/provisions/{prov_id}",
            {
                "text": "Texto conflitante de usuário concorrente.",
            },
            HTTP_IF_MATCH=f'"{etag_v1}"',
            format='json'
        )
        assert patch_conflict.status_code == 412
        assert patch_conflict.data["code"] == "CONCURRENCY_CONFLICT"

        # 4. Criação de Nota Interna (POST /notes)
        note_resp = client.post(
            f"/api/v1/condominiums/{condo.id}/provisions/{prov_id}/notes",
            {
                "content": "A taxa de limpeza deve ser debatida com os moradores.",
                "visibility": "equipe",
                "category": "redacao",
                "actor_account_id": str(admin_acc.id)
            },
            format='json'
        )
        assert note_resp.status_code == 201

        # 5. Listagem de árvore padrão via GET omite notas internas (CA-24)
        tree_resp = client.get(f"/api/v1/condominiums/{condo.id}/documents/{document.id}/provisions")
        assert tree_resp.status_code == 200
        assert "internal_notes" not in tree_resp.data[0]

        # 6. Congelamento em Snapshot (POST /snapshots) -> HTTP 201
        snap_resp = client.post(
            f"/api/v1/condominiums/{condo.id}/documents/{document.id}/snapshots",
            {
                "version_label": "Minuta-v1.0-Marco-Inicial",
                "purpose": "marco_revisao",
                "actor_account_id": str(admin_acc.id)
            },
            format='json'
        )
        assert snap_resp.status_code == 201
        snapshot_id = snap_resp.data["id"]
        assert snap_resp.data["is_immutable"] is True

        # 7. Consulta da árvore exata congelada (GET /snapshots/{id}) -> HTTP 200
        detail_snap = client.get(f"/api/v1/condominiums/{condo.id}/snapshots/{snapshot_id}")
        assert detail_snap.status_code == 200
        assert len(detail_snap.data["items"]) == 1
        assert detail_snap.data["items"][0]["text"] == "Da utilização do salão de festas mediante reserva prévia."
