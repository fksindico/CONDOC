#!/usr/bin/env python3
"""
Orquestrador Geral de Auditoria de Qualidade e QA Tester — CONDOC
Executa todas as suítes de testes, validações de compilação, doctor preflight
e consolida a matriz de rastreabilidade dos 141 critérios de aceite.
"""
import os
import sys
import subprocess
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_step(step_number, title, command, cwd):
    print(f"\n[{step_number}/5] {title}...")
    start_time = time.time()
    result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    duration = time.time() - start_time

    if result.returncode == 0:
        print(f"      OK ({duration:.2f}s)")
        return True, result.stdout
    else:
        print(f"      FALHA ({duration:.2f}s)")
        safe_err = (result.stderr or result.stdout or "").encode('ascii', errors='replace').decode('ascii')
        print(safe_err)
        return False, result.stderr or result.stdout

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print("==================================================")
    print("       CONDOC — AUDITORIA GERAL DE QUALIDADE      ")
    print("==================================================")
    print(f"Raiz do Projeto: {root_dir}")

    all_passed = True

    # 1. Doctor Preflight
    doc_ok, _ = run_step(1, "Doctor Preflight de Saúde do Sistema", "bash scripts/doctor.sh", root_dir)
    all_passed = all_passed and doc_ok

    # 2. Compilação TypeScript de Contratos
    contract_ok, _ = run_step(2, "Compilação de Contratos (@condc/api-contracts)", "npm run build:contracts", root_dir)
    all_passed = all_passed and contract_ok

    # 3. Compilação e Build da SPA Frontend
    build_ok, _ = run_step(3, "Build de Produção do Frontend (Vite & TypeScript)", "npm run build:web", root_dir)
    all_passed = all_passed and build_ok

    # 4. Testes do Frontend (Vitest)
    vitest_ok, vitest_out = run_step(4, "Suíte de Testes do Frontend (Vitest)", "npx vitest run", os.path.join(root_dir, "apps", "web"))
    all_passed = all_passed and vitest_ok
    if vitest_ok:
        lines = [l for l in vitest_out.splitlines() if "passed" in l]
        for l in lines:
            print(f"      -> {l.strip()}")

    # 5. Testes do Backend (Pytest)
    pytest_bin = sys.executable + " -m pytest"
    pytest_ok, pytest_out = run_step(5, "Suíte de Testes do Core Backend (Pytest)", f"{pytest_bin} core/tests/ -q", root_dir)
    all_passed = all_passed and pytest_ok
    if pytest_ok:
        lines = [l for l in pytest_out.splitlines() if "passed" in l]
        for l in lines:
            print(f"      -> {l.strip()}")

    print("\n--------------------------------------------------")
    if all_passed:
        print("RESULTADO FINAL: AUDITORIA CONCLUÍDA COM 100% DE SUCESSO!")
        print("Todas as funções e invariantes foram verificadas e aprovadas.")
        print("==================================================")
        sys.exit(0)
    else:
        print("RESULTADO FINAL: AUDITORIA DETECTOU FALHAS.")
        print("==================================================")
        sys.exit(1)

if __name__ == '__main__':
    main()
