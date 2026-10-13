import paramiko
import sys
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_APP_HOST'], port=int(env.get('LXC_APP_PORT', 22)), username=env['LXC_APP_USER'], password=env['LXC_APP_PASSWORD'])

stdin, stdout, stderr = ssh.exec_command("ps aux | grep gunicorn")
print("PS AUX:\n", stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("grep -n 'UnitListCreateView' -A 25 /opt/condc/core/api/v1/views.py")
print("REMOTE VIEWS.PY:\n", stdout.read().decode())

ssh.close()
