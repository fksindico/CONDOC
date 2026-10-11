import os
import sys
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
    user = env.get('LXC_SUPABASE_USER', 'condoc')
    password = env.get('LXC_SUPABASE_PASSWORD') or env.get('LXC_APP_PASSWORD')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=22, username=user, password=password, timeout=15)

    print("Tables in auth schema:")
    code, out, _ = exec_sudo(ssh, password, "docker exec supabase_db psql -U postgres -d condc_dev -c \"\\dt auth.*\"")
    print(out)

    print("\nTypes in auth schema:")
    code, out, _ = exec_sudo(ssh, password, "docker exec supabase_db psql -U postgres -d condc_dev -c \"\\dT auth.*\"")
    print(out)

    print("\nColumns of auth.mfa_factors:")
    code, out, _ = exec_sudo(ssh, password, "docker exec supabase_db psql -U postgres -d condc_dev -c \"\\d auth.mfa_factors\"")
    print(out)

    print("\nAll types across schemas with 'factor':")
    code, out, _ = exec_sudo(ssh, password, "docker exec supabase_db psql -U postgres -d condc_dev -c \"SELECT n.nspname, t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname LIKE '%factor%';\"")
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
