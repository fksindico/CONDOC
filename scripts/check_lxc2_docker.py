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
    sub_host = env.get('LXC_SUPABASE_HOST', '192.168.10.201')
    user = env.get('LXC_SUPABASE_USER', 'condoc')
    password = env.get('LXC_SUPABASE_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(sub_host, port=22, username=user, password=password, timeout=10)

    commands = [
        "docker --version",
        "docker compose version",
        "docker ps -a",
        "free -h",
        "df -h /",
        "ls -la /opt/supabase 2>/dev/null || true"
    ]

    for cmd in commands:
        print(f"\n--- {cmd} ---")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        if out:
            print(out)
        if err:
            print("STDERR:", err)

    ssh.close()

if __name__ == '__main__':
    main()
