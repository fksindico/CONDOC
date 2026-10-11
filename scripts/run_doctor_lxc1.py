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
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    password = env.get('LXC_APP_PASSWORD')
    ssh.connect(env.get('LXC_APP_HOST', '192.168.10.200'), username=env.get('LXC_APP_USER', 'condoc'), password=password)

    code, out, err = exec_sudo(ssh, password, "su - condoc -c 'cd /opt/condc ; bash scripts/doctor.sh'")
    print("Doctor output:")
    print(out)
    print("Doctor err:")
    print(err)
    print("Return code:", code)

    ssh.close()

if __name__ == '__main__':
    main()
