"""
Views da API v1 — CONDC
Controladores REST para Identidade, Estrutura Física, Importação Cadastral e Convites de Acesso.
Compatível com PRD Mestre v3.0 e Contrato_API_v3.md.
"""
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.renderers import BaseRenderer, JSONRenderer
from django.http import HttpResponse, FileResponse, Http404
from django.utils import timezone
from django.conf import settings
from django.db import models
import os
import uuid

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    ResidentRegistration,
    Resident,
    UnitMembership,
    RoleAssignment,
    ImportBatch,
    ImportRow,
    AccessInvitation,
    Project,
    Document,
    SourceFile,
    SourceTranscription,
    SourceProvision,
    Provision,
    ProvisionRevision,
    InternalNote,
    DocumentSnapshot,
    SnapshotItem,
    OriginMapping,
    CrossReference,
    ConsultationCampaign,
    CampaignParticipant,
    Suggestion,
    SuggestionRevision,
    PublishedSuggestionRevision,
    SuggestionEditorialDecision,
    SuggestionAttachment,
    ConsultativeAgreement,
    AgreementEvent,
    SuggestionIncorporation,
    ConsultationSnapshot,
    ExportArtifact,
    PublicConsultation,
    ConsultationSuggestion,
)
from application.identity.services import (
    CondominiumService,
    ResidentRegistrationService,
    MembershipVerificationService,
    UnitMembershipService,
    RoleService,
    IdentityAuditService,
)
from application.imports.services import ImportService
from application.invitations.services import InvitationService
from application.documents.services import (
    ProjectService,
    DocumentService,
    SourceFileService,
    TranscriptionService,
    ProvisionService,
    InternalNoteService,
    SnapshotService,
)
from application.documents.canonical_export_service import CanonicalExportService
from application.comparison.services import (
    OriginMappingService,
    ComparisonService,
    CrossReferenceService,
    RenumberingService,
    ExportService,
)
from application.moderation.services import (
    CampaignService,
    SuggestionService,
    ModerationService,
)
from application.agreements.services import (
    AgreementService,
    IncorporationService,
)
from application.preservation.services import PreservationService
from application.consultation.services import SimplifiedConsultationService
from domain.identity.exceptions import (
    DuplicateBuildingError,
    DuplicateUnitError,
    TenantMismatchError,
    DomainError,
)
from application.common.idempotency import IdempotencyService
from domain.imports.exceptions import (
    ImportPreviewOutdatedError,
    UnresolvedConflictError,
    FormulaInjectionDetectedError,
    InvalidImportFileError,
    UnknownUnitError,
    IdempotencyConflictError,
)
from domain.invitations.exceptions import (
    InvitationExpiredOrExhaustedError,
    InvitationRevokedError,
    InvalidExpectedContactError,
    InvitationRedemptionForbiddenError,
)
from domain.documents.exceptions import (
    CircularReferenceError,
    ConcurrencyConflictError,
    SnapshotImmutableError,
    PrivateNoteAccessForbiddenError,
)
from domain.comparison.exceptions import (
    FictitiousOriginError,
    ExcludedProvisionInCleanExportError,
    InvalidOriginMappingError,
    BrokenCrossReferenceError,
    RenumberingError,
    CleanExportIntegrityError,
)
from domain.moderation.exceptions import (
    CampaignNotOpenError,
    ParticipantNotEligibleError,
    UnauthorizedPublicationError,
    AutoPublicationForbiddenError,
    HiddenSuggestionAccessError,
    IdentityAccessWithoutJustificationError,
    PrivateNoteExposureError,
    AttachmentNotApprovedError,
    ComplementWithoutParentError,
)
from domain.agreements.exceptions import (
    CampaignClosedForAgreementsError,
    AuthorCannotAgreeWithOwnSuggestionError,
    ElectoralVocabularyForbiddenError,
    SubstantialChangeAgreementTransferForbiddenError,
    IncorporationIntegrityError,
)
from domain.preservation.exceptions import (
    PublicExportExposureError,
    ManifestIntegrityError,
    ElectoralDeliberationForbiddenError,
)
from .serializers import (
    CondominiumSerializer,
    BuildingSerializer,
    UnitSerializer,
    ResidentRegistrationCreateSerializer,
    UnitMembershipListSerializer,
    VerifyMembershipActionSerializer,
    RoleAssignmentSerializer,
    ImportBatchSerializer,
    ImportRowSerializer,
    ImportRowActionSerializer,
    ImportConfirmActionSerializer,
    AccessInvitationCreateSerializer,
    AccessInvitationListSerializer,
    InvitationRevokeActionSerializer,
    InvitationRedeemActionSerializer,
    ProjectSerializer,
    DocumentSerializer,
    SourceFileSerializer,
    SourceTranscriptionSerializer,
    TranscriptionConfirmActionSerializer,
    TranscriptionCorrectActionSerializer,
    ProvisionCreateSerializer,
    ProvisionUpdateSerializer,
    InternalNoteSerializer,
    DocumentSnapshotCreateSerializer,
    OriginMappingSerializer,
    OriginMappingCreateSerializer,
    CrossReferenceSerializer,
    CrossReferenceCreateSerializer,
    RenumberingApplySerializer,
    ConsultationCampaignSerializer,
    ConsultationCampaignCreateSerializer,
    CampaignParticipantSerializer,
    CampaignParticipantCreateSerializer,
    SuggestionCreateSerializer,
    SuggestionComplementCreateSerializer,
    SuggestionUpdateSerializer,
    TechnicalAnalysisActionSerializer,
    EditorialDecisionActionSerializer,
    PublicationAuthorizeActionSerializer,
    PublicationHideActionSerializer,
    IdentityAccessActionSerializer,
    ConsultativeAgreementCreateSerializer,
    ConsultativeAgreementSerializer,
    AgreementWithdrawSerializer,
    SuggestionIncorporationCreateSerializer,
    SuggestionIncorporationSerializer,
    ConsultationSnapshotSerializer,
    ExportArtifactSerializer,
    ManifestVerificationSerializer,
    IdentityAccessEventSerializer,
    PublicConsultationDetailSerializer,
    PublicSuggestionSubmitSerializer,
    PublicConsultationSuggestionConfirmationSerializer,
    AdminConsultationListCreateSerializer,
    AdminConsultationSuggestionListSerializer,
)

# ============================================================================
# FASE 1: SESSÃO E IDENTIDADE
# ============================================================================

def _resolve_actor_and_role(request, condominium_id=None):
    """
    Resolve o actor_id e o papel ativo (role) a partir da sessão segura BFF ou credencial autenticada.
    Não assume 'sindico' por padrão em ausência de papel comprovado.
    """
    actor_id = getattr(request.user, 'account_id', None)
    user_roles = getattr(request.user, 'roles', [])
    user_role = None

    if user_roles:
        user_role = 'sindico' if 'sindico' in user_roles else user_roles[0]

    # Se não autenticado via request.user, tenta sessão HTTP
    if not actor_id and hasattr(request, 'session'):
        actor_id = request.session.get('account_id')
        session_roles = request.session.get('roles', [])
        if session_roles and not user_role:
            user_role = 'sindico' if 'sindico' in session_roles else session_roles[0]

    # Se for informado explicitamente via header ou query param (ex.: testes negativos ?role=comissao)
    override_role = request.headers.get('X-User-Role') or request.query_params.get('role')
    if override_role:
        user_role = override_role

    # Em dados de requisição (compatibilidade)
    if not actor_id and hasattr(request, 'data') and isinstance(request.data, dict):
        actor_id = request.data.get('actor_account_id')

    # Se houver actor_id e condomínio mas não tivermos user_role determinado, busca RoleAssignment no banco
    if actor_id and condominium_id and not user_role:
        try:
            role_obj = RoleAssignment.objects.filter(
                condominium_id=condominium_id,
                account_id=actor_id,
                status='active'
            ).first()
            if role_obj:
                user_role = role_obj.role
        except Exception:
            pass

    # Fallback seguro para ambiente de desenvolvimento/teste automatizado
    if not actor_id:
        from django.conf import settings
        if getattr(settings, 'TESTING', False) or getattr(settings, 'DEBUG', False):
            acc = Account.objects.first()
            if acc:
                actor_id = acc.id
                if condominium_id and not user_role:
                    try:
                        role_obj = RoleAssignment.objects.filter(
                            condominium_id=condominium_id,
                            account_id=actor_id,
                            status='active'
                        ).first()
                        user_role = role_obj.role if role_obj else 'morador'
                    except Exception:
                        pass

    return actor_id, user_role


def _get_or_create_actor_id(request, condominium_id=None):
    actor_id, _ = _resolve_actor_and_role(request, condominium_id)
    return actor_id


class SessionInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not getattr(request.user, "is_authenticated", False):
            return Response(
                {
                    "authenticated": False,
                    "account": None,
                },
                status=status.HTTP_200_OK
            )

        return Response({
            "authenticated": True,
            "account": {
                "account_id": getattr(request.user, "account_id", None),
                "full_name": getattr(request.user, "full_name", ""),
                "email": getattr(request.user, "email", ""),
                "tenant_id": getattr(request.user, "tenant_id", None),
                "roles": getattr(request.user, "roles", []),
            }
        })


class LoginView(APIView):
    """
    Autenticação BFF de Sessão (ADR-002, PRD Mestre v3.0 Seção 21).
    Valida a conta, resolve papéis ativos no condomínio e popula request.session.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        condominium_id = request.data.get('condominium_id')

        if not email:
            return Response({"error": "E-mail obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        account = Account.objects.filter(email__iexact=email).first()
        if not account:
            return Response({"error": "Conta não encontrada para o e-mail informado."}, status=status.HTTP_404_NOT_FOUND)

        if not account.is_active or getattr(account, 'status', 'active') != 'active':
            return Response({"error": "Conta inativa ou suspensa."}, status=status.HTTP_403_FORBIDDEN)

        # Determina o condomínio ativo
        condo = None
        if condominium_id:
            try:
                condo = Condominium.objects.filter(id=condominium_id).first()
            except Exception:
                pass

        if not condo:
            # Busca primeiro papel associado à conta
            role_obj = RoleAssignment.objects.filter(account=account, status='active').first()
            if role_obj:
                condo = role_obj.condominium
            else:
                # Busca se tem vínculo como morador/residente
                res = Resident.objects.filter(account=account).first()
                if res:
                    condo = res.condominium
                else:
                    condo = Condominium.objects.first()

        tenant_id = str(condo.id) if condo else None

        # Busca papéis da conta no condomínio selecionado
        roles = []
        if condo:
            role_objs = RoleAssignment.objects.filter(
                condominium=condo,
                account=account,
                status='active'
            )
            roles = [r.role.lower() for r in role_objs]

        # Se a conta for residente, garante o papel 'morador'
        if condo and Resident.objects.filter(condominium=condo, account=account).exists():
            if 'morador' not in roles:
                roles.append('morador')

        if not roles:
            roles = ['morador']

        # Popula a sessão do Django para o BFFSessionAuthentication
        request.session['account_id'] = str(account.id)
        request.session['email'] = account.email
        request.session['full_name'] = account.full_name
        request.session['tenant_id'] = tenant_id
        request.session['roles'] = roles
        request.session.modified = True

        return Response({
            "authenticated": True,
            "account": {
                "account_id": str(account.id),
                "full_name": account.full_name,
                "email": account.email,
                "tenant_id": tenant_id,
                "roles": roles,
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Encerra a sessão BFF e expira o cookie no navegador."""
    permission_classes = [AllowAny]

    def post(self, request):
        request.session.flush()
        return Response({
            "authenticated": False,
            "account": None
        }, status=status.HTTP_200_OK)


class CondominiumListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        status_param = request.query_params.get('status')
        if status_param == 'all':
            condos = Condominium.objects.all().order_by('name')
        elif status_param:
            condos = Condominium.objects.filter(status=status_param).order_by('name')
        else:
            condos = Condominium.objects.all().order_by('name')
        serializer = CondominiumSerializer(condos, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CondominiumSerializer(data=request.data)
        if serializer.is_valid():
            condo = CondominiumService.create_condominium(**serializer.validated_data)
            return Response(CondominiumSerializer(condo).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BuildingListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        if not Condominium.objects.filter(id=condominium_id).exists():
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        status_param = request.query_params.get('status')
        if status_param == 'all':
            buildings = Building.objects.filter(condominium_id=condominium_id).order_by('display_order', 'name')
        elif status_param:
            buildings = Building.objects.filter(condominium_id=condominium_id, status=status_param).order_by('display_order', 'name')
        else:
            buildings = Building.objects.filter(condominium_id=condominium_id, status='active').order_by('display_order', 'name')
        return Response(BuildingSerializer(buildings, many=True).data)

    def post(self, request, condominium_id):
        if not Condominium.objects.filter(id=condominium_id).exists():
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BuildingSerializer(data=request.data)
        if serializer.is_valid():
            try:
                building = CondominiumService.create_building(
                    condominium_id=condominium_id,
                    **serializer.validated_data
                )
                return Response(BuildingSerializer(building).data, status=status.HTTP_201_CREATED)
            except DuplicateBuildingError as e:
                return Response({"error": "Torre/Bloco com este código já existe para este condomínio."}, status=status.HTTP_400_BAD_REQUEST)
            except DomainError as e:
                if "não encontrado" in str(e).lower() or "não encontrada" in str(e).lower():
                    return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CondominiumDetailUpdateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        try:
            condo = Condominium.objects.get(id=condominium_id)
        except Condominium.DoesNotExist:
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CondominiumSerializer(condo).data, status=status.HTTP_200_OK)

    def put(self, request, condominium_id):
        return self._update(request, condominium_id, partial=False)

    def patch(self, request, condominium_id):
        return self._update(request, condominium_id, partial=True)

    def _update(self, request, condominium_id, partial=False):
        try:
            condo = Condominium.objects.get(id=condominium_id)
        except Condominium.DoesNotExist:
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CondominiumSerializer(condo, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                updated = CondominiumService.update_condominium(
                    condominium_id=condominium_id,
                    **serializer.validated_data
                )
                return Response(CondominiumSerializer(updated).data, status=status.HTTP_200_OK)
            except DomainError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, condominium_id):
        is_permanent = request.query_params.get('permanent', '').lower() in ('true', '1')
        try:
            if is_permanent:
                CondominiumService.purge_condominium(condominium_id)
            else:
                CondominiumService.archive_condominium(condominium_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Condominium.DoesNotExist:
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class BuildingDetailUpdateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, building_id):
        try:
            building = Building.objects.get(id=building_id, condominium_id=condominium_id)
        except Building.DoesNotExist:
            return Response({"error": "Torre/Bloco não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(BuildingSerializer(building).data, status=status.HTTP_200_OK)

    def put(self, request, condominium_id, building_id):
        return self._update(request, condominium_id, building_id, partial=False)

    def patch(self, request, condominium_id, building_id):
        return self._update(request, condominium_id, building_id, partial=True)

    def _update(self, request, condominium_id, building_id, partial=False):
        try:
            building = Building.objects.get(id=building_id, condominium_id=condominium_id)
        except Building.DoesNotExist:
            return Response({"error": "Torre/Bloco não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BuildingSerializer(building, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                updated = CondominiumService.update_building(
                    building_id=building_id,
                    **serializer.validated_data
                )
                return Response(BuildingSerializer(updated).data, status=status.HTTP_200_OK)
            except DuplicateBuildingError as e:
                return Response({"error": "Torre/Bloco com este código já existe para este condomínio."}, status=status.HTTP_400_BAD_REQUEST)
            except DomainError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, condominium_id, building_id):
        is_permanent = request.query_params.get('permanent', '').lower() in ('true', '1')
        try:
            if is_permanent:
                CondominiumService.purge_building(condominium_id, building_id)
            else:
                building = Building.objects.get(id=building_id, condominium_id=condominium_id)
                building.status = 'inactive'
                building.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Building.DoesNotExist:
            return Response({"error": "Torre/Bloco não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UnitListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        if not Condominium.objects.filter(id=condominium_id).exists():
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        status_param = request.query_params.get('status')
        qs = Unit.objects.filter(condominium_id=condominium_id).select_related('building')
        if status_param == 'all':
            units = qs.order_by('code')
        elif status_param:
            units = qs.filter(status=status_param).order_by('code')
        else:
            units = qs.filter(status='active').order_by('code')
        return Response(UnitSerializer(units, many=True).data)

    def post(self, request, condominium_id):
        if not Condominium.objects.filter(id=condominium_id).exists():
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data.copy()
            building_id = data.pop('building_id', None)
            try:
                unit = CondominiumService.create_unit(
                    condominium_id=condominium_id,
                    building_id=building_id,
                    **data
                )
                return Response(UnitSerializer(unit).data, status=status.HTTP_201_CREATED)
            except DuplicateUnitError as e:
                return Response({"error": "Unidade com este código já existe para esta torre/condomínio."}, status=status.HTTP_400_BAD_REQUEST)
            except TenantMismatchError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except DomainError as e:
                if "não encontrado" in str(e).lower() or "não encontrada" in str(e).lower():
                    return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitDetailUpdateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, unit_id):
        try:
            unit = Unit.objects.select_related('building').get(id=unit_id, condominium_id=condominium_id)
        except Unit.DoesNotExist:
            return Response({"error": "Unidade não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UnitSerializer(unit).data, status=status.HTTP_200_OK)

    def put(self, request, condominium_id, unit_id):
        return self._update(request, condominium_id, unit_id, partial=False)

    def patch(self, request, condominium_id, unit_id):
        return self._update(request, condominium_id, unit_id, partial=True)

    def _update(self, request, condominium_id, unit_id, partial=False):
        try:
            unit = Unit.objects.get(id=unit_id, condominium_id=condominium_id)
        except Unit.DoesNotExist:
            return Response({"error": "Unidade não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UnitSerializer(unit, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                data = serializer.validated_data.copy()
                updated = CondominiumService.update_unit(
                    unit_id=unit_id,
                    **data
                )
                return Response(UnitSerializer(updated).data, status=status.HTTP_200_OK)
            except DuplicateUnitError as e:
                return Response({"error": "Unidade com este código já existe para esta torre/condomínio."}, status=status.HTTP_400_BAD_REQUEST)
            except TenantMismatchError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except DomainError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, condominium_id, unit_id):
        is_permanent = request.query_params.get('permanent', '').lower() in ('true', '1')
        try:
            if is_permanent:
                CondominiumService.purge_unit(condominium_id, unit_id)
            else:
                unit = Unit.objects.get(id=unit_id, condominium_id=condominium_id)
                unit.status = 'inactive'
                unit.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Unit.DoesNotExist:
            return Response({"error": "Unidade não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UnitBatchGenerateView(APIView):
    """
    Geração em lote de torres e unidades autônomas para um condomínio.
    Permite configurar andar inicial, andar final e quantidade de apartamentos por andar.
    Ex: 3º andar ao 15º andar, 6 por andar => 301..306, 401..406...
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id):
        if not Condominium.objects.filter(id=condominium_id).exists():
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            building_id = request.data.get('building_id')
            new_building_name = request.data.get('new_building_name')
            new_building_code = request.data.get('new_building_code')
            start_floor = int(request.data.get('start_floor', 1))
            end_floor = int(request.data.get('end_floor', 10))
            units_per_floor = int(request.data.get('units_per_floor', 4))
            suffix_digits = int(request.data.get('suffix_digits', 2))
            custom_prefix = request.data.get('custom_prefix')

            result = CondominiumService.batch_generate_units(
                condominium_id=condominium_id,
                building_id=uuid.UUID(building_id) if building_id else None,
                new_building_name=new_building_name,
                new_building_code=new_building_code,
                start_floor=start_floor,
                end_floor=end_floor,
                units_per_floor=units_per_floor,
                suffix_digits=suffix_digits,
                custom_prefix=custom_prefix,
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except (ValueError, TypeError) as e:
            return Response({"error": f"Parâmetros inválidos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Erro interno ao gerar unidades: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ResidentRegistrationListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        registrations = ResidentRegistration.objects.filter(
            condominium_id=condominium_id
        ).select_related('unit', 'unit__building').order_by('-created_at')

        results = []
        for reg in registrations:
            unit_code = reg.unit.code if reg.unit else ''
            building_name = reg.unit.building.name if (reg.unit and reg.unit.building) else (reg.unit.block or '—') if reg.unit else '—'
            phone_clean = "".join(filter(str.isdigit, reg.phone_e164 or ""))

            sug_qs = ConsultationSuggestion.objects.filter(condominium_id=condominium_id)
            cond = models.Q(unit_code__iexact=unit_code)
            if phone_clean:
                cond &= (models.Q(resident_phone__icontains=phone_clean[-8:]) | models.Q(resident_name__iexact=reg.full_name))
            else:
                cond &= models.Q(resident_name__iexact=reg.full_name)

            suggestions = sug_qs.filter(cond)
            sug_count = suggestions.count()
            last_sug = suggestions.order_by('-created_at').first()

            results.append({
                "id": str(reg.id),
                "unit_id": str(reg.unit_id) if reg.unit_id else None,
                "unit_code": unit_code or '—',
                "building_name": building_name,
                "building_code": reg.unit.building.code if (reg.unit and reg.unit.building) else '',
                "full_name": reg.full_name,
                "phone_e164": reg.phone_e164,
                "email": reg.email,
                "relationship": reg.relationship,
                "source": reg.source,
                "status": reg.status,
                "notes": reg.notes,
                "suggestions_count": sug_count,
                "last_suggestion_date": last_sug.created_at.isoformat() if last_sug else None,
                "created_at": reg.created_at.isoformat() if reg.created_at else None,
                "updated_at": reg.updated_at.isoformat() if reg.updated_at else None,
            })
        return Response(results, status=status.HTTP_200_OK)

    def post(self, request, condominium_id):
        unit_id = request.data.get('unit_id')
        unit_code = request.data.get('unit_code')
        block_tower = request.data.get('block_tower')

        if not unit_id and unit_code:
            building = None
            if block_tower:
                clean_tower = str(block_tower).strip()
                building = Building.objects.filter(
                    condominium_id=condominium_id,
                    status='active'
                ).filter(
                    models.Q(code__iexact=clean_tower) | models.Q(name__iexact=clean_tower)
                ).first()
                if not building:
                    building = Building.objects.create(
                        id=uuid.uuid4(),
                        condominium_id=condominium_id,
                        code=clean_tower[:50].upper(),
                        name=clean_tower[:255],
                        status='active'
                    )

            clean_u = str(unit_code).strip()
            unit = Unit.objects.filter(
                condominium_id=condominium_id,
                status='active',
                code__iexact=clean_u
            ).first()
            if not unit:
                unit = Unit.objects.create(
                    id=uuid.uuid4(),
                    condominium_id=condominium_id,
                    building=building,
                    code=clean_u[:50],
                    status='active'
                )
            unit_id = unit.id

        data = request.data.copy()
        data['unit_id'] = unit_id

        serializer = ResidentRegistrationCreateSerializer(data=data)
        if serializer.is_valid():
            v_data = serializer.validated_data.copy()
            u_id = v_data.pop('unit_id')
            registration = ResidentRegistrationService.create_manual_registration(
                condominium_id=condominium_id,
                unit_id=u_id,
                **v_data
            )
            return Response(ResidentRegistrationCreateSerializer(registration).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResidentRegistrationDetailUpdateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, registration_id):
        try:
            reg = ResidentRegistration.objects.select_related('unit', 'unit__building').get(
                id=registration_id,
                condominium_id=condominium_id
            )
        except ResidentRegistration.DoesNotExist:
            return Response({"error": "Morador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ResidentRegistrationCreateSerializer(reg).data, status=status.HTTP_200_OK)

    def patch(self, request, condominium_id, registration_id):
        try:
            reg = ResidentRegistration.objects.get(id=registration_id, condominium_id=condominium_id)
            if 'full_name' in request.data:
                reg.full_name = request.data['full_name'].strip()
            if 'phone_e164' in request.data:
                reg.phone_e164 = "".join(filter(str.isdigit, request.data['phone_e164']))
            if 'email' in request.data:
                reg.email = request.data['email'].strip().lower() if request.data['email'] else None
            if 'notes' in request.data:
                reg.notes = request.data['notes']
            reg.save()
            return Response(ResidentRegistrationCreateSerializer(reg).data, status=status.HTTP_200_OK)
        except ResidentRegistration.DoesNotExist:
            return Response({"error": "Morador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, condominium_id, registration_id):
        try:
            reg = ResidentRegistration.objects.get(id=registration_id, condominium_id=condominium_id)
            reg.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ResidentRegistration.DoesNotExist:
            return Response({"error": "Morador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResidentSuggestionsListView(APIView):
    """
    Retorna as sugestões associadas a um morador específico para visualização
    exclusiva do síndico em caso de dúvidas sobre as propostas enviadas.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, registration_id):
        try:
            reg = ResidentRegistration.objects.select_related('unit').get(
                id=registration_id,
                condominium_id=condominium_id
            )
        except ResidentRegistration.DoesNotExist:
            return Response({"error": "Morador não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        unit_code = reg.unit.code if reg.unit else ''
        phone_clean = "".join(filter(str.isdigit, reg.phone_e164 or ""))

        sug_qs = ConsultationSuggestion.objects.filter(condominium_id=condominium_id)
        cond = models.Q(unit_code__iexact=unit_code)
        if phone_clean:
            cond &= (models.Q(resident_phone__icontains=phone_clean[-8:]) | models.Q(resident_name__iexact=reg.full_name))
        else:
            cond &= models.Q(resident_name__iexact=reg.full_name)

        suggestions = sug_qs.filter(cond).select_related('consultation').order_by('-created_at')
        serializer = AdminConsultationSuggestionListSerializer(suggestions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UnitMembershipListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        memberships = UnitMembership.objects.filter(
            condominium_id=condominium_id
        ).select_related('unit', 'resident')
        return Response(UnitMembershipListSerializer(memberships, many=True).data)


class VerifyMembershipActionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, membership_id):
        serializer = VerifyMembershipActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_account_id = _get_or_create_actor_id(request)
        membership = MembershipVerificationService.verify_membership(
            condominium_id=condominium_id,
            membership_id=membership_id,
            new_status=serializer.validated_data['new_status'],
            method=serializer.validated_data['method'],
            reason=serializer.validated_data['reason'],
            actor_account_id=actor_account_id
        )
        return Response(UnitMembershipListSerializer(membership).data, status=status.HTTP_200_OK)


class UnitMembershipDetailUpdateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, membership_id):
        try:
            m = UnitMembership.objects.select_related('unit', 'resident').get(
                id=membership_id,
                condominium_id=condominium_id
            )
        except UnitMembership.DoesNotExist:
            return Response({"error": "Vínculo de morador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UnitMembershipListSerializer(m).data, status=status.HTTP_200_OK)

    def patch(self, request, condominium_id, membership_id):
        try:
            updated = UnitMembershipService.update_membership(
                condominium_id=condominium_id,
                membership_id=membership_id,
                **request.data
            )
            return Response(UnitMembershipListSerializer(updated).data, status=status.HTTP_200_OK)
        except UnitMembership.DoesNotExist:
            return Response({"error": "Vínculo de morador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, condominium_id, membership_id):
        is_permanent = request.query_params.get('permanent', '').lower() in ('true', '1')
        actor_id = _get_or_create_actor_id(request)
        try:
            if is_permanent:
                UnitMembershipService.purge_membership(
                    condominium_id=condominium_id,
                    membership_id=membership_id
                )
            else:
                UnitMembershipService.delete_membership(
                    condominium_id=condominium_id,
                    membership_id=membership_id,
                    actor_account_id=actor_id
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UnitMembership.DoesNotExist:
            return Response({"error": "Vínculo de morador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RoleAssignmentListCreateView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        roles = RoleAssignment.objects.filter(condominium_id=condominium_id, status='active').select_related('account')
        return Response(RoleAssignmentSerializer(roles, many=True).data)

    def post(self, request, condominium_id):
        account_id = request.data.get('account_id')
        role = request.data.get('role')
        if not account_id or not role:
            return Response({"error": "account_id e role são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

        assignment = RoleService.assign_role(
            condominium_id=condominium_id,
            account_id=account_id,
            role=role
        )
        return Response(RoleAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


# ============================================================================
# FASE 2: IMPORTAÇÃO CADASTRAL
# ============================================================================

class ResidentImportTemplateView(APIView):
    """Retorna o modelo de planilha fictícia sem fórmulas (CSV)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        csv_content = ImportService.generate_template_csv()
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="modelo_importacao_condc.csv"'
        return response


class ResidentImportListCreateView(APIView):
    """Listagem e upload de arquivos para importação de moradores."""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, condominium_id):
        batches = ImportBatch.objects.filter(condominium_id=condominium_id)
        return Response(ImportBatchSerializer(batches, many=True).data)

    def post(self, request, condominium_id):
        # CA-03, V21-06: Upload cria lote sem alterar cadastros
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "Nenhum arquivo enviado no campo 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        actor_id = getattr(request.user, 'account_id', None) or request.data.get('actor_account_id')
        if not actor_id:
            # Cria conta temporária de auditoria se inexistente no ambiente de teste
            acc = Account.objects.first()
            if not acc:
                acc = Account.objects.create(auth_user_id=uuid.uuid4(), email="importador@condc.local", full_name="Operador Importador")
            actor_id = acc.id

        source_label = request.data.get('source_label', 'upload_manual')

        try:
            batch = ImportService.create_batch_from_file(
                condominium_id=condominium_id,
                file_obj=file_obj,
                actor_id=actor_id,
                file_name=file_obj.name,
                source_label=source_label
            )
            return Response(
                {
                    "id": str(batch.id),
                    "status": batch.status,
                    "revision": batch.revision,
                    "totals": batch.totals
                },
                status=status.HTTP_202_ACCEPTED
            )
        except (InvalidImportFileError, FormulaInjectionDetectedError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResidentImportDetailView(APIView):
    """Consulta detalhes e status de um lote de importação."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, batch_id):
        try:
            batch = ImportBatch.objects.get(id=batch_id, condominium_id=condominium_id)
            return Response(ImportBatchSerializer(batch).data)
        except ImportBatch.DoesNotExist:
            return Response({"error": "Lote de importação não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class ResidentImportMappingView(APIView):
    """Atualização de mapeamento de colunas do lote (incrementa revisão e invalida prévia)."""
    permission_classes = [AllowAny]

    def put(self, request, condominium_id, batch_id):
        actor_id = getattr(request.user, 'account_id', None) or request.data.get('actor_account_id')
        if not actor_id:
            acc = Account.objects.first()
            actor_id = acc.id if acc else uuid.uuid4()
        mapping_data = request.data.get('mapping') or request.data
        try:
            batch = ImportService.update_mapping(
                condominium_id=condominium_id,
                batch_id=batch_id,
                mapping_data=mapping_data,
                actor_id=actor_id
            )
            return Response(ImportBatchSerializer(batch).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResidentImportRowsListView(APIView):
    """Listagem das linhas do lote com suas classificações e status."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, batch_id):
        classification = request.query_params.get('classification')
        rows = ImportRow.objects.filter(batch_id=batch_id)
        if classification:
            rows = rows.filter(classification=classification)
        return Response(ImportRowSerializer(rows, many=True).data)


class ResidentImportRowDetailView(APIView):
    """Resolução manual de uma linha do lote."""
    permission_classes = [AllowAny]

    def patch(self, request, condominium_id, batch_id, row_id):
        serializer = ImportRowActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        try:
            row = ImportService.update_row_resolution(
                condominium_id=condominium_id,
                batch_id=batch_id,
                row_id=row_id,
                selected=serializer.validated_data['selected'],
                action=serializer.validated_data['action'],
                target_registration_id=serializer.validated_data.get('target_registration_id'),
                actor_id=actor_id
            )
            return Response(ImportRowSerializer(row).data, status=status.HTTP_200_OK)
        except UnresolvedConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResidentImportPreviewView(APIView):
    """Consulta da prévia do lote com totais e confirmação de não envio de convites."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, batch_id):
        try:
            preview_data = ImportService.get_preview(condominium_id=condominium_id, batch_id=batch_id)
            return Response(preview_data, status=status.HTTP_200_OK)
        except ImportBatch.DoesNotExist:
            return Response({"error": "Lote não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class ResidentImportConfirmView(APIView):
    """
    Confirmação atômica do lote com verificação de revisão concorrente e suporte a idempotência.
    CA-03, V21-13, V21-16, V21-17, V21-18.
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, batch_id):
        serializer = ImportConfirmActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        expected_revision = serializer.validated_data['expected_revision']
        idempotency_key = request.headers.get('Idempotency-Key')
        actor_id = getattr(request.user, 'account_id', None) or request.data.get('actor_account_id')
        if not actor_id:
            acc = Account.objects.first()
            if not acc:
                acc = Account.objects.create(
                    auth_user_id=uuid.uuid4(),
                    email="sistema.confirm@condc.local",
                    full_name="Sistema Auditoria"
                )
            actor_id = acc.id

        def _execute():
            res = ImportService.confirm_and_apply_batch(
                condominium_id=condominium_id,
                batch_id=batch_id,
                expected_revision=expected_revision,
                actor_id=actor_id,
                acknowledge_selected_operations=serializer.validated_data['acknowledge_selected_operations']
            )
            return status.HTTP_202_ACCEPTED, res

        try:
            resp_code, resp_body = IdempotencyService.execute_with_idempotency(
                operation=f"import_confirm_{batch_id}",
                key=idempotency_key,
                payload=request.data,
                tenant_id=condominium_id,
                actor_account_id=actor_id,
                handler=_execute
            )
            return Response(resp_body, status=resp_code)
        except ImportPreviewOutdatedError as e:
            return Response(
                {
                    "code": "IMPORT_PREVIEW_OUTDATED",
                    "message": str(e),
                },
                status=status.HTTP_412_PRECONDITION_FAILED
            )
        except UnresolvedConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except IdempotencyConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)


# ============================================================================
# FASE 2: CONVITES DE ACESSO
# ============================================================================

class AccessInvitationListCreateView(APIView):
    """Criação e listagem de convites do condomínio."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        invitations = AccessInvitation.objects.filter(condominium_id=condominium_id).select_related('target_unit')
        return Response(AccessInvitationListSerializer(invitations, many=True).data)

    def post(self, request, condominium_id):
        serializer = AccessInvitationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        actor_id = getattr(request.user, 'account_id', None)
        if not actor_id:
            acc = Account.objects.first()
            if not acc:
                acc = Account.objects.create(auth_user_id=uuid.uuid4(), email="admin.invites@condc.local", full_name="Admin de Convites")
            actor_id = acc.id

        expires_at = timezone.now() + timedelta(days=data.get('expires_in_days', 7))

        invitation, raw_token = InvitationService.create_invitation(
            condominium_id=condominium_id,
            kind=data['kind'],
            created_by_id=actor_id,
            expires_at=expires_at,
            target_registration_id=data.get('target_registration_id'),
            target_unit_id=data.get('target_unit_id'),
            target_building_id=data.get('target_building_id'),
            expected_contact=data.get('expected_contact'),
            max_redemptions=data.get('max_redemptions', 1)
        )

        resp_data = AccessInvitationListSerializer(invitation).data
        resp_data['token'] = raw_token  # Token exibido uma única vez
        return Response(resp_data, status=status.HTTP_201_CREATED)


class AccessInvitationRevokeView(APIView):
    """Revogação de convite pela administração (CA-11, V21-23)."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, invitation_id):
        serializer = InvitationRevokeActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        try:
            invitation = InvitationService.revoke_invitation(
                condominium_id=condominium_id,
                invitation_id=invitation_id,
                actor_id=actor_id,
                reason=serializer.validated_data['reason']
            )
            return Response(AccessInvitationListSerializer(invitation).data, status=status.HTTP_200_OK)
        except AccessInvitation.DoesNotExist:
            return Response({"error": "Convite não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class PublicInvitationInspectView(APIView):
    """
    CA-10, V21-19: Inspeção pública do convite via GET.
    NÃO consome o convite e NÃO autentica o usuário.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Parâmetro 'token' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        inspect_info = InvitationService.inspect_invitation(token)
        return Response(inspect_info, status=status.HTTP_200_OK)


class PublicInvitationRedeemView(APIView):
    """
    Resgate transacional de convite de acesso.
    CA-07 a CA-11; V21-20 a V21-24.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InvitationRedeemActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        account_id = getattr(request.user, 'account_id', None) or request.data.get('account_id')
        if not account_id:
            # Conta fornecida ou criada para o resgate
            acc_email = request.data.get('account_email', 'morador.novo@condc.local')
            acc = Account.objects.filter(email=acc_email).first()
            if not acc:
                acc = Account.objects.create(
                    auth_user_id=uuid.uuid4(),
                    email=acc_email,
                    full_name=request.data.get('account_full_name', 'Morador Resgatado')
                )
            account_id = acc.id

        idempotency_key = request.headers.get('Idempotency-Key')
        raw_token = serializer.validated_data['token']
        provided_contact = serializer.validated_data.get('provided_contact')

        def _execute():
            res = InvitationService.redeem_invitation(
                raw_token=raw_token,
                account_id=account_id,
                provided_contact=provided_contact,
                idempotency_key=idempotency_key,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            return status.HTTP_200_OK, res

        try:
            resp_code, resp_body = IdempotencyService.execute_with_idempotency(
                operation=f"invitation_redeem_{raw_token[:8]}",
                key=idempotency_key,
                payload=request.data,
                tenant_id=None,
                actor_account_id=account_id,
                handler=_execute
            )
            return Response(resp_body, status=resp_code)
        except (InvitationExpiredOrExhaustedError, InvitationRevokedError, InvalidExpectedContactError, InvitationRedemptionForbiddenError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except IdempotencyConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)


# ============================================================================
# FASE 3: NÚCLEO DOCUMENTAL, OCR, DISPOSITIVOS E SNAPSHOTS
# ============================================================================

class ProjectListCreateView(APIView):
    """Listagem e criação de projetos documentais."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        projects = ProjectService.list_projects(condominium_id)
        return Response(ProjectSerializer(projects, many=True).data)

    def post(self, request, condominium_id):
        serializer = ProjectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        project = ProjectService.create_project(
            condominium_id=condominium_id,
            name=data['name'],
            purpose=data.get('purpose'),
            kind=data.get('kind', 'revisao'),
            coordinator_account_id=data.get('coordinator_account_id'),
            settings=data.get('settings')
        )
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class DocumentListCreateView(APIView):
    """Listagem e criação de documentos vinculados a um projeto."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, project_id):
        docs = DocumentService.list_documents(project_id)
        return Response(DocumentSerializer(docs, many=True).data)

    def post(self, request, condominium_id, project_id):
        serializer = DocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        document = DocumentService.create_document(
            project_id=project_id,
            condominium_id=condominium_id,
            title=data['title'],
            type=data.get('type', 'regimento_interno'),
            numbering_policy=data.get('numbering_policy', 'preservar_original')
        )
        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    """Detalhes de um documento normativo."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        try:
            doc = Document.objects.get(id=document_id, condominium_id=condominium_id)
            return Response(DocumentSerializer(doc).data)
        except Document.DoesNotExist:
            return Response({"error": "Documento não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class SourceFileUploadView(APIView):
    """Upload de arquivo original com extração e registro de hash (CA-17, AR-10)."""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, condominium_id, document_id):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "Nenhum arquivo enviado no campo 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        content_bytes = file_obj.read()

        source_file = SourceFileService.register_source_file(
            condominium_id=condominium_id,
            uploaded_by_id=actor_id,
            filename=file_obj.name,
            mime_type=getattr(file_obj, 'content_type', 'application/octet-stream'),
            size_bytes=len(content_bytes),
            file_content=content_bytes
        )

        # Transcrição inicial (simulação de extração OCR para teste)
        raw_text = request.data.get('raw_text') or f"Transcrição inicial do arquivo {file_obj.name}"
        transcription = TranscriptionService.create_initial_transcription(
            document_id=document_id,
            condominium_id=condominium_id,
            source_file_id=source_file.id,
            raw_text=raw_text
        )

        return Response({
            "source_file": SourceFileSerializer(source_file).data,
            "transcription": SourceTranscriptionSerializer(transcription).data
        }, status=status.HTTP_201_CREATED)


class TranscriptionDetailConfirmView(APIView):
    """Conferência humana e correção de transcrição original (CA-17, CA-18)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, transcription_id):
        try:
            trans = SourceTranscription.objects.get(id=transcription_id, condominium_id=condominium_id)
            return Response(SourceTranscriptionSerializer(trans).data)
        except SourceTranscription.DoesNotExist:
            return Response({"error": "Transcrição não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, condominium_id, transcription_id, action=None):
        actor_id = _get_or_create_actor_id(request)
        action_name = (action or request.data.get('action') or 'confirm').lower()

        if action_name == 'confirm':
            # CA-17: Conferência humana do original
            serializer = TranscriptionConfirmActionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            trans = TranscriptionService.confirm_transcription(
                transcription_id=transcription_id,
                checked_by_id=actor_id,
                corrected_text=serializer.validated_data.get('corrected_text')
            )
            return Response(SourceTranscriptionSerializer(trans).data, status=status.HTTP_200_OK)

        elif action_name == 'correct':
            # CA-18: Correção humana gera nova versão de transcrição
            serializer = TranscriptionCorrectActionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            new_trans = TranscriptionService.correct_transcription(
                transcription_id=transcription_id,
                checked_by_id=actor_id,
                corrected_text=serializer.validated_data['corrected_text']
            )
            return Response(SourceTranscriptionSerializer(new_trans).data, status=status.HTTP_201_CREATED)

        return Response({"error": "Ação inválida. Use 'confirm' ou 'correct'."}, status=status.HTTP_400_BAD_REQUEST)


class ProvisionListCreateView(APIView):
    """
    Listagem em árvore e criação de dispositivos normativos.
    CA-24: Por padrão omite notas internas, garantindo privacidade em superfícies públicas.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        include_notes = request.query_params.get('include_notes', 'false').lower() == 'true'
        actor_id = getattr(request.user, 'account_id', None) or request.query_params.get('actor_account_id')

        if include_notes:
            # CA-24: Apenas gestão/equipe autorizada pode ver notas internas
            has_role = RoleAssignment.objects.filter(
                condominium_id=condominium_id,
                account_id=actor_id,
                role__in=['sindico', 'admin', 'juridico', 'comissao'],
                status='active'
            ).exists() if actor_id else False

            if not has_role:
                return Response(
                    {"error": "Acesso a notas internas restrito a equipe administrativa autorizada (CA-24)."},
                    status=status.HTTP_403_FORBIDDEN
                )

        tree = ProvisionService.get_document_tree(document_id=document_id, include_notes=include_notes)
        return Response(tree, status=status.HTTP_200_OK)

    def post(self, request, condominium_id, document_id):
        serializer = ProvisionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data

        provision = ProvisionService.create_provision(
            document_id=document_id,
            condominium_id=condominium_id,
            kind=data.get('kind', 'artigo'),
            label=data['label'],
            text=data['text'],
            parent_provision_id=data.get('parent_provision_id'),
            position=data.get('position', 0),
            theme=data.get('theme'),
            change_type=data.get('change_type', 'mantido'),
            author_account_id=actor_id
        )

        latest_rev = ProvisionService.get_latest_revision(provision.id)
        response_data = {
            "id": str(provision.id),
            "kind": provision.kind,
            "revision_number": latest_rev.revision_number,
            "label": latest_rev.label,
            "text": latest_rev.text,
            "position": latest_rev.position,
            "parent_provision_id": str(latest_rev.parent_provision_id) if latest_rev.parent_provision_id else None,
            "etag": latest_rev.etag,
        }
        res = Response(response_data, status=status.HTTP_201_CREATED)
        res['ETag'] = f'"{latest_rev.etag}"'
        return res


class ProvisionDetailUpdateView(APIView):
    """
    Consulta e atualização de dispositivo com concorrência otimista (CA-23)
    e detecção de ciclos na hierarquia.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, provision_id):
        try:
            prov = Provision.objects.get(id=provision_id, condominium_id=condominium_id)
            latest_rev = ProvisionService.get_latest_revision(prov.id)
            if not latest_rev:
                return Response({"error": "Revisão não encontrada."}, status=status.HTTP_404_NOT_FOUND)

            data = {
                "id": str(prov.id),
                "kind": prov.kind,
                "revision_number": latest_rev.revision_number,
                "label": latest_rev.label,
                "text": latest_rev.text,
                "theme": latest_rev.theme,
                "position": latest_rev.position,
                "parent_provision_id": str(latest_rev.parent_provision_id) if latest_rev.parent_provision_id else None,
                "etag": latest_rev.etag,
            }
            res = Response(data)
            res['ETag'] = f'"{latest_rev.etag}"'
            return res
        except Provision.DoesNotExist:
            return Response({"error": "Dispositivo não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, condominium_id, provision_id):
        serializer = ProvisionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # CA-23: ETag no header If-Match ou payload
        expected_etag = (
            request.headers.get('If-Match')
            or request.META.get('HTTP_IF_MATCH')
            or request.data.get('expected_etag')
        )

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data

        try:
            new_rev = ProvisionService.update_provision(
                provision_id=provision_id,
                expected_etag=expected_etag,
                text=data['text'],
                label=data.get('label'),
                parent_provision_id=data.get('parent_provision_id'),
                position=data.get('position'),
                theme=data.get('theme'),
                change_type=data.get('change_type', 'alterado'),
                author_account_id=actor_id
            )
            response_data = {
                "id": str(provision_id),
                "revision_number": new_rev.revision_number,
                "label": new_rev.label,
                "text": new_rev.text,
                "etag": new_rev.etag,
                "change_type": new_rev.change_type,
            }
            res = Response(response_data, status=status.HTTP_200_OK)
            res['ETag'] = f'"{new_rev.etag}"'
            return res
        except ConcurrencyConflictError as e:
            # CA-23: Conflito de concorrência otimista (HTTP 412)
            return Response(
                {
                    "code": "CONCURRENCY_CONFLICT",
                    "message": str(e),
                    "error": str(e),
                },
                status=status.HTTP_412_PRECONDITION_FAILED
            )
        except CircularReferenceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProvisionInternalNoteListCreateView(APIView):
    """Criação e listagem de notas internas privadas (CA-24)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, provision_id):
        actor_id = getattr(request.user, 'account_id', None) or request.query_params.get('actor_account_id')
        role_obj = RoleAssignment.objects.filter(
            condominium_id=condominium_id,
            account_id=actor_id,
            status='active'
        ).first() if actor_id else None

        user_role = role_obj.role if role_obj else 'morador'

        try:
            notes = InternalNoteService.list_notes_for_provision(provision_id=provision_id, user_role=user_role)
            return Response(InternalNoteSerializer(notes, many=True).data)
        except PrivateNoteAccessForbiddenError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request, condominium_id, provision_id):
        actor_id = _get_or_create_actor_id(request)
        serializer = InternalNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        note = InternalNoteService.create_note(
            condominium_id=condominium_id,
            provision_id=provision_id,
            author_account_id=actor_id,
            content=data['content'],
            visibility=data.get('visibility', 'equipe'),
            category=data.get('category', 'redacao'),
            revision_id=data.get('revision_id')
        )
        return Response(InternalNoteSerializer(note).data, status=status.HTTP_201_CREATED)


class DocumentSnapshotListCreateView(APIView):
    """Criação e listagem de snapshots imutáveis (CA-41)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        snaps = DocumentSnapshot.objects.filter(document_id=document_id, condominium_id=condominium_id).order_by('-frozen_at')
        return Response([
            {
                "id": str(s.id),
                "version_label": s.version_label,
                "purpose": s.purpose,
                "frozen_at": s.frozen_at.isoformat(),
                "content_hash": s.content_hash,
                "is_immutable": s.is_immutable,
            }
            for s in snaps
        ])

    def post(self, request, condominium_id, document_id):
        serializer = DocumentSnapshotCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data

        snapshot = SnapshotService.create_snapshot(
            document_id=document_id,
            condominium_id=condominium_id,
            version_label=data['version_label'],
            frozen_by_id=actor_id,
            purpose=data.get('purpose', 'consulta_publica')
        )

        return Response({
            "id": str(snapshot.id),
            "version_label": snapshot.version_label,
            "purpose": snapshot.purpose,
            "content_hash": snapshot.content_hash,
            "is_immutable": snapshot.is_immutable,
            "frozen_at": snapshot.frozen_at.isoformat()
        }, status=status.HTTP_201_CREATED)


class DocumentSnapshotDetailView(APIView):
    """Recuperação da árvore congelada imutável a partir do snapshot (CA-41)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, snapshot_id):
        try:
            tree = SnapshotService.get_snapshot_tree(snapshot_id)
            return Response(tree, status=status.HTTP_200_OK)
        except DocumentSnapshot.DoesNotExist:
            return Response({"error": "Snapshot não encontrado."}, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# FASE 4: COMPARAÇÃO, MAPEAMENTO DE ORIGENS, RENUMERAÇÃO E EXPORTAÇÃO
# ============================================================================

class ProvisionOriginMappingListCreateView(APIView):
    """
    Mapeamento explícito de origens N:M (CA-21).
    CA-19: Dispositivo incluído (novo) não pode inventar origem fictícia.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, provision_id):
        latest_rev = ProvisionService.get_latest_revision(provision_id)
        if not latest_rev:
            return Response({"error": "Revisão não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        mappings = OriginMappingService.list_mappings_for_revision(
            condominium_id=condominium_id,
            revision_id=latest_rev.id
        )
        return Response(OriginMappingSerializer(mappings, many=True).data)

    def post(self, request, condominium_id, provision_id):
        serializer = OriginMappingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        latest_rev = ProvisionService.get_latest_revision(provision_id)
        if not latest_rev:
            return Response({"error": "Revisão não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        data = serializer.validated_data
        try:
            mapping = OriginMappingService.create_mapping(
                condominium_id=condominium_id,
                revision_id=latest_rev.id,
                source_provision_id=data['source_provision_id'],
                relation_type=data.get('relation_type', 'mantido'),
                excerpt=data.get('excerpt'),
                reason=data.get('reason')
            )
            return Response(OriginMappingSerializer(mapping).data, status=status.HTTP_201_CREATED)
        except FictitiousOriginError as e:
            # CA-19: Dispositivo incluído não inventa origem
            return Response({"error": str(e), "code": "FICTITIOUS_ORIGIN_PROHIBITED"}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidOriginMappingError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DocumentCompareView(APIView):
    """Comparação lado a lado entre minuta e fonte original com diff granular."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        revision_id = request.query_params.get('revision_id')
        source_provision_id = request.query_params.get('source_provision_id')

        if not revision_id:
            return Response({"error": "Parâmetro 'revision_id' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rev_uuid = uuid.UUID(revision_id)
            source_uuid = uuid.UUID(source_provision_id) if source_provision_id else None
            result = ComparisonService.compare_revision_with_source(
                condominium_id=condominium_id,
                revision_id=rev_uuid,
                source_provision_id=source_uuid
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DocumentDeParaReportView(APIView):
    """
    Relatório DePara estruturado (CA-19, CA-20, CA-21).
    Demonstra dispositivos incluídos sem origem, excluídos mantidos e relações N:M.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        try:
            report = ComparisonService.generate_depara_report(
                condominium_id=condominium_id,
                document_id=document_id
            )
            return Response(report, status=status.HTTP_200_OK)
        except Document.DoesNotExist:
            return Response({"error": "Documento não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class DocumentCrossReferenceListCreateView(APIView):
    """Gerenciamento de referências cruzadas vinculadas a UUIDs estáveis (CA-22)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        provision_id = request.query_params.get('provision_id')
        if provision_id:
            latest_rev = ProvisionService.get_latest_revision(uuid.UUID(provision_id))
            if not latest_rev:
                return Response({"error": "Revisão não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            resolved = CrossReferenceService.resolve_references_for_revision(
                condominium_id=condominium_id,
                revision_id=latest_rev.id
            )
            return Response(resolved)

        xrefs = CrossReference.objects.filter(condominium_id=condominium_id)
        return Response(CrossReferenceSerializer(xrefs, many=True).data)

    def post(self, request, condominium_id, document_id):
        provision_id = request.data.get('provision_id')
        if not provision_id:
            return Response({"error": "Campo 'provision_id' de origem é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CrossReferenceCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        latest_rev = ProvisionService.get_latest_revision(uuid.UUID(provision_id))
        if not latest_rev:
            return Response({"error": "Revisão não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        data = serializer.validated_data
        xref = CrossReferenceService.create_cross_reference(
            condominium_id=condominium_id,
            revision_id=latest_rev.id,
            target_provision_id=data['target_provision_id'],
            label_template=data.get('label_template', 'art. {target_label}')
        )
        return Response(CrossReferenceSerializer(xref).data, status=status.HTTP_201_CREATED)


class DocumentRenumberingView(APIView):
    """
    Renumeração estruturada com preservação de UUIDs e integridade de referências (CA-22).
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        strategy = request.query_params.get('strategy', 'renumeracao_automatica')
        preview = RenumberingService.preview_renumbering(
            condominium_id=condominium_id,
            document_id=document_id,
            strategy=strategy
        )
        return Response(preview, status=status.HTTP_200_OK)

    def post(self, request, condominium_id, document_id):
        serializer = RenumberingApplySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        strategy = serializer.validated_data.get('strategy', 'renumeracao_automatica')

        result = RenumberingService.apply_renumbering(
            condominium_id=condominium_id,
            document_id=document_id,
            author_account_id=actor_id,
            strategy=strategy
        )
        return Response(result, status=status.HTTP_200_OK)


class PlainTextRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'text'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, str):
            return data.encode('utf-8')
        return str(data).encode('utf-8')


class DocumentExportCleanView(APIView):
    """
    Exportação limpa preliminar do documento normativo (CA-42).
    Exclui itens excluídos (CA-20), omite autoria e notas internas (CA-24).
    """
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer, PlainTextRenderer]

    def get(self, request, condominium_id, document_id):
        export_format = request.query_params.get('format', 'json').lower()

        if export_format == 'text' or getattr(request.accepted_renderer, 'format', None) == 'text':
            clean_text = ExportService.export_clean_text(
                condominium_id=condominium_id,
                document_id=document_id
            )
            return Response(clean_text, content_type='text/plain; charset=utf-8')

        clean_data = ExportService.export_clean_document(
            condominium_id=condominium_id,
            document_id=document_id
        )
        return Response(clean_data, status=status.HTTP_200_OK)


class DocumentExportDeParaView(APIView):
    """Exportação do relatório DePara em formato estruturado (CA-20, CA-21)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        report = ComparisonService.generate_depara_report(
            condominium_id=condominium_id,
            document_id=document_id
        )
        return Response(report, status=status.HTTP_200_OK)


class DocumentPreflightView(APIView):
    """
    Auditoria prévia (Preflight) da árvore normativa (EDOSS-EX-01, EDOSS-EX-02).
    Verifica Caputs obrigatórios, contenção estrita, notas órfãs e ausência de ciclos.
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, document_id):
        profile = request.data.get('profile', 'clean_working')
        try:
            report = CanonicalExportService.run_preflight(
                condominium_id=condominium_id,
                document_id=document_id,
                profile=profile
            )
            return Response(report.to_dict(), status=status.HTTP_200_OK)
        except Document.DoesNotExist:
            return Response({"error": "Documento não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DocumentCanonicalExportView(APIView):
    """
    Exportação Canônica Unificada Open Source DOCX e PDF (ED-OSS-2.0).
    Pipeline: python-docx + LibreOffice headless + Hashing SHA-256 + Manifesto.
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, document_id):
        profile = request.data.get('profile', 'clean_working')
        export_format = request.data.get('format', 'json').lower()
        force_without_soffice = request.data.get('force_without_soffice', False)

        actor_id = _get_or_create_actor_id(request)

        try:
            result = CanonicalExportService.export_canonical_pair(
                condominium_id=condominium_id,
                document_id=document_id,
                author_account_id=actor_id,
                profile=profile,
                force_without_soffice=force_without_soffice
            )

            if not result.success:
                return Response({
                    "error": result.error_message,
                    "preflight": result.preflight_report.to_dict() if result.preflight_report else None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Download binário direto se solicitado
            if export_format == 'pdf' and result.pdf_path and os.path.exists(result.pdf_path):
                with open(result.pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                filename = os.path.basename(result.pdf_path)
                resp = HttpResponse(pdf_bytes, content_type='application/pdf')
                resp['Content-Disposition'] = f'attachment; filename="{filename}"'
                resp['X-File-SHA256'] = result.pdf_sha256
                return resp

            if export_format == 'docx' and result.docx_path and os.path.exists(result.docx_path):
                with open(result.docx_path, 'rb') as f:
                    docx_bytes = f.read()
                filename = os.path.basename(result.docx_path)
                resp = HttpResponse(docx_bytes, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                resp['Content-Disposition'] = f'attachment; filename="{filename}"'
                resp['X-File-SHA256'] = result.docx_sha256
                return resp

            # Resposta JSON padrão com dados dos arquivos e manifesto
            return Response({
                "success": True,
                "profile": profile,
                "artifacts": {
                    "docx": {
                        "filename": os.path.basename(result.docx_path),
                        "sha256": result.docx_sha256,
                        "size_bytes": result.docx_size_bytes,
                    },
                    "pdf": {
                        "filename": os.path.basename(result.pdf_path) if result.pdf_path else None,
                        "sha256": result.pdf_sha256,
                        "size_bytes": result.pdf_size_bytes,
                    } if result.pdf_path else None,
                },
                "manifest": result.manifest,
                "preflight_passed": result.preflight_report.is_valid,
            }, status=status.HTTP_200_OK)

        except Document.DoesNotExist:
            return Response({"error": "Documento não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DocumentInstantiateTemplateView(APIView):
    """
    Instanciação de documento normativo completo a partir de template OSS aberto (EDOSS-OSS-04).
    Gera novos UUIDs estáveis e preserva hierarquia LC 95.
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, project_id):
        template_type = request.data.get('template_type', 'regimento')
        title = request.data.get('title')
        if not title:
            title = "Regimento Interno" if template_type == 'regimento' else "Convenção de Condomínio"

        actor_id = _get_or_create_actor_id(request)

        try:
            doc, provisions = CanonicalExportService.instantiate_template_to_document(
                condominium_id=condominium_id,
                project_id=project_id,
                title=title,
                template_type=template_type,
                author_account_id=actor_id
            )
            return Response({
                "id": str(doc.id),
                "title": doc.title,
                "type": doc.type,
                "editorial_status": doc.editorial_status,
                "provisions_count": len(provisions),
                "created_at": doc.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        except Project.DoesNotExist:
            return Response({"error": "Projeto documental não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# FASE 5: CONSULTA PÚBLICA, PARTICIPAÇÃO E MODERAÇÃO EDITORIAL
# ============================================================================

class ConsultationCampaignListCreateView(APIView):
    """Listagem e criação de campanhas de consulta pública vinculadas a snapshots imutáveis."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        campaigns = ConsultationCampaign.objects.filter(condominium_id=condominium_id).order_by('-created_at')
        return Response(ConsultationCampaignSerializer(campaigns, many=True).data)

    def post(self, request, condominium_id):
        serializer = ConsultationCampaignCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        campaign = CampaignService.create_campaign(
            condominium_id=condominium_id,
            project_id=data['project_id'],
            snapshot_id=data['snapshot_id'],
            name=data['name'],
            description=data.get('description'),
            settings=data.get('settings')
        )
        return Response(ConsultationCampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)


class ConsultationCampaignDetailView(APIView):
    """Detalhe e transição de estado da campanha de consulta pública."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, campaign_id):
        try:
            campaign = ConsultationCampaign.objects.get(id=campaign_id, condominium_id=condominium_id)
            return Response(ConsultationCampaignSerializer(campaign).data)
        except ConsultationCampaign.DoesNotExist:
            return Response({"error": "Campanha não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, condominium_id, campaign_id, action=None):
        action = action or request.data.get('action')
        try:
            if action == 'open':
                campaign = CampaignService.open_campaign(campaign_id, condominium_id)
            elif action == 'close':
                campaign = CampaignService.close_campaign(campaign_id, condominium_id)
            else:
                return Response({"error": "Ação inválida. Use 'open' ou 'close'."}, status=status.HTTP_400_BAD_REQUEST)
            return Response(ConsultationCampaignSerializer(campaign).data)
        except ConsultationCampaign.DoesNotExist:
            return Response({"error": "Campanha não encontrada."}, status=status.HTTP_404_NOT_FOUND)


class CampaignParticipantListCreateView(APIView):
    """Listagem e habilitação de participantes da campanha."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, campaign_id):
        participants = CampaignParticipant.objects.filter(
            campaign_id=campaign_id,
            condominium_id=condominium_id
        ).select_related('resident', 'reference_membership', 'reference_membership__unit')
        return Response(CampaignParticipantSerializer(participants, many=True).data)

    def post(self, request, condominium_id, campaign_id):
        serializer = CampaignParticipantCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data
        participant = CampaignService.register_participant(
            condominium_id=condominium_id,
            campaign_id=campaign_id,
            resident_id=data['resident_id'],
            reference_membership_id=data['reference_membership_id'],
            authorized_by_id=actor_id
        )
        return Response(CampaignParticipantSerializer(participant).data, status=status.HTTP_201_CREATED)


class CampaignDocumentSnapshotView(APIView):
    """M05: Retorna a árvore de dispositivos do snapshot imutável congelado na campanha."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, campaign_id):
        try:
            tree = CampaignService.get_campaign_snapshot_tree(campaign_id, condominium_id)
            return Response(tree, status=status.HTTP_200_OK)
        except ConsultationCampaign.DoesNotExist:
            return Response({"error": "Campanha não encontrada."}, status=status.HTTP_404_NOT_FOUND)


class CampaignSuggestionListCreateView(APIView):
    """
    CA-25: Envio de sugestão privada recebendo protocolo e versão consultada.
    CA-29 / UI-25: Listagem de sugestões públicas sanitizadas sem dados de autoria.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, campaign_id):
        target_provision_id = request.query_params.get('target_provision_id')
        target_uuid = uuid.UUID(target_provision_id) if target_provision_id else None
        public_sugs = SuggestionService.list_public_suggestions(
            condominium_id=condominium_id,
            campaign_id=campaign_id,
            target_provision_id=target_uuid
        )
        return Response(public_sugs, status=status.HTTP_200_OK)

    def post(self, request, condominium_id, campaign_id):
        serializer = SuggestionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data
        try:
            suggestion = SuggestionService.create_suggestion(
                condominium_id=condominium_id,
                campaign_id=campaign_id,
                participant_id=data['participant_id'],
                text=data['text'],
                justification=data['justification'],
                category=data.get('category', 'redacao'),
                target_provision_id=data.get('target_provision_id'),
                alternative_text=data.get('alternative_text'),
                author_account_id=actor_id
            )
            return Response({
                "id": str(suggestion.id),
                "public_protocol": suggestion.public_protocol,
                "category": suggestion.category,
                "analysis_status": suggestion.analysis_status,
                "editorial_decision": suggestion.editorial_decision,
                "publication_status": suggestion.publication_status,
                "created_at": suggestion.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        except (CampaignNotOpenError, ParticipantNotEligibleError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SuggestionDetailView(APIView):
    """
    CA-32: Consulta de sugestão pública sanitizada (bloqueia se oculta).
    CA-31: Edição da sugestão gerando nova versão pendente de nova moderação.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, suggestion_id):
        try:
            sug = SuggestionService.get_public_suggestion(condominium_id, suggestion_id)
            return Response(sug, status=status.HTTP_200_OK)
        except HiddenSuggestionAccessError as e:
            return Response({"error": str(e), "code": "SUGGESTION_HIDDEN"}, status=status.HTTP_404_NOT_FOUND)
        except Suggestion.DoesNotExist:
            return Response({"error": "Sugestão não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, condominium_id, suggestion_id):
        serializer = SuggestionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data
        try:
            new_rev = SuggestionService.update_suggestion(
                suggestion_id=suggestion_id,
                condominium_id=condominium_id,
                author_account_id=actor_id,
                new_text=data['text'],
                new_justification=data['justification'],
                alternative_text=data.get('alternative_text')
            )
            return Response({
                "suggestion_id": str(suggestion_id),
                "version_number": new_rev.version_number,
                "status": "pending_moderation"
            }, status=status.HTTP_200_OK)
        except Suggestion.DoesNotExist:
            return Response({"error": "Sugestão não encontrada."}, status=status.HTTP_404_NOT_FOUND)


class SuggestionComplementCreateView(APIView):
    """CA-30: Envio de complemento sobre sugestão pública existente (moderado independentemente)."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, suggestion_id):
        serializer = SuggestionComplementCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data
        try:
            complement = SuggestionService.create_complement_suggestion(
                condominium_id=condominium_id,
                parent_published_suggestion_id=suggestion_id,
                participant_id=data['participant_id'],
                text=data['text'],
                justification=data['justification'],
                category=data.get('category', 'redacao'),
                author_account_id=actor_id
            )
            return Response({
                "id": str(complement.id),
                "public_protocol": complement.public_protocol,
                "parent_published_suggestion_id": str(suggestion_id),
                "publication_status": complement.publication_status,
                "created_at": complement.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        except ComplementWithoutParentError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (CampaignNotOpenError, ParticipantNotEligibleError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MySuggestionListView(APIView):
    """M09 / M10 / V21-32: Acompanhamento de sugestões próprias do morador (sem notas internas)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        participant_id = request.query_params.get('participant_id')
        if not participant_id:
            return Response({"error": "Parâmetro 'participant_id' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            sugs = SuggestionService.list_my_suggestions(condominium_id, uuid.UUID(participant_id))
            return Response(sugs, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ModerationQueueListView(APIView):
    """S16 / CA-26: Fila de moderação com 4 dimensões (sem expor identidade por padrão)."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        campaign_id = request.query_params.get('campaign_id')
        analysis_status = request.query_params.get('analysis_status')
        publication_status = request.query_params.get('publication_status')

        camp_uuid = uuid.UUID(campaign_id) if campaign_id else None
        queue = ModerationService.list_moderation_queue(
            condominium_id=condominium_id,
            campaign_id=camp_uuid,
            analysis_status=analysis_status,
            publication_status=publication_status
        )
        return Response(queue, status=status.HTTP_200_OK)


class ModerationTechnicalAnalysisView(APIView):
    """CA-27: Realiza análise técnica da sugestão sem publicar automaticamente."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, suggestion_id):
        serializer = TechnicalAnalysisActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data
        try:
            sug = ModerationService.perform_technical_analysis(
                suggestion_id=suggestion_id,
                condominium_id=condominium_id,
                analyst_account_id=actor_id,
                new_status=data['new_status']
            )
            return Response({
                "id": str(sug.id),
                "analysis_status": sug.analysis_status,
                "publication_status": sug.publication_status
            }, status=status.HTTP_200_OK)
        except AutoPublicationForbiddenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ModerationEditorialDecisionView(APIView):
    """CA-27: Registra decisão editorial (acolhida/parcial/rejeitada/duplicada) sem publicar automaticamente."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, suggestion_id):
        serializer = EditorialDecisionActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data
        try:
            dec = ModerationService.register_editorial_decision(
                suggestion_id=suggestion_id,
                condominium_id=condominium_id,
                decider_account_id=actor_id,
                decision=data['decision'],
                public_shared_reason=data['public_shared_reason'],
                internal_note=data.get('internal_note')
            )
            return Response({
                "id": str(dec.id),
                "decision": dec.decision,
                "public_shared_reason": dec.public_shared_reason,
                "decided_at": dec.decided_at.isoformat()
            }, status=status.HTTP_200_OK)
        except AutoPublicationForbiddenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ModerationPublicationAuthorizeView(APIView):
    """
    S18 / CA-28: Mesa de publicação do síndico.
    Apenas o síndico ativo com mandato pode autorizar a publicação pública sanitizada.
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, suggestion_id):
        serializer = PublicationAuthorizeActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id, user_role = _resolve_actor_and_role(request, condominium_id)
        data = serializer.validated_data

        try:
            pub_rev = ModerationService.authorize_publication(
                suggestion_id=suggestion_id,
                condominium_id=condominium_id,
                actor_role=user_role,
                authorizer_account_id=actor_id,
                sanitized_text=data.get('sanitized_text'),
                sanitized_justification=data.get('sanitized_justification')
            )
            return Response({
                "id": str(pub_rev.id),
                "suggestion_id": str(suggestion_id),
                "sanitized_public_text": pub_rev.sanitized_public_text,
                "sanitized_justification": pub_rev.sanitized_justification,
                "authorized_at": pub_rev.authorized_at.isoformat(),
                "status": "publicada"
            }, status=status.HTTP_200_OK)
        except UnauthorizedPublicationError as e:
            return Response({"error": str(e), "code": "UNAUTHORIZED_PUBLICATION_SINDICO_ONLY"}, status=status.HTTP_403_FORBIDDEN)


class ModerationPublicationHideView(APIView):
    """CA-32: Ocultação da publicação pelo síndico (bloqueia imediatamente de todas as superfícies)."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, suggestion_id):
        serializer = PublicationHideActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id, user_role = _resolve_actor_and_role(request, condominium_id)
        data = serializer.validated_data

        try:
            pub_rev = ModerationService.hide_published_suggestion(
                suggestion_id=suggestion_id,
                condominium_id=condominium_id,
                actor_role=user_role,
                actor_account_id=actor_id,
                reason=data['reason']
            )
            return Response({
                "suggestion_id": str(suggestion_id),
                "status": "oculta",
                "hidden_at": pub_rev.hidden_at.isoformat() if pub_rev and pub_rev.hidden_at else None
            }, status=status.HTTP_200_OK)
        except UnauthorizedPublicationError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


class ModerationIdentityAccessView(APIView):
    """CA-33: Consulta justificada e auditada de dados de autoria/identidade da sugestão."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, suggestion_id):
        serializer = IdentityAccessActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id, user_role = _resolve_actor_and_role(request, condominium_id)
        data = serializer.validated_data

        try:
            identity_data = ModerationService.access_suggestion_identity(
                suggestion_id=suggestion_id,
                condominium_id=condominium_id,
                actor_role=user_role,
                actor_account_id=actor_id,
                justification=data['justification']
            )
            return Response(identity_data, status=status.HTTP_200_OK)
        except IdentityAccessWithoutJustificationError as e:
            return Response({"error": str(e), "code": "IDENTITY_ACCESS_FORBIDDEN"}, status=status.HTTP_403_FORBIDDEN)


# ============================================================================
# FASE 6: CONCORDÂNCIAS CONSULTIVAS E CONSOLIDAÇÃO NA MINUTA
# ============================================================================

class AgreementRegisterView(APIView):
    """
    CA-35: Registro consultivo de concordância sobre versão publicada exata (idempotente).
    CA-36: Retirada da manifestação de concordância com preservação de evento.
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, suggestion_id):
        serializer = ConsultativeAgreementCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            sug = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
            agreement = AgreementService.register_agreement(
                condominium_id=condominium_id,
                campaign_id=sug.campaign_id,
                participant_id=data['participant_id'],
                published_suggestion_revision_id=data['published_suggestion_revision_id'],
                reason=data.get('reason')
            )
            return Response(ConsultativeAgreementSerializer(agreement).data, status=status.HTTP_200_OK)
        except (CampaignClosedForAgreementsError, AuthorCannotAgreeWithOwnSuggestionError, ParticipantNotEligibleError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ElectoralVocabularyForbiddenError as e:
            return Response({"error": str(e), "code": "ELECTORAL_TERMS_FORBIDDEN"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, condominium_id, suggestion_id):
        serializer = AgreementWithdrawSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            sug = Suggestion.objects.get(id=suggestion_id, condominium_id=condominium_id)
            agreement = AgreementService.withdraw_agreement(
                condominium_id=condominium_id,
                campaign_id=sug.campaign_id,
                participant_id=data['participant_id'],
                published_suggestion_revision_id=data['published_suggestion_revision_id'],
                reason=data.get('reason')
            )
            return Response(ConsultativeAgreementSerializer(agreement).data, status=status.HTTP_200_OK)
        except CampaignClosedForAgreementsError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RevisionAgreementStatsView(APIView):
    """
    CA-39: Métricas agregadas por indivíduo e por unidade.
    CA-38 / UI-30: Se hide_counts for True e viewer for morador/público, suprime contagens.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, suggestion_id):
        pub_rev_id = request.query_params.get('published_suggestion_revision_id')
        if not pub_rev_id:
            # Obtém a publicação ativa
            pub_rev = PublishedSuggestionRevision.objects.filter(
                suggestion_id=suggestion_id,
                is_active_publication=True
            ).first()
            if not pub_rev:
                return Response({"error": "Revisão publicada não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            pub_rev_uuid = pub_rev.id
        else:
            pub_rev_uuid = uuid.UUID(pub_rev_id)

        _, actor_role = _resolve_actor_and_role(request, condominium_id)
        has_admin_role = actor_role in ('sindico', 'admin', 'subsyndico', 'comissao')
        viewer_param = request.query_params.get('viewer', 'public').lower()
        is_public = not (has_admin_role and viewer_param in ('admin', 'sindico', 'gestao'))
        try:
            stats = AgreementService.get_revision_agreement_stats(
                condominium_id=condominium_id,
                published_suggestion_revision_id=pub_rev_uuid,
                is_public_viewer=is_public
            )
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MyAgreementListView(APIView):
    """M11: Lista as concordâncias consultivas do morador."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        participant_id = request.query_params.get('participant_id')
        if not participant_id:
            return Response({"error": "Parâmetro 'participant_id' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            agrs = AgreementService.list_my_agreements(condominium_id, uuid.UUID(participant_id))
            return Response(agrs, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SuggestionIncorporationView(APIView):
    """CA-40: Transação atômica que consolida a sugestão acolhida na minuta normativa."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, suggestion_id):
        serializer = SuggestionIncorporationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        actor_id = _get_or_create_actor_id(request)
        data = serializer.validated_data

        try:
            inc = IncorporationService.incorporate_suggestion(
                condominium_id=condominium_id,
                suggestion_id=suggestion_id,
                target_provision_id=data['target_provision_id'],
                incorporated_by_id=actor_id,
                new_text=data['new_text'],
                description=data.get('description'),
                new_label=data.get('new_label')
            )
            return Response(SuggestionIncorporationSerializer(inc).data, status=status.HTTP_201_CREATED)
        except IncorporationIntegrityError as e:
            return Response({"error": str(e), "code": "INCORPORATION_INTEGRITY_ERROR"}, status=status.HTTP_400_BAD_REQUEST)


class CampaignConsultationSnapshotView(APIView):
    """CA-39: Gera fotografia estatística imutável e substitutiva da campanha."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, campaign_id):
        actor_id = _get_or_create_actor_id(request)
        try:
            snap = AgreementService.create_consultation_snapshot(
                condominium_id=condominium_id,
                campaign_id=campaign_id,
                created_by_id=actor_id
            )
            return Response(ConsultationSnapshotSerializer(snap).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# FASE 7: PRESERVAÇÃO E PUBLICAÇÃO DE CONTEÚDO
# ============================================================================

class DocumentFinalPublicPackageView(APIView):
    """
    UI-33 / UI-38 / CA-42 / CA-45: Gera o pacote externo público com manifesto de integridade SHA-256.
    Segrega estritamente o pacote público do relatório interno, omitindo PII e notas confidenciais.
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, document_id):
        actor_id = _get_or_create_actor_id(request)
        try:
            package = PreservationService.generate_final_public_package(
                condominium_id=condominium_id,
                document_id=document_id,
                generated_by_id=actor_id
            )
            return Response(package, status=status.HTTP_201_CREATED)
        except PublicExportExposureError as e:
            return Response({"error": str(e), "code": "PII_OR_INTERNAL_NOTE_EXPOSURE"}, status=status.HTTP_400_BAD_REQUEST)
        except Document.DoesNotExist:
            return Response({"error": "Documento não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class DocumentCommissionInternalReportView(APIView):
    """
    UI-33: Gera relatório interno completo da comissão e síndico com histórico e notas.
    is_public = False.
    """
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, document_id):
        actor_id = _get_or_create_actor_id(request)
        campaign_id = request.data.get('campaign_id')
        camp_uuid = uuid.UUID(campaign_id) if campaign_id else None

        try:
            report = PreservationService.generate_internal_commission_report(
                condominium_id=condominium_id,
                document_id=document_id,
                campaign_id=camp_uuid,
                generated_by_id=actor_id
            )
            return Response(report, status=status.HTTP_201_CREATED)
        except Document.DoesNotExist:
            return Response({"error": "Documento não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class DocumentAssemblyReadingView(APIView):
    """
    CA-45 / UI-38: Modo de leitura pública autorizada para apresentação em assembleia.
    Somente leitura estruturado, sem controles ou módulos de votação ou aprovação vinculante.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, document_id):
        try:
            reading_data = PreservationService.get_assembly_reading_view(
                condominium_id=condominium_id,
                document_id=document_id
            )
            return Response(reading_data, status=status.HTTP_200_OK)
        except ElectoralDeliberationForbiddenError as e:
            return Response({"error": str(e), "code": "ELECTORAL_CONTROLS_FORBIDDEN"}, status=status.HTTP_400_BAD_REQUEST)
        except Document.DoesNotExist:
            return Response({"error": "Documento não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class ExportArtifactDetailView(APIView):
    """Consulta detalhe de um artefato de exportação registrado."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, artifact_id):
        try:
            artifact = ExportArtifact.objects.get(id=artifact_id, condominium_id=condominium_id)
            return Response(ExportArtifactSerializer(artifact).data, status=status.HTTP_200_OK)
        except ExportArtifact.DoesNotExist:
            return Response({"error": "Artefato não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class ManifestVerifyView(APIView):
    """Verifica a integridade dos arquivos de um pacote contra o manifesto SHA-256 registrado."""
    permission_classes = [AllowAny]

    def post(self, request, condominium_id, artifact_id):
        serializer = ManifestVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            result = PreservationService.verify_manifest_integrity(
                artifact_id=artifact_id,
                condominium_id=condominium_id,
                files_content_map=data['files_content_map']
            )
            return Response(result, status=status.HTTP_200_OK)
        except ManifestIntegrityError as e:
            return Response({"error": str(e), "code": "MANIFEST_INTEGRITY_TAMPERED"}, status=status.HTTP_400_BAD_REQUEST)
        except ExportArtifact.DoesNotExist:
            return Response({"error": "Artefato não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class AuditLogsListView(APIView):
    """
    S21A / CA-33: Consulta da trilha imutável de eventos de auditoria e acesso a dados pessoais.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        events = IdentityAuditService.list_access_events(condominium_id=condominium_id)
        serializer = IdentityAccessEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================================
# CONSULTAS PÚBLICAS SIMPLIFICADAS (PDF & Sugestões Ágeis)
# ============================================================================

class PublicConsultationDetailView(APIView):
    """
    Retorna os detalhes públicos da consulta para o morador via token de acesso compartilhado.
    Zero necessidade de login.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            consultation = SimplifiedConsultationService.get_consultation_by_token(token)
            serializer = PublicConsultationDetailSerializer(consultation, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PublicConsultation.DoesNotExist:
            return Response({"error": "Consulta pública não encontrada ou link inválido."}, status=status.HTTP_404_NOT_FOUND)


class PublicConsultationPdfView(APIView):
    """
    Entrega o arquivo PDF da consulta diretamente para o visualizador (iframe) do morador.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            consultation = SimplifiedConsultationService.get_consultation_by_token(token)
        except PublicConsultation.DoesNotExist:
            return Response({"error": "Consulta não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        full_path = os.path.join(media_root, consultation.pdf_file_path)

        if not os.path.exists(full_path):
            return Response({"error": "Arquivo PDF não encontrado no servidor."}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(open(full_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{consultation.pdf_original_name}"'
        return response


class PublicSuggestionSubmitView(APIView):
    """
    Submissão ágil de sugestão de alteração/remoção/inclusão pelo morador via token público.
    """
    permission_classes = [AllowAny]

    def post(self, request, token):
        serializer = PublicSuggestionSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            suggestion = SimplifiedConsultationService.submit_suggestion(
                token=token,
                **serializer.validated_data
            )
            response_serializer = PublicConsultationSuggestionConfirmationSerializer(suggestion)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except PublicConsultation.DoesNotExist:
            return Response({"error": "Consulta pública não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Erro interno ao registrar sugestão: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PublicMySuggestionsListView(APIView):
    """
    Permite ao morador consultar o status de uma sugestão por ele enviada
    EXCLUSIVAMENTE mediante apresentação do número de protocolo secreto (SUG-2026-XXXX).
    
    MEDIDA DE SEGURANÇA DA INFORMAÇÃO (LGPD & Anti-IDOR):
    É terminantemente PROIBIDO filtrar por unidade ou telefone neste endpoint público
    para evitar que terceiros (vizinhos curiosos ou mal-intencionados) visualizem
    sugestões enviadas por outros moradores apenas digitando o número de outro apartamento.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            consultation = SimplifiedConsultationService.get_consultation_by_token(token)
        except PublicConsultation.DoesNotExist:
            return Response({"error": "Consulta pública não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        protocol = request.query_params.get('protocol')
        if not protocol or not protocol.strip():
            # Sem protocolo secreto, não devolve nenhuma sugestão
            return Response([], status=status.HTTP_200_OK)

        # Consulta estrita e unívoca pelo protocolo secreto
        qs = ConsultationSuggestion.objects.filter(
            consultation=consultation,
            protocol__iexact=protocol.strip()
        )

        serializer = PublicConsultationSuggestionConfirmationSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminConsultationListCreateView(APIView):
    """
    Listagem e criação de consultas públicas simplificadas no painel do síndico.
    Suporta upload de PDF multipart/form-data.
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, condominium_id):
        consultations = PublicConsultation.objects.filter(condominium_id=condominium_id).order_by('-created_at')
        items = []
        for c in consultations:
            data = AdminConsultationListCreateSerializer(c).data
            data['suggestions_count'] = ConsultationSuggestion.objects.filter(consultation_id=c.id).count()
            items.append(data)
        return Response(items, status=status.HTTP_200_OK)

    def post(self, request, condominium_id):
        actor_id, role = _resolve_actor_and_role(request, condominium_id)
        title = request.data.get('title')
        document_type = request.data.get('document_type', 'regimento')
        description = request.data.get('description', '')
        deadline = request.data.get('deadline')
        pdf_file = request.FILES.get('pdf_file')

        if not title or not str(title).strip():
            return Response({"error": "Título da consulta é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        if not pdf_file:
            return Response({"error": "Arquivo PDF do documento é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            consultation = SimplifiedConsultationService.create_consultation(
                condominium_id=condominium_id,
                title=str(title),
                document_type=str(document_type),
                pdf_file=pdf_file,
                description=str(description) if description else None,
                created_by_id=actor_id,
                deadline=deadline,
            )
            data = AdminConsultationListCreateSerializer(consultation).data
            data['suggestions_count'] = 0
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Erro ao criar consulta: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class AdminConsultationDetailUpdateDeleteView(APIView):
    """
    Consulta, alteração de status e exclusão de consulta pelo síndico.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, consultation_id):
        try:
            consultation = PublicConsultation.objects.get(id=consultation_id, condominium_id=condominium_id)
            data = AdminConsultationListCreateSerializer(consultation).data
            data['suggestions_count'] = ConsultationSuggestion.objects.filter(consultation_id=consultation.id).count()
            return Response(data, status=status.HTTP_200_OK)
        except PublicConsultation.DoesNotExist:
            return Response({"error": "Consulta não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, condominium_id, consultation_id):
        try:
            consultation = PublicConsultation.objects.get(id=consultation_id, condominium_id=condominium_id)
            if 'status' in request.data:
                new_status = request.data['status']
                if new_status in ('aberta', 'pausada', 'encerrada'):
                    consultation.status = new_status
            if 'title' in request.data:
                consultation.title = request.data['title'].strip()
            if 'description' in request.data:
                consultation.description = request.data['description']
            if 'deadline' in request.data:
                consultation.deadline = request.data['deadline']
            consultation.save()
            data = AdminConsultationListCreateSerializer(consultation).data
            data['suggestions_count'] = ConsultationSuggestion.objects.filter(consultation_id=consultation.id).count()
            return Response(data, status=status.HTTP_200_OK)
        except PublicConsultation.DoesNotExist:
            return Response({"error": "Consulta não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, condominium_id, consultation_id):
        try:
            consultation = PublicConsultation.objects.get(id=consultation_id, condominium_id=condominium_id)
            media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
            full_path = os.path.join(media_root, consultation.pdf_file_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except Exception:
                    pass
            consultation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PublicConsultation.DoesNotExist:
            return Response({"error": "Consulta não encontrada."}, status=status.HTTP_404_NOT_FOUND)


class AdminConsultationSuggestionsListView(APIView):
    """
    Listagem filtrável das sugestões recebidas para acompanhamento pelo síndico.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, consultation_id):
        action_type = request.query_params.get('action_type')
        unit_code = request.query_params.get('unit_code')
        block_tower = request.query_params.get('block_tower')
        search_text = request.query_params.get('search')

        suggestions = SimplifiedConsultationService.list_suggestions(
            condominium_id=condominium_id,
            consultation_id=consultation_id,
            action_type=action_type,
            unit_code=unit_code,
            block_tower=block_tower,
            search_text=search_text,
        )
        serializer = AdminConsultationSuggestionListSerializer(suggestions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminConsultationExportView(APIView):
    """
    Exporta todas as sugestões em CSV para abertura perfeita no Microsoft Excel/Sheets.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id, consultation_id):
        try:
            csv_content = SimplifiedConsultationService.export_suggestions_csv(
                condominium_id=condominium_id,
                consultation_id=consultation_id,
            )
            response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="sugestoes_consulta_{consultation_id}.csv"'
            return response
        except PublicConsultation.DoesNotExist:
            return Response({"error": "Consulta não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Erro na exportação: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CondominiumDashboardMetricsView(APIView):
    """
    Retorna métricas consolidadas e 100% reais para o Painel da Gestão do condomínio ativo.
    Elimina números fictícios/hardcoded e reflete fielmente o estado do banco.
    """
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        if not Condominium.objects.filter(id=condominium_id).exists():
            return Response({"error": "Condomínio não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # 1. Consultas Públicas em PDF
        consultations_open = PublicConsultation.objects.filter(
            condominium_id=condominium_id,
            status='aberta'
        ).count()
        consultations_total = PublicConsultation.objects.filter(
            condominium_id=condominium_id
        ).count()

        # 2. Sugestões de moradores recebidas
        suggestions_count = ConsultationSuggestion.objects.filter(
            condominium_id=condominium_id
        ).count()
        suggestions_pending = ConsultationSuggestion.objects.filter(
            condominium_id=condominium_id,
            status__in=['recebida', 'em_analise']
        ).count()

        # 3. Moradores cadastrados (Pré-cadastros/Cadastros orgânicos sem vínculo + Vínculos ativos)
        reg_count = ResidentRegistration.objects.filter(
            condominium_id=condominium_id,
            status__in=['pendente', 'pre_aprovado', 'ativado', 'aprovado'],
            linked_membership_id__isnull=True
        ).count()
        mem_count = UnitMembership.objects.filter(
            condominium_id=condominium_id,
            membership_status='active'
        ).count()
        residents_count = reg_count + mem_count

        # 4. Estrutura predial (Torres e Unidades)
        buildings_count = Building.objects.filter(
            condominium_id=condominium_id,
            status='active'
        ).count()
        units_count = Unit.objects.filter(
            condominium_id=condominium_id,
            status='active'
        ).count()

        # 5. Projetos normativos (Minutas)
        projects_count = Project.objects.filter(
            condominium_id=condominium_id,
            status='active'
        ).count()

        return Response({
            "condominium_id": str(condominium_id),
            "consultations_open": consultations_open,
            "consultations_total": consultations_total,
            "suggestions_count": suggestions_count,
            "suggestions_pending": suggestions_pending,
            "residents_count": residents_count,
            "registrations_count": reg_count,
            "memberships_count": mem_count,
            "buildings_count": buildings_count,
            "units_count": units_count,
            "projects_count": projects_count,
        }, status=status.HTTP_200_OK)







