import paramiko
import sys
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
password = env.get('LXC_APP_PASSWORD')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_APP_HOST'], port=int(env.get('LXC_APP_PORT', 22)), username=env['LXC_APP_USER'], password=password)

stdin, stdout, stderr = ssh.exec_command("sudo -S systemctl restart condc-backend")
stdin.write(password + "\n")
stdin.flush()
print("RESTART CODE:", stdout.channel.recv_exit_status())

stdin, stdout, stderr = ssh.exec_command("ps aux | grep gunicorn")
print("NEW PS AUX:\n", stdout.read().decode())

ssh.close()
