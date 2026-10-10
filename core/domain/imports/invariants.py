"""
Invariantes de Domínio para Importação Cadastral — CONDC (Fase 2)
Regras de segurança, mitigação de injeção de fórmulas e preservação textual.
"""
from typing import Any, Optional
from domain.identity.invariants import assert_no_electoral_intent
from .exceptions import (
    FormulaInjectionDetectedError,
    ImportPreviewOutdatedError,
)

FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')

def sanitize_csv_cell(value: Any) -> str:
    """
    Neutraliza conteúdo interpretável como fórmula em planilhas/CSVs (CWE-1236, PRD 8).
    Se o valor iniciar com =, +, -, @, \\t ou \\r, prefixa com apóstrofo (') para desarmar execução.
    """
    if value is None:
        return ""
    str_val = str(value)
    if str_val.startswith(FORMULA_PREFIXES):
        return f"'{str_val}"
    return str_val


def assert_no_formula_injection(raw_value: Any) -> None:
    """
    Rejeita dados de cadastro que contenham fórmulas maliciosas disfarçadas.
    """
    if raw_value is None:
        return
    str_val = str(raw_value).strip()
    if str_val.startswith(FORMULA_PREFIXES) and len(str_val) > 1:
        # Permite números negativos simples como "-1", mas rejeita fórmulas como "=SUM", "+cmd", "@SUM", "-2+cmd"
        if str_val.startswith(('-', '+')) and str_val[1:].replace('.', '', 1).isdigit():
            return
        raise FormulaInjectionDetectedError(
            f"Tentativa de injeção de fórmula ou caractere de execução perigoso detectado: '{str_val[:10]}...'"
        )


def preserve_textual_code(val: Any) -> str:
    """
    Preserva zeros iniciais em identificadores de unidades, torres e blocos (V21-08).
    Exemplos: '0101' -> '0101', '02' -> '02', '004B' -> '004B'.
    """
    if val is None:
        return ""
    str_val = str(val).strip()
    # Remove pontuação excessiva de float caso venha como "101.0"
    if str_val.endswith(".0") and str_val[:-2].isdigit():
        return str_val[:-2]
    return str_val


def assert_revision_matches(current_revision: int, expected_revision: int) -> None:
    """
    Garante concorrência otimista e validação de prévia atualizada (V21-13).
    """
    if current_revision != expected_revision:
        raise ImportPreviewOutdatedError(
            f"A prévia do lote foi modificada (revisão atual: {current_revision}, revisão enviada: {expected_revision}). "
            "Atualize a prévia antes de confirmar."
        )
