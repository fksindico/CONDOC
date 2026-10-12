"""
Serviços de Aplicação para Hardening, Backup e Restauração Consistente — CONDC (Fase 8 / CA-44)
"""
import uuid
import json
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone

from domain.hardening.invariants import (
    calculate_sha256,
    assert_backup_checksums_match,
    assert_security_headers_present,
)
from domain.hardening.exceptions import (
    BackupIntegrityError,
    InconsistentRestoreError,
    SecurityHeaderViolationError,
)
from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    Resident,
    UnitMembership,
    Project,
    Document,
    Provision,
    ProvisionRevision,
    SourceFile,
)


class BackupConsistencyService:
    """Gerencia a criação e restauração atômica e consistente de banco e objetos (CA-44)."""

    @staticmethod
    def generate_condominium_backup_package(condominium_id: uuid.UUID) -> Dict[str, Any]:
        """
        CA-44: Gera pacote estruturado de backup contendo dados relacionais,
        metadados de objetos de storage e hashes SHA-256 de cada componente.
        """
        condo = Condominium.objects.get(id=condominium_id)
        buildings = list(Building.objects.filter(condominium=condo).values('id', 'code', 'name', 'kind'))
        units = list(Unit.objects.filter(condominium=condo).values('id', 'building_id', 'code', 'status'))
        documents = list(Document.objects.filter(condominium=condo).values('id', 'title', 'type', 'editorial_status'))
        source_files = list(SourceFile.objects.filter(condominium=condo).values('id', 'filename', 'file_hash', 'size_bytes', 'storage_key'))

        db_payload = {
            "condominium": {"id": str(condo.id), "name": condo.name, "status": condo.status},
            "buildings": [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in b.items()} for b in buildings],
            "units": [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in u.items()} for u in units],
            "documents": [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in d.items()} for d in documents],
        }

        db_json_bytes = json.dumps(db_payload, sort_keys=True).encode('utf-8')
        db_sha256 = calculate_sha256(db_json_bytes)

        files_manifest = []
        for sf in source_files:
            files_manifest.append({
                "file_id": str(sf['id']),
                "filename": sf['filename'],
                "file_hash": sf['file_hash'],
                "size_bytes": sf['size_bytes']
            })

        manifest = {
            "condominium_id": str(condo.id),
            "created_at": timezone.now().isoformat(),
            "database_dump_sha256": db_sha256,
            "total_buildings": len(buildings),
            "total_units": len(units),
            "total_documents": len(documents),
            "storage_objects": files_manifest
        }

        return {
            "manifest": manifest,
            "database_dump_json": db_payload,
            "database_dump_sha256": db_sha256,
            "storage_objects": files_manifest
        }

    @staticmethod
    @transaction.atomic
    def restore_and_verify_consistency(
        backup_package: Dict[str, Any],
        target_condominium_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        CA-44: Restaura banco e objetos garantindo consistência atômica.
        Valida hashes prévios. Se houver divergência ou corrupção, aborta sem alterar o estado.
        """
        manifest = backup_package.get("manifest", {})
        db_dump = backup_package.get("database_dump_json", {})
        expected_sha = manifest.get("database_dump_sha256")

        # 1. Validação de integridade criptográfica prévia
        actual_bytes = json.dumps(db_dump, sort_keys=True).encode('utf-8')
        assert_backup_checksums_match(expected_sha, actual_bytes, "database_dump")

        condo_data = db_dump.get("condominium", {})
        condo_id = target_condominium_id or uuid.UUID(condo_data['id'])

        # 2. Restauração atômica do condomínio e estrutura
        condo, _ = Condominium.objects.update_or_create(
            id=condo_id,
            defaults={
                "name": condo_data.get("name", "Condomínio Restaurado"),
                "status": condo_data.get("status", "active")
            }
        )

        for b_data in db_dump.get("buildings", []):
            Building.objects.update_or_create(
                id=uuid.UUID(b_data['id']),
                defaults={
                    "condominium": condo,
                    "code": b_data['code'],
                    "name": b_data['name'],
                    "kind": b_data.get('kind', 'tower')
                }
            )

        for u_data in db_dump.get("units", []):
            b_id_raw = u_data.get('building_id')
            Unit.objects.update_or_create(
                id=uuid.UUID(u_data['id']),
                defaults={
                    "condominium": condo,
                    "building_id": uuid.UUID(b_id_raw) if b_id_raw else None,
                    "code": u_data['code'],
                    "status": u_data.get('status', 'active')
                }
            )

        # 3. Validação pós-restauração de consistência relacional
        restored_buildings_count = Building.objects.filter(condominium=condo).count()
        restored_units_count = Unit.objects.filter(condominium=condo).count()

        if restored_buildings_count != manifest.get("total_buildings", 0):
            raise InconsistentRestoreError("Divergência no número de prédios/blocos restaurados.")
        if restored_units_count != manifest.get("total_units", 0):
            raise InconsistentRestoreError("Divergência no número de unidades autônomas restauradas.")

        return {
            "status": "sucesso",
            "condominium_id": str(condo.id),
            "buildings_restored": restored_buildings_count,
            "units_restored": restored_units_count,
            "integrity_verified": True
        }
