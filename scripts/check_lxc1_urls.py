import os
import paramiko

def load_env():
    env = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def main():
    env = load_env()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(env.get('LXC_APP_HOST', '192.168.10.200'), username=env.get('LXC_APP_USER', 'condoc'), password=env.get('LXC_APP_PASSWORD'))

    stdin, stdout, stderr = ssh.exec_command("grep -n 'audit-logs' /opt/condc/core/api/v1/urls.py")
    print("Grep na LXC 1:\n", stdout.read().decode('utf-8'))

    def exec_sudo(cmd):
        stdin, stdout, stderr = ssh.exec_command("sudo -S " + cmd)
        stdin.write(env.get('LXC_APP_PASSWORD') + "\n")
        stdin.flush()
        return stdout.read().decode('utf-8', errors='ignore')

    status_out = exec_sudo("systemctl status condc-backend")
    print("Status systemctl:\n", status_out.encode('ascii', errors='replace').decode('ascii'))
    print("Reiniciando forçadamente condc-backend...")
    exec_sudo("systemctl restart condc-backend")
    import time
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("curl -sI 'http://127.0.0.1:8000/api/v1/condominiums/a0000000-0000-0000-0000-000000000002/audit-logs'")
    print("Curl Gunicorn após restart:\n", stdout.read().decode('utf-8'))

    # Testa o curl local no caddy porta 80
    stdin, stdout, stderr = ssh.exec_command("curl -sI 'http://127.0.0.1/api/v1/condominiums/a0000000-0000-0000-0000-000000000002/audit-logs'")
    print("Curl Caddy porta 80:\n", stdout.read().decode('utf-8'))

    ssh.close()

if __name__ == '__main__':
    main()
