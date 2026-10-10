import os
import sys
import paramiko

def load_env():
    env_vars = {}
    if not os.path.exists('.env'):
        print("ERRO: Arquivo .env não encontrado.")
        sys.exit(1)
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip()
    return env_vars

def main():
    env = load_env()
    host = env.get('LXC_APP_HOST', '192.168.10.200')
    port = int(env.get('LXC_APP_PORT', 22))
    user = env.get('LXC_APP_USER', 'condoc')
    password = env.get('LXC_APP_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=10)

    commands = [
        ("Caddyfile", "cat /etc/caddy/Caddyfile"),
        ("Portas Escutando", "ss -tulpn"),
        ("Status Caddy", "systemctl status caddy --no-pager"),
        ("Arquivos em /var/www", "ls -la /var/www /var/www/html 2>/dev/null || echo 'Sem /var/www'"),
        ("Processos Node / Python", "ps aux | grep -E 'node|vite|python|gunicorn|caddy' | grep -v grep"),
    ]

    for title, cmd in commands:
        print(f"\n=== {title} ===")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        if out:
            print(out)
        if err:
            print("STDERR:", err)

    ssh.close()

if __name__ == '__main__':
    main()
