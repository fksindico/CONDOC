import os
import sys
import paramiko
import tarfile
import io

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

    print(f"Conectando a LXC 1 ({host})...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=15)
    print("Conexão SSH estabelecida!")

    # 1. Cria pacote tar do dist local em memória
    print("Empacotando apps/web/dist...")
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w:gz') as tar:
        dist_dir = os.path.abspath('apps/web/dist')
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_dir)
                tar.add(full_path, arcname=rel_path)
    tar_stream.seek(0)

    # 2. Upload via SFTP para /tmp/frontend_dist.tar.gz
    print("Enviando pacote frontend via SFTP...")
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/frontend_dist.tar.gz', 'wb') as remote_file:
        remote_file.write(tar_stream.read())
    sftp.close()
    print("Upload concluído!")

    # 3. Extrai em /opt/condc/frontend
    print("Extraindo em /opt/condc/frontend...")
    exec_sudo(ssh, password, "mkdir -p /opt/condc/frontend && rm -rf /opt/condc/frontend/*")
    exec_sudo(ssh, password, "tar -xzf /tmp/frontend_dist.tar.gz -C /opt/condc/frontend")
    exec_sudo(ssh, password, "chown -R caddy:caddy /opt/condc/frontend || chown -R www-data:www-data /opt/condc/frontend || true")
    exec_sudo(ssh, password, "chmod -R 755 /opt/condc/frontend")
    exec_sudo(ssh, password, "rm -f /tmp/frontend_dist.tar.gz")

    # 4. Configura /etc/caddy/Caddyfile
    print("Configurando /etc/caddy/Caddyfile...")
    caddy_content = """# Configuração Caddy para CONDOC — LXC 1
:80 {
    # API Backend Core Django
    handle /api/* {
        reverse_proxy 127.0.0.1:8000 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    handle /static/* {
        reverse_proxy 127.0.0.1:8000
    }

    # Frontend SPA React
    handle {
        header {
            X-Content-Type-Options nosniff
            X-Frame-Options SAMEORIGIN
            Referrer-Policy strict-origin-when-cross-origin
            Strict-Transport-Security "max-age=31536000; includeSubDomains"
        }
        root * /opt/condc/frontend
        try_files {path} /index.html
        file_server
    }
}
"""
    # Escreve o novo Caddyfile temporário e move com sudo
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/Caddyfile.new', 'w') as f:
        f.write(caddy_content)
    sftp.close()

    exec_sudo(ssh, password, "mv /tmp/Caddyfile.new /etc/caddy/Caddyfile")
    exec_sudo(ssh, password, "chown root:root /etc/caddy/Caddyfile && chmod 644 /etc/caddy/Caddyfile")

    # 5. Reinicia Caddy
    print("Reiniciando Caddy...")
    code, out, err = exec_sudo(ssh, password, "systemctl reload caddy || systemctl restart caddy")
    print(f"Caddy recarregado (status code: {code})")

    # 6. Teste local via curl na LXC 1
    stdin, stdout, stderr = ssh.exec_command("curl -sI http://127.0.0.1 | head -n 10")
    print("\nResposta HTTP local na porta 80:")
    print(stdout.read().decode('utf-8', errors='ignore'))

    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1 | head -n 15")
    print("\nHTML retornado na porta 80:")
    print(stdout.read().decode('utf-8', errors='ignore'))

    ssh.close()
    print("\n[SUCESSO] Frontend implantado na LXC 1!")

if __name__ == '__main__':
    main()
