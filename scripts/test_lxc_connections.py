import os
import sys
import paramiko

def load_env():
    env_vars = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip()
    return env_vars

def test_lxc(label, host, port, user, password, key_path):
    print(f"\n=======================================================")
    print(f" Testando Conexão SSH: {label}")
    print(f" Host: {host}:{port} | Usuário: {user}")
    print(f"=======================================================")

    if not host or not user:
        print(" [AVISO] Host ou Usuário não definidos.")
        return None

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        connect_kwargs = {
            'hostname': host,
            'port': int(port or 22),
            'username': user,
            'timeout': 10
        }
        if key_path and os.path.exists(key_path):
            connect_kwargs['key_filename'] = key_path
        elif password:
            connect_kwargs['password'] = password

        ssh.connect(**connect_kwargs)
        print(" [SUCESSO] Conexão SSH estabelecida com sucesso!")

        commands = {
            "Sistema Operacional": "cat /etc/os-release | grep PRETTY_NAME | cut -d '=' -f2 | tr -d '\"'",
            "Kernel": "uname -r",
            "Arquitetura": "uname -m",
            "CPU (Cores)": "nproc",
            "Memória RAM": "free -h | awk '/^Mem:/ {print $2 \" total, \" $3 \" usado, \" $7 \" disponível\"}'",
            "Disco (/)": "df -h / | awk 'NR==2 {print $2 \" total, \" $3 \" usado, \" $4 \" livre (\" $5 \")\"}'",
            "IPs Locais": "hostname -I",
            "Docker": "docker --version 2>/dev/null || echo 'Não instalado'",
            "Docker Compose": "docker compose version 2>/dev/null || echo 'Não instalado'",
            "Python 3": "python3 --version 2>/dev/null || echo 'Não instalado'",
            "Node.js": "node -v 2>/dev/null || echo 'Não instalado'",
            "Git": "git --version 2>/dev/null || echo 'Não instalado'"
        }

        results = {}
        for cmd_name, cmd in commands.items():
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
            out = stdout.read().decode('utf-8', errors='ignore').strip()
            err = stderr.read().decode('utf-8', errors='ignore').strip()
            results[cmd_name] = out if out else (f"Erro: {err}" if err else "N/A")
            print(f" - {cmd_name:20}: {results[cmd_name]}")

        # Testar permissão sudo com senha informada
        sudo_stdin, sudo_stdout, sudo_stderr = ssh.exec_command(f"echo '{password}' | sudo -S whoami", timeout=5)
        sudo_user = sudo_stdout.read().decode('utf-8', errors='ignore').strip()
        if "root" in sudo_user:
            print(f" - Privilégios Sudo    : SUCESSO (Acesso root verificado)")
        else:
            print(f" - Privilégios Sudo    : Requer verificação ({sudo_stderr.read().decode('utf-8', errors='ignore').strip()})")

        return ssh
    except Exception as e:
        print(f" [FALHA] Erro ao conectar SSH: {e}")
        return None

def main():
    env = load_env()

    app_host = env.get('LXC_APP_HOST')
    app_port = env.get('LXC_APP_PORT', '22')
    app_user = env.get('LXC_APP_USER')
    app_pass = env.get('LXC_APP_PASSWORD')
    app_key = env.get('LXC_APP_SSH_KEY')

    sub_host = env.get('LXC_SUPABASE_HOST')
    sub_port = env.get('LXC_SUPABASE_PORT', '22')
    sub_user = env.get('LXC_SUPABASE_USER')
    sub_pass = env.get('LXC_SUPABASE_PASSWORD')
    sub_key = env.get('LXC_SUPABASE_SSH_KEY')

    ssh_app = test_lxc("LXC 1 — Aplicação CONDC", app_host, app_port, app_user, app_pass, app_key)
    ssh_sub = test_lxc("LXC 2 — Supabase Local Stack", sub_host, sub_port, sub_user, sub_pass, sub_key)

    if ssh_app and sub_host:
        print(f"\n=======================================================")
        print(f" Testando Comunicação Direta entre LXC 1 e LXC 2")
        print(f"=======================================================")
        stdin, stdout, stderr = ssh_app.exec_command(f"ping -c 2 {sub_host}", timeout=5)
        ping_out = stdout.read().decode('utf-8', errors='ignore').strip()
        if "2 packets transmitted, 2 received" in ping_out or "0% packet loss" in ping_out:
            print(f" [SUCESSO] LXC 1 alcança LXC 2 com 0% de perda de pacotes!")
        else:
            print(f" [AVISO] Resultado do ping:\n{ping_out}")

    if ssh_app:
        ssh_app.close()
    if ssh_sub:
        ssh_sub.close()

if __name__ == '__main__':
    main()
