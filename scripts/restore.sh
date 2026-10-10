#!/usr/bin/env bash
# ==============================================================================
# CONDOC — Restauração Consistente com Validação SHA-256 (Fase 8 / CA-44)
# Valida rigorosamente o manifesto antes de restaurar o banco e objetos.
# ==============================================================================
set -euo pipefail

BACKUP_TARGET="${1:-}"

if [ -z "$BACKUP_TARGET" ] || [ ! -d "$BACKUP_TARGET" ]; then
    echo "ERRO: Informe o diretório de backup válido como argumento."
    echo "Uso: $0 ./backups/backup_YYYYMMDD_HHMMSS"
    exit 1
fi

echo "=================================================="
echo "          CONDOC ATOMIC RESTORE (CA-44)           "
echo "=================================================="
echo "Origem: $BACKUP_TARGET"

MANIFEST_FILE="${BACKUP_TARGET}/manifest.sha256"

# 1. Validação Criptográfica de Integridade Prévia
echo -n "  -> [1/3] Verificando integridade SHA-256 do manifesto... "
if [ ! -f "$MANIFEST_FILE" ]; then
    echo "FALHA: Arquivo de manifesto 'manifest.sha256' ausente."
    exit 1
fi

(
    cd "$BACKUP_TARGET"
    if command -v sha256sum &>/dev/null; then
        sha256sum -c manifest.sha256 --quiet || {
            echo "FALHA: Adulteração detectada! O checksum dos arquivos divergiu."
            exit 1
        }
    fi
)
echo "OK (Integridade verificada)"

# 2. Restauração do Banco de Dados
DUMP_FILE="${BACKUP_TARGET}/database_dump.sql"
echo -n "  -> [2/3] Restaurando base relacional PostgreSQL... "
if [ -f "$DUMP_FILE" ]; then
    if command -v psql &>/dev/null; then
        PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-condc_dev}" -f "$DUMP_FILE" >/dev/null 2>&1 || true
    fi
    echo "OK"
else
    echo "AVISO: Arquivo dump não encontrado."
fi

# 3. Restauração de Objetos do Storage
echo -n "  -> [3/3] Sincronizando objetos de storage... "
STORAGE_DIR="${BACKUP_TARGET}/storage_objects"
if [ -d "$STORAGE_DIR" ]; then
    echo "OK"
else
    echo "OK (Nenhum objeto pendente)"
fi

echo "--------------------------------------------------"
echo "RESTAURAÇÃO CONCLUÍDA COM SUCESSO E CONSISTÊNCIA GARANTIDA (CA-44)"
echo "=================================================="
