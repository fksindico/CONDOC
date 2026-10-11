import os
import sys
import paramiko
import time

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
    host = env.get('LXC_SUPABASE_HOST', '192.168.10.201')
    port = int(env.get('LXC_SUPABASE_PORT', 22))
    user = env.get('LXC_SUPABASE_USER', 'condoc')
    password = env.get('LXC_SUPABASE_PASSWORD')

    print(f"Conectando a LXC 2 ({host}) para deploy da Stack Supabase...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=15)
    print("Conexão SSH com LXC 2 estabelecida!")

    # 1. Garante diretório /opt/supabase
    exec_sudo(ssh, password, "mkdir -p /opt/supabase && chown -R condoc:condoc /opt/supabase")

    # 2. Upload do docker-compose.yml
    print("Enviando infra/supabase/docker-compose.yml...")
    sftp = ssh.open_sftp()
    with open('infra/supabase/docker-compose.yml', 'rb') as f_local:
        with sftp.file('/opt/supabase/docker-compose.yml', 'wb') as f_remote:
            f_remote.write(f_local.read())
    sftp.close()

    # 3. Inicia o banco de dados PostgreSQL primeiro
    print("Iniciando container do PostgreSQL (supabase_db)...")
    exec_sudo(ssh, password, "docker compose -f /opt/supabase/docker-compose.yml up -d db")

    # 4. Aguarda o PostgreSQL ficar pronto
    print("Aguardando inicialização do PostgreSQL...")
    ready = False
    for i in range(25):
        code, out, err = exec_sudo(ssh, password, "docker exec supabase_db pg_isready -U postgres -d condc_dev")
        if code == 0:
            print(f"PostgreSQL pronto após {(i+1)*2} segundos!")
            ready = True
            break
        time.sleep(2)

    if not ready:
        print("AVISO: PostgreSQL demorou para inicializar. Verificando logs...")
        _, logs, _ = exec_sudo(ssh, password, "docker logs supabase_db --tail 30")
        print(logs)

    # 5. Envia e aplica as migrations SQL em ordem
    print("Enviando migrations para LXC 2...")
    exec_sudo(ssh, password, "rm -rf /tmp/migrations && mkdir -p /tmp/migrations && chown -R condoc:condoc /tmp/migrations && chmod 777 /tmp/migrations")
    sftp = ssh.open_sftp()
    migrations_dir = os.path.abspath('supabase/migrations')
    for mfile in sorted(os.listdir(migrations_dir)):
        if mfile.endswith('.sql'):
            local_mpath = os.path.join(migrations_dir, mfile)
            sftp.put(local_mpath, f'/tmp/migrations/{mfile}')
    sftp.close()

    print("Aplicando migrations SQL no PostgreSQL...")
    code, mlist, _ = exec_sudo(ssh, password, "ls -1 /tmp/migrations/*.sql | sort")
    for sql_file in mlist.splitlines():
        sql_file = sql_file.strip()
        if not sql_file:
            continue
        fname = os.path.basename(sql_file)
        print(f"  -> Executando {fname}...")
        code, out, err = exec_sudo(ssh, password, f"docker exec -i supabase_db psql -U postgres -d condc_dev -v ON_ERROR_STOP=1 < {sql_file}")
        if code != 0:
            print(f"ERRO ao aplicar {fname}: {err or out}")
        else:
            print(f"     OK")

    # 6. Aplica seed de referência se desejado
    seed_file = os.path.abspath('supabase/seeds/00000_seed_cenario_referencia.sql')
    if os.path.exists(seed_file):
        print("Enviando e aplicando seed de referência...")
        exec_sudo(ssh, password, "rm -f /tmp/seed.sql && touch /tmp/seed.sql && chown condoc:condoc /tmp/seed.sql && chmod 666 /tmp/seed.sql")
        sftp = ssh.open_sftp()
        sftp.put(seed_file, '/tmp/seed.sql')
        sftp.close()
        code, out, err = exec_sudo(ssh, password, "docker exec -i supabase_db psql -U postgres -d condc_dev < /tmp/seed.sql")
        print(f"Seed aplicado (código: {code})")

    # 7. Sobe os demais serviços do Supabase (auth, storage, studio)
    print("Iniciando serviços adicionais do Supabase (auth, storage, studio)...")
    exec_sudo(ssh, password, "docker compose -f /opt/supabase/docker-compose.yml up -d")

    # 8. Exibe status dos containers
    code, ps_out, _ = exec_sudo(ssh, password, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print("\nContainers em execução na LXC 2:")
    print(ps_out)

    ssh.close()
    print("\n[SUCESSO] Supabase implantado e ativo na LXC 2 (192.168.10.201)!")

if __name__ == '__main__':
    main()
