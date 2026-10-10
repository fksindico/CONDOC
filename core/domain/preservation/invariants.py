"""
Invariantes de Domínio para Preservação e Publicação de Conteúdo — CONDC (Fase 7)
PRD Mestre v3.0 (Critérios CA-41, CA-42, CA-45, UI-33, UI-38)
"""
import hashlib
import json
from typing import Any, Dict, List

from .exceptions import (
    PublicExportExposureError,
    ManifestIntegrityError,
    ElectoralDeliberationForbiddenError,
)

DISCLAIMER_FINAL_PUBLICATION = (
    "Minuta consolidada para subsidiar deliberação assemblear. A plataforma CONDC apoia a gestão "
    "e a redação prévia e NÃO realiza votação, apuração de votos, cálculo de quórum de assembleia, "
    "aprovação vinculante ou registro cartorial."
)

FORBIDDEN_PII_KEYS = {
    'author_account_id', 'resident_id', 'email', 'phone', 'phone_e164',
    'internal_note', 'internal_notes', 'auth_user_id', 'session_token_hash'
}

FORBIDDEN_DELIBERATIVE_CONTROLS = {
    'votar', 'aprovar_em_assembleia', 'apurar_votos', 'calcular_quorum',
    'eleger', 'voto_sim', 'voto_nao', 'abstencao'
}


def calculate_content_sha256(content: str) -> str:
    """Calcula hash SHA-256 reproduzível para o conteúdo de um arquivo do pacote (normaliza quebras de linha)."""
    normalized = content.replace('\r\n', '\n')
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def calculate_manifest_sha256(manifest_entries: List[Dict[str, Any]]) -> str:
    """Calcula hash consolidado do manifesto a partir da ordenação canônica dos arquivos."""
    canonical_list = sorted(manifest_entries, key=lambda x: x.get('path', ''))
    canonical_json = json.dumps(canonical_list, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()


def assert_public_export_contains_no_pii_or_internal_notes(data: Any, path: str = "root") -> None:
    """
    UI-33: Garante que pacotes públicos externos não contenham PII de moradores nem notas internas.
    Varre recursivamente dicionários e listas.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k in FORBIDDEN_PII_KEYS:
                raise PublicExportExposureError(
                    f"Vazamento de dado confidencial '{k}' detectado no caminho '{path}.{k}' do pacote público."
                )
            assert_public_export_contains_no_pii_or_internal_notes(v, path=f"{path}.{k}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            assert_public_export_contains_no_pii_or_internal_notes(item, path=f"{path}[{idx}]")


def assert_assembly_reading_view_has_no_voting_controls(controls: List[str]) -> None:
    """
    CA-45 / UI-38: Garante que o modo de leitura para assembleia não contenha controles de votação ou deliberação.
    """
    for ctrl in controls:
        if ctrl.lower() in FORBIDDEN_DELIBERATIVE_CONTROLS:
            raise ElectoralDeliberationForbiddenError(
                f"Controle deliberativo proibido '{ctrl}'. O modo assembleia é estritamente de leitura informativa."
            )
