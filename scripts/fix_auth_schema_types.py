import os
import sys
import time
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

    commands = [
        "ALTER TYPE public.factor_type SET SCHEMA auth;",
        "ALTER TYPE public.factor_status SET SCHEMA auth;",
        "ALTER TYPE public.aal_level SET SCHEMA auth;",
        "ALTER TYPE public.code_challenge_method SET SCHEMA auth;",
        "ALTER TYPE public.one_time_token_type SET SCHEMA auth;"
    ]

    print("Moving auth types from public to auth schema...")
    for cmd in commands:
        code, out, err = exec_sudo(ssh, password, f"docker exec -i supabase_db psql -U postgres -d condc_dev -c '{cmd}'")
        print(f"Executed: {cmd} -> Code: {code}, Out: {out.strip()}, Err: {err.strip()}")

    print("\nRestarting supabase_auth container...")
    code, out, err = exec_sudo(ssh, password, "docker restart supabase_auth")
    print("Restart result:", code, out, err)

    print("Waiting 6 seconds...")
    time.sleep(6)

    code, ps_out, _ = exec_sudo(ssh, password, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print("\nContainers status:")
    print(ps_out)

    code, logs, _ = exec_sudo(ssh, password, "docker logs supabase_auth 2>&1 | tail -n 15")
    print("\nsupabase_auth logs:")
    print(logs)

    ssh.close()

if __name__ == '__main__':
    main()
