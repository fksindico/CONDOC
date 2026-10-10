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
from django.http import HttpResponse
from django.utils import timezone
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
)
from application.identity.services import (
    CondominiumService,
    ResidentRegistrationService,
    MembershipVerificationService,
    RoleService,
    IdentityAuditService,
)
from application.imports.services import ImportService
from application.invitations.services import InvitationService
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
)

# ============================================================================
# FASE 1: SESSÃO E IDENTIDADE
# ============================================================================

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


class CondominiumListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        condos = Condominium.objects.filter(status='active')
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
        buildings = Building.objects.filter(condominium_id=condominium_id, status='active')
        return Response(BuildingSerializer(buildings, many=True).data)

    def post(self, request, condominium_id):
        serializer = BuildingSerializer(data=request.data)
        if serializer.is_valid():
            building = CondominiumService.create_building(
                condominium_id=condominium_id,
                **serializer.validated_data
            )
            return Response(BuildingSerializer(building).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        units = Unit.objects.filter(condominium_id=condominium_id, status='active').select_related('building')
        return Response(UnitSerializer(units, many=True).data)

    def post(self, request, condominium_id):
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data.copy()
            building_id = data.pop('building_id', None)
            unit = CondominiumService.create_unit(
                condominium_id=condominium_id,
                building_id=building_id,
                **data
            )
            return Response(UnitSerializer(unit).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResidentRegistrationListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        registrations = ResidentRegistration.objects.filter(condominium_id=condominium_id)
        return Response(ResidentRegistrationCreateSerializer(registrations, many=True).data)

    def post(self, request, condominium_id):
        serializer = ResidentRegistrationCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data.copy()
            unit_id = data.pop('unit_id')
            registration = ResidentRegistrationService.create_manual_registration(
                condominium_id=condominium_id,
                unit_id=unit_id,
                **data
            )
            return Response(ResidentRegistrationCreateSerializer(registration).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

        actor_account_id = getattr(request.user, 'account_id', None) or uuid.uuid4()
        membership = MembershipVerificationService.verify_membership(
            condominium_id=condominium_id,
            membership_id=membership_id,
            new_status=serializer.validated_data['new_status'],
            method=serializer.validated_data['method'],
            reason=serializer.validated_data['reason'],
            actor_account_id=actor_account_id
        )
        return Response(UnitMembershipListSerializer(membership).data, status=status.HTTP_200_OK)


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

def _get_or_create_actor_id(request):
    actor_id = getattr(request.user, 'account_id', None) or request.data.get('actor_account_id')
    if not actor_id:
        acc = Account.objects.first()
        if not acc:
            acc = Account.objects.create(
                auth_user_id=uuid.uuid4(),
                email="sistema.auditoria@condc.local",
                full_name="Sistema Auditoria"
            )
        actor_id = acc.id
    return actor_id


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

        actor_id = getattr(request.user, 'account_id', None) or uuid.uuid4()
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

        actor_id = getattr(request.user, 'account_id', None) or uuid.uuid4()
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
