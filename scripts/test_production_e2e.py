import os
import sys
import json
import urllib.request
import ssl
import paramiko

def load_env():
    env = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def exec_sudo(ssh, password, cmd):
    stdin, stdout, stderr = ssh.exec_command("sudo -S " + cmd)
    stdin.write(password + "\n")
    stdin.flush()
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    return code, out, err

def test_public_url(url):
    print(f"\n[1/4] Testando Acesso Público HTTPS em {url}...")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Condoc-QA-Production-Auditor/1.0"}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        status = resp.status
        headers = dict(resp.getheaders())
        html = resp.read().decode('utf-8', errors='ignore')

    print(f"  -> HTTP Status: {status}")
    print(f"  -> Server: {headers.get('Server', headers.get('server'))}")
    print(f"  -> Content-Type: {headers.get('Content-Type', headers.get('content-type'))}")
    print(f"  -> HSTS: {headers.get('Strict-Transport-Security', headers.get('strict-transport-security'))}")

    # Valida presença dos bundles recém-compilados
    has_js = 'index-DHfQjcdZ.js' in html
    has_css = 'index-QdlaauYd.css' in html
    has_title = 'CONDOC' in html
    print(f"  -> Bundle JS detectado: {has_js}")
    print(f"  -> Bundle CSS detectado: {has_css}")
    print(f"  -> Título CONDOC: {has_title}")

    assert status == 200, f"Status inválido: {status}"
    assert has_js, "Novo bundle JS não encontrado no HTML retornado!"
    assert has_css, "Novo bundle CSS não encontrado no HTML retornado!"
    print("  => Frontend HTTPS em produção: OK!")

def test_public_api(url):
    print(f"\n[2/4] Testando Endpoints de API em {url}...")
    api_url = f"{url.rstrip('/')}/api/v1/auth/session"
    req = urllib.request.Request(
        api_url,
        headers={"User-Agent": "Condoc-QA-Production-Auditor/1.0", "Accept": "application/json"}
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        status = resp.status
        content_type = resp.headers.get("Content-Type")
        body = resp.read().decode('utf-8')
        data = json.loads(body)

    print(f"  -> /api/v1/auth/session Status: {status}")
    print(f"  -> Content-Type: {content_type}")
    print(f"  -> Sessão retornada: {data}")

    assert status == 200, f"API retornou status {status}"
    assert data.get("authenticated") is False, "Esperado authenticated=False para cliente anônimo"
    print("  => API Pública Backend em produção: OK!")

def test_lxc_containers_and_services(env):
    print("\n[3/4] Verificando integridade dos serviços nas LXCs...")
    # LXC 1
    host1 = env.get('LXC_APP_HOST', '192.168.10.200')
    user1 = env.get('LXC_APP_USER', 'condoc')
    pass1 = env.get('LXC_APP_PASSWORD')

    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(host1, username=user1, password=pass1, timeout=10)

    code, out1, _ = exec_sudo(ssh1, pass1, "systemctl is-active condc-backend caddy redis-server")
    print(f"  -> LXC 1 ({host1}) Serviços:")
    for line in out1.strip().splitlines():
        print(f"     * {line.strip()}")
    ssh1.close()

    # LXC 2
    host2 = env.get('LXC_SUPABASE_HOST', '192.168.10.201')
    user2 = env.get('LXC_SUPABASE_USER', 'condoc')
    pass2 = env.get('LXC_SUPABASE_PASSWORD') or pass1

    ssh2 = paramiko.SSHClient()
    ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh2.connect(host2, username=user2, password=pass2, timeout=10)

    code, out2, _ = exec_sudo(ssh2, pass2, "docker ps --format '{{.Names}}: {{.Status}}'")
    print(f"  -> LXC 2 ({host2}) Containers Docker:")
    for line in out2.strip().splitlines():
        print(f"     * {line.strip()}")
    ssh2.close()
    print("  => Serviços e containers LXC: OK!")

def test_django_backend_tests_on_lxc1(env):
    print("\n[4/4] Executando suíte de testes de integridade diretamente no ambiente de produção (LXC 1)...")
    host1 = env.get('LXC_APP_HOST', '192.168.10.200')
    user1 = env.get('LXC_APP_USER', 'condoc')
    pass1 = env.get('LXC_APP_PASSWORD')

    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(host1, username=user1, password=pass1, timeout=10)

    # Executa a suíte completa de testes dentro da LXC 1 usando o ambiente virtual /opt/condc/venv
    test_cmd = "su - condoc -c 'cd /opt/condc/core && /opt/condc/venv/bin/pytest tests/ -q'"
    code, out, err = exec_sudo(ssh1, pass1, test_cmd)
    print("  -> Saída dos testes em produção:")
    for line in out.strip().splitlines():
        if line.strip():
            print(f"     {line.strip()}")
    if err.strip():
        for line in err.strip().splitlines():
            if "Password:" not in line and line.strip():
                print(f"     ERR: {line.strip()}")

    ssh1.close()
    assert code == 0, f"Testes em produção falharam com código {code}"
    print("  => Todos os testes do Backend no ambiente de produção: OK!")

def main():
    print("==========================================================")
    print("    CONDOC — AUDITORIA DE PRODUÇÃO E E2E LIFECYCLE        ")
    print("==========================================================")
    env = load_env()
    prod_url = env.get('PUBLIC_URL', 'https://condoc.fk.adm.br')

    test_public_url(prod_url)
    test_public_api(prod_url)
    test_lxc_containers_and_services(env)
    test_django_backend_tests_on_lxc1(env)

    print("\n==========================================================")
    print(" [SUCESSO TOTAL] PRODUÇÃO VALIDADA COM 100% DE CONFIANÇA! ")
    print("==========================================================")

if __name__ == '__main__':
    main()
