import sys
import paramiko
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

test_script = """
SELECT r.rolname, r.rolsuper, r.rolbypassrls, r.rolcanlogin
FROM pg_roles r
ORDER BY r.rolname;
"""

stdin, stdout, stderr = ssh.exec_command('docker exec -i supabase_db psql -U postgres -d condc_dev')
stdin.write(test_script)
stdin.close()

print(stdout.read().decode())
ssh.close()
