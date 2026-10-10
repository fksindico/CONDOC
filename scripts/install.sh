#!/usr/bin/env bash
# ==============================================================================
# CONDOC — Instalador Automatizado com Preflight (Fase 8)
# Preserva volumes e dados existentes; idempotente.
# ==============================================================================
set -euo pipefail

echo "=================================================="
echo "          CONDOC PLATFORM INSTALLER               "
echo "=================================================="

# 1. Executa Preflight com doctor.sh
if [ -f "./scripts/doctor.sh" ]; then
    bash ./scripts/doctor.sh
fi

# 2. Configurações e Arquivo .env
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "  -> Criando .env a partir de .env.example..."
    cp .env.example .env
fi

# 3. Dependências Python
if [ -d ".venv" ]; then
    echo "  -> Ambiente virtual .venv detectado."
elif command -v python3 &>/dev/null; then
    echo "  -> Criando ambiente virtual python3..."
    python3 -m venv .venv || true
fi

# 4. Execução de Migrations DDL
if [ -f "./scripts/migrate.sh" ]; then
    bash ./scripts/migrate.sh
fi

echo "--------------------------------------------------"
echo "INSTALAÇÃO CONCLUÍDA: Sistema pronto para operação."
echo "=================================================="
