import sys
import paramiko
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_APP_HOST'], 22, env['LXC_APP_USER'], env['LXC_APP_PASSWORD'], timeout=10)

cmd = "su - condoc -c 'cd /opt/condc && /opt/condc/venv/bin/pytest core/tests/ -q'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
