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

    # Test connecting with psql over TCP using @@Condoc#
    cmd = "docker exec -e PGPASSWORD='@@Condoc#' supabase_db psql -h 127.0.0.1 -U postgres -d condc_dev -c 'SELECT current_user, current_database();'"
    code, out, err = exec_sudo(ssh, password, cmd)
    print("TCP connection test result:")
    print("Code:", code)
    print("Out:", out)
    print("Err:", err)

    ssh.close()

if __name__ == '__main__':
    main()
