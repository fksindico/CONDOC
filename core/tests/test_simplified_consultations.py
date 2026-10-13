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
        assert suggestion.protocol.startswith("SUG-")
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
        assert data["protocol"].startswith("SUG-")
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
