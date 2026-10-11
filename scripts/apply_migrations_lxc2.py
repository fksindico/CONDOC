import os
import sys
import paramiko
import time

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

def main():
    env = load_env()
    host = env.get('LXC_SUPABASE_HOST', '192.168.10.201')
    port = int(env.get('LXC_SUPABASE_PORT', 22))
    user = env.get('LXC_SUPABASE_USER', 'condoc')
    password = env.get('LXC_SUPABASE_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=15)
    print("Conectado a LXC 2 via SSH!")

    # 1. Copia migrations locais para dentro do container supabase_db
    print("Copiando migrations diretamente para supabase_db:/tmp/migrations...")
    ssh.exec_command("docker exec supabase_db mkdir -p /tmp/migrations")

    sftp = ssh.open_sftp()
    migrations_dir = os.path.abspath('supabase/migrations')
    for mfile in sorted(os.listdir(migrations_dir)):
        if mfile.endswith('.sql'):
            local_path = os.path.join(migrations_dir, mfile)
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            stdin, stdout, stderr = ssh.exec_command(f"docker exec -i supabase_db tee /tmp/migrations/{mfile} > /dev/null")
            stdin.write(content)
            stdin.close()
            stdout.channel.recv_exit_status()
            print(f"  -> Upload de {mfile} concluído no container.")
    sftp.close()

    # 2. Executa as migrations ordenadas
    print("\nExecutando psql nas migrations...")
    for mfile in sorted(os.listdir(migrations_dir)):
        if mfile.endswith('.sql'):
            cmd = f"docker exec supabase_db psql -U postgres -d condc_dev -v ON_ERROR_STOP=1 -f /tmp/migrations/{mfile}"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='ignore').strip()
            err = stderr.read().decode('utf-8', errors='ignore').strip()
            if code == 0:
                print(f"  [OK] {mfile}")
            else:
                print(f"  [ERRO {code}] {mfile}\n{err or out}")

    # 3. Aplica o seed
    seed_path = os.path.abspath('supabase/seeds/00000_seed_cenario_referencia.sql')
    if os.path.exists(seed_path):
        print("\nExecutando seed de referência...")
        with open(seed_path, 'r', encoding='utf-8') as f:
            seed_content = f.read()
        stdin, stdout, stderr = ssh.exec_command("docker exec -i supabase_db tee /tmp/seed.sql > /dev/null")
        stdin.write(seed_content)
        stdin.close()
        stdout.channel.recv_exit_status()

        cmd = "docker exec supabase_db psql -U postgres -d condc_dev -f /tmp/seed.sql"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"Seed executado (código {code})")

    # 4. Verifica tabelas criadas no schema app
    print("\nVerificando tabelas no schema app:")
    cmd = "docker exec supabase_db psql -U postgres -d condc_dev -c \"\\dt app.*\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='ignore'))

    ssh.close()

if __name__ == '__main__':
    main()
