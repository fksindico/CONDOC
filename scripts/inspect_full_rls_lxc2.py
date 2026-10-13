import os
import sys
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

    # 1. Total tables and count with RLS / FORCE RLS
    query_summary = """
    SELECT 
        count(*) AS total_tables,
        count(*) FILTER (WHERE c.relrowsecurity) AS rls_enabled_count,
        count(*) FILTER (WHERE c.relforcerowsecurity) AS rls_forced_count
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'app' AND c.relkind = 'r';
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{query_summary}"'
    _, out, _ = ssh.exec_command(cmd)
    print("=== RESUMO RLS SCHEMA APP ===")
    print(out.read().decode('utf-8'))

    # 2. Tabelas onde RLS não está habilitado ou não está forçado
    query_unprotected = """
    SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'app' AND c.relkind = 'r'
      AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity);
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{query_unprotected}"'
    _, out, _ = ssh.exec_command(cmd)
    print("=== TABELAS COM RLS DESABILITADO OU NÃO FORÇADO ===")
    print(out.read().decode('utf-8'))

    # 3. Lista completa de tabelas
    query_all = """
    SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'app' AND c.relkind = 'r'
    ORDER BY c.relname;
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{query_all}"'
    _, out, _ = ssh.exec_command(cmd)
    print("=== TODAS AS TABELAS DO SCHEMA APP ===")
    print(out.read().decode('utf-8'))

    ssh.close()

if __name__ == '__main__':
    main()
