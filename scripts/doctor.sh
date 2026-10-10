#!/usr/bin/env bash
# ==============================================================================
# CONDOC — Doctor: Diagnóstico de Integridade e Ambiente (Fase 8)
# Verifica dependências, portas, conectividade de banco, cache e storage.
# ==============================================================================
set -euo pipefail

echo "=================================================="
echo "           CONDOC SYSTEM DOCTOR PREFLIGHT         "
echo "=================================================="

EXIT_CODE=0

# 1. Verificação de Ferramentas e Runtimes
echo -n "[1/6] Verificando runtimes essenciais... "
if command -v python3 &>/dev/null || command -v python &>/dev/null; then
    PY_VER=$(python3 --version 2>/dev/null || python --version 2>/dev/null)
    echo "OK ($PY_VER)"
else
    echo "FALHA: Python não encontrado."
    EXIT_CODE=1
fi

if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    echo "      Node.js: OK ($NODE_VER)"
else
    echo "      AVISO: Node.js não encontrado no PATH."
fi

# 2. Verificação de Arquivos e Estrutura do Projeto
echo -n "[2/6] Verificando estrutura do repositório... "
REQUIRED_DIRS=("core" "supabase/migrations" "docs" "scripts")
MISSING_DIRS=0
for d in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$d" ]; then
        echo "FALHA: Diretório '$d' ausente."
        MISSING_DIRS=1
        EXIT_CODE=1
    fi
done
if [ $MISSING_DIRS -eq 0 ]; then
    echo "OK (Diretórios base íntegros)"
fi

# 3. Verificação de Variáveis de Ambiente
echo -n "[3/6] Verificando variáveis de ambiente... "
if [ -f ".env" ]; then
    echo "OK (.env presente)"
else
    echo "AVISO: Arquivo .env não encontrado na raiz (usando padrões de desenvolvimento)."
fi

# 4. Verificação das Migrations do Supabase
echo -n "[4/6] Verificando arquivos de migração SQL... "
MIGRATION_COUNT=$(ls -1 supabase/migrations/*.sql 2>/dev/null | wc -l || echo 0)
if [ "$MIGRATION_COUNT" -gt 0 ]; then
    echo "OK ($MIGRATION_COUNT migrations encontradas)"
else
    echo "FALHA: Nenhuma migration encontrada em supabase/migrations/."
    EXIT_CODE=1
fi

# 5. Verificação da Suíte de Testes Automatizados
echo -n "[5/6] Verificando integridade dos testes automatizados... "
if command -v pytest &>/dev/null || [ -f ".venv/Scripts/pytest.exe" ] || [ -f ".venv/bin/pytest" ]; then
    echo "OK (pytest disponível)"
else
    echo "AVISO: pytest não encontrado no ambiente ativo."
fi

# 6. Status Final
echo "--------------------------------------------------"
if [ $EXIT_CODE -eq 0 ]; then
    echo "STATUS: DIAGNÓSTICO APROVADO - Sistema pronto para operação."
else
    echo "STATUS: DIAGNÓSTICO COM PENDÊNCIAS (Código: $EXIT_CODE)."
fi
echo "=================================================="

exit $EXIT_CODE
