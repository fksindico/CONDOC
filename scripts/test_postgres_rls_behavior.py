import sys
import paramiko
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

test_script = """
-- 1. Teste como postgres (superuser)
SET app.current_tenant_id = '00000000-0000-0000-0000-000000000000';
SELECT current_user, usesuper FROM pg_user WHERE usename = current_user;
SELECT count(*) AS count_as_postgres_with_fake_tenant FROM app.public_consultations;

-- 2. Teste como test_app_user (non-superuser com FORCE RLS)
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'test_app_user') THEN
        CREATE ROLE test_app_user NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END $$;
GRANT test_app_user TO postgres;
GRANT USAGE ON SCHEMA app TO test_app_user;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO test_app_user;

SET LOCAL ROLE test_app_user;
SET LOCAL app.current_tenant_id = '00000000-0000-0000-0000-000000000000';
SELECT current_user;
SELECT count(*) AS count_as_test_app_user_with_fake_tenant FROM app.public_consultations;
ROLLBACK;
"""

stdin, stdout, stderr = ssh.exec_command('docker exec -i supabase_db psql -U postgres -d condc_dev')
stdin.write(test_script)
stdin.close()

print(stdout.read().decode())
print("STDERR:", stderr.read().decode())
ssh.close()
