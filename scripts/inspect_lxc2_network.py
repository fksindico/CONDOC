import sys
import paramiko
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

commands = [
    ("Portas Escutando em LXC 2", "ss -tulpn"),
    ("Containers Docker Supabase", "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"),
    ("Permissões /opt/supabase/.env", "ls -la /opt/supabase/.env 2>/dev/null || true"),
    ("Firewall / UFW Status", "sudo ufw status 2>/dev/null || echo 'UFW inactive or not installed'"),
]

for title, cmd in commands:
    print(f"\n=== {title} ===")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
