import sys
import paramiko
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

test_script = """
BEGIN;
GRANT authenticated TO postgres;
SET LOCAL ROLE authenticated;
SET LOCAL app.current_tenant_id = '00000000-0000-0000-0000-000000000000';
SELECT current_user, count(*) AS count_as_authenticated FROM app.public_consultations;

SET LOCAL app.current_tenant_id = '7e044fb7-8819-4072-8a70-d346bad3a9b4';
SELECT current_user, count(*) AS count_as_authenticated_valid_tenant FROM app.public_consultations;
ROLLBACK;
"""

stdin, stdout, stderr = ssh.exec_command('docker exec -i supabase_db psql -U postgres -d condc_dev')
stdin.write(test_script)
stdin.close()

print(stdout.read().decode())
print("STDERR:", stderr.read().decode())
ssh.close()
