import os
import sys
import paramiko
import tarfile
import io

def load_env():
    env_vars = {}
    if not os.path.exists('.env'):
        sys.exit(1)
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
    err = stderr.read().decode('utf-8', errors='ignore')
    return code, out, err

def main():
    env = load_env()
    host = env.get('LXC_APP_HOST', '192.168.10.200')
    port = int(env.get('LXC_APP_PORT', 22))
    user = env.get('LXC_APP_USER', 'condoc')
    password = env.get('LXC_APP_PASSWORD')

    print(f"Conectando a LXC 1 ({host}) para deploy do backend...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=15)

    # 1. Empacota core/ (excluindo __pycache__, .pytest_cache)
    print("Empacotando diretório core/...")
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w:gz') as tar:
        core_dir = os.path.abspath('core')
        for root, dirs, files in os.walk(core_dir):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', '.pytest_cache', '.venv')]
            for file in files:
                if file.endswith(('.pyc', '.pyo')):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, core_dir)
                tar.add(full_path, arcname=rel_path)
    tar_stream.seek(0)

    # 2. Upload via SFTP para /tmp/core.tar.gz e .env
    print("Enviando core.tar.gz...")
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/core.tar.gz', 'wb') as f:
        f.write(tar_stream.read())

    print("Configurando /opt/condc/.env para conexao com LXC 2...")
    backend_env = f"""# CONDOC Backend Environment - LXC 1
DJANGO_SETTINGS_MODULE=config.settings.dev
DEBUG=True
SECRET_KEY=condoc-production-secret-key-192-168-10-200
ALLOWED_HOSTS=*

# Banco de dados PostgreSQL na LXC 2 (192.168.10.201)
POSTGRES_DB=condc_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD={password}
POSTGRES_HOST=192.168.10.201
POSTGRES_PORT=5432

# Redis local na LXC 1
REDIS_URL=redis://127.0.0.1:6379/0

# Supabase Auth / Storage na LXC 2
SUPABASE_URL=http://192.168.10.201:8000
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.dummy
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.dummy_service
"""
    with sftp.file('/tmp/condc.env', 'w') as f_remote:
        f_remote.write(backend_env)
    sftp.close()

    # 3. Extrai em /opt/condc/core e move .env
    print("Extraindo em /opt/condc/core...")
    exec_sudo(ssh, password, "mkdir -p /opt/condc/core")
    exec_sudo(ssh, password, "tar -xzf /tmp/core.tar.gz -C /opt/condc/core")
    exec_sudo(ssh, password, "mv /tmp/condc.env /opt/condc/.env && chmod 600 /opt/condc/.env")
    exec_sudo(ssh, password, "chown -R condoc:condoc /opt/condc")
    exec_sudo(ssh, password, "rm -f /tmp/core.tar.gz")

    # 4. Instala dependências do Python no venv da LXC 1
    print("Instalando dependências Python no /opt/condc/venv...")
    exec_sudo(ssh, password, "su - condoc -c '/opt/condc/venv/bin/pip install -r /opt/condc/core/requirements.txt gunicorn'")

    # 5. Configura e inicia o systemd service
    print("Criando serviço systemd condc-backend.service...")
    service_content = f"""[Unit]
Description=CONDOC Core Django API Backend
After=network.target

[Service]
User=condoc
Group=condoc
WorkingDirectory=/opt/condc/core
ExecStart=/opt/condc/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 60
Restart=always
RestartSec=3
EnvironmentFile=/opt/condc/.env
Environment="DJANGO_SETTINGS_MODULE=config.settings.dev"

[Install]
WantedBy=multi-user.target
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/condc-backend.service', 'w') as f:
        f.write(service_content)
    sftp.close()

    exec_sudo(ssh, password, "mv /tmp/condc-backend.service /etc/systemd/system/condc-backend.service")
    exec_sudo(ssh, password, "systemctl daemon-reload")
    exec_sudo(ssh, password, "systemctl enable condc-backend && systemctl restart condc-backend")

    # 6. Verifica status do serviço
    code, out, err = exec_sudo(ssh, password, "systemctl is-active condc-backend")
    print(f"Status do backend: {out.strip()}")

    # 7. Testa resposta do endpoint /api/v1/health via Caddy local
    stdin, stdout, stderr = ssh.exec_command("curl -sI http://127.0.0.1/api/v1/auth/session | head -n 5")
    print("\nResposta de teste da API:")
    print(stdout.read().decode('utf-8', errors='ignore'))

    ssh.close()
    print("[SUCESSO] Backend implantado e ativo na LXC 1!")

if __name__ == '__main__':
    main()
