"""
Invariantes de Domínio de Identidade — CONDC
Implementação das regras de negócio e limites inegociáveis de governança.
"""
from typing import Optional, List
from .exceptions import (
    ElectoralFeatureForbiddenError,
    TenantMismatchError,
    MissingAuditPurposeError,
    UnauthorizedPublicationError,
    DuplicateBuildingError,
    DuplicateUnitError,
)

FORBIDDEN_ELECTORAL_TERMS = {
    "voto", "votacao", "eleicao", "apuracao", "quorum", "peso_eleitoral",
    "fracao_ponderada", "assembleia_deliberativa", "aprovacao_vinculante"
}

def assert_no_electoral_intent(context_name: str, payload: Optional[dict] = None) -> None:
    """
    Garante a proibição terminante e inegociável de termos e mecânicas eleitorais (CA-45).
    """
    name_lower = context_name.lower()
    for term in FORBIDDEN_ELECTORAL_TERMS:
        if term in name_lower:
            raise ElectoralFeatureForbiddenError(
                f"Termo eleitoral ou deliberativo proibido detectado: '{term}'. "
                "O sistema CONDC veda terminantemente votações, eleições ou apuração de quórum."
            )
    if payload:
        for k, v in payload.items():
            if any(term in str(k).lower() or (isinstance(v, str) and term in v.lower()) for term in FORBIDDEN_ELECTORAL_TERMS):
                raise ElectoralFeatureForbiddenError(
                    f"Mecânica eleitoral detectada no payload ('{k}'). "
                    "Operação abortada por violação dos limites normativos do PRD Mestre v3.0."
                )

def assert_same_tenant(tenant_a: str, tenant_b: str, resource_name: str = "Recurso") -> None:
    """
    Garante o isolamento absoluto entre tenants (CA-01).
    """
    if str(tenant_a) != str(tenant_b):
        raise TenantMismatchError(
            f"Violação de isolamento multi-tenant: {resource_name} pertence a outro condomínio."
        )

def assert_audit_purpose(purpose: Optional[str]) -> None:
    """
    Exige justificativa expressa para qualquer acesso a dados de identidade pessoal (CA-33).
    """
    if not purpose or len(purpose.strip()) < 5:
        raise MissingAuditPurposeError(
            "Acesso negado: a consulta de dados de identidade exige justificativa de auditoria de no mínimo 5 caracteres."
        )

def assert_sindico_publication_authority(roles: List[str]) -> None:
    """
    Garante que apenas o síndico ativo possui autoridade de publicação (CA-28).
    Administradores ou comissões NÃO podem publicar sem o papel de síndico.
    """
    if "sindico" not in [r.lower() for r in roles]:
        raise UnauthorizedPublicationError(
            "Apenas o síndico ativo tem autoridade para publicar documentos ou revisões públicas."
        )

def assert_unique_building_code(is_duplicate: bool, code: str) -> None:
    """
    Garante a unicidade do código do prédio/torre dentro do condomínio (UQ-BUILDING-01).
    """
    if is_duplicate:
        raise DuplicateBuildingError(
            f"Torre/Bloco com código '{code}' já existe neste condomínio."
        )

def assert_unique_unit_code(is_duplicate: bool, code: str) -> None:
    """
    Garante a unicidade do código da unidade dentro da torre/condomínio (UQ-UNIT-01).
    """
    if is_duplicate:
        raise DuplicateUnitError(
            f"Unidade com código '{code}' já existe para esta torre/condomínio."
        )

