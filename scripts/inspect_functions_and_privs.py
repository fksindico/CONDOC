import os
import paramiko

def load_env():
    env_vars = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

def main():
    env = load_env()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=15)

    sql = """
    SELECT n.nspname, p.proname 
    FROM pg_proc p 
    JOIN pg_namespace n ON n.oid = p.pronamespace 
    WHERE n.nspname IN ('app', 'public')
    ORDER BY n.nspname, p.proname;
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql}"'
    _, out, _ = ssh.exec_command(cmd)
    print("=== FUNÇÕES NOS SCHEMAS app E public ===")
    print(out.read().decode('utf-8'))

    # Verifica permissões específicas de UPDATE/DELETE concedidas na tabela identity_access_events
    sql_privs = """
    SELECT grantee, privilege_type 
    FROM information_schema.role_table_grants 
    WHERE table_schema = 'app' AND table_name = 'identity_access_events';
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_privs}"'
    _, out, _ = ssh.exec_command(cmd)
    print("=== PRIVILÉGIOS EM app.identity_access_events ===")
    print(out.read().decode('utf-8'))

    ssh.close()

if __name__ == '__main__':
    main()
