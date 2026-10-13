import paramiko
import sys

sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh_db = paramiko.SSHClient()
ssh_db.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_db.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

cmd = """docker exec supabase_db psql -U postgres -d condc_dev -c "UPDATE app.buildings SET status = 'active' WHERE condominium_id = 'a0000000-0000-0000-0000-000000000001';" """
stdin, stdout, stderr = ssh_db.exec_command(cmd)
print('UPDATE BUILDINGS:\n', stdout.read().decode())

ssh_db.close()
