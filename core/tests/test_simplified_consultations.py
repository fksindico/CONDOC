"""
Testes Automatizados para Consultas Públicas Simplificadas de Documentos em PDF
Testa o fluxo zero-atrito para moradores, submissão de sugestões, link tokenizado,
filtros de pesquisa e exportação CSV para o síndico.
"""
import io
import uuid
import pytest
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

from infrastructure.models import (
    Condominium,
    Account,
    PublicConsultation,
    ConsultationSuggestion,
)
from application.consultation.services import SimplifiedConsultationService


@pytest.mark.django_db
class TestSimplifiedConsultationService:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.condo = Condominium.objects.create(
            name="Condomínio Residencial Jardins",
            cnpj="12.345.678/0001-90",
            address_city="São Paulo",
            address_state="SP",
        )
        self.account = Account.objects.create(
            email="sindico@jardins.com",
            full_name="Síndico João da Silva",
            auth_user_id=uuid.uuid4(),
        )
        self.dummy_pdf = SimpleUploadedFile(
            "Regimento_Interno_2026.pdf",
            b"%PDF-1.4 Mock PDF Document Content for Testing",
            content_type="application/pdf"
        )

    def test_create_consultation_generates_token_and_persists_pdf(self):
        """Valida a criação da consulta com geração automática de token seguro."""
        consultation = SimplifiedConsultationService.create_consultation(
            condominium_id=self.condo.id,
            title="Revisão Participativa do Regimento Interno 2026",
            document_type="regimento",
            pdf_file=self.dummy_pdf,
            description="Envie suas sugestões de melhoria para o regimento.",
            created_by_id=self.account.id,
        )

        assert consultation.id is not None
        assert consultation.public_token is not None
        assert len(consultation.public_token) >= 16
        assert consultation.status == "aberta"
        assert consultation.pdf_original_name == "Regimento_Interno_2026.pdf"
        assert consultation.pdf_size_bytes > 0
        assert "consultations" in consultation.pdf_file_path

    def test_submit_suggestion_zero_friction_and_unique_protocol(self):
        """Valida que morador submete sugestão sem login e recebe protocolo único."""
        consultation = SimplifiedConsultationService.create_consultation(
            condominium_id=self.condo.id,
            title="Consulta Teste",
            document_type="regimento",
            pdf_file=self.dummy_pdf,
        )

        suggestion = SimplifiedConsultationService.submit_suggestion(
            token=consultation.public_token,
            resident_name="Maria Souza",
            resident_phone="(11) 98765-4321",
            resident_email="maria@exemplo.com",
            block_tower="Torre A",
            unit_code="402",
            target_reference="Artigo 15, Parágrafo 2º",
            action_type="alterar",
            suggestion_text="Permitir animais de estimação de pequeno porte nas áreas comuns com coleira.",
            justification="Facilita a circulação com animais idosos sem prejuízo à higiene.",
        )

        assert suggestion.id is not None
        assert suggestion.protocol.startswith("Torre A-402-")
        assert len(suggestion.protocol.split("-")[-1]) == 5
        assert suggestion.action_type == "alterar"
        assert suggestion.unit_code == "402"
        assert suggestion.status == "recebida"

    def test_reject_suggestion_for_closed_consultation(self):
        """Valida bloqueio de envios quando a consulta estiver encerrada."""
        consultation = SimplifiedConsultationService.create_consultation(
            condominium_id=self.condo.id,
            title="Consulta Encerrada",
            document_type="regimento",
            pdf_file=self.dummy_pdf,
        )
        consultation.status = "encerrada"
        consultation.save()

        with pytest.raises(ValueError) as exc:
            SimplifiedConsultationService.submit_suggestion(
                token=consultation.public_token,
                resident_name="Carlos",
                resident_phone="11999998888",
                unit_code="101",
                target_reference="Art. 1",
                action_type="incluir",
                suggestion_text="Nova regra",
            )
        assert "não aceita novos envios" in str(exc.value)

    def test_export_suggestions_csv_format(self):
        """Valida que o CSV gerado tem BOM UTF-8 e os dados das sugestões."""
        consultation = SimplifiedConsultationService.create_consultation(
            condominium_id=self.condo.id,
            title="Consulta CSV",
            document_type="regimento",
            pdf_file=self.dummy_pdf,
        )
        SimplifiedConsultationService.submit_suggestion(
            token=consultation.public_token,
            resident_name="Ana Paula",
            resident_phone="(11) 91234-5678",
            resident_email="anapaula@teste.com",
            block_tower="Bloco 2",
            unit_code="104",
            target_reference="Artigo 22",
            action_type="remover",
            suggestion_text="Excluir taxa extra de churrasqueira.",
            justification="Custo já coberto pela taxa ordinária.",
        )

        csv_content = SimplifiedConsultationService.export_suggestions_csv(
            condominium_id=self.condo.id,
            consultation_id=consultation.id,
        )

        assert csv_content.startswith("\ufeff")  # BOM UTF-8
        assert "Protocolo;Data e Hora;Morador" in csv_content
        assert "Ana Paula" in csv_content
        assert "104" in csv_content
        assert "Artigo 22" in csv_content
        assert "Remover Dispositivo" in csv_content

    def test_reject_suggestion_without_resident_email(self):
        """Valida que o e-mail do morador é estritamente obrigatório."""
        consultation = SimplifiedConsultationService.create_consultation(
            condominium_id=self.condo.id,
            title="Consulta Obrigatória de Email",
            document_type="regimento",
            pdf_file=self.dummy_pdf,
        )

        with pytest.raises(ValueError) as exc:
            SimplifiedConsultationService.submit_suggestion(
                token=consultation.public_token,
                resident_name="Marcos",
                resident_phone="(11) 99999-0000",
                resident_email="",  # Vazio
                unit_code="301",
                target_reference="Art. 5",
                action_type="alterar",
                suggestion_text="Alteração teste",
            )
        assert "e-mail do morador é obrigatório" in str(exc.value)


