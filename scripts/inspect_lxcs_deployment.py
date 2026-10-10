import os
import sys
import paramiko

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
    return stdout.read().decode('utf-8', errors='ignore')

def main():
    env = load_env()
    app_host = env.get('LXC_APP_HOST', '192.168.10.200')
    sub_host = env.get('LXC_SUPABASE_HOST', '192.168.10.201')
    user = env.get('LXC_APP_USER', 'condoc')
    password = env.get('LXC_APP_PASSWORD')

    print("=== LXC 1 (192.168.10.200) ===")
    ssh1 = paramiko.SSHClient()
    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh1.connect(app_host, port=22, username=user, password=password, timeout=10)

    out1 = exec_sudo(ssh1, password, "ls -la /opt/condc")
    print("Contedo /opt/condc:\n" + out1.encode('ascii', errors='replace').decode('ascii'))
    ssh1.close()

    print("=== LXC 2 (192.168.10.201) ===")
    ssh2 = paramiko.SSHClient()
    ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh2.connect(sub_host, port=22, username=user, password=password, timeout=10)

    out2 = exec_sudo(ssh2, password, "docker ps -a")
    print("Containers Docker:\n" + out2.encode('ascii', errors='replace').decode('ascii'))
    ssh2.close()

if __name__ == '__main__':
    main()
