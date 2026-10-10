"""
Serviços de Aplicação para Preservação e Publicação de Conteúdo — CONDC (Fase 7)
Implementa os casos de uso para os critérios CA-41, CA-42, CA-45, UI-33, UI-38 do PRD Mestre v3.0.
"""
import uuid
import json
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone

from domain.preservation.invariants import (
    DISCLAIMER_FINAL_PUBLICATION,
    calculate_content_sha256,
    calculate_manifest_sha256,
    assert_public_export_contains_no_pii_or_internal_notes,
    assert_assembly_reading_view_has_no_voting_controls,
)
from domain.preservation.exceptions import (
    PublicExportExposureError,
    ManifestIntegrityError,
    ElectoralDeliberationForbiddenError,
)
from infrastructure.models import (
    Condominium,
    Account,
    Document,
    DocumentSnapshot,
    Provision,
    ProvisionRevision,
    ConsultationCampaign,
    Suggestion,
    SuggestionRevision,
    SuggestionEditorialDecision,
    SuggestionIncorporation,
    ConsultationSnapshot,
    ExportArtifact,
)
from application.comparison.services import ExportService, ComparisonService


class PreservationService:
    """Orquestra pacotes de preservação externa com manifesto SHA-256 e relatórios internos da comissão."""

    @staticmethod
    @transaction.atomic
    def generate_final_public_package(
        condominium_id: uuid.UUID,
        document_id: uuid.UUID,
        generated_by_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        UI-33 / UI-38 / CA-42 / CA-45:
        Gera pacote externo público para a assembleia e condomínio:
        1. Minuta limpa final (JSON estruturado e Texto normativo).
        2. Relatório DePara consolidado de origens e alterações.
        3. Manifesto de integridade com hashes SHA-256 de cada arquivo.
        4. Aviso legal obrigatório de que não constitui votação nem registro cartorial.
        """
        document = Document.objects.get(id=document_id, condominium_id=condominium_id)

        clean_doc_payload = ExportService.export_clean_document(condominium_id, document_id)
        clean_text_content = ExportService.export_clean_text(condominium_id, document_id)
        depara_payload = ComparisonService.generate_depara_report(condominium_id, document_id)

        # UI-33: Auditoria estrita contra vazamento de PII ou notas internas no pacote público
        assert_public_export_contains_no_pii_or_internal_notes(clean_doc_payload)
        assert_public_export_contains_no_pii_or_internal_notes(depara_payload)

        # Serializa conteúdos canonicamente
        json_clean_str = json.dumps(clean_doc_payload, sort_keys=True, indent=2, ensure_ascii=False)
        json_depara_str = json.dumps(depara_payload, sort_keys=True, indent=2, ensure_ascii=False)

        # Gera entradas do manifesto com hashes SHA-256
        manifest_files = [
            {
                "path": "minuta_limpa_final.json",
                "sha256": calculate_content_sha256(json_clean_str),
                "size_bytes": len(json_clean_str.encode('utf-8')),
                "mime_type": "application/json"
            },
            {
                "path": "minuta_limpa_final.txt",
                "sha256": calculate_content_sha256(clean_text_content),
                "size_bytes": len(clean_text_content.encode('utf-8')),
                "mime_type": "text/plain"
            },
            {
                "path": "relatorio_depara_consolidado.json",
                "sha256": calculate_content_sha256(json_depara_str),
                "size_bytes": len(json_depara_str.encode('utf-8')),
                "mime_type": "application/json"
            }
        ]

        manifest_hash = calculate_manifest_sha256(manifest_files)

        artifact = ExportArtifact.objects.create(
            condominium_id=condominium_id,
            document=document,
            kind='pacote_externo_publico',
            status='concluido',
            is_public=True,
            manifest_hash=manifest_hash,
            files_manifest=manifest_files,
            disclaimer=DISCLAIMER_FINAL_PUBLICATION,
            generated_by_id=generated_by_id
        )

        return {
            "artifact_id": str(artifact.id),
            "document_id": str(document.id),
            "document_title": document.title,
            "manifest_hash": manifest_hash,
            "files_manifest": manifest_files,
            "disclaimer": DISCLAIMER_FINAL_PUBLICATION,
            "files_content": {
                "minuta_limpa_final.json": clean_doc_payload,
                "minuta_limpa_final.txt": clean_text_content,
                "relatorio_depara_consolidado.json": depara_payload
            },
            "created_at": artifact.created_at.isoformat()
        }

    @staticmethod
    @transaction.atomic
    def generate_internal_commission_report(
        condominium_id: uuid.UUID,
        document_id: uuid.UUID,
        campaign_id: Optional[uuid.UUID] = None,
        generated_by_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        UI-33: Gera relatório interno completo e restrito da comissão de revisão e síndico:
        Contém o histórico detalhado de todas as sugestões, pareceres, notas internas e decisões.
        is_public = False.
        """
        document = Document.objects.get(id=document_id, condominium_id=condominium_id)

        suggestions_query = Suggestion.objects.filter(condominium_id=condominium_id)
        if campaign_id:
            suggestions_query = suggestions_query.filter(campaign_id=campaign_id)

        detailed_suggestions = []
        for sug in suggestions_query.select_related('target_provision'):
            latest_rev = SuggestionRevision.objects.filter(suggestion=sug).order_by('-version_number').first()
            decision = SuggestionEditorialDecision.objects.filter(suggestion=sug).order_by('-decided_at').first()
            inc = SuggestionIncorporation.objects.filter(suggestion=sug).first()

            detailed_suggestions.append({
                "suggestion_id": str(sug.id),
                "public_protocol": sug.public_protocol,
                "category": sug.category,
                "target_provision_label": sug.target_provision.kind if sug.target_provision else None,
                "text": latest_rev.text if latest_rev else "",
                "justification": latest_rev.justification if latest_rev else "",
                "analysis_status": sug.analysis_status,
                "editorial_decision": sug.editorial_decision,
                "public_shared_reason": decision.public_shared_reason if decision else None,
                "internal_note": decision.internal_note if decision else None,  # Permitido no relatório interno
                "incorporation_status": sug.incorporation_status,
                "incorporated_provision_revision_id": str(inc.provision_revision_id) if inc else None,
                "created_at": sug.created_at.isoformat()
            })

        report_payload = {
            "document_id": str(document.id),
            "document_title": document.title,
            "report_kind": "relatorio_interno_comissao",
            "is_internal_confidential": True,
            "total_suggestions_analyzed": len(detailed_suggestions),
            "total_suggestions_incorporated": sum(1 for s in detailed_suggestions if s['incorporation_status'] == 'incorporada'),
            "suggestions": detailed_suggestions,
            "generated_at": timezone.now().isoformat()
        }

        report_json = json.dumps(report_payload, sort_keys=True, indent=2, ensure_ascii=False)
        report_sha = calculate_content_sha256(report_json)

        files_manifest = [
            {
                "path": "relatorio_interno_comissao.json",
                "sha256": report_sha,
                "size_bytes": len(report_json.encode('utf-8')),
                "mime_type": "application/json"
            }
        ]
        manifest_hash = calculate_manifest_sha256(files_manifest)

        artifact = ExportArtifact.objects.create(
            condominium_id=condominium_id,
            document=document,
            kind='relatorio_interno_comissao',
            status='concluido',
            is_public=False,
            manifest_hash=manifest_hash,
            files_manifest=files_manifest,
            disclaimer="Documento confidencial de governança interna da comissão de revisão e síndico.",
            generated_by_id=generated_by_id
        )

        return {
            "artifact_id": str(artifact.id),
            "document_id": str(document.id),
            "manifest_hash": manifest_hash,
            "is_public": False,
            "report_content": report_payload,
            "created_at": artifact.created_at.isoformat()
        }

    @staticmethod
    def verify_manifest_integrity(
        artifact_id: uuid.UUID,
        condominium_id: uuid.UUID,
        files_content_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Verifica a integridade criptográfica dos arquivos do pacote contra o manifesto SHA-256.
        Levanta ManifestIntegrityError se houver qualquer adulteração.
        """
        artifact = ExportArtifact.objects.get(id=artifact_id, condominium_id=condominium_id)
        verified_files = []

        for entry in artifact.files_manifest:
            file_path = entry['path']
            expected_sha = entry['sha256']
            content = files_content_map.get(file_path)

            if content is None:
                raise ManifestIntegrityError(f"Arquivo '{file_path}' ausente no pacote fornecido para verificação.")

            computed_sha = calculate_content_sha256(content)
            if computed_sha != expected_sha:
                raise ManifestIntegrityError(
                    f"Divergência de hash SHA-256 no arquivo '{file_path}'. "
                    f"Esperado: {expected_sha}, Calculado: {computed_sha}."
                )

            verified_files.append({"path": file_path, "sha256": computed_sha, "valid": True})

        return {
            "artifact_id": str(artifact.id),
            "integrity_verified": True,
            "manifest_hash": artifact.manifest_hash,
            "verified_files": verified_files
        }

    @staticmethod
    def get_assembly_reading_view(
        condominium_id: uuid.UUID,
        document_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        CA-45 / UI-38: Modo de leitura pública autorizada para apresentação em assembleia.
        Somente leitura estruturado, sem controles de votação ou deliberação.
        """
        document = Document.objects.get(id=document_id, condominium_id=condominium_id)
        clean_doc = ExportService.export_clean_document(condominium_id, document_id)

        # Garante que nenhum controle deliberativo seja introduzido
        available_controls = ["scroll", "zoom", "search", "export_pdf", "fullscreen"]
        assert_assembly_reading_view_has_no_voting_controls(available_controls)

        return {
            "document_id": str(document.id),
            "title": document.title,
            "document_type": document.type,
            "reading_mode": "assembleia_somente_leitura",
            "available_controls": available_controls,
            "has_voting_module": False,
            "provisions": clean_doc['provisions'],
            "disclaimer": DISCLAIMER_FINAL_PUBLICATION
        }
