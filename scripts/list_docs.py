import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.200', username='condoc', password=os.environ.get('LXC_APP_PASSWORD', '@@Condoc#'))

cmd = """/opt/condc/venv/bin/python /opt/condc/core/manage.py shell << 'EOF'
from infrastructure.models import Document, Condominium
for d in Document.objects.select_related('condominium', 'project').all():
    print(f"DOC: {d.id} | Titulo: {d.title} | Tipo: {d.type} | Status: {d.status} | Condo: {d.condominium.name}")
EOF
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("DOCUMENTS:\n", stdout.read().decode())
ssh.close()
