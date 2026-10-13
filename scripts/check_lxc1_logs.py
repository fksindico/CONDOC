import paramiko
from deploy_backend_lxc1 import load_env

env = load_env()
host = env.get('LXC_APP_HOST', '192.168.10.200')
port = int(env.get('LXC_APP_PORT', 22))
user = env.get('LXC_APP_USER', 'condoc')
password = env.get('LXC_APP_PASSWORD')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=port, username=user, password=password, timeout=10)

stdin, stdout, stderr = ssh.exec_command("sudo -S journalctl -u condc-backend -n 60 --no-pager")
stdin.write(password + "\n")
stdin.flush()
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print("OUT:\n", out)
if err:
    print("ERR:\n", err)
ssh.close()
