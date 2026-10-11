import os
import sys
import subprocess

def load_env():
    env = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def main():
    env = load_env()
    token = env.get('GITHUB_TOKEN')
    username = env.get('GITHUB_USERNAME', 'fksindico')
    repo = env.get('GITHUB_REPO', 'fksindico/CONDOC')

    if not token:
        print("[ERRO] GITHUB_TOKEN não configurado no .env")
        sys.exit(1)

    remote_url = env.get('GITHUB_REMOTE_URL') or 'https://github.com/fksindico/CONDOC.git'
    if 'github.com/' in remote_url:
        repo_path = remote_url.split('github.com/', 1)[1].rstrip('.git')
    else:
        repo_path = 'fksindico/CONDOC'

    push_url = f"https://{username}:{token}@github.com/{repo_path}.git"
    
    print(f"Executando git push para https://github.com/{repo_path}.git (branch main)...")
    res = subprocess.run(
        ["git", "push", push_url, "main"],
        capture_output=True,
        text=True
    )
    
    # Filter token from output if any
    safe_out = res.stdout.replace(token, "***")
    safe_err = res.stderr.replace(token, "***")
    
    if safe_out.strip():
        print("Output:", safe_out.strip())
    if safe_err.strip():
        print("Status/Log:", safe_err.strip())
        
    if res.returncode == 0:
        print("[SUCESSO] Código sincronizado com o GitHub com sucesso!")
    else:
        print(f"[ERRO] Falha no git push (código {res.returncode})")
        sys.exit(res.returncode)

if __name__ == '__main__':
    main()
