import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_APP_HOST'], 22, env['LXC_APP_USER'], env['LXC_APP_PASSWORD'], timeout=10)

stdin, stdout, stderr = ssh.exec_command('systemctl is-active condc-backend')
print('STATUS:', stdout.read().decode().strip())

stdin, stdout, stderr = ssh.exec_command('journalctl -u condc-backend -n 25 --no-pager')
print('LOGS:\n', stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8000/api/v1/condominiums/7e044fb7-8819-4072-8a70-d346bad3a9b4/dashboard-metrics')
print('CURL DIRECT:\n', stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1/api/v1/condominiums/7e044fb7-8819-4072-8a70-d346bad3a9b4/dashboard-metrics')
print('CURL VIA CADDY:\n', stdout.read().decode())

ssh.close()
