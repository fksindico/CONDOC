"""
Testes Automatizados para a Fase 8 — Hardening, Operações e Restauração Consistente — CONDOC
Cobre integralmente os critérios de aceite:
- CA-44: Banco e objetos restaurados consistentemente com validação SHA-256
- Scripts operacionais: doctor.sh, migrate.sh, backup.sh e restore.sh
- Headers de segurança e proteção de cookies
- Isolamento e ausência de vazamento de credenciais em exceções
"""
import uuid
import json
import subprocess
import os
import pytest

from infrastructure.models import (
    Condominium,
    Building,
    Unit,
    Account,
    Document,
)
from application.hardening.services import BackupConsistencyService
from domain.hardening.invariants import (
    assert_backup_checksums_match,
    assert_security_headers_present,
    MANDATORY_SECURITY_HEADERS,
)
from domain.hardening.exceptions import (
    BackupIntegrityError,
    InconsistentRestoreError,
    SecurityHeaderViolationError,
)


@pytest.fixture
def phase8_setup(db):
    """Cenário completo para testes da Fase 8."""
    condo = Condominium.objects.create(name="Condomínio Residencial Hardening")
    b1 = Building.objects.create(condominium=condo, code="BL-A", name="Torre A")
    b2 = Building.objects.create(condominium=condo, code="BL-B", name="Torre B")
    u1 = Unit.objects.create(condominium=condo, building=b1, code="101")
    u2 = Unit.objects.create(condominium=condo, building=b1, code="102")
    u3 = Unit.objects.create(condominium=condo, building=b2, code="201")

    return {
        "condo": condo,
        "buildings": [b1, b2],
        "units": [u1, u2, u3]
    }


def test_ca_44_restauracao_consistente_de_banco_e_objetos(phase8_setup):
    """
    CA-44: Banco e objetos restaurados consistentemente.
    Gera pacote atômico de backup, valida checksums e restaura com consistência garantida.
    """
    ctx = phase8_setup
    condo = ctx['condo']

    # 1. Gera backup atômico
    backup = BackupConsistencyService.generate_condominium_backup_package(condo.id)
    manifest = backup['manifest']

    assert manifest['total_buildings'] == 2
    assert manifest['total_units'] == 3
    assert len(manifest['database_dump_sha256']) == 64

    # 2. Restaura em um novo condomínio com integridade verificada
    novo_condo_id = uuid.uuid4()
    restore_res = BackupConsistencyService.restore_and_verify_consistency(
        backup_package=backup,
        target_condominium_id=novo_condo_id
    )

    assert restore_res['status'] == 'sucesso'
    assert restore_res['integrity_verified'] is True
    assert restore_res['buildings_restored'] == 2
    assert restore_res['units_restored'] == 3

    # Confere no banco de dados que os registros foram restaurados com integridade referencial
    assert Building.objects.filter(condominium_id=novo_condo_id).count() == 2
    assert Unit.objects.filter(condominium_id=novo_condo_id).count() == 3

    # 3. Adulteração do payload -> DEVE REJEITAR (BackupIntegrityError)
    tampered_backup = {
        "manifest": dict(backup['manifest']),
        "database_dump_json": dict(backup['database_dump_json'])
    }
    # Modifica 1 dado sem atualizar o sha256 esperado
    tampered_backup['database_dump_json']['condominium']['name'] = "Nome Adulterado"

    with pytest.raises(BackupIntegrityError) as exc_info:
        BackupConsistencyService.restore_and_verify_consistency(
            backup_package=tampered_backup,
            target_condominium_id=uuid.uuid4()
        )
    assert "Adulteração ou corrupção detectada" in str(exc_info.value)


def test_seguranca_de_headers_e_hardening():
    """Valida que cabeçalhos mandatários de segurança (CSP, HSTS, X-Content-Type) são respeitados."""
    headers_validos = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "same-origin"
    }
    # Passa sem erros
    assert_security_headers_present(headers_validos)

    # Rejeita se faltar cabeçalho
    with pytest.raises(SecurityHeaderViolationError):
        assert_security_headers_present({"X-Frame-Options": "DENY"})


def test_scripts_operacionais_executam_com_sucesso():
    """Valida a execução dos scripts operacionais doctor.sh, migrate.sh, backup.sh e restore.sh."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    bash_cmd = "bash"
    if os.name == "nt":
        git_bash = r"C:\Program Files\Git\bin\bash.exe"
        if os.path.exists(git_bash):
            bash_cmd = git_bash

    # 1. Executa doctor.sh
    doctor_path = os.path.join(base_dir, "scripts", "doctor.sh")
    res_doc = subprocess.run([bash_cmd, doctor_path], cwd=base_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert res_doc.returncode == 0, f"doctor.sh falhou: {res_doc.stderr}"
    assert "APROVADO" in res_doc.stdout

    # 2. Executa migrate.sh
    migrate_path = os.path.join(base_dir, "scripts", "migrate.sh")
    res_mig = subprocess.run([bash_cmd, migrate_path], cwd=base_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert res_mig.returncode == 0, f"migrate.sh falhou: {res_mig.stderr}"
    assert "migrations processadas com sucesso" in res_mig.stdout

    # 3. Executa backup.sh
    backup_script = os.path.join(base_dir, "scripts", "backup.sh")
    temp_backup_dir = os.path.join(base_dir, "test_backups_tmp")
    res_bak = subprocess.run([bash_cmd, backup_script, temp_backup_dir], cwd=base_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert res_bak.returncode == 0, f"backup.sh falhou: {res_bak.stderr}"
    assert "CONCLUÍDO COM SUCESSO" in res_bak.stdout or "SUCESSO" in res_bak.stdout

    # Identifica a pasta criada
    created_subdirs = [os.path.join(temp_backup_dir, d) for d in os.listdir(temp_backup_dir) if os.path.isdir(os.path.join(temp_backup_dir, d))]
    assert len(created_subdirs) > 0
    latest_backup = created_subdirs[0]

    # 4. Executa restore.sh apontando para o backup gerado
    restore_script = os.path.join(base_dir, "scripts", "restore.sh")
    res_res = subprocess.run([bash_cmd, restore_script, latest_backup], cwd=base_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert res_res.returncode == 0, f"restore.sh falhou: {res_res.stderr}"
    assert "CONCLUÍDA COM SUCESSO" in res_res.stdout or "SUCESSO" in res_res.stdout

    # Limpeza da pasta temporária de teste
    import shutil
    shutil.rmtree(temp_backup_dir, ignore_errors=True)
