import os
import sys
import paramiko

def load_env():
    env_vars = {}
    if not os.path.exists('.env'):
        sys.exit(1)
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

def main():
    env = load_env()
    host = env.get('LXC_SUPABASE_HOST', '192.168.10.201')
    user = env.get('LXC_SUPABASE_USER', 'condoc')
    password = env.get('LXC_SUPABASE_PASSWORD')

    print(f"Conectando a LXC 2 ({host}) para aplicar a migration 008...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=22, username=user, password=password, timeout=15)

    migration_file = '20261012000008_simplified_public_consultation.sql'
    local_path = os.path.join('supabase', 'migrations', migration_file)
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()

    stdin, stdout, stderr = ssh.exec_command(f"docker exec -i supabase_db tee /tmp/migrations/{migration_file} > /dev/null")
    stdin.write(content)
    stdin.close()
    stdout.channel.recv_exit_status()
    print(f"Upload de {migration_file} concluído no container supabase_db.")

    cmd = f"docker exec supabase_db psql -U postgres -d condc_dev -v ON_ERROR_STOP=1 -f /tmp/migrations/{migration_file}"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    err = stderr.read().decode('utf-8', errors='ignore').strip()
    if code == 0:
        print(f"[OK] {migration_file} aplicada com sucesso!")
        if out:
            print(out)
    else:
        print(f"[ERRO {code}] Falha ao aplicar {migration_file}:\n{err or out}")
        sys.exit(code)

    # Força RLS nas novas tabelas
    force_rls = """
    ALTER TABLE app.public_consultations FORCE ROW LEVEL SECURITY;
    ALTER TABLE app.consultation_suggestions FORCE ROW LEVEL SECURITY;
    """
    cmd_rls = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{force_rls}"'
    stdin, stdout, stderr = ssh.exec_command(cmd_rls)
    stdout.channel.recv_exit_status()
    print("RLS forçado nas tabelas public_consultations e consultation_suggestions.")

    # Verifica existência das novas tabelas
    cmd_check = "docker exec supabase_db psql -U postgres -d condc_dev -c \"\\dt app.*consultation*\""
    _, stdout_c, _ = ssh.exec_command(cmd_check)
    print("\nTabelas criadas no PostgreSQL:")
    print(stdout_c.read().decode('utf-8', errors='ignore'))

    ssh.close()

if __name__ == '__main__':
    main()
