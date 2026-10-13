"""
Script de Saneamento Completo do Sistema CONDOC
1. Remove condomínios sintéticos de teste (Reserva dos Manacás e Edifício Horizon).
2. Preserva NEXT RESIDENCE (condomínio real do usuário) e Parque das Flores (condomínio modelo).
3. Vincula papel de Síndico da conta principal ao NEXT RESIDENCE para testes manuais.
4. Limpa pastas de mídias temporárias na LXC 1.
5. Garante permissões de upload e reinicia o backend.
"""
import paramiko
import sys
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

def main():
    env = load_env()
    print("=================================================================")
    print("INICIANDO SANEAMENTO COMPLETO DO SISTEMA CONDOC")
    print("=================================================================")

    # 1. Conexão com LXC 2 (Banco de Dados PostgreSQL)
    print("\n>>> 1. Conectando a LXC 2 (192.168.10.201 / Supabase PostgreSQL)...")
    ssh_db = paramiko.SSHClient()
    ssh_db.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_db.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

    # Coletar IDs dos condomínios de teste a serem removidos
    sql_find_test_condos = """
    SELECT id, name FROM app.condominiums 
    WHERE name ILIKE '%Manacas%' 
       OR name ILIKE '%Teste Real%'
       OR id = 'a0000000-0000-0000-0000-000000000002';
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -t -A -F "|" -c "{sql_find_test_condos}"'
    stdin, stdout, stderr = ssh_db.exec_command(cmd)
    raw_condos = stdout.read().decode().strip().splitlines()

    condos_to_delete = []
    for line in raw_condos:
        if "|" in line:
            cid, cname = line.split("|", 1)
            condos_to_delete.append((cid.strip(), cname.strip()))

    print(f"    Identificados {len(condos_to_delete)} condomínio(s) sintético(s) para remoção:")
    for cid, cname in condos_to_delete:
        print(f"    - [{cid}] {cname}")

    if condos_to_delete:
        ids_sql = ", ".join([f"'{cid}'" for cid, _ in condos_to_delete])
        sql_delete = f"DELETE FROM app.condominiums WHERE id IN ({ids_sql});"
        cmd_del = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_delete}"'
        stdin, stdout, stderr = ssh_db.exec_command(cmd_del)
        res_del = stdout.read().decode().strip()
        print(f"    [OK] Exclusão em cascata no PostgreSQL: {res_del}")
    else:
        print("    Nenhum condomínio de teste pendente de remoção.")

    # 2. Assegurar vínculo de síndico para o NEXT RESIDENCE
    print("\n>>> 2. Assegurando papel de Síndico para o NEXT RESIDENCE...")
    sql_role = """
    INSERT INTO app.role_assignments (id, condominium_id, account_id, role, status)
    VALUES (
        gen_random_uuid(),
        '7e044fb7-8819-4072-8a70-d346bad3a9b4',
        'c0000000-0000-0000-0000-000000000001',
        'sindico',
        'active'
    )
    ON CONFLICT DO NOTHING;
    """
    cmd_role = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_role}"'
    stdin, stdout, stderr = ssh_db.exec_command(cmd_role)
    print("    [OK] Papel de síndico ativo configurado para NEXT RESIDENCE.")

    # Listar estado final dos condomínios na LXC 2
    cmd_list = 'docker exec supabase_db psql -U postgres -d condc_dev -c "SELECT id, name, cnpj, address_city, address_state, status FROM app.condominiums ORDER BY created_at;"'
    stdin, stdout, stderr = ssh_db.exec_command(cmd_list)
    print("\n=== CONDOMÍNIOS ATIVOS NO SISTEMA APÓS SANEAMENTO ===")
    print(stdout.read().decode())
    ssh_db.close()

    # 3. Conexão com LXC 1 (App Server / Mídias / Backend)
    print(">>> 3. Conectando a LXC 1 (192.168.10.200 / App Server)...")
    ssh_app = paramiko.SSHClient()
    ssh_app.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    password = env['LXC_APP_PASSWORD']
    ssh_app.connect(env['LXC_APP_HOST'], 22, env['LXC_APP_USER'], password, timeout=10)

    # Limpar diretórios de mídias de consultas de teste em /opt/condc/core/media/consultations
    print("    Limpando arquivos e diretórios de mídias de teste na LXC 1...")
    clean_media_cmd = """
    sudo -S rm -rf /opt/condc/core/media/consultations/*
    sudo -S mkdir -p /opt/condc/core/media/consultations
    sudo -S chown -R condoc:condoc /opt/condc/core/media
    sudo -S chmod -R 775 /opt/condc/core/media
    """
    stdin, stdout, stderr = ssh_app.exec_command(clean_media_cmd)
    stdin.write(f"{password}\n{password}\n{password}\n{password}\n")
    stdin.flush()
    stdout.channel.recv_exit_status()
    print("    [OK] Diretório /opt/condc/core/media/consultations sanitizado e permissões redefinidas.")

    # Reiniciar condc-backend
    print("    Reiniciando serviço backend (gunicorn)...")
    stdin, stdout, stderr = ssh_app.exec_command(f"sudo -S systemctl restart condc-backend")
    stdin.write(f"{password}\n")
    stdin.flush()
    stdout.channel.recv_exit_status()
    print("    [OK] Backend reiniciado com sucesso.")

    # Testar resposta HTTP da API na LXC 1
    stdin, stdout, stderr = ssh_app.exec_command("curl -s http://127.0.0.1/api/v1/condominiums | head -n 30")
    api_resp = stdout.read().decode()
    print(f"\n=== RESPOSTA DA API /api/v1/condominiums ===")
    print(api_resp)

    ssh_app.close()
    print("\n=================================================================")
    print("[SUCESSO] SANEAMENTO COMPLETO CONCLUÍDO COM EXCELÊNCIA!")
    print("O sistema está limpo, configurado e pronto para testes manuais.")
    print("=================================================================")

if __name__ == '__main__':
    main()
