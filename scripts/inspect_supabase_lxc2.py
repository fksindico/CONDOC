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

    code, out, err = exec_sudo(ssh, password, "docker logs supabase_auth 2>&1 | tail -n 25")
    print("Logs (stdout + stderr):")
    print(out)

    code, inspect_out, _ = exec_sudo(ssh, password, "docker inspect supabase_auth --format 'State: {{.State.Status}} ExitCode: {{.State.ExitCode}} Error: {{.State.Error}}'")
    print("Inspect status:")
    print(inspect_out)

    ssh.close()

if __name__ == '__main__':
    main()
