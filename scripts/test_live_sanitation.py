import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://condoc.fk.adm.br/api/v1'

def req(url, method='GET', data=None):
    bdata = json.dumps(data).encode('utf-8') if data else None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    if data or method in ('POST', 'PUT', 'PATCH'):
        headers['Content-Type'] = 'application/json'
    r = urllib.request.Request(url, data=bdata, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, context=ctx) as resp:
            raw = resp.read().decode('utf-8')
            return resp.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8')
        print(f"DEBUG HTTPError code={e.code}, raw={raw[:200]}")
        try:
            return e.code, json.loads(raw) if raw.strip() else {}
        except Exception:
            return e.code, {"raw": raw}

print("1. Criando condominio de teste para saneamento...")
s, d = req(f'{BASE_URL}/condominiums', 'POST', {
    'name': 'Condominio Saneamento Prod Test',
    'timezone': 'America/Sao_Paulo',
    'address_city': 'Curitiba',
    'address_state': 'PR'
})
print("Status:", s, d)
assert s == 201, f"Falha ao criar: {d}"
condo_id = d['id']
print("Condominio criado ID:", condo_id)

print("\n2. Tentativa de expurgo DIRETO (ativo) -> Deve retornar 400...")
s, d = req(f'{BASE_URL}/condominiums/{condo_id}?permanent=true', 'DELETE')
print("Status:", s, d)
assert s == 400, f"Esperado 400, obteve {s}: {d}"

print("\n3. Arquivando condominio -> Deve retornar 204...")
s, d = req(f'{BASE_URL}/condominiums/{condo_id}', 'DELETE')
print("Status:", s, d)
assert s == 204, f"Esperado 204, obteve {s}: {d}"

print("\n4. Executando SANEAMENTO DEFINITIVO no condominio arquivado -> Deve retornar 204...")
s, d = req(f'{BASE_URL}/condominiums/{condo_id}?permanent=true', 'DELETE')
print("Status:", s, d)
assert s == 204, f"Esperado 204, obteve {s}: {d}"

print("\n5. Verificando se o condominio sumiu completamente do banco...")
s, d = req(f'{BASE_URL}/condominiums/{condo_id}', 'GET')
print("Status busca por ID:", s, d)
assert s == 404, f"Esperado 404, obteve {s}: {d}"

print("\n6. Testando saneamento de Torre e Unidade...")
s, d = req(f'{BASE_URL}/condominiums', 'POST', {'name': 'Condo San 2 Prod'})
assert s == 201
c2_id = d['id']

s, d = req(f'{BASE_URL}/condominiums/{c2_id}/buildings', 'POST', {'code': 'T1', 'name': 'Torre 1'})
assert s == 201
b_id = d['id']

s, d = req(f'{BASE_URL}/condominiums/{c2_id}/units', 'POST', {'code': 'U101', 'building_id': b_id})
assert s == 201
u_id = d['id']

# Tentativa expurgo unidade ativa -> 400
s_act, _ = req(f'{BASE_URL}/condominiums/{c2_id}/units/{u_id}?permanent=true', 'DELETE')
print("Tentativa expurgo unidade ativa:", s_act)
assert s_act == 400

# Desativa unidade -> 204
s_des, _ = req(f'{BASE_URL}/condominiums/{c2_id}/units/{u_id}', 'DELETE')
print("Desativacao unidade:", s_des)
assert s_des == 204

# Expurga unidade inativa -> 204
s_pur, _ = req(f'{BASE_URL}/condominiums/{c2_id}/units/{u_id}?permanent=true', 'DELETE')
print("Expurgo definitivo unidade:", s_pur)
assert s_pur == 204

# Tentativa expurgo torre ativa -> 400
s_bt_act, _ = req(f'{BASE_URL}/condominiums/{c2_id}/buildings/{b_id}?permanent=true', 'DELETE')
print("Tentativa expurgo torre ativa:", s_bt_act)
assert s_bt_act == 400

# Desativa torre -> 204
s_bt_des, _ = req(f'{BASE_URL}/condominiums/{c2_id}/buildings/{b_id}', 'DELETE')
print("Desativacao torre:", s_bt_des)
assert s_bt_des == 204

# Expurga torre inativa -> 204
s_bt_pur, _ = req(f'{BASE_URL}/condominiums/{c2_id}/buildings/{b_id}?permanent=true', 'DELETE')
print("Expurgo definitivo torre:", s_bt_pur)
assert s_bt_pur == 204

# Limpeza final do condo 2
req(f'{BASE_URL}/condominiums/{c2_id}', 'DELETE')
req(f'{BASE_URL}/condominiums/{c2_id}?permanent=true', 'DELETE')

print("\n=== TODOS OS TESTES DE SANEAMENTO EM PRODUCAO PASSARAM COM 100% DE SUCESSO! ===")
