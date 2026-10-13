import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://192.168.10.200"

def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'TowerIsolationTester/1.0'})
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read(), resp.headers

def http_post_json(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'TowerIsolationTester/1.0'
        }
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read(), resp.headers

def run_test():
    print("=== TESTE LIVE: VÍNCULO DE CONDOMÍNIO E FILTRO POR TORRE (192.168.10.200) ===")

    # 1. Lista condomínios
    status, body, _ = http_get(f"{BASE_URL}/api/v1/condominiums")
    assert status == 200
    condos = json.loads(body.decode('utf-8'))
    assert len(condos) >= 2, "Devem existir ao menos 2 condomínios para o teste de isolamento!"
    
    condo_a = condos[0]
    condo_b = condos[1]
    print(f"[OK] Condomínio A: {condo_a['name']} ({condo_a['id']})")
    print(f"[OK] Condomínio B: {condo_b['name']} ({condo_b['id']})")

    # 2. Cria Torre A1 e lote de 6 unidades no Condomínio A
    batch_payload_a = {
        "new_building_name": "Torre A1 - Sol",
        "new_building_code": "SOL",
        "start_floor": 1,
        "end_floor": 2,
        "units_per_floor": 3,
        "suffix_digits": 2,
    }
    status, body, _ = http_post_json(f"{BASE_URL}/api/v1/condominiums/{condo_a['id']}/units/batch-generate", batch_payload_a)
    assert status in (200, 201)
    res_a = json.loads(body.decode('utf-8'))
    bldg_a1_id = res_a['building']['id']
    print(f"[OK] Torre A1 criada no Condomínio A com {res_a['total_units']} apartamentos.")

    # 3. Cria Torre B1 e lote de 4 unidades no Condomínio B
    batch_payload_b = {
        "new_building_name": "Torre B1 - Lua",
        "new_building_code": "LUA",
        "start_floor": 1,
        "end_floor": 2,
        "units_per_floor": 2,
        "suffix_digits": 2,
    }
    status, body, _ = http_post_json(f"{BASE_URL}/api/v1/condominiums/{condo_b['id']}/units/batch-generate", batch_payload_b)
    assert status in (200, 201)
    res_b = json.loads(body.decode('utf-8'))
    bldg_b1_id = res_b['building']['id']
    print(f"[OK] Torre B1 criada no Condomínio B com {res_b['total_units']} apartamentos.")

    # 4. Verifica Isolamento: Condomínio A só lista Torre A1, nunca Torre B1
    status, body, _ = http_get(f"{BASE_URL}/api/v1/condominiums/{condo_a['id']}/buildings")
    assert status == 200
    bldgs_a = json.loads(body.decode('utf-8'))
    names_a = [b['name'] for b in bldgs_a]
    assert "Torre A1 - Sol" in names_a
    assert "Torre B1 - Lua" not in names_a, "Violação de isolamento: Torre do Condomínio B vazou no Condomínio A!"
    print(f"[OK] Isolamento de Torres validado: Condomínio A contém apenas: {names_a}")

    # 5. Verifica Isolamento: Condomínio B só lista Torre B1, nunca Torre A1
    status, body, _ = http_get(f"{BASE_URL}/api/v1/condominiums/{condo_b['id']}/buildings")
    assert status == 200
    bldgs_b = json.loads(body.decode('utf-8'))
    names_b = [b['name'] for b in bldgs_b]
    assert "Torre B1 - Lua" in names_b
    assert "Torre A1 - Sol" not in names_b, "Violação de isolamento: Torre do Condomínio A vazou no Condomínio B!"
    print(f"[OK] Isolamento de Torres validado: Condomínio B contém apenas: {names_b}")

    # 6. Verifica Filtro por Torre no Condomínio A (GET ?building_id=...)
    status, body, _ = http_get(f"{BASE_URL}/api/v1/condominiums/{condo_a['id']}/units?building_id={bldg_a1_id}")
    assert status == 200
    units_t1 = json.loads(body.decode('utf-8'))
    assert len(units_t1) == 6
    codes_t1 = [u['code'] for u in units_t1]
    assert codes_t1 == ["101", "102", "103", "201", "202", "203"]
    print(f"[OK] Filtro por Torre validado com sucesso! Unidades da Torre A1: {codes_t1}")

    # 7. Saneamento ao final do teste para deixar a base limpa
    print("\n--- Limpando dados do teste de isolamento ---")
    sys.path.insert(0, 'scripts')
    from sanitize_database_for_manual_tests import sanitize_db
    sanitize_db()

    print("\n=======================================================")
    print("[SUCESSO TOTAL] ISOLAMENTO E FILTRAGEM POR TORRE VALIDADOS EM PRODUÇÃO!")
    print("=======================================================")

if __name__ == '__main__':
    try:
        run_test()
    except Exception as e:
        print(f"\n[ERRO]: {e}")
        sys.exit(1)
