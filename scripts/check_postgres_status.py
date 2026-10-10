import os
import sys
import paramiko

def load_env():
    env_vars = {}
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
    return code, out

def main():
    env = load_env()
    app_host = env.get('LXC_APP_HOST', '192.168.10.200')
    sub_host = env.get('LXC_SUPABASE_HOST', '192.168.10.201')
    user = env.get('LXC_APP_USER', 'condoc')
    password = env.get('LXC_APP_PASSWORD')

    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(app_host, port=22, username=user, password=password, timeout=10)

    code, out1 = exec_sudo(ssh1, password, "which psql; which postgres; systemctl status postgresql 2>/dev/null || echo 'No postgres on LXC1'")
    print("=== LXC 1 Postgres check ===")
    print(out1)
    ssh1.close()

    ssh2 = paramiko.SSHClient()
    ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh2.connect(sub_host, port=22, username=user, password=password, timeout=10)

    code, out2 = exec_sudo(ssh2, password, "docker ps -a; which psql; which postgres")
    print("=== LXC 2 Postgres check ===")
    print(out2)
    ssh2.close()

if __name__ == '__main__':
    main()
