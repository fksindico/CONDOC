"""
Módulo de Validação Pré-Voo (Preflight) do Núcleo Documental — CONDOC (ED-OSS-2.0)
Garante a integridade semântica, jurídica e estrutural do documento antes do
congelamento de snapshot imutável ou exportação final (EDOSS-EX-04).
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PreflightIssue:
    severity: str  # 'info', 'warning', 'blocking'
    node_id: Optional[str]
    rule_code: str
    message: str
    location_label: Optional[str] = None


@dataclass
class PreflightReport:
    is_valid: bool
    total_nodes_checked: int
    blocking_count: int
    warning_count: int
    issues: List[PreflightIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_nodes_checked": self.total_nodes_checked,
            "blocking_count": self.blocking_count,
            "warning_count": self.warning_count,
            "issues": [
                {
                    "severity": iss.severity,
                    "node_id": iss.node_id,
                    "rule_code": iss.rule_code,
                    "message": iss.message,
                    "location_label": iss.location_label,
                }
                for iss in self.issues
            ]
        }


class PreflightValidator:
    """Validador de integridade pré-congelamento e pré-exportação oficial."""

    PLACEHOLDER_REGEX = re.compile(r'(\[PREENCHER.*?\]|\{placeholder.*?\}|\[.*?a conferir.*?\])', re.IGNORECASE)

    @classmethod
    def validate_document_tree(
        cls,
        nodes: List[Dict[str, Any]],
        notes: Optional[Dict[str, Any]] = None,
        profile: str = 'clean_working'
    ) -> PreflightReport:
        """
        Executa todas as verificações essenciais sobre a árvore de dispositivos:
        - Todo artigo deve possuir ao menos um caput inicial.
        - Não pode haver referências circulares de parentesco.
        - Não pode haver notas de rodapé referenciadas que não existam (órfãs).
        - Se perfil for 'final_presentation', placeholders de redação são BLOQUEANTES.
        """
        issues: List[PreflightIssue] = []
        notes = notes or {}
        is_final_profile = (profile in ('final_presentation', 'preservation'))

        node_map = {str(n.get('id') or n.get('provision_id')): n for n in nodes if n.get('id') or n.get('provision_id')}
        article_has_caput: Dict[str, bool] = {}

        for n in nodes:
            nid = str(n.get('id') or n.get('provision_id', ''))
            kind = n.get('kind') or n.get('type', '')
            label = n.get('label') or n.get('rendered_label', '')
            text = n.get('text') or ''
            parent_id = str(n.get('parent_id') or n.get('parent_provision_id', '')) if (n.get('parent_id') or n.get('parent_provision_id')) else None

            # 1. Rastrear caput em artigos
            if kind == 'article':
                if nid not in article_has_caput:
                    article_has_caput[nid] = False
            elif kind == 'caput' and parent_id:
                article_has_caput[parent_id] = True

            # 2. Verificar hierarquia de parentesco
            if parent_id and parent_id not in node_map:
                issues.append(PreflightIssue(
                    severity='blocking',
                    node_id=nid,
                    rule_code='EDOSS-BL-01',
                    message=f"Dispositivo aponta para elemento pai inexistente ({parent_id}).",
                    location_label=label
                ))

            # 3. Verificar ciclo direto
            if parent_id and parent_id == nid:
                issues.append(PreflightIssue(
                    severity='blocking',
                    node_id=nid,
                    rule_code='EDOSS-BL-03',
                    message="Referência circular: elemento não pode ser pai de si mesmo.",
                    location_label=label
                ))

            # 4. Detecção de placeholders não resolvidos
            if text and cls.PLACEHOLDER_REGEX.search(text):
                severity = 'blocking' if is_final_profile else 'warning'
                issues.append(PreflightIssue(
                    severity=severity,
                    node_id=nid,
                    rule_code='EDOSS-EX-04',
                    message=f"Contém texto provisório ou placeholder não preenchido: '{text[:60]}...'",
                    location_label=label
                ))

            # Se nó contiver body com runs/placeholders em rich JSON
            body = n.get('body')
            if isinstance(body, list):
                for block in body:
                    runs = block.get('runs', []) if isinstance(block, dict) else []
                    for run in runs:
                        if isinstance(run, dict) and run.get('type') == 'placeholder' and not run.get('resolved', False):
                            severity = 'blocking' if is_final_profile else 'warning'
                            issues.append(PreflightIssue(
                                severity=severity,
                                node_id=nid,
                                rule_code='EDOSS-EX-04',
                                message=f"Placeholder pendente no bloco de redação: {run.get('key', 'desconhecido')}",
                                location_label=label
                            ))

            # 5. Validação de notas de rodapé referenciadas
            note_refs = n.get('note_references') or []
            for nref in note_refs:
                ref_id = str(nref.get('note_id') if isinstance(nref, dict) else nref)
                if ref_id not in notes:
                    issues.append(PreflightIssue(
                        severity='blocking',
                        node_id=nid,
                        rule_code='EDOSS-NT-06',
                        message=f"Dispositivo referencia nota de rodapé inexistente ou órfã ({ref_id}).",
                        location_label=label
                    ))

        # Conferir se algum artigo ficou sem caput
        for art_id, has_caput in article_has_caput.items():
            if not has_caput:
                art_node = node_map.get(art_id, {})
                art_label = art_node.get('label') or art_node.get('rendered_label', 'Artigo sem identificação')
                issues.append(PreflightIssue(
                    severity='blocking',
                    node_id=art_id,
                    rule_code='EDOSS-BL-02',
                    message=f"O artigo '{art_label}' não possui um caput inicial obrigatório.",
                    location_label=art_label
                ))

        blocking = sum(1 for iss in issues if iss.severity == 'blocking')
        warnings = sum(1 for iss in issues if iss.severity == 'warning')

        return PreflightReport(
            is_valid=(blocking == 0),
            total_nodes_checked=len(nodes),
            blocking_count=blocking,
            warning_count=warnings,
            issues=issues
        )
