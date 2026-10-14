import sys
import paramiko
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(env['LXC_APP_HOST'], 22, env['LXC_APP_USER'], env['LXC_APP_PASSWORD'], timeout=10)

# De dentro de LXC 1, tenta chamar o PostgREST diretamente em LXC 2
cmd = 'curl -s -i "http://192.168.10.201:3001/public_consultations" -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.dummy"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Resposta PostgREST para requisição externa anon:")
print(stdout.read().decode('utf-8', errors='ignore'))

cmd_app = 'curl -s -i "http://192.168.10.201:3001/app.public_consultations" -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.dummy"'
stdin, stdout, stderr = ssh.exec_command(cmd_app)
print("Resposta PostgREST para schema app:")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
