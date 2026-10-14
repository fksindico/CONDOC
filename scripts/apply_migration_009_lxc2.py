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

    print(f"Conectando a LXC 2 ({host}) para aplicar a migration 009...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=22, username=user, password=password, timeout=15)

    migration_file = '20261014000009_landing_and_divergence.sql'
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

    # Verifica colunas adicionadas
    cmd_check = "docker exec supabase_db psql -U postgres -d condc_dev -c \"\\d app.condominiums; \\d app.public_consultations; \\d app.consultation_suggestions;\""
    _, stdout_c, _ = ssh.exec_command(cmd_check)
    print("\nEstrutura atualizada no PostgreSQL:")
    out_c = stdout_c.read().decode('utf-8', errors='ignore')
    for line in out_c.split('\n'):
        if any(term in line for term in ['landing_', 'thank_you_message', 'has_divergence', 'divergence_details', 'registered_email']):
            print("  ->", line.strip())

    ssh.close()

if __name__ == '__main__':
    main()