@pytest.mark.django_db
class TestSimplifiedConsultationApi:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.client = Client()
        self.condo = Condominium.objects.create(
            name="Edifício Solar das Palmeiras",
            cnpj="98.765.432/0001-10",
        )
        self.pdf_file = SimpleUploadedFile(
            "Regimento_Solar.pdf",
            b"%PDF-1.4 Test PDF content",
            content_type="application/pdf"
        )
        self.consultation = SimplifiedConsultationService.create_consultation(
            condominium_id=self.condo.id,
            title="Consulta Pública Regimento",
            document_type="regimento",
            pdf_file=self.pdf_file,
            description="Descrição da consulta pública",
        )

    def test_public_get_consultation_by_token(self):
        """Morador consulta detalhes via token sem login."""
        url = f"/api/v1/public/consultations/{self.consultation.public_token}"
        response = self.client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Consulta Pública Regimento"
        assert data["condominium_name"] == "Edifício Solar das Palmeiras"
        assert "pdf_download_url" in data
        assert self.consultation.public_token in data["pdf_download_url"]

    def test_public_get_pdf_streaming(self):
        """Morador visualiza PDF através da URL pública do documento."""
        url = f"/api/v1/public/consultations/{self.consultation.public_token}/pdf"
        response = self.client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "inline" in response["Content-Disposition"]

    def test_public_submit_suggestion(self):
        """Morador envia sugestão e recebe protocolo."""
        url = f"/api/v1/public/consultations/{self.consultation.public_token}/suggestions"
        payload = {
            "resident_name": "Roberto Firmino",
            "resident_phone": "(11) 97777-6666",
            "resident_email": "roberto@teste.com",
            "block_tower": "Torre Sul",
            "unit_code": "801",
            "target_reference": "Artigo 45, § 1º",
            "action_type": "incluir",
            "suggestion_text": "Incluir horário de silêncio estendido aos domingos até as 10h.",
            "justification": "Garantir descanso aos moradores aos domingos.",
        }
        response = self.client.post(url, data=payload, content_type="application/json")

        assert response.status_code == 201
        data = response.json()
        assert "protocol" in data
        assert data["protocol"].startswith("Torre Sul-801-")
        assert len(data["protocol"].split("-")[-1]) == 5
        assert data["resident_name"] == "Roberto Firmino"
        assert data["unit_code"] == "801"
        assert data["action_type"] == "incluir"

    def test_admin_list_consultations_and_export_csv(self):
        """Síndico lista consultas e exporta CSV de sugestões."""
        # Envia uma sugestão pública
        SimplifiedConsultationService.submit_suggestion(
            token=self.consultation.public_token,
            resident_name="Beatriz",
            resident_phone="11911112222",
            resident_email="beatriz@teste.com",
            unit_code="202",
            target_reference="Art. 10",
            action_type="alterar",
            suggestion_text="Modificar redação do art. 10",
        )

        # 1. Admin lista consultas
        list_url = f"/api/v1/condominiums/{self.condo.id}/consultations"
        resp_list = self.client.get(list_url)
        assert resp_list.status_code == 200
        items = resp_list.json()
        assert len(items) >= 1
        assert items[0]["suggestions_count"] == 1

        # 2. Admin exporta CSV
        export_url = f"/api/v1/condominiums/{self.condo.id}/consultations/{self.consultation.id}/export"
        resp_export = self.client.get(export_url)
        assert resp_export.status_code == 200
        assert "text/csv" in resp_export["Content-Type"]
        assert "Beatriz" in resp_export.content.decode("utf-8")

    def test_resident_deduplication_on_multiple_suggestions(self):
        """
        Valida que múltiplos envios de sugestão pelo mesmo morador no link universal
        NÃO criam registros duplicados no cadastro de moradores, e consolidam o histórico.
        """
        from infrastructure.models import ResidentRegistration

        # 1. Primeiro envio
        SimplifiedConsultationService.submit_suggestion(
            token=self.consultation.public_token,
            resident_name="Carlos Eduardo Silva",
            resident_phone="(11) 98888-7777",
            resident_email="carlos.eduardo@teste.com",
            block_tower="Torre Alpha",
            unit_code="501",
            target_reference="Artigo 12",
            action_type="alterar",
            suggestion_text="Primeira sugestão de teste",
        )

        regs = ResidentRegistration.objects.filter(condominium=self.condo)
        assert regs.count() == 1
        reg = regs.first()
        assert reg.full_name == "Carlos Eduardo Silva"
        assert reg.phone_e164 == "11988887777"
        assert reg.email == "carlos.eduardo@teste.com"
        assert reg.unit.code == "501"

        # 2. Segundo envio pelo mesmo morador na mesma unidade
        SimplifiedConsultationService.submit_suggestion(
            token=self.consultation.public_token,
            resident_name="Carlos Eduardo Silva",
            resident_phone="11988887777",
            resident_email="carlos.eduardo@teste.com",
            block_tower="Torre Alpha",
            unit_code="501",
            target_reference="Artigo 18",
            action_type="remover",
            suggestion_text="Segunda sugestão do mesmo morador",
        )

        # Continua sendo exatamente 1 cadastro!
        assert ResidentRegistration.objects.filter(condominium=self.condo).count() == 1

        # 3. Terceiro envio com e-mail divergente
        sug3 = SimplifiedConsultationService.submit_suggestion(
            token=self.consultation.public_token,
            resident_name="Carlos Eduardo Silva",
            resident_phone="11988887777",
            resident_email="carlos.silva.novo@teste.com",
            block_tower="Torre Alpha",
            unit_code="501",
            target_reference="Artigo 25",
            action_type="incluir",
            suggestion_text="Terceira sugestão incluindo novo parágrafo",
        )

        # Continua sendo exatamente 1 cadastro de morador, preservando o e-mail do titular legítimo
        regs_after = ResidentRegistration.objects.filter(condominium=self.condo)
        assert regs_after.count() == 1
        assert regs_after.first().email == "carlos.eduardo@teste.com"

        # A sugestão foi aceita, mas sinalizada com divergência cadastral para o síndico!
        assert sug3.has_divergence is True
        assert sug3.registered_email == "carlos.eduardo@teste.com"
        assert "carlos.silva.novo@teste.com" in sug3.divergence_details

        # Sugestões totais enviadas: 3
        assert ConsultationSuggestion.objects.filter(condominium=self.condo).count() == 3

        # 4. Verifica API do Síndico: lista de moradores exibe suggestions_count == 3
        list_url = f"/api/v1/condominiums/{self.condo.id}/registrations"
        resp = self.client.get(list_url)
        assert resp.status_code == 200
        moradores = resp.json()
        assert len(moradores) == 1
        assert moradores[0]["full_name"] == "Carlos Eduardo Silva"
        assert moradores[0]["suggestions_count"] == 3

        # 5. Verifica endpoint de sugestões do morador
        reg_id = moradores[0]["id"]
        sug_url = f"/api/v1/condominiums/{self.condo.id}/registrations/{reg_id}/suggestions"
        resp_sug = self.client.get(sug_url)
        assert resp_sug.status_code == 200
        user_sugs = resp_sug.json()
        assert len(user_sugs) == 3

    def test_different_resident_creates_second_record(self):
        """Valida que morador de unidade diferente gera um novo registro legítimo."""
        from infrastructure.models import ResidentRegistration

        # Morador 1 (Apto 501)
        SimplifiedConsultationService.submit_suggestion(
            token=self.consultation.public_token,
            resident_name="Carlos Silva",
            resident_phone="11988887777",
            resident_email="carlos@teste.com",
            unit_code="501",
            target_reference="Art. 1",
            action_type="alterar",
            suggestion_text="Sugestão 1",
        )

        # Morador 2 (Apto 502)
        SimplifiedConsultationService.submit_suggestion(
            token=self.consultation.public_token,
            resident_name="Ana Paula",
            resident_phone="11999998888",
            resident_email="anapaula@teste.com",
            unit_code="502",
            target_reference="Art. 2",
            action_type="incluir",
            suggestion_text="Sugestão 2",
        )

        assert ResidentRegistration.objects.filter(condominium=self.condo).count() == 2

    def test_security_cannot_view_third_party_suggestions_by_unit_or_phone(self):
        """
        SEGURANÇA DA INFORMAÇÃO E PRIVACIDADE (Anti-IDOR):
        Garante que um morador NÃO consiga visualizar sugestões de outros vizinhos
        informando o número de unidade ou telefone de terceiros no endpoint público.
        """
        # Vizinho 1 (Apto 701) envia uma sugestão legítima
        sug_vizinho = SimplifiedConsultationService.submit_suggestion(
            token=self.consultation.public_token,
            resident_name="Mariana Vizinha",
            resident_phone="11977771111",
            resident_email="mariana@teste.com",
            unit_code="701",
            target_reference="Art. 20",
            action_type="alterar",
            suggestion_text="Proibir animais no elevador social.",
            justification="Higiene e alergias."
        )

        base_url = f"/api/v1/public/consultations/{self.consultation.public_token}/my-suggestions"

        # 1. Terceiro curioso tenta consultar passando a unidade do vizinho: unit=701
        resp_by_unit = self.client.get(f"{base_url}?unit=701")
        assert resp_by_unit.status_code == 200
        assert resp_by_unit.json() == [], "FALHA DE SEGURANÇA: Endpoint público revelou sugestão de terceiro por unidade!"

        # 2. Terceiro curioso tenta consultar passando o telefone do vizinho
        resp_by_phone = self.client.get(f"{base_url}?phone=11977771111")
        assert resp_by_phone.status_code == 200
        assert resp_by_phone.json() == [], "FALHA DE SEGURANÇA: Endpoint público revelou sugestão de terceiro por telefone!"

        # 3. Terceiro curioso tenta consultar passando unidade E telefone do vizinho
        resp_by_both = self.client.get(f"{base_url}?unit=701&phone=11977771111")
        assert resp_by_both.status_code == 200
        assert resp_by_both.json() == [], "FALHA DE SEGURANÇA: Endpoint público revelou sugestão de terceiro!"

        # 4. Sem parâmetros: também vazio
        resp_empty = self.client.get(base_url)
        assert resp_empty.status_code == 200
        assert resp_empty.json() == []

        # 5. Apenas com o protocolo secreto unívoco (que só quem enviou possui): retorna a sugestão
        resp_protocol = self.client.get(f"{base_url}?protocol={sug_vizinho.protocol}")
        assert resp_protocol.status_code == 200
        res_data = resp_protocol.json()
        assert len(res_data) == 1
        assert res_data[0]["protocol"] == sug_vizinho.protocol
        assert res_data[0]["suggestion_text"] == "Proibir animais no elevador social."
        # Garante que dados de contato confidenciais (telefone/email) NÃO são expostos nem pelo protocolo
        assert "resident_phone" not in res_data[0]
        assert "resident_email" not in res_data[0]

    def test_public_submit_suggestion_requires_email(self):
        """Valida que a API pública rejeita requisição sem e-mail do morador."""
        url = f"/api/v1/public/consultations/{self.consultation.public_token}/suggestions"
        payload = {
            "resident_name": "Juliana Santos",
            "resident_phone": "(11) 96666-5555",
            # Sem resident_email
            "unit_code": "102",
            "target_reference": "Artigo 1",
            "action_type": "alterar",
            "suggestion_text": "Alteração no Artigo 1",
        }
        response = self.client.post(url, data=payload, content_type="application/json")
        assert response.status_code == 400
        assert "resident_email" in response.json()

    def test_public_landing_info_endpoint(self):
        """Valida que o endpoint público da Landing Page retorna as consultas abertas e dados institucionais."""
        self.condo.landing_title = "Residencial Jardins de Versalhes"
        self.condo.landing_subtitle = "Governança Participativa 2026"
        self.condo.landing_description = "Sejam bem-vindos ao portal de revisão de regras."
        self.condo.save()

        url = "/api/v1/public/landing-info"
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Edifício Solar das Palmeiras"
        assert data["landing_title"] == "Residencial Jardins de Versalhes"
        assert len(data["open_consultations"]) >= 1
        assert data["open_consultations"][0]["public_token"] == self.consultation.public_token

    def test_submission_returns_thank_you_message_and_divergence(self):
        """Valida que o retorno da submissão traz a mensagem de agradecimento e status de divergência."""
        # Configura mensagem customizada na consulta
        self.consultation.thank_you_message = "Mensagem personalizada: Muito obrigado por sua ajuda!"
        self.consultation.save()

        # Pré-cadastra morador com e-mail original
        from infrastructure.models import Unit, ResidentRegistration
        unit = Unit.objects.create(condominium=self.condo, code="302A")
        ResidentRegistration.objects.create(
            condominium=self.condo,
            unit=unit,
            full_name="Maria Oliveira",
            phone_e164="11955554444",
            email="maria.titular@teste.com",
            relationship="proprietario_residente",
        )

        # Envio com e-mail DIVERGENTE
        url = f"/api/v1/public/consultations/{self.consultation.public_token}/suggestions"
        payload = {
            "resident_name": "Maria Oliveira",
            "resident_phone": "(11) 95555-4444",
            "resident_email": "outro.email@teste.com",
            "unit_code": "302A",
            "target_reference": "Artigo 15",
            "action_type": "alterar",
            "suggestion_text": "Proposta de mudança com e-mail alternativo",
        }
        response = self.client.post(url, data=payload, content_type="application/json")
        assert response.status_code == 201
        data = response.json()
        assert data["has_divergence"] is True
        assert data["thank_you_message"] == "Mensagem personalizada: Muito obrigado por sua ajuda!"

        # Verifica filtro no painel do síndico
        admin_url = f"/api/v1/condominiums/{self.condo.id}/consultations/{self.consultation.id}/suggestions?has_divergence=true"
        admin_resp = self.client.get(admin_url)
        assert admin_resp.status_code == 200
        sug_list = admin_resp.json()
        assert len(sug_list) >= 1
        assert sug_list[0]["has_divergence"] is True
        assert sug_list[0]["registered_email"] == "maria.titular@teste.com"
        assert sug_list[0]["resident_email"] == "outro.email@teste.com"



