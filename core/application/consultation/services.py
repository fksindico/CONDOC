"""
Serviços de aplicação para Consultas Públicas Simplificadas de Documentos em PDF
Zero atrito para o morador, link tokenizado e exportação para tratamento externo.
"""
import os
import uuid
import secrets
import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from infrastructure.models import (
    Condominium,
    Account,
    PublicConsultation,
    ConsultationSuggestion,
)


class SimplifiedConsultationService:
    @staticmethod
    def generate_token() -> str:
        """Gera um token alfanumérico seguro para URLs públicas de consulta."""
        return secrets.token_urlsafe(16).replace('-', '').replace('_', '')[:20]

    @staticmethod
    def generate_protocol() -> str:
        """Gera protocolo amigável e legível para o morador, ex: SUG-2026-8491."""
        year = timezone.now().year
        rand = secrets.randbelow(9000) + 1000
        return f"SUG-{year}-{rand}"

    @classmethod
    def create_consultation(
        cls,
        condominium_id: uuid.UUID,
        title: str,
        document_type: str,
        pdf_file: Any,
        description: Optional[str] = None,
        created_by_id: Optional[uuid.UUID] = None,
        deadline: Optional[datetime] = None,
    ) -> PublicConsultation:
        """
        Cria uma nova consulta de documento com upload físico do PDF
        e token público de compartilhamento.
        """
        condo = Condominium.objects.get(id=condominium_id)
        token = cls.generate_token()

        # Garante unicidade do token
        while PublicConsultation.objects.filter(public_token=token).exists():
            token = cls.generate_token()

        # Diretório de armazenamento de mídia
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        consultation_dir = os.path.join(media_root, 'consultations', str(condominium_id))
        os.makedirs(consultation_dir, exist_ok=True)

        # Salva o arquivo PDF no disco
        orig_name = getattr(pdf_file, 'name', 'documento.pdf')
        clean_name = os.path.basename(orig_name).replace(' ', '_')
        save_filename = f"{token}_{clean_name}"
        full_path = os.path.join(consultation_dir, save_filename)

        size_bytes = 0
        with open(full_path, 'wb+') as destination:
            if hasattr(pdf_file, 'chunks'):
                for chunk in pdf_file.chunks():
                    destination.write(chunk)
                    size_bytes += len(chunk)
            elif hasattr(pdf_file, 'read'):
                data = pdf_file.read()
                destination.write(data)
                size_bytes = len(data)

        # Caminho relativo para portabilidade
        rel_path = os.path.join('consultations', str(condominium_id), save_filename)

        consultation = PublicConsultation.objects.create(
            condominium=condo,
            title=title.strip(),
            document_type=document_type if document_type in ('regimento', 'convencao') else 'regimento',
            description=description.strip() if description else None,
            pdf_file_path=rel_path,
            pdf_original_name=orig_name,
            pdf_size_bytes=size_bytes,
            public_token=token,
            status='aberta',
            deadline=deadline,
            created_by_id=created_by_id,
        )
        return consultation

    @staticmethod
    def get_consultation_by_token(token: str) -> PublicConsultation:
        """Busca consulta ativa ou existente pelo token público."""
        return PublicConsultation.objects.select_related('condominium').get(public_token=token)

    @classmethod
    def submit_suggestion(
        cls,
        token: str,
        resident_name: str,
        resident_phone: str,
        unit_code: str,
        target_reference: str,
        action_type: str,
        suggestion_text: str,
        resident_email: Optional[str] = None,
        block_tower: Optional[str] = None,
        justification: Optional[str] = None,
    ) -> ConsultationSuggestion:
        """
        Submissão zero-atrito da sugestão do morador via token público.
        Gera protocolo automático e registra os dados de contato.
        """
        consultation = PublicConsultation.objects.select_related('condominium').get(public_token=token)

        if consultation.status != 'aberta':
            raise ValueError(f"Esta consulta está com status '{consultation.status}' e não aceita novos envios.")

        # Valida ação
        valid_actions = ('alterar', 'remover', 'incluir')
        normalized_action = action_type.lower().strip()
        if normalized_action not in valid_actions:
            raise ValueError(f"Tipo de ação inválido: {action_type}. Deve ser uma de: alterar, remover, incluir.")

        # Gera protocolo único
        protocol = cls.generate_protocol()
        while ConsultationSuggestion.objects.filter(protocol=protocol).exists():
            protocol = cls.generate_protocol()

        suggestion = ConsultationSuggestion.objects.create(
            condominium=consultation.condominium,
            consultation=consultation,
            protocol=protocol,
            resident_name=resident_name.strip(),
            resident_phone=resident_phone.strip(),
            resident_email=resident_email.strip() if resident_email else None,
            block_tower=block_tower.strip() if block_tower else None,
            unit_code=unit_code.strip(),
            target_reference=target_reference.strip(),
            action_type=normalized_action,
            suggestion_text=suggestion_text.strip(),
            justification=justification.strip() if justification else None,
            status='recebida',
        )
        return suggestion

    @staticmethod
    def list_suggestions(
        condominium_id: uuid.UUID,
        consultation_id: Optional[uuid.UUID] = None,
        action_type: Optional[str] = None,
        unit_code: Optional[str] = None,
        block_tower: Optional[str] = None,
        search_text: Optional[str] = None,
    ):
        """Lista sugestões com suporte a filtros dinâmicos."""
        qs = ConsultationSuggestion.objects.filter(condominium_id=condominium_id)
        if consultation_id:
            qs = qs.filter(consultation_id=consultation_id)
        if action_type and action_type != 'todos':
            qs = qs.filter(action_type=action_type.lower())
        if unit_code:
            qs = qs.filter(unit_code__icontains=unit_code.strip())
        if block_tower:
            qs = qs.filter(block_tower__icontains=block_tower.strip())
        if search_text:
            s = search_text.strip()
            from django.db.models import Q
            qs = qs.filter(
                Q(target_reference__icontains=s) |
                Q(suggestion_text__icontains=s) |
                Q(justification__icontains=s) |
                Q(resident_name__icontains=s) |
                Q(protocol__icontains=s)
            )
        return qs.order_by('-created_at')

    @classmethod
    def export_suggestions_csv(cls, condominium_id: uuid.UUID, consultation_id: uuid.UUID) -> str:
        """
        Exporta todas as sugestões em formato CSV formatado com BOM UTF-8
        para abertura perfeita no Microsoft Excel e Google Sheets.
        """
        consultation = PublicConsultation.objects.select_related('condominium').get(
            id=consultation_id,
            condominium_id=condominium_id
        )
        suggestions = ConsultationSuggestion.objects.filter(
            consultation=consultation,
            condominium_id=condominium_id
        ).order_by('target_reference', 'created_at')

        output = io.StringIO()
        # Escreve BOM UTF-8 para compatibilidade nativa com Excel
        output.write('\ufeff')
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # Cabeçalho
        writer.writerow([
            'Protocolo',
            'Data e Hora',
            'Morador / Condômino',
            'Telefone (WhatsApp)',
            'E-mail',
            'Bloco / Torre',
            'Unidade',
            'Artigo / Dispositivo',
            'Tipo de Ação',
            'Texto Sugerido / Nova Redação',
            'Justificativa',
            'Status',
        ])

        action_labels = {
            'alterar': 'Alterar Redação',
            'remover': 'Remover Dispositivo',
            'incluir': 'Incluir Nova Regra',
        }

        for s in suggestions:
            writer.writerow([
                s.protocol,
                s.created_at.strftime('%d/%m/%Y %H:%M'),
                s.resident_name,
                s.resident_phone,
                s.resident_email or '—',
                s.block_tower or '—',
                s.unit_code,
                s.target_reference,
                action_labels.get(s.action_type, s.action_type.capitalize()),
                s.suggestion_text.replace('\r\n', ' ').replace('\n', ' '),
                (s.justification or '—').replace('\r\n', ' ').replace('\n', ' '),
                s.status.capitalize(),
            ])

        return output.getvalue()
