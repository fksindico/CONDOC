"""
Views da API v1 — CONDC
Controladores REST para Identidade, Estrutura Física e Sessão BFF.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
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
)
from application.identity.services import (
    CondominiumService,
    ResidentRegistrationService,
    MembershipVerificationService,
    RoleService,
    IdentityAuditService,
)
from .serializers import (
    CondominiumSerializer,
    BuildingSerializer,
    UnitSerializer,
    ResidentRegistrationCreateSerializer,
    UnitMembershipListSerializer,
    VerifyMembershipActionSerializer,
    RoleAssignmentSerializer,
)

class SessionInfoView(APIView):
    """
    Retorna o estado da sessão do usuário autenticado (BFF).
    """
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
    """Listagem e cadastro de condomínios."""
    permission_classes = [AllowAny]  # Criador de condomínio ou setup

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
    """Listagem e cadastro de torres/blocos em um condomínio."""
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
    """Listagem e cadastro de unidades autônomas."""
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
    """
    Pré-cadastro manual de moradores (CA-02: cria registro sem conta automática).
    """
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
    """Listagem de vínculos de moradores com unidades."""
    permission_classes = [AllowAny]

    def get(self, request, condominium_id):
        memberships = UnitMembership.objects.filter(
            condominium_id=condominium_id
        ).select_related('unit', 'resident')
        return Response(UnitMembershipListSerializer(memberships, many=True).data)


class VerifyMembershipActionView(APIView):
    """
    Validação documental auditada de vínculo (CA-12, CA-15).
    """
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
    """Gestão de papéis no condomínio (síndico, comissão, morador)."""
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
