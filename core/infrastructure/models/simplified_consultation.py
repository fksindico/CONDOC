"""
Modelos ORM Django para Consultas Públicas Simplificadas de Documentos em PDF
Fonte única de DDL: supabase/migrations/20261012000008_simplified_public_consultation.sql
ADR-003: managed = False
"""
import uuid
from django.db import models
from .identity import Condominium, Account


class PublicConsultation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=50, default='regimento')  # 'regimento' ou 'convencao'
    description = models.TextField(null=True, blank=True)
    pdf_file_path = models.CharField(max_length=500)
    pdf_original_name = models.CharField(max_length=255)
    pdf_size_bytes = models.BigIntegerField(default=0)
    public_token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=50, default='aberta')  # 'aberta', 'pausada', 'encerrada'
    deadline = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, db_column='created_by_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."public_consultations'
        verbose_name = 'Consulta Pública Simplificada'
        verbose_name_plural = 'Consultas Públicas Simplificadas'

    def __str__(self):
        return f"{self.title} ({self.status})"


class ConsultationSuggestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    consultation = models.ForeignKey(PublicConsultation, on_delete=models.CASCADE, db_column='consultation_id')
    protocol = models.CharField(max_length=100, unique=True)
    resident_name = models.CharField(max_length=255)
    resident_phone = models.CharField(max_length=50)
    resident_email = models.CharField(max_length=255, null=True, blank=True)
    block_tower = models.CharField(max_length=100, null=True, blank=True)
    unit_code = models.CharField(max_length=50)
    target_reference = models.CharField(max_length=255)
    action_type = models.CharField(max_length=20)  # 'alterar', 'remover', 'incluir'
    suggestion_text = models.TextField()
    justification = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default='recebida')  # 'recebida', 'em_analise', 'destaque', 'arquivada'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."consultation_suggestions'
        verbose_name = 'Sugestão do Morador'
        verbose_name_plural = 'Sugestões dos Moradores'

    def __str__(self):
        return f"{self.protocol} - {self.target_reference} ({self.action_type})"
