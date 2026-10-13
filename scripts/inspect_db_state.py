import paramiko, sys
sys.path.insert(0, 'scripts')
from deploy_backend_lxc1 import load_env

env = load_env()
ssh_db = paramiko.SSHClient()
ssh_db.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_db.connect(env['LXC_SUPABASE_HOST'], 22, env['LXC_SUPABASE_USER'], env['LXC_SUPABASE_PASSWORD'], timeout=10)

def query(sql, title):
    print(f'=== {title} ===')
    cmd = f'docker exec supabase_db psql -U postgres -d condc_dev -c "{sql}"'
    stdin, stdout, stderr = ssh_db.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print('ERR:', err)

query("SELECT id, name, created_at FROM app.condominiums;", "CONDOMINIUMS")
query("SELECT b.id, b.condominium_id, c.name as condo, b.name, b.status FROM app.buildings b JOIN app.condominiums c ON b.condominium_id = c.id;", "BUILDINGS")
query("SELECT u.id, c.name as condo, b.name as building, u.code, u.status FROM app.units u JOIN app.condominiums c ON u.condominium_id = c.id LEFT JOIN app.buildings b ON u.building_id = b.id;", "UNITS")
query("SELECT r.id, c.name as condo, r.full_name, r.email, r.phone_e164, r.status, r.unit_id FROM app.resident_registrations r JOIN app.condominiums c ON r.condominium_id = c.id;", "RESIDENT REGISTRATIONS")
query("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'app' AND table_name = 'unit_memberships' ORDER BY ordinal_position;", "UNIT_MEMBERSHIPS COLUMNS")
query("SELECT * FROM app.unit_memberships;", "ALL UNIT MEMBERSHIPS")
query("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'app' AND table_name = 'residents' ORDER BY ordinal_position;", "RESIDENTS COLUMNS")
query("SELECT * FROM app.residents;", "ALL RESIDENTS")

query("SELECT ra.id, c.name as condo, a.email, a.full_name, ra.role, ra.status FROM app.role_assignments ra JOIN app.condominiums c ON ra.condominium_id = c.id JOIN app.accounts a ON ra.account_id = a.id;", "ROLE ASSIGNMENTS")
query("SELECT id, condominium_id, title, status, access_token FROM app.public_consultations;", "PUBLIC CONSULTATIONS")
query("SELECT id, public_consultation_id, author_name, author_phone, author_unit, action_type, status FROM app.consultation_suggestions;", "CONSULTATION SUGGESTIONS")


ssh_db.close()
