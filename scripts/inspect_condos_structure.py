import paramiko
import sys

sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

def inspect():
    env = load_env()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

    sql = """
    SELECT 
        c.name as condo, 
        COALESCE(b.name, 'SEM TORRE') as bldg, 
        count(u.id) as unit_count,
        string_agg(u.code, ', ' ORDER BY u.code) filter (where u.code is not null) as sample_units
    FROM app.condominiums c 
    LEFT JOIN app.buildings b ON b.condominium_id = c.id 
    LEFT JOIN app.units u ON (u.building_id = b.id OR (b.id IS NULL AND u.building_id IS NULL)) AND u.condominium_id = c.id
    GROUP BY c.name, b.name 
    ORDER BY c.name, b.name;
    """

    cmd = f"docker exec supabase_db psql -U postgres -d condc_dev -c \"{sql}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    ssh.close()

if __name__ == '__main__':
    inspect()
