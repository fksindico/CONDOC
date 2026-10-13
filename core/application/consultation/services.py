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
from django.db import transaction, models

from infrastructure.models import (
    Condominium,
    Account,
    Building,
    Unit,
    ResidentRegistration,
    PublicConsultation,
    ConsultationSuggestion,
)


class SimplifiedConsultationService:
    @staticmethod
    def generate_token() -> str:
        """Gera um token alfanumérico seguro para URLs públicas de consulta."""
        return secrets.token_urlsafe(16).replace('-', '').replace('_', '')[:20]

    @staticmethod
    def generate_protocol(block_tower: Optional[str] = None, unit_code: Optional[str] = None) -> str:
        """
        Gera protocolo com formato Torre-Apartamento-##### para facilitar a identificação.
        Ex: Torre B-604-84912 ou 604-84912 caso não haja torre informada.
        """
        rand_5 = secrets.randbelow(90000) + 10000  # 5 dígitos (10000 a 99999)
        clean_tower = block_tower.strip() if block_tower else ""
        clean_unit = unit_code.strip() if unit_code else ""

        if clean_tower and clean_unit:
            return f"{clean_tower}-{clean_unit}-{rand_5}"
        elif clean_unit:
            return f"{clean_unit}-{rand_5}"
        elif clean_tower:
            return f"{clean_tower}-{rand_5}"
        else:
            year = timezone.now().year
            return f"SUG-{year}-{rand_5}"

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
        Submissão zero-atrito da sugestão do morador via token público universal.
        Gera protocolo único, organiza o cadastro do morador e impede múltiplos cadastros
        para a mesma pessoa e unidade a cada acesso.
        """
        consultation = PublicConsultation.objects.select_related('condominium').get(public_token=token)

        if consultation.status != 'aberta':
            raise ValueError(f"Esta consulta está com status '{consultation.status}' e não aceita novos envios.")

        # Valida ação
        valid_actions = ('alterar', 'remover', 'incluir')
        normalized_action = action_type.lower().strip()
        if normalized_action not in valid_actions:
            raise ValueError(f"Tipo de ação inválido: {action_type}. Deve ser uma de: alterar, remover, incluir.")

        if not resident_email or not str(resident_email).strip():
            raise ValueError("O e-mail do morador é obrigatório.")

        with transaction.atomic():
            # 1. Normalização de dados
            clean_name = resident_name.strip()
            clean_phone = "".join(filter(str.isdigit, resident_phone))
            clean_email = resident_email.strip().lower()
            clean_unit = unit_code.strip()
            clean_tower = block_tower.strip() if block_tower else None

            # 2. Localiza ou cria a estrutura predial (Building e Unit)
            building = None
            if clean_tower:
                building = Building.objects.filter(
                    condominium=consultation.condominium,
                    status='active'
                ).filter(
                    models.Q(code__iexact=clean_tower) | models.Q(name__iexact=clean_tower)
                ).first()
                if not building:
                    building = Building.objects.create(
                        id=uuid.uuid4(),
                        condominium=consultation.condominium,
                        code=clean_tower[:50].upper(),
                        name=clean_tower[:255],
                        status='active'
                    )

            unit = Unit.objects.filter(
                condominium=consultation.condominium,
                status='active',
                code__iexact=clean_unit
            ).first()

            if not unit:
                unit = Unit.objects.create(
                    id=uuid.uuid4(),
                    condominium=consultation.condominium,
                    building=building,
                    code=clean_unit[:50],
                    status='active'
                )
            elif building and not unit.building_id:
                unit.building = building
                unit.save(update_fields=['building'])

            # 3. Deduplicação inteligente do Morador no Condomínio
            # Evita duplicar cadastros para a mesma pessoa/unidade em acessos subsequentes
            existing_reg = None
            reg_candidates = ResidentRegistration.objects.filter(
                condominium=consultation.condominium,
                unit=unit
            )
            for r in reg_candidates:
                r_phone = "".join(filter(str.isdigit, r.phone_e164 or ""))
                r_email = (r.email or "").strip().lower()
                if (clean_phone and r_phone == clean_phone) or (clean_email and r_email == clean_email):
                    existing_reg = r
                    break
                if r.full_name.strip().lower() == clean_name.lower():
                    existing_reg = r
                    break

            if not existing_reg and clean_phone:
                # Busca pelo telefone no condomínio caso a unidade tenha sido digitada ligeiramente diferente
                existing_reg = ResidentRegistration.objects.filter(
                    condominium=consultation.condominium,
                    phone_e164__icontains=clean_phone[-9:] if len(clean_phone) >= 9 else clean_phone
                ).first()

            if existing_reg:
                # Reutiliza o cadastro existente! Atualiza campos de contato se o novo for mais completo
                changed = False
                if clean_email and existing_reg.email != clean_email:
                    existing_reg.email = clean_email
                    changed = True
                if clean_phone and (not existing_reg.phone_e164 or len(existing_reg.phone_e164) < len(clean_phone)):
                    existing_reg.phone_e164 = clean_phone
                    changed = True
                if clean_name and len(clean_name) > len(existing_reg.full_name):
                    existing_reg.full_name = clean_name
                    changed = True
                if changed:
                    existing_reg.save()
            else:
                # Criação única do registro de morador a partir da sugestão
                ResidentRegistration.objects.create(
                    id=uuid.uuid4(),
                    condominium=consultation.condominium,
                    unit=unit,
                    full_name=clean_name,
                    phone_e164=clean_phone,
                    email=clean_email,
                    relationship='proprietario_residente',
                    source='auto_cadastro',
                    status='ativado',
                    notes=f"Cadastrado automaticamente via participação na consulta '{consultation.title}'"
                )

            # 4. Gera protocolo único e grava a sugestão
            protocol = cls.generate_protocol(clean_tower, clean_unit)
            while ConsultationSuggestion.objects.filter(protocol=protocol).exists():
                protocol = cls.generate_protocol(clean_tower, clean_unit)

            suggestion = ConsultationSuggestion.objects.create(
                condominium=consultation.condominium,
                consultation=consultation,
                protocol=protocol,
                resident_name=clean_name,
                resident_phone=clean_phone if clean_phone else resident_phone.strip(),
                resident_email=clean_email,
                block_tower=clean_tower,
                unit_code=clean_unit,
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
