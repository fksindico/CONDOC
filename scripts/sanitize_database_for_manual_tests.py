import paramiko
import sys
import os

sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

def sanitize_db():
    env = load_env()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

    print(">>> Conectado a LXC 2 (Database). Executando saneamento de dados de teste...")

    sql = """
    -- 1. Remove sugestões de teste
    DELETE FROM app.consultation_suggestions;
    
    -- 2. Remove consultas públicas de teste
    DELETE FROM app.public_consultations;
    
    -- 3. Remove moradores e registros de teste
    DELETE FROM app.unit_memberships;
    DELETE FROM app.residents;
    DELETE FROM app.resident_registrations;
    
    -- 4. Mantem condomínio e limpa unidades temporárias se necessário
    -- Mantem as unidades base ou limpa
    """

    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql}"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()

    print(out)
    if err:
        print("ERR:", err)

    ssh.close()
    print(">>> Saneamento do banco concluído com sucesso!")

if __name__ == '__main__':
    sanitize_db()
