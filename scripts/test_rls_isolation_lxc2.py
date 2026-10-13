import paramiko
import os

def load_env():
    env = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def main():
    env = load_env()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'])

    # Verifica permissões no schema app
    cmd_dn = 'docker exec supabase_db psql -U postgres -d condc_dev -c "\\dn+ app"'
    _, out, _ = ssh.exec_command(cmd_dn)
    print("=== PERMISSÕES NO SCHEMA app ===")
    print(out.read().decode('utf-8'))

    # Cria uma role não-superuser temporária dentro da transação para testar o RLS
    test_script = """
    BEGIN;
    -- Cria um papel não-superuser temporário com permissão apenas no schema app
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'test_app_user') THEN
            CREATE ROLE test_app_user NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
        END IF;
    END $$;

    GRANT test_app_user TO postgres;
    GRANT USAGE ON SCHEMA app TO test_app_user;
    GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA app TO test_app_user;

    -- 1. Cria consultas vinculadas aos condomínios existentes:
    -- c1 = a0000000-0000-0000-0000-000000000001 (Parque das Flores)
    -- c2 = a0000000-0000-0000-0000-000000000002 (Edifício Horizon)
    INSERT INTO app.public_consultations (id, condominium_id, title, pdf_file_path, pdf_original_name, public_token)
    VALUES 
        ('a1111111-1111-1111-1111-111111111111', 'a0000000-0000-0000-0000-000000000001', 'Regimento Parque das Flores', 'flores.pdf', 'flores.pdf', 'tok_flores_rls'),
        ('b2222222-2222-2222-2222-222222222222', 'a0000000-0000-0000-0000-000000000002', 'Regimento Horizon', 'horizon.pdf', 'horizon.pdf', 'tok_horizon_rls')
    ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title;

    -- 2. Ativa o papel restrito test_app_user
    SET LOCAL ROLE test_app_user;

    -- 3. Caso A: Tenant = Parque das Flores (c1)
    SET LOCAL app.current_tenant_id = 'a0000000-0000-0000-0000-000000000001';
    SELECT title, public_token FROM app.public_consultations WHERE id IN ('a1111111-1111-1111-1111-111111111111', 'b2222222-2222-2222-2222-222222222222');

    -- 4. Caso B: Tenant = Edifício Horizon (c2)
    SET LOCAL app.current_tenant_id = 'a0000000-0000-0000-0000-000000000002';
    SELECT title, public_token FROM app.public_consultations WHERE id IN ('a1111111-1111-1111-1111-111111111111', 'b2222222-2222-2222-2222-222222222222');

    -- 5. Caso C: Sem tenant configurado
    SET LOCAL app.current_tenant_id = '';
    SELECT count(*) AS total_sem_tenant FROM app.public_consultations WHERE id IN ('a1111111-1111-1111-1111-111111111111', 'b2222222-2222-2222-2222-222222222222');

    ROLLBACK;
    """

    stdin, stdout, stderr = ssh.exec_command('docker exec -i supabase_db psql -U postgres -d condc_dev')
    stdin.write(test_script)
    stdin.close()
    print("=== RESULTADO DO TESTE RLS ISOLATION ===")
    print(stdout.read().decode('utf-8'))
    print("STDERR:")
    print(stderr.read().decode('utf-8'))

    # Remove a role temporária se foi criada fora do rollback
    ssh.exec_command('docker exec supabase_db psql -U postgres -d condc_dev -c "DROP ROLE IF EXISTS test_app_user;"')

    ssh.close()

if __name__ == '__main__':
    main()
