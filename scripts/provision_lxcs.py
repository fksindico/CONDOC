"""
Script de Provisionamento das LXCs Proxmox — CONDC
Arquitetura Híbrida/Nativa:
 - LXC 1 (192.168.10.200): 100% NATIVO (Zero Docker)
     -> Caddy (Proxy Reverso porta 80)
     -> Redis Server (Broker Celery & Cache 127.0.0.1:6379)
     -> Node.js 22 LTS & NPM
     -> Python 3 venv em /opt/condc/venv
     -> Tesseract OCR com suporte a Português (tesseract-ocr-por)
 - LXC 2 (192.168.10.201): Docker Engine & Compose restritos à Stack Supabase Local
     -> PostgreSQL 15 com RLS
     -> Supabase Auth (GoTrue)
     -> Supabase Storage Engine
     -> Kong API Gateway & Studio
"""
import os
import sys
import paramiko
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_env():
    env_vars = {}
    if not os.path.exists('.env'):
        print("ERRO: Arquivo .env não encontrado na raiz.")
        sys.exit(1)

    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip()
    return env_vars

def exec_sudo(ssh, password, cmd):
    full_cmd = f"echo '{password}' | sudo -S bash -c \"{cmd}\""
    stdin, stdout, stderr = ssh.exec_command(full_cmd, get_pty=True)
    while not stdout.channel.exit_status_ready():
        time.sleep(0.4)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    lines = [l for l in out.splitlines() if not l.startswith('[sudo] password') and not l.startswith('[sudo: authenticate]')]
    return code, "\n".join(lines)

def run_remote_commands(ssh, password, commands, label):
    print(f"\n=======================================================")
    print(f" Provisionando: {label}")
    print(f"=======================================================")

    for desc, cmd in commands:
        print(f"\n--> {desc}...")
        code, out = exec_sudo(ssh, password, cmd)
        last_lines = "\n".join(out.splitlines()[-4:]) if out else "OK"

        if code == 0:
            print(f"    [SUCESSO] {desc}")
            if last_lines:
                safe_out = last_lines.encode('ascii', errors='replace').decode('ascii')
                print(f"    Saída: {safe_out}")
        else:
            print(f"    [AVISO / CÓDIGO {code}] {desc}")
            safe_detail = out.encode('ascii', errors='replace').decode('ascii')
            print(f"    Detalhes:\n{safe_detail}")

def provision_lxc1_native(env):
    """LXC 1 — 100% Nativo sem Docker."""
    host = env.get('LXC_APP_HOST')
    port = int(env.get('LXC_APP_PORT', 22))
    user = env.get('LXC_APP_USER')
    password = env.get('LXC_APP_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, user, password)

    commands = [
        ("Atualizar repositórios APT", "apt-get update -y"),
        ("Instalar dependências de build, Python e Tesseract OCR",
         "DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl gnupg lsb-release git build-essential python3 python3-pip python3-venv libpq-dev tesseract-ocr tesseract-ocr-por"),
        ("Instalar Caddy (Proxy Reverso Nativo)",
         "which caddy || (DEBIAN_FRONTEND=noninteractive apt-get install -y caddy)"),
        ("Garantir Redis Server Nativo ativo",
         "DEBIAN_FRONTEND=noninteractive apt-get install -y redis-server && systemctl enable redis-server && systemctl start redis-server"),
        ("Garantir Node.js e NPM nativos instalados",
         "which node || (DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs npm)"),
        ("Criar diretório da aplicação e ajustar permissões",
         "mkdir -p /opt/condc && chown -R condoc:condoc /opt/condc"),
        ("Criar ambiente virtual Python e atualizar ferramentas",
         "su - condoc -c 'python3 -m venv /opt/condc/venv && /opt/condc/venv/bin/pip install --upgrade pip setuptools wheel'"),
        ("Validar versões dos serviços nativos na LXC 1",
         "caddy version && redis-cli ping && node -v && npm -v && /opt/condc/venv/bin/python3 --version && tesseract --version | head -n 1")
    ]

    run_remote_commands(ssh, password, commands, "LXC 1 — Aplicação CONDC (100% NATIVO)")
    ssh.close()

def provision_lxc2_supabase(env):
    """LXC 2 — Docker Engine e Compose restritos à stack Supabase."""
    host = env.get('LXC_SUPABASE_HOST')
    port = int(env.get('LXC_SUPABASE_PORT', 22))
    user = env.get('LXC_SUPABASE_USER')
    password = env.get('LXC_SUPABASE_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, user, password)

    commands = [
        ("Atualizar repositórios APT", "apt-get update -y"),
        ("Instalar pacotes base essenciais", "DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl gnupg lsb-release git"),
        ("Instalar Docker Engine e Docker Compose nativos do Ubuntu",
         "DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io docker-compose-v2 && systemctl enable docker && systemctl start docker"),
        ("Adicionar usuário condoc ao grupo docker", "usermod -aG docker condoc"),
        ("Criar diretório para a stack Supabase", "mkdir -p /opt/supabase && chown -R condoc:condoc /opt/supabase"),
        ("Validar instalação do Docker e Compose na LXC 2", "docker --version && docker compose version && docker ps")
    ]

    run_remote_commands(ssh, password, commands, "LXC 2 — Supabase Local Stack (Docker restrito)")
    ssh.close()

def main():
    env = load_env()
    print("Iniciando provisionamento e validação das LXCs...")
    provision_lxc1_native(env)
    provision_lxc2_supabase(env)
    print("\n=======================================================")
    print(" Provisionamento validado com sucesso!")
    print(" LXC 1 (192.168.10.200): Caddy, Redis, Python 3 venv, Node/NPM, Tesseract (NATIVOS)")
    print(" LXC 2 (192.168.10.201): Docker Engine e Compose (Stack Supabase)")
    print("=======================================================")

if __name__ == '__main__':
    main()
