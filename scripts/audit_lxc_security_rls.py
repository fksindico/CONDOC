import os
import sys
import json
import urllib.request
import paramiko

def load_env():
    env_vars = {}
    if not os.path.exists('.env'):
        print("ERRO: .env não encontrado.")
        sys.exit(1)
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

def audit_lxc1(env):
    print("\n=======================================================")
    print(">>> 1. AUDITORIA LXC 1 (APP SERVER - 192.168.10.200)")
    print("=======================================================")
    host = env.get('LXC_APP_HOST', '192.168.10.200')
    port = int(env.get('LXC_APP_PORT', 22))
    user = env.get('LXC_APP_USER', 'condoc')
    password = env.get('LXC_APP_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=15)
    print(f"[OK] Conectado via SSH a LXC 1 ({host})")

    # Hostname e uptime
    _, out, _ = ssh.exec_command("hostname && uptime")
    print("Host / Uptime:", out.read().decode('utf-8').strip())

    # Caddy status
    _, out, _ = ssh.exec_command("systemctl is-active caddy")
    print("Status Caddy:", out.read().decode('utf-8').strip())

    # Backend status
    _, out, _ = ssh.exec_command("systemctl is-active condc-backend")
    print("Status Backend (Gunicorn):", out.read().decode('utf-8').strip())

    # Caddyfile contents
    _, out, _ = ssh.exec_command("cat /etc/caddy/Caddyfile")
    caddyfile = out.read().decode('utf-8')
    print("\n--- Conteúdo /etc/caddy/Caddyfile ---")
    print(caddyfile)

    # Permissões do .env na LXC 1
    _, out, _ = ssh.exec_command("ls -la /opt/condc/.env")
    print("Permissões /opt/condc/.env:", out.read().decode('utf-8').strip())

    ssh.close()

    # Headers HTTP via Caddy (requisição externa de fora da LXC)
    print("\n--- Teste de Headers HTTP Remotos (http://192.168.10.200) ---")
    req = urllib.request.Request("http://192.168.10.200", headers={"User-Agent": "CONDOC-Security-Auditor"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"Status HTTP: {resp.status}")
        headers = dict(resp.headers)
        for h in ['x-content-type-options', 'x-frame-options', 'strict-transport-security', 'referrer-policy', 'server']:
            val = headers.get(h) or headers.get(h.title()) or headers.get(h.lower())
            print(f"Header {h}: {val}")

    # Headers HTTP via endpoint API
    print("\n--- Teste de Headers HTTP na API (http://192.168.10.200/api/health) ---")
    req_api = urllib.request.Request("http://192.168.10.200/api/health", headers={"User-Agent": "CONDOC-Security-Auditor"})
    with urllib.request.urlopen(req_api, timeout=10) as resp:
        print(f"API Health Status: {resp.status}")
        headers = dict(resp.headers)
        for h in ['x-content-type-options', 'x-frame-options', 'strict-transport-security', 'referrer-policy', 'server']:
            val = headers.get(h) or headers.get(h.title()) or headers.get(h.lower())
            print(f"Header {h}: {val}")


def audit_lxc2(env):
    print("\n=======================================================")
    print(">>> 2. AUDITORIA LXC 2 (SUPABASE / DB - 192.168.10.201)")
    print("=======================================================")
    host = env.get('LXC_SUPABASE_HOST', '192.168.10.201')
    port = int(env.get('LXC_SUPABASE_PORT', 22))
    user = env.get('LXC_SUPABASE_USER', 'condoc')
    password = env.get('LXC_SUPABASE_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=15)
    print(f"[OK] Conectado via SSH a LXC 2 ({host})")

    # Hostname e uptime
    _, out, _ = ssh.exec_command("hostname && uptime")
    print("Host / Uptime:", out.read().decode('utf-8').strip())

    # Docker status
    _, out, _ = ssh.exec_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print("\nContainers Supabase ativos:")
    print(out.read().decode('utf-8').strip())

    # 1. Auditoria de RLS em TODAS as tabelas do schema 'app'
    print("\n--- Status de RLS e FORCE RLS em todas as tabelas do schema 'app' ---")
    sql_rls_status = """
    SELECT 
        c.relname AS table_name,
        c.relrowsecurity AS rls_enabled,
        c.relforcerowsecurity AS rls_forced
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'app' AND c.relkind = 'r'
    ORDER BY c.relname;
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_rls_status}"'
    _, out, _ = ssh.exec_command(cmd)
    print(out.read().decode('utf-8'))

    # 2. Políticas RLS existentes no schema 'app'
    print("\n--- Políticas RLS cadastradas no schema 'app' ---")
    sql_policies = """
    SELECT 
        tablename,
        policyname,
        permissive,
        roles,
        cmd,
        qual AS using_expr,
        with_check AS with_check_expr
    FROM pg_policies
    WHERE schemaname = 'app'
    ORDER BY tablename, policyname;
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_policies}"'
    _, out, _ = ssh.exec_command(cmd)
    print(out.read().decode('utf-8'))

    # 3. Auditoria específica da tabela identity_access_events
    print("\n--- Estrutura e Imutabilidade da tabela app.identity_access_events ---")
    sql_iae = """
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'app' AND table_name = 'identity_access_events'
    ORDER BY ordinal_position;
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_iae}"'
    _, out, _ = ssh.exec_command(cmd)
    print("Colunas:")
    print(out.read().decode('utf-8'))

    # Verifica triggers e constraints em identity_access_events
    sql_triggers = """
    SELECT tgname, tgenabled, proname 
    FROM pg_trigger tg
    JOIN pg_proc pr ON tg.tgfoid = pr.oid
    JOIN pg_class c ON tg.tgrelid = c.oid
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = 'app' AND c.relname = 'identity_access_events';
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_triggers}"'
    _, out, _ = ssh.exec_command(cmd)
    print("Triggers em identity_access_events:")
    print(out.read().decode('utf-8'))

    # Verifica permissões/regras em identity_access_events
    sql_rules = """
    SELECT rulename, ev_type, is_instead
    FROM pg_rewrite rw
    JOIN pg_class c ON rw.ev_class = c.oid
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = 'app' AND c.relname = 'identity_access_events';
    """
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_rules}"'
    _, out, _ = ssh.exec_command(cmd)
    print("Regras (rules) em identity_access_events:")
    print(out.read().decode('utf-8'))

    # Total de eventos de auditoria registrados
    sql_count = "SELECT count(*) AS total_audit_events FROM app.identity_access_events;"
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql_count}"'
    _, out, _ = ssh.exec_command(cmd)
    print(out.read().decode('utf-8'))

    ssh.close()

def main():
    env = load_env()
    audit_lxc1(env)
    audit_lxc2(env)

if __name__ == '__main__':
    main()
