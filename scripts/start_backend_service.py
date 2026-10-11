import os
import sys
import paramiko

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_env():
    env_vars = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip()
    return env_vars

def exec_sudo(ssh, password, cmd):
    stdin, stdout, stderr = ssh.exec_command("sudo -S " + cmd)
    stdin.write(password + "\n")
    stdin.flush()
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    return code, out

def main():
    env = load_env()
    host = env.get('LXC_APP_HOST', '192.168.10.200')
    user = env.get('LXC_APP_USER', 'condoc')
    password = env.get('LXC_APP_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=22, username=user, password=password, timeout=10)

    print("Iniciando serviço condc-backend...")
    exec_sudo(ssh, password, "systemctl daemon-reload")
    code, out = exec_sudo(ssh, password, "systemctl start condc-backend.service")
    print("Start code:", code)

    code, out = exec_sudo(ssh, password, "systemctl status condc-backend.service --no-pager")
    print(out)

    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:8000/api/health")
    print("\nResposta direta do Django em 127.0.0.1:8000/api/health:")
    print(stdout.read().decode())

    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1/api/health")
    print("\nResposta via Caddy em 127.0.0.1/api/health:")
    print(stdout.read().decode())

    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1/api/v1/auth/session")
    print("\nResposta de Sessão BFF via Caddy:")
    print(stdout.read().decode())

    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1/api/v1/condominiums")
    print("\nResposta de Condomínios do PostgreSQL na LXC 2:")
    print(stdout.read().decode())

    ssh.close()

if __name__ == '__main__':
    main()
