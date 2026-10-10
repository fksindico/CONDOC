"""
Invariantes de Domínio para Concordâncias Consultivas e Consolidação — CONDC (Fase 6)
PRD Mestre v3.0 (Critérios CA-35 a CA-40, CA-45, V21-29 a V21-31, V21-34, V21-37)
"""
from typing import Any, Dict, List, Set, Optional
import uuid

from .exceptions import (
    CampaignClosedForAgreementsError,
    AuthorCannotAgreeWithOwnSuggestionError,
    ElectoralVocabularyForbiddenError,
    SubstantialChangeAgreementTransferForbiddenError,
    IncorporationIntegrityError,
)

DISCLAIMER_CONSULTATIVE_AGREEMENT = (
    "Manifestação consultiva sobre esta redação. Não constitui voto, eleição, "
    "quórum de assembleia, aprovação vinculante ou alteração da Convenção/Regimento."
)

PROHIBITED_ELECTORAL_TERMS = (
    "voto",
    "votacao",
    "votação",
    "apuracao",
    "apuração",
    "quorum",
    "quórum",
    "eleicao",
    "eleição",
    "aprovacao vinculante",
    "aprovação vinculante",
    "peso eleitoral",
    "peso por fração",
    "peso por fracao"
)


def assert_no_electoral_terms(text: str) -> None:
    """
    CA-45: Proibição terminante de termos eleitorais, cálculo de quórum ou apuração de votos.
    Garante que textos e relatórios não empreguem vocabulário eleitoral indevido.
    """
    lower = text.lower()
    for term in PROHIBITED_ELECTORAL_TERMS:
        if term in lower:
            raise ElectoralVocabularyForbiddenError(
                f"Uso do termo proibido '{term}'. O sistema veda terminantemente votações, "
                f"eleições, cálculo de quórum de assembleia e apuração vinculante."
            )


def assert_campaign_allows_agreements(campaign_state: str, allow_agreements: bool = True) -> None:
    """Valida se a campanha de consulta pública está aberta e permite registro de concordâncias."""
    if campaign_state != 'aberta':
        raise CampaignClosedForAgreementsError(
            f"Campanha não está aberta para manifestações consultivas (estado atual: {campaign_state})."
        )
    if not allow_agreements:
        raise CampaignClosedForAgreementsError(
            "Registro de concordâncias consultivas desativado nas configurações da campanha."
        )


def assert_author_cannot_agree_with_own_suggestion(
    author_account_id: Optional[uuid.UUID],
    participant_account_id: Optional[uuid.UUID]
) -> None:
    """
    PRD 257: Autor não acrescenta concordância à própria contribuição.
    Impede que o morador infle artificialmente o apoio de sua própria sugestão.
    """
    if author_account_id and participant_account_id and author_account_id == participant_account_id:
        raise AuthorCannotAgreeWithOwnSuggestionError(
            "O autor de uma sugestão não pode registrar manifestação de concordância sobre a própria contribuição."
        )


def calculate_agreement_metrics(
    active_agreements: List[Dict[str, Any]],
    total_eligible_residents: int,
    total_eligible_units: int,
    disclaimer: str = DISCLAIMER_CONSULTATIVE_AGREEMENT
) -> Dict[str, Any]:
    """
    CA-39 / V21-30 / V21-34 / UI-31 / S19:
    Calcula métricas agregadas em duas dimensões estritamente segregadas:
    1. Por indivíduo (pessoas únicas concordantes: distinct resident_id).
    2. Por unidade (unidades autônomas com pelo menos uma concordância: distinct unit_id).
    V21-30: Várias unidades da mesma pessoa NÃO multiplicam apoio individual (1 pessoa = 1 apoio).
    Apresenta denominadores de habilitados e ressalva legal permanente.
    """
    unique_residents: Set[str] = set()
    unique_units: Set[str] = set()

    for agr in active_agreements:
        if agr.get('active', True):
            res_id = str(agr.get('resident_id'))
            unit_id = str(agr.get('unit_id'))
            if res_id:
                unique_residents.add(res_id)
            if unit_id:
                unique_units.add(unit_id)

    count_individuals = len(unique_residents)
    count_units = len(unique_units)

    pct_individuals = round((count_individuals / total_eligible_residents * 100), 1) if total_eligible_residents > 0 else 0.0
    pct_units = round((count_units / total_eligible_units * 100), 1) if total_eligible_units > 0 else 0.0

    return {
        "concordant_individuals": count_individuals,
        "eligible_individuals_denominator": total_eligible_residents,
        "percentage_individuals": pct_individuals,
        "concordant_units": count_units,
        "eligible_units_denominator": total_eligible_units,
        "percentage_units": pct_units,
        "disclaimer": disclaimer,
        "is_consultative_only": True
    }


def sanitize_public_metrics_payload(stats: Dict[str, Any], hide_counts: bool = False) -> Dict[str, Any]:
    """
    CA-38 / V21-31 / UI-30:
    Se hide_counts for True, suprime contagens numéricas e percentuais de concordâncias do payload público.
    Envia apenas o aviso legal de voluntariedade e estado da consulta.
    """
    if hide_counts:
        return {
            "hide_counts": True,
            "status": "contagens_ocultas",
            "disclaimer": stats.get("disclaimer", DISCLAIMER_CONSULTATIVE_AGREEMENT),
            "is_consultative_only": True
        }
    return dict(stats)
