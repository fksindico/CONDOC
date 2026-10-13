"""
Serviços de Aplicação de Identidade e Multi-tenancy — CONDC (Fase 1)
Orquestração transacional de casos de uso respeitando isolamento RLS e invariantes.
"""
import uuid
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    ResidentRegistration,
    Resident,
    UnitMembership,
    MembershipVerificationEvent,
    RoleAssignment,
    IdentityAccessEvent,
)
from domain.identity.invariants import (
    assert_no_electoral_intent,
    assert_same_tenant,
    assert_audit_purpose,
    assert_sindico_publication_authority,
    assert_unique_building_code,
    assert_unique_unit_code,
)
from domain.identity.exceptions import (
    DomainError,
    TenantMismatchError,
    InvalidMembershipStatusError,
    DuplicateBuildingError,
    DuplicateUnitError,
)

class CondominiumService:
    @staticmethod
    def create_condominium(name: str, cnpj: Optional[str] = None, timezone: str = 'America/Sao_Paulo', **address_kwargs) -> Condominium:
        assert_no_electoral_intent(name)
        return Condominium.objects.create(
            name=name,
            cnpj=cnpj,
            timezone=timezone,
            **address_kwargs
        )

    @staticmethod
    def update_condominium(condominium_id: uuid.UUID, **fields) -> Condominium:
        condo = Condominium.objects.get(id=condominium_id)
        if 'name' in fields and fields['name']:
            assert_no_electoral_intent(fields['name'])
        for key, value in fields.items():
            if hasattr(condo, key):
                setattr(condo, key, value)
        condo.save()
        return condo

    @staticmethod
    def archive_condominium(condominium_id: uuid.UUID) -> Condominium:
        condo = Condominium.objects.get(id=condominium_id)
        condo.status = 'archived'
        condo.save()
        return condo

    @staticmethod
    def reactivate_condominium(condominium_id: uuid.UUID) -> Condominium:
        condo = Condominium.objects.get(id=condominium_id)
        condo.status = 'active'
        condo.save()
        return condo

    @staticmethod
    def purge_condominium(condominium_id: uuid.UUID) -> None:
        """
        Saneamento / Expurgo Definitivo de Condomínio:
        Exclui permanentemente o condomínio arquivado e seus registros em cascata.
        Regra mandatória: O condomínio DEVE estar previamente arquivado ou inativo.
        """
        condo = Condominium.objects.get(id=condominium_id)
        if condo.status not in ('archived', 'inactive'):
            raise DomainError(
                "Apenas condomínios previamente arquivados ou inativos podem ser excluídos definitivamente no saneamento."
            )
        condo.delete()

    @staticmethod
    def purge_building(condominium_id: uuid.UUID, building_id: uuid.UUID) -> None:
        """
        Saneamento / Expurgo Definitivo de Torre/Bloco:
        Exclui permanentemente a torre arquivada/inativa se não possuir unidades ativas vinculadas.
        """
        building = Building.objects.get(id=building_id, condominium_id=condominium_id)
        if building.status not in ('inactive', 'archived'):
            raise DomainError(
                "Apenas torres/blocos previamente inativados podem ser excluídos definitivamente no saneamento."
            )
        if Unit.objects.filter(building_id=building.id, status='active').exists():
            raise DomainError(
                "Não é possível excluir definitivamente uma torre que ainda possui unidades ativas vinculadas."
            )
        building.delete()

    @staticmethod
    def purge_unit(condominium_id: uuid.UUID, unit_id: uuid.UUID) -> None:
        """
        Saneamento / Expurgo Definitivo de Unidade Autônoma:
        Exclui permanentemente a unidade arquivada/inativa se não possuir vínculos de moradores ativos.
        """
        unit = Unit.objects.get(id=unit_id, condominium_id=condominium_id)
        if unit.status not in ('inactive', 'archived'):
            raise DomainError(
                "Apenas unidades previamente inativadas podem ser excluídas definitivamente no saneamento."
            )
        if UnitMembership.objects.filter(unit_id=unit.id, membership_status='active').exists():
            raise DomainError(
                "Não é possível excluir definitivamente uma unidade que ainda possui vínculos de moradores ativos."
            )
        unit.delete()


    @staticmethod
    def create_building(condominium_id: uuid.UUID, code: str, name: str, kind: str = 'tower', display_order: int = 0) -> Building:
        if not Condominium.objects.filter(id=condominium_id).exists():
            raise DomainError("Condomínio não encontrado.")
        if Building.objects.filter(condominium_id=condominium_id, code=code).exists():
            raise DuplicateBuildingError(f"Torre/Bloco com código '{code}' já existe neste condomínio.")
        return Building.objects.create(
            condominium_id=condominium_id,
            code=code,
            name=name,
            kind=kind,
            display_order=display_order
        )

    @staticmethod
    def update_building(building_id: uuid.UUID, **fields) -> Building:
        building = Building.objects.get(id=building_id)
        new_code = fields.get('code')
        if new_code is not None and new_code != building.code:
            if Building.objects.filter(condominium_id=building.condominium_id, code=new_code).exclude(id=building.id).exists():
                raise DuplicateBuildingError(f"Torre/Bloco com código '{new_code}' já existe neste condomínio.")
        for key, value in fields.items():
            if hasattr(building, key):
                setattr(building, key, value)
        building.save()
        return building

    @staticmethod
    def create_unit(condominium_id: uuid.UUID, code: str, building_id: Optional[uuid.UUID] = None, ideal_fraction: Optional[float] = None, **kwargs) -> Unit:
        if not Condominium.objects.filter(id=condominium_id).exists():
            raise DomainError("Condomínio não encontrado.")
        if building_id:
            try:
                building = Building.objects.get(id=building_id)
            except Building.DoesNotExist:
                raise DomainError("Torre/Bloco não encontrada.")
            assert_same_tenant(condominium_id, building.condominium_id, "Prédio/Bloco")

        if Unit.objects.filter(condominium_id=condominium_id, building_id=building_id, code=code).exists():
            raise DuplicateUnitError(f"Unidade com código '{code}' já existe para esta torre/condomínio.")

        return Unit.objects.create(
            condominium_id=condominium_id,
            building_id=building_id,
            code=code,
            ideal_fraction=ideal_fraction,
            **kwargs
        )

    @staticmethod
    def update_unit(unit_id: uuid.UUID, **fields) -> Unit:
        unit = Unit.objects.get(id=unit_id)
        new_code = fields.get('code', unit.code)
        
        if 'building_id' in fields:
            bid = fields['building_id']
            if bid in ('', 'null', None):
                fields['building_id'] = None
                new_building_id = None
            else:
                new_building_id = bid
                target_building = Building.objects.get(id=bid)
                assert_same_tenant(unit.condominium_id, target_building.condominium_id, "Prédio/Bloco")
        else:
            new_building_id = unit.building_id

        code_changed = 'code' in fields and fields['code'] != unit.code
        building_changed = 'building_id' in fields and fields['building_id'] != unit.building_id

        if code_changed or building_changed:
            if Unit.objects.filter(
                condominium_id=unit.condominium_id,
                building_id=new_building_id,
                code=new_code
            ).exclude(id=unit.id).exists():
                raise DuplicateUnitError(f"Unidade com código '{new_code}' já existe para esta torre/condomínio.")

        for key, value in fields.items():
            if key == 'building_id':
                unit.building_id = value
            elif hasattr(unit, key):
                setattr(unit, key, value)
        unit.save()
        return unit

    @staticmethod
    def batch_generate_units(
        condominium_id: uuid.UUID,
        building_id: Optional[uuid.UUID] = None,
        new_building_name: Optional[str] = None,
        new_building_code: Optional[str] = None,
        start_floor: int = 1,
        end_floor: int = 10,
        units_per_floor: int = 4,
        suffix_digits: int = 2,
        custom_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gera em lote torres e apartamentos para o condomínio.
        Exemplo:
            Torre A, início 3º andar, término 15º andar, 6 apartamentos por andar.
            Resultará em: 301..306, 401..406, ..., 1501..1506.
        """
        condo = Condominium.objects.get(id=condominium_id)

        if start_floor > end_floor:
            raise DomainError("O andar inicial não pode ser maior que o andar final.")
        if units_per_floor <= 0 or units_per_floor > 50:
            raise DomainError("A quantidade de apartamentos por andar deve ser entre 1 e 50.")
        if (end_floor - start_floor + 1) > 100:
            raise DomainError("O intervalo de andares não pode exceder 100 andares.")

        with transaction.atomic():
            building = None
            if building_id:
                building = Building.objects.get(id=building_id, condominium=condo)
            elif new_building_name and new_building_name.strip():
                b_name = new_building_name.strip()
                b_code = (new_building_code or b_name).strip()[:50].upper()
                building, _ = Building.objects.get_or_create(
                    condominium=condo,
                    code=b_code,
                    defaults={"name": b_name, "status": "active"}
                )

            created_units = []
            existing_units = []
            all_codes = []

            for floor in range(start_floor, end_floor + 1):
                floor_label = "Térreo" if floor == 0 else f"{floor}º Andar"
                for u_idx in range(1, units_per_floor + 1):
                    if suffix_digits == 2:
                        suffix_str = f"{u_idx:02d}"
                    else:
                        suffix_str = str(u_idx)

                    if custom_prefix:
                        unit_code = f"{custom_prefix}{floor}{suffix_str}"
                    else:
                        unit_code = f"{floor}{suffix_str}"

                    all_codes.append(unit_code)

                    # Verifica se já existe para este condomínio e prédio
                    existing = Unit.objects.filter(
                        condominium=condo,
                        building=building,
                        code=unit_code
                    ).first()

                    if existing:
                        if existing.status != 'active':
                            existing.status = 'active'
                            existing.save(update_fields=['status'])
                        existing_units.append(unit_code)
                    else:
                        Unit.objects.create(
                            id=uuid.uuid4(),
                            condominium=condo,
                            building=building,
                            code=unit_code,
                            floor_label=floor_label,
                            status='active'
                        )
                        created_units.append(unit_code)

            return {
                "building": {
                    "id": str(building.id) if building else None,
                    "name": building.name if building else None,
                    "code": building.code if building else None,
                } if building else None,
                "created_count": len(created_units),
                "existing_count": len(existing_units),
                "total_units": len(all_codes),
                "start_floor": start_floor,
                "end_floor": end_floor,
                "units_per_floor": units_per_floor,
                "sample_codes": all_codes[:12],
            }



class ResidentRegistrationService:
    """
    CA-02: Cadastro manual cria registro prévio SEM credencial ou conta automática.
    """
    @staticmethod
    def create_manual_registration(
        condominium_id: uuid.UUID,
        unit_id: uuid.UUID,
        full_name: str,
        relationship: str,
        phone_e164: Optional[str] = None,
        email: Optional[str] = None,
        notes: Optional[str] = None,
        preverified_by: Optional[uuid.UUID] = None,
    ) -> ResidentRegistration:
        unit = unit_id if isinstance(unit_id, Unit) else Unit.objects.get(id=unit_id)
        assert_same_tenant(condominium_id, unit.condominium_id, "Unidade")

        return ResidentRegistration.objects.create(
            condominium_id=condominium_id,
            unit=unit,
            full_name=full_name,
            relationship=relationship,
            phone_e164=phone_e164,
            email=email,
            source='manual',
            status='pendente',
            notes=notes,
            preverified_by_id=preverified_by
        )

    @staticmethod
    def update_registration(
        condominium_id: uuid.UUID,
        registration_id: uuid.UUID,
        **fields
    ) -> ResidentRegistration:
        reg = ResidentRegistration.objects.select_related('unit').get(
            id=registration_id,
            condominium_id=condominium_id
        )
        if 'unit_id' in fields and fields['unit_id']:
            unit = Unit.objects.get(id=fields['unit_id'])
            assert_same_tenant(condominium_id, unit.condominium_id, "Unidade")
            reg.unit = unit
        if 'full_name' in fields and fields['full_name']:
            reg.full_name = fields['full_name'].strip()
        if 'phone_e164' in fields:
            reg.phone_e164 = fields['phone_e164'].strip() if fields['phone_e164'] else None
        if 'email' in fields:
            reg.email = fields['email'].strip() if fields['email'] else None
        if 'relationship' in fields and fields['relationship']:
            reg.relationship = fields['relationship']
        if 'status' in fields and fields['status']:
            reg.status = fields['status']
        if 'notes' in fields:
            reg.notes = fields['notes']
        reg.save()
        return reg

    @staticmethod
    def delete_registration(
        condominium_id: uuid.UUID,
        registration_id: uuid.UUID
    ) -> None:
        reg = ResidentRegistration.objects.get(
            id=registration_id,
            condominium_id=condominium_id
        )
        reg.delete()


class MembershipVerificationService:
    """
    CA-12, CA-15: Validação auditada documental de vínculo.
    Confirmação de e-mail/telefone NÃO valida residência.
    """
    VALID_STATUSES = {'pendente', 'em_analise', 'validado', 'recusado', 'revogado'}

    @classmethod
    @transaction.atomic
    def verify_membership(
        cls,
        condominium_id: uuid.UUID,
        membership_id: uuid.UUID,
        new_status: str,
        method: str,
        reason: str,
        actor_account_id: uuid.UUID
    ) -> UnitMembership:
        if new_status not in cls.VALID_STATUSES:
            raise InvalidMembershipStatusError(f"Status '{new_status}' inválido para verificação de vínculo.")

        membership = UnitMembership.objects.select_for_update().get(id=membership_id)
        assert_same_tenant(condominium_id, membership.condominium_id, "Vínculo de Unidade")

        previous_status = membership.verification_status
        membership.verification_status = new_status
        membership.verification_method = method
        membership.reviewed_by_id = actor_account_id
        membership.reviewed_at = timezone.now()
        membership.review_reason = reason

        if new_status in ('recusado', 'revogado'):
            membership.membership_status = 'ended'
            membership.ended_at = timezone.now()
        elif new_status == 'validado':
            membership.membership_status = 'active'

        membership.save()

        # Criação mandatória do evento imutável de auditoria documental
        MembershipVerificationEvent.objects.create(
            condominium_id=condominium_id,
            membership_id=membership.id,
            previous_status=previous_status,
            new_status=new_status,
            method=method,
            reason=reason,
            actor_account_id=actor_account_id
        )

        return membership


class UnitMembershipService:
    @staticmethod
    def update_membership(
        condominium_id: uuid.UUID,
        membership_id: uuid.UUID,
        **fields
    ) -> UnitMembership:
        membership = UnitMembership.objects.select_related('resident', 'unit').get(
            id=membership_id,
            condominium_id=condominium_id
        )
        if 'category' in fields and fields['category']:
            membership.category = fields['category']
        if 'membership_status' in fields and fields['membership_status']:
            membership.membership_status = fields['membership_status']
        if 'verification_status' in fields and fields['verification_status']:
            membership.verification_status = fields['verification_status']

        resident = membership.resident
        if resident:
            if 'resident_name' in fields and fields['resident_name']:
                resident.full_name = fields['resident_name']
            if 'phone_e164' in fields:
                resident.phone_e164 = fields['phone_e164']
            resident.save()

        membership.save()
        return membership

    @staticmethod
    def delete_membership(
        condominium_id: uuid.UUID,
        membership_id: uuid.UUID,
        actor_account_id: Optional[uuid.UUID] = None
    ) -> UnitMembership:
        membership = UnitMembership.objects.get(
            id=membership_id,
            condominium_id=condominium_id
        )
        prev_status = membership.verification_status
        membership.membership_status = 'ended'
        membership.verification_status = 'revogado'
        membership.ended_at = timezone.now()
        membership.save()

        if actor_account_id:
            MembershipVerificationEvent.objects.create(
                condominium_id=condominium_id,
                membership_id=membership.id,
                previous_status=prev_status,
                new_status='revogado',
                method='administrativo',
                reason='Revogação/Exclusão de vínculo realizada pelo síndico ou gestor.',
                actor_account_id=actor_account_id
            )
        return membership

    @staticmethod
    def purge_membership(
        condominium_id: uuid.UUID,
        membership_id: uuid.UUID,
    ) -> None:
        """
        Saneamento / Expurgo Definitivo de Vínculo de Morador:
        Exclui permanentemente o vínculo se já estiver encerrado, inativo ou revogado.
        """
        membership = UnitMembership.objects.get(
            id=membership_id,
            condominium_id=condominium_id
        )
        if membership.membership_status == 'active' and membership.verification_status not in ('revogado', 'recusado'):
            raise DomainError(
                "Apenas vínculos de moradores previamente encerrados, desativados ou revogados podem ser excluídos definitivamente no saneamento."
            )
        membership.delete()



class RoleService:
    @staticmethod
    def assign_role(
        condominium_id: uuid.UUID,
        account_id: uuid.UUID,
        role: str,
        valid_until: Optional[Any] = None
    ) -> RoleAssignment:
        assert_no_electoral_intent(role)
        return RoleAssignment.objects.create(
            condominium_id=condominium_id,
            account_id=account_id,
            role=role.lower(),
            valid_until=valid_until,
            status='active'
        )

    @staticmethod
    def list_roles_for_account(condominium_id: uuid.UUID, account_id: uuid.UUID) -> List[str]:
        now = timezone.now()
        assignments = RoleAssignment.objects.filter(
            condominium_id=condominium_id,
            account_id=account_id,
            status='active'
        )
        active_roles = []
        for a in assignments:
            if a.valid_until is None or a.valid_until > now:
                active_roles.append(a.role)
        return active_roles


class IdentityAuditService:
    """
    CA-33: Toda visualização ou exportação de dados de identificação pessoal exige justificativa e auditoria.
    """
    @staticmethod
    def log_access(
        actor_account_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        purpose: str,
        condominium_id: Optional[uuid.UUID] = None
    ) -> IdentityAccessEvent:
        assert_audit_purpose(purpose)
        return IdentityAccessEvent.objects.create(
            condominium_id=condominium_id,
            actor_account_id=actor_account_id,
            target_type=target_type,
            target_id=target_id,
            purpose=purpose.strip()
        )

    @staticmethod
    def list_access_events(condominium_id: uuid.UUID, limit: int = 50) -> List[IdentityAccessEvent]:
        return list(
            IdentityAccessEvent.objects.filter(condominium_id=condominium_id)
            .select_related('actor_account')
            .order_by('-created_at')[:limit]
        )
