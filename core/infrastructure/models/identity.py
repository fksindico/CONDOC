"""
Modelos ORM de Identidade e Multi-tenancy — CONDC (Fase 1)
ADR-003: managed = False. O schema SQL em supabase/migrations é a fonte única de DDL.
"""
import uuid
from django.db import models

class Condominium(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, null=True, blank=True)
    status = models.CharField(max_length=50, default='active')
    timezone = models.CharField(max_length=50, default='America/Sao_Paulo')
    address_street = models.CharField(max_length=255, null=True, blank=True)
    address_number = models.CharField(max_length=50, null=True, blank=True)
    address_complement = models.CharField(max_length=255, null=True, blank=True)
    address_neighborhood = models.CharField(max_length=100, null=True, blank=True)
    address_city = models.CharField(max_length=100, null=True, blank=True)
    address_state = models.CharField(max_length=2, null=True, blank=True)
    address_zip_code = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."condominiums'
        verbose_name = 'Condomínio'
        verbose_name_plural = 'Condomínios'

    def __str__(self):
        return self.name


class Building(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=50, default='tower')
    display_order = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."buildings'
        verbose_name = 'Prédio/Bloco'
        verbose_name_plural = 'Prédios/Blocos'

    def __str__(self):
        return f"{self.name} ({self.code})"


class Unit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True, db_column='building_id')
    code = models.CharField(max_length=50)
    floor_label = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    ideal_fraction = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    block = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."units'
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'

    def __str__(self):
        return f"Unidade {self.code}"


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth_user_id = models.UUIDField(unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, default='active')
    is_active = models.BooleanField(default=True)
    mfa_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."accounts'
        verbose_name = 'Conta de Usuário'
        verbose_name_plural = 'Contas de Usuário'

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class ResidentRegistration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, db_column='unit_id')
    full_name = models.CharField(max_length=255)
    phone_e164 = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    relationship = models.CharField(max_length=50)
    source = models.CharField(max_length=50, default='manual')
    external_reference = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, default='pendente')
    preverified_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, db_column='preverified_by')
    preverified_at = models.DateTimeField(null=True, blank=True)
    linked_resident_id = models.UUIDField(null=True, blank=True)
    linked_membership_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."resident_registrations'
        verbose_name = 'Pré-cadastro de Morador'
        verbose_name_plural = 'Pré-cadastros de Moradores'


class Resident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, db_column='account_id')
    full_name = models.CharField(max_length=255)
    phone_e164 = models.CharField(max_length=30, null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."residents'
        verbose_name = 'Morador'
        verbose_name_plural = 'Moradores'


class UnitMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, db_column='resident_id')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, db_column='unit_id')
    category = models.CharField(max_length=50)
    verification_status = models.CharField(max_length=50, default='pendente')
    membership_status = models.CharField(max_length=50, default='active')
    verification_method = models.CharField(max_length=50, null=True, blank=True)
    reviewed_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, db_column='reviewed_by')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_reason = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."unit_memberships'
        verbose_name = 'Vínculo de Unidade'
        verbose_name_plural = 'Vínculos de Unidade'


class MembershipVerificationEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    membership = models.ForeignKey(UnitMembership, on_delete=models.CASCADE, db_column='membership_id')
    previous_status = models.CharField(max_length=50, null=True, blank=True)
    new_status = models.CharField(max_length=50)
    method = models.CharField(max_length=50)
    reason = models.TextField()
    actor_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, db_column='actor_account_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."membership_verification_events'
        verbose_name = 'Evento de Verificação de Vínculo'
        verbose_name_plural = 'Eventos de Verificação de Vínculo'


class RoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, db_column='account_id')
    role = models.CharField(max_length=50)
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'app"."role_assignments'
        verbose_name = 'Atribuição de Papel'
        verbose_name_plural = 'Atribuições de Papel'


class PermissionGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id')
    role_assignment = models.ForeignKey(RoleAssignment, on_delete=models.CASCADE, db_column='role_assignment_id')
    permission = models.CharField(max_length=100)
    scope = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."permission_grants'


class CoreSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_token_hash = models.CharField(max_length=64, unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, db_column='account_id')
    active_condominium = models.ForeignKey(Condominium, on_delete=models.SET_NULL, null=True, blank=True, db_column='active_condominium_id')
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."core_sessions'


class IdentityAccessEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominium = models.ForeignKey(Condominium, on_delete=models.CASCADE, db_column='condominium_id', null=True, blank=True)
    actor_account = models.ForeignKey(Account, on_delete=models.CASCADE, db_column='actor_account_id')
    target_type = models.CharField(max_length=50)
    target_id = models.UUIDField()
    purpose = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'app"."identity_access_events'
