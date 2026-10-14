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


def mask_personal_name(name: Optional[str]) -> str:
    """
    LGPD / CA-33: Mascara nome pessoal para papéis não administrativos (ex: Comissão, Conselho).
    Ex: 'Carlos Eduardo Silva' -> 'C***** E****** S****'
    """
    if not name or not name.strip():
        return "Anônimo"
    parts = name.strip().split()
    masked = []
    for p in parts:
        if len(p) <= 2:
            masked.append(p[0] + "*")
        else:
            masked.append(p[0] + "*" * (len(p) - 1))
    return " ".join(masked)


def mask_phone_number(phone: Optional[str]) -> str:
    """
    LGPD / CA-33: Mascara telefone/WhatsApp para papéis não administrativos.
    Ex: '11987654321' -> '(11) 9****-**21'
    """
    if not phone or not phone.strip():
        return "—"
    digits = "".join(filter(str.isdigit, phone))
    if len(digits) >= 10:
        ddd = digits[:2]
        first = digits[2] if len(digits) == 11 else ""
        last = digits[-2:]
        return f"({ddd}) {first}****-**{last}"
    return "—"


def mask_email_address(email: Optional[str]) -> str:
    """
    LGPD / CA-33: Mascara endereço de e-mail para papéis não administrativos.
    Ex: 'carlos.silva@provedor.com.br' -> 'c***a@p***.com.br'
    """
    if not email or not email.strip() or '@' not in email:
        return "—"
    user, domain = email.strip().split('@', 1)
    masked_user = user[0] + "***" + (user[-1] if len(user) > 2 else "")
    domain_parts = domain.split('.')
    masked_domain = domain_parts[0][0] + "***" if domain_parts else "***"
    tld = ".".join(domain_parts[1:]) if len(domain_parts) > 1 else "com"
    return f"{masked_user}@{masked_domain}.{tld}"


