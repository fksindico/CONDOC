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

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=22, username=user, password=password, timeout=15)

    sql = """
    DO $$ 
    DECLARE 
        r RECORD; 
    BEGIN 
        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'app') LOOP 
            EXECUTE 'ALTER TABLE app.' || quote_ident(r.tablename) || ' FORCE ROW LEVEL SECURITY;'; 
        END LOOP; 
    END $$;
    """

    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql}"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print("Resultado FORCE RLS:", out, err)

    # Verifica status das tabelas com rowsecurity e relforcerowsecurity
    verify_sql = """
    SELECT relname, relrowsecurity, relforcerowsecurity 
    FROM pg_class c 
    JOIN pg_namespace n ON n.oid = c.relnamespace 
    WHERE n.nspname = 'app' AND c.relkind = 'r' 
    LIMIT 10;
    """
    cmd_verify = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{verify_sql}"'
    _, stdout_v, _ = ssh.exec_command(cmd_verify)
    print("\nAmostra de tabelas com relforcerowsecurity no app:")
    print(stdout_v.read().decode('utf-8', errors='ignore'))
    ssh.close()

if __name__ == '__main__':
    main()
