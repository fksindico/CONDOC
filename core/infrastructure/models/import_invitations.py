"""
Modelos ORM Django — Fase 2: Importação Cadastral e Convites de Acesso (ADR-003)
Todos os modelos possuem managed = False e db_table = 'app.<tabela>'.
A DDL canônica reside em supabase/migrations/20261009000002_phase2_import_invitations.sql.
"""
import uuid
from django.db import models
from .identity import Condominium, Building, Unit, Account, ResidentRegistration, Resident, UnitMembership

class ImportBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, related_name='import_batches')
    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64)
    source_label = models.CharField(max_length=100, default='upload_manual')
    status = models.CharField(
        max_length=50,
        default='received',
        choices=[
            ('received', 'Recebido'),
            ('parsing', 'Processando Estrutura'),
            ('awaiting_mapping', 'Aguardando Mapeamento'),
            ('validating', 'Validando Linhas'),
            ('awaiting_review', 'Aguardando Revisão'),
            ('applying', 'Aplicando Transação'),
            ('completed', 'Concluído'),
            ('failed', 'Falhou'),
            ('cancelled', 'Cancelado'),
        ]
    )
    revision = models.IntegerField(default=1)
    mapping = models.JSONField(default=dict)
    totals = models.JSONField(default=dict)
    error_message = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='created_import_batches')
    confirmed_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_import_batches')
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."import_batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch {self.id} ({self.file_name} - {self.status})"


class ImportRow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name='rows')
    row_number = models.IntegerField()
    raw_data = models.JSONField(default=dict)
    normalized_data = models.JSONField(default=dict)
    classification = models.CharField(
        max_length=50,
        default='nova_pendente',
        choices=[
            ('nova_completa', 'Nova Completa'),
            ('nova_pendente', 'Nova Pendente'),
            ('existente_igual', 'Existente Igual'),
            ('atualizacao_proposta', 'Atualização Proposta'),
            ('vinculo_adicional', 'Vínculo Adicional'),
            ('conflito_identidade', 'Conflito de Identidade'),
            ('unidade_desconhecida', 'Unidade Desconhecida'),
            ('formato_invalido', 'Formato Inválido'),
            ('duplicada_no_arquivo', 'Duplicada no Arquivo'),
        ]
    )
    issues = models.JSONField(default=list)
    selected = models.BooleanField(default=True)
    action = models.CharField(
        max_length=50,
        default='create_registration',
        choices=[
            ('create_registration', 'Criar Pré-cadastro'),
            ('update_registration', 'Atualizar Pré-cadastro'),
            ('add_registration_for_unit', 'Adicionar Vínculo à Unidade'),
            ('skip', 'Ignorar Linha'),
            ('request_manual_review', 'Solicitar Revisão Manual'),
        ]
    )
    target_registration = models.ForeignKey(
        ResidentRegistration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_row_targets'
    )
    target_version = models.IntegerField(null=True, blank=True)
    result_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."import_rows'
        ordering = ['batch_id', 'row_number']
        unique_together = ('batch', 'row_number')

    def __str__(self):
        return f"Row {self.row_number} - Batch {self.batch_id} ({self.classification})"


class AccessInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, related_name='access_invitations')
    campaign_id = models.UUIDField(null=True, blank=True)
    kind = models.CharField(
        max_length=50,
        choices=[
            ('individual_preconferido', 'Individual Pré-conferido'),
            ('individual_padrao', 'Individual Padrão'),
            ('unidade_fixa', 'Unidade Fixa'),
            ('torre_bloco', 'Torre/Bloco'),
            ('amplo', 'Convite Amplo'),
            ('leitura', 'Apenas Leitura'),
        ]
    )
    target_registration = models.ForeignKey(
        ResidentRegistration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_invitations'
    )
    target_unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unit_invitations'
    )
    target_building = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='building_invitations'
    )
    expected_contact = models.CharField(max_length=255, null=True, blank=True)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    max_redemptions = models.IntegerField(default=1)
    redemption_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=50,
        default='ativo',
        choices=[
            ('ativo', 'Ativo'),
            ('expirado', 'Expirado'),
            ('esgotado', 'Esgotado'),
            ('revogado', 'Revogado'),
        ]
    )
    created_by = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='created_invitations')
    revoked_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='revoked_invitations')
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."access_invitations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation {self.id} ({self.kind} - {self.status})"


class InvitationRedemption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(AccessInvitation, on_delete=models.CASCADE, related_name='redemptions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='invitation_redemptions')
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, blank=True, related_name='invitation_redemptions')
    membership = models.ForeignKey(UnitMembership, on_delete=models.SET_NULL, null=True, blank=True, related_name='invitation_redemptions')
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    ip_address_masked = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."invitation_redemptions'
        ordering = ['-redeemed_at']

    def __str__(self):
        return f"Redemption {self.id} (Invitation {self.invitation_id} by Account {self.account_id})"


class DeliveryAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(AccessInvitation, on_delete=models.CASCADE, related_name='delivery_attempts')
    channel = models.CharField(
        max_length=50,
        choices=[
            ('email', 'E-mail'),
            ('manual_link', 'Link Manual'),
            ('qr_code', 'QR Code'),
            ('export', 'Exportação Restrita'),
        ]
    )
    destination_masked = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=50,
        default='nao_enviada',
        choices=[
            ('nao_enviada', 'Não Enviada'),
            ('enfileirada', 'Enfileirada'),
            ('enviada', 'Enviada'),
            ('falhou', 'Falhou'),
        ]
    )
    provider_ref = models.CharField(max_length=255, null=True, blank=True)
    error_code = models.CharField(max_length=100, null=True, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."delivery_attempts'
        ordering = ['-attempted_at']


class IdempotencyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True)
    actor_account_id = models.UUIDField(null=True, blank=True)
    operation = models.CharField(max_length=100)
    key = models.CharField(max_length=255)
    payload_hash = models.CharField(max_length=64)
    response_code = models.IntegerField()
    response_body = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."idempotency_records'
        unique_together = ('tenant_id', 'operation', 'key')

    def __str__(self):
        return f"Idempotency {self.operation}:{self.key} ({self.response_code})"
