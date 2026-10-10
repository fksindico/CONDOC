"""
Modelos ORM para Campanhas de Consulta Pública, Participação e Moderação Editorial — CONDC (Fase 5)
ADR-003: managed = False. O schema SQL em supabase/migrations é a fonte única de DDL.
"""
import uuid
from django.db import models
from .identity import Condominium, Account, Resident, UnitMembership, IdentityAccessEvent
from .documents import Project, DocumentSnapshot, Provision, ProvisionRevision, SourceFile


class ConsultationCampaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id')
    snapshot = models.ForeignKey(DocumentSnapshot, on_delete=models.RESTRICT, db_column='snapshot_id')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=50, default='rascunho')  # rascunho, aberta, pausada, encerrada
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."consultation_campaigns'
        verbose_name = 'Campanha de Consulta Pública'
        verbose_name_plural = 'Campanhas de Consulta Pública'

    def __str__(self):
        return f"{self.name} ({self.state})"


class CampaignParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    campaign = models.ForeignKey(ConsultationCampaign, on_delete=models.CASCADE, db_column='campaign_id')
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, db_column='resident_id')
    reference_membership = models.ForeignKey(UnitMembership, on_delete=models.RESTRICT, db_column='reference_membership_id')
    status = models.CharField(max_length=50, default='habilitado')  # habilitado, suspenso, revogado
    authorized_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, db_column='authorized_by_id')
    authorized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."campaign_participants'
        unique_together = (('campaign', 'resident'),)
        verbose_name = 'Participante da Campanha'
        verbose_name_plural = 'Participantes da Campanha'


class Suggestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_protocol = models.CharField(max_length=50, unique=True)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    campaign = models.ForeignKey(ConsultationCampaign, on_delete=models.CASCADE, db_column='campaign_id')
    participant = models.ForeignKey(CampaignParticipant, on_delete=models.RESTRICT, db_column='participant_id')
    submitted_membership = models.ForeignKey(UnitMembership, on_delete=models.RESTRICT, db_column='submitted_membership_id')
    target_provision = models.ForeignKey(Provision, on_delete=models.SET_NULL, null=True, blank=True, db_column='target_provision_id')
    target_snapshot_revision = models.ForeignKey(ProvisionRevision, on_delete=models.SET_NULL, null=True, blank=True, db_column='target_snapshot_revision_id')
    category = models.CharField(max_length=50, default='redacao')
    analysis_status = models.CharField(max_length=50, default='pendente')  # pendente, em_analise, concluida
    editorial_decision = models.CharField(max_length=50, default='pendente')  # pendente, acolhida, acolhida_parcial, rejeitada, duplicada
    publication_status = models.CharField(max_length=50, default='nao_publicada')  # nao_publicada, publicada, oculta
    incorporation_status = models.CharField(max_length=50, default='nao_incorporada')  # nao_incorporada, incorporada
    parent_published_suggestion = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, db_column='parent_published_suggestion_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."suggestions'
        verbose_name = 'Sugestão'
        verbose_name_plural = 'Sugestões'

    def __str__(self):
        return f"{self.public_protocol} ({self.category})"


class SuggestionRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, db_column='suggestion_id')
    version_number = models.IntegerField(default=1)
    text = models.TextField()
    justification = models.TextField()
    alternative_text = models.TextField(null=True, blank=True)
    author_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, db_column='author_account_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."suggestion_revisions'
        unique_together = (('suggestion', 'version_number'),)
        verbose_name = 'Revisão da Sugestão'
        verbose_name_plural = 'Revisões da Sugestão'


class PublishedSuggestionRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, db_column='suggestion_id')
    suggestion_revision = models.ForeignKey(SuggestionRevision, on_delete=models.CASCADE, db_column='suggestion_revision_id')
    sanitized_public_text = models.TextField()
    sanitized_justification = models.TextField()
    authorized_by = models.ForeignKey(Account, on_delete=models.RESTRICT, db_column='authorized_by_id')
    authorized_at = models.DateTimeField(auto_now_add=True)
    hidden_at = models.DateTimeField(null=True, blank=True)
    hidden_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='hidden_suggestions', db_column='hidden_by_id')
    hide_reason = models.TextField(null=True, blank=True)
    is_active_publication = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."published_suggestion_revisions'
        verbose_name = 'Revisão Publicada da Sugestão'
        verbose_name_plural = 'Revisões Publicadas da Sugestão'


class SuggestionEditorialDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, db_column='suggestion_id')
    decision = models.CharField(max_length=50)  # acolhida, acolhida_parcial, rejeitada, duplicada
    public_shared_reason = models.TextField()
    internal_note = models.TextField(null=True, blank=True)
    decided_by = models.ForeignKey(Account, on_delete=models.RESTRICT, db_column='decided_by_id')
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."suggestion_editorial_decisions'
        verbose_name = 'Decisão Editorial da Sugestão'
        verbose_name_plural = 'Decisões Editoriais da Sugestão'


class SuggestionAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, db_column='suggestion_id')
    source_file = models.ForeignKey(SourceFile, on_delete=models.CASCADE, db_column='source_file_id')
    is_publicly_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, db_column='approved_by_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."suggestion_attachments'
        verbose_name = 'Anexo de Sugestão'
        verbose_name_plural = 'Anexos de Sugestão'
