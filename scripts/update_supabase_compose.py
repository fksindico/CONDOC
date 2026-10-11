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

    print("Uploading updated infra/supabase/docker-compose.yml to /opt/supabase/docker-compose.yml...")
    sftp = ssh.open_sftp()
    with open('infra/supabase/docker-compose.yml', 'rb') as f_local:
        with sftp.file('/opt/supabase/docker-compose.yml', 'wb') as f_remote:
            f_remote.write(f_local.read())
    sftp.close()

    print("Recreating Supabase containers (auth, storage, rest, studio)...")
    code, out, err = exec_sudo(ssh, password, "docker compose -f /opt/supabase/docker-compose.yml up -d --force-recreate auth storage rest studio")
    print("Compose output:\n", out, err)

    print("Waiting 5 seconds to check container health...")
    time.sleep(5)

    code, ps_out, _ = exec_sudo(ssh, password, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print("\nUpdated container status on LXC 2:")
    print(ps_out)

    # Check logs of auth and storage
    _, log_auth, _ = exec_sudo(ssh, password, "docker logs supabase_auth --tail 10")
    print("\nsupabase_auth recent logs:")
    print(log_auth)

    _, log_storage, _ = exec_sudo(ssh, password, "docker logs supabase_storage --tail 10")
    print("\nsupabase_storage recent logs:")
    print(log_storage)

    ssh.close()

if __name__ == '__main__':
    main()
