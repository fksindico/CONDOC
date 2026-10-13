import urllib.request
import urllib.parse
import json
import uuid

BASE_URL = 'http://192.168.10.200/api/v1'
CONDO_ID = '7e044fb7-8819-4072-8a70-d346bad3a9b4'

def test_lifecycle():
    print("=================================================================")
    print("TESTE DE CICLO REAL: CONSULTA, SUGESTÃO E DEDUPLICAÇÃO DE MORADOR")
    print("=================================================================")

    # 1. Cria Consulta Pública Simplificada
    print("\n>>> 1. Criando consulta pública no NEXT RESIDENCE...")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body_parts = []
    
    def add_field(name, value):
        body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n')
    
    add_field("title", "Revisão Geral do Regimento Interno 2026")
    add_field("document_type", "regimento")
    add_field("description", "Consulta pública para envio de sugestões pelos moradores.")
    
    # PDF dummy
    pdf_content = b"%PDF-1.4 Mock Regimento Interno Next Residence"
    file_header = f'--{boundary}\r\nContent-Disposition: form-data; name="pdf_file"; filename="Regimento_Next_Residence.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
    
    full_body = "".join(body_parts).encode('utf-8') + file_header.encode('utf-8') + pdf_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    req = urllib.request.Request(
        f"{BASE_URL}/condominiums/{CONDO_ID}/consultations",
        data=full_body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    
    with urllib.request.urlopen(req) as resp:
        consultation = json.loads(resp.read().decode())
        print(f"    [OK] Consulta criada! ID: {consultation['id']}")
        print(f"    [OK] Token universal gerado: {consultation['public_token']}")
    
    token = consultation['public_token']

    # 2. Morador envia 1ª Sugestão (Fabiano Silva, Apto 1004)
    print("\n>>> 2. Morador envia 1ª sugestão no link universal...")
    sug1_payload = json.dumps({
        "resident_name": "Fabiano Silva",
        "resident_phone": "(27) 93500-9626",
        "resident_email": "sindico@fabianochaves.com.br",
        "block_tower": "VILLE",
        "unit_code": "1004",
        "target_reference": "Artigo 12, Parágrafo 1º",
        "action_type": "alterar",
        "suggestion_text": "Permitir mudança aos sábados até as 14h mediante agendamento prévio.",
        "justification": "Facilita para moradores que trabalham durante a semana."
    }).encode('utf-8')

    req_sug1 = urllib.request.Request(
        f"{BASE_URL}/public/consultations/{token}/suggestions",
        data=sug1_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req_sug1) as resp:
        sug1 = json.loads(resp.read().decode())
        print(f"    [OK] Sugestão 1 enviada! Protocolo: {sug1['protocol']}")

    # 3. Morador envia 2ª Sugestão (mesma pessoa, mesmo link)
    print("\n>>> 3. Morador envia 2ª sugestão no mesmo link universal...")
    sug2_payload = json.dumps({
        "resident_name": "Fabiano Silva",
        "resident_phone": "27935009626",
        "block_tower": "VILLE",
        "unit_code": "1004",
        "target_reference": "Artigo 24, Caput",
        "action_type": "incluir",
        "suggestion_text": "Incluir regra para recarga de veículos elétricos nas vagas privativas.",
        "justification": "Adequar às novas demandas de sustentabilidade do condomínio."
    }).encode('utf-8')

    req_sug2 = urllib.request.Request(
        f"{BASE_URL}/public/consultations/{token}/suggestions",
        data=sug2_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req_sug2) as resp:
        sug2 = json.loads(resp.read().decode())
        print(f"    [OK] Sugestão 2 enviada! Protocolo: {sug2['protocol']}")

    # 4. Verifica deduplicação no cadastro de moradores
    print("\n>>> 4. Consultando cadastro de moradores do síndico (/registrations)...")
    req_reg = urllib.request.Request(f"{BASE_URL}/condominiums/{CONDO_ID}/registrations")
    with urllib.request.urlopen(req_reg) as resp:
        residents = json.loads(resp.read().decode())
        print(f"    Total de moradores cadastrados: {len(residents)}")
        for r in residents:
            print(f"    - [{r['id']}] {r['full_name']} | Unidade: {r['unit_code']} ({r['building_name']}) | WhatsApp: {r['phone_e164']} | Sugestões: {r['suggestions_count']}")

    assert len(residents) == 1, f"ERRO: Esperado 1 morador deduplicado, mas foram encontrados {len(residents)}!"
    assert residents[0]['suggestions_count'] >= 2, f"ERRO: Esperado pelo menos 2 sugestões para o morador, mas foram encontradas {residents[0]['suggestions_count']}!"
    print("    [SUCESSO] Deduplicação 100% confirmada! Nenhum registro duplicado criado.")

    # 5. Verifica endpoint de sugestões do morador
    reg_id = residents[0]['id']
    print(f"\n>>> 5. Consultando sugestões do morador ({reg_id})...")
    req_sugs = urllib.request.Request(f"{BASE_URL}/condominiums/{CONDO_ID}/registrations/{reg_id}/suggestions")
    with urllib.request.urlopen(req_sugs) as resp:
        sug_list = json.loads(resp.read().decode())
        print(f"    Total de sugestões retornadas para o morador: {len(sug_list)}")
        for s in sug_list:
            print(f"    - Protocolo: {s['protocol']} | Ação: {s['action_type']} | Ref: {s['target_reference']}")

    # 6. Verifica Métricas do Dashboard
    print("\n>>> 6. Consultando métricas reais do Dashboard...")
    req_metrics = urllib.request.Request(f"{BASE_URL}/condominiums/{CONDO_ID}/dashboard-metrics")
    with urllib.request.urlopen(req_metrics) as resp:
        metrics = json.loads(resp.read().decode())
        print(f"    - Moradores cadastrados: {metrics['residents_count']}")
        print(f"    - Unidades ativas: {metrics['units_count']}")
        print(f"    - Torres: {metrics['buildings_count']}")
        print(f"    - Consultas abertas: {metrics['consultations_open']}")
        print(f"    - Sugestões coletadas: {metrics['suggestions_count']}")
        print(f"    - Sugestões pendentes: {metrics['suggestions_pending']}")

    print("\n=================================================================")
    print("TODAS AS VALIDAÇÕES DO NOVO CICLO FORAM HOMOLOGADAS COM SUCESSO!")
    print("=================================================================")

if __name__ == '__main__':
    test_lifecycle()
