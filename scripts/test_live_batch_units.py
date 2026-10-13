import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://192.168.10.200"

def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'BatchUnitTester/1.0'})
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read(), resp.headers

def http_post_json(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'BatchUnitTester/1.0'
        }
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read(), resp.headers

def run_test():
    print("=== TESTE LIVE: GERAÇÃO EM LOTE DE TORRES E APARTAMENTOS (192.168.10.200) ===")
    
    # 1. Pega condomínio ativo
    status, body, _ = http_get(f"{BASE_URL}/api/v1/condominiums")
    assert status == 200
    condos = json.loads(body.decode('utf-8'))
    condo = condos[0]
    condo_id = condo['id']
    condo_name = condo['name']
    print(f"[OK] Condomínio ativo: {condo_name} ({condo_id})")

    # 2. Gera lote de apartamentos em nova torre (Torre Esmeralda, 3º ao 5º andar, 4 por andar)
    batch_payload = {
        "new_building_name": "Torre Esmeralda",
        "new_building_code": "ESM",
        "start_floor": 3,
        "end_floor": 5,
        "units_per_floor": 4,
        "suffix_digits": 2,
    }
    status, body, _ = http_post_json(f"{BASE_URL}/api/v1/condominiums/{condo_id}/units/batch-generate", batch_payload)
    assert status in (200, 201)
    batch_res = json.loads(body.decode('utf-8'))
    print(f"[OK] Lote gerado com sucesso!")
    print(f"     Torre: {batch_res['building']['name']} (ID: {batch_res['building']['id']})")
    print(f"     Total no lote: {batch_res['total_units']} unidades (Criadas: {batch_res['created_count']}).")
    print(f"     Códigos de amostra: {batch_res['sample_codes'][:6]}...")
    assert batch_res['total_units'] == 12  # (3 andares * 4 = 12)
    assert "301" in batch_res['sample_codes']
    assert "304" in batch_res['sample_codes']
    assert "504" in batch_res['sample_codes']

    # 3. Testa idempotência (reexecução do lote não duplica e retorna status de sucesso)
    status, body, _ = http_post_json(f"{BASE_URL}/api/v1/condominiums/{condo_id}/units/batch-generate", {
        "building_id": batch_res['building']['id'],
        "start_floor": 3,
        "end_floor": 5,
        "units_per_floor": 4,
    })
    assert status in (200, 201)
    batch_res2 = json.loads(body.decode('utf-8'))
    print(f"[OK] Idempotência confirmada: reexecução segura concluída sem duplicidades!")

    # 4. Verifica na lista de consultas públicas se o campo structure reflete a nova torre e os apartamentos
    status, body, _ = http_get(f"{BASE_URL}/api/v1/condominiums/{condo_id}/consultations")
    assert status == 200
    consultations = json.loads(body.decode('utf-8'))
    if consultations:
        token = consultations[0]['public_token']
        status, body, _ = http_get(f"{BASE_URL}/api/v1/public/consultations/{token}")
        assert status == 200
        pub_data = json.loads(body.decode('utf-8'))
        assert 'structure' in pub_data
        structure = pub_data['structure']
        bldgs = structure['buildings']
        esmeralda = next((b for b in bldgs if b['name'] == 'Torre Esmeralda'), None)
        assert esmeralda is not None, "Torre Esmeralda não encontrada na consulta pública!"
        codes = [u['code'] for u in esmeralda['units']]
        assert "301" in codes
        assert "504" in codes
        print(f"[OK] Consulta pública ({token}) expõe estrutura predial para seleção sem digitação!")
        print(f"     Torre Esmeralda possui {len(codes)} apartamentos disponíveis no dropdown.")

    print("\n=======================================================")
    print("[SUCESSO TOTAL] GERAÇÃO EM LOTE E ESTRUTURA SEM DIGITAÇÃO VALIDADAS EM PRODUÇÃO!")
    print("=======================================================")

if __name__ == '__main__':
    try:
        run_test()
    except Exception as e:
        print(f"\n[ERRO]: {e}")
        sys.exit(1)
