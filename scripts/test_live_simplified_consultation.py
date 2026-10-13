"""
Script de Validação E2E Live da Refatoração Simplificada do CONDOC
Utiliza a biblioteca padrão urllib do Python (sem dependências extras).
"""
import urllib.request
import urllib.parse
import json
import io
import sys
import uuid

BASE_URL = "http://192.168.10.200"

def http_get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read(), resp.headers

def http_post_json(url, data_dict):
    payload = json.dumps(data_dict).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read(), resp.headers

def http_post_multipart(url, fields, files):
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = io.BytesIO()

    for k, v in fields.items():
        body.write(f"--{boundary}\r\n".encode('utf-8'))
        body.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode('utf-8'))
        body.write(f"{v}\r\n".encode('utf-8'))

    for k, (filename, file_bytes, content_type) in files.items():
        body.write(f"--{boundary}\r\n".encode('utf-8'))
        body.write(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'.encode('utf-8'))
        body.write(f"Content-Type: {content_type}\r\n\r\n".encode('utf-8'))
        body.write(file_bytes)
        body.write(b"\r\n")

    body.write(f"--{boundary}--\r\n".encode('utf-8'))
    data = body.getvalue()

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read(), resp.headers

def run_test():
    print(f"=== TESTE LIVE E2E: CONSULTAS SIMPLIFICADAS EM PDF ({BASE_URL}) ===")

    # 1. Health check
    status, body, _ = http_get(f"{BASE_URL}/api/health")
    assert status == 200
    print("[OK] Health check operacional.")

    # 2. Condomínio existente
    status, body, _ = http_get(f"{BASE_URL}/api/v1/condominiums")
    assert status == 200
    condos = json.loads(body.decode('utf-8'))
    assert len(condos) > 0, "Nenhum condomínio encontrado."
    condo = condos[0]
    condo_id = condo['id']
    print(f"[OK] Condomínio ativo: {condo['name']} ({condo_id})")

    # 3. Cria consulta pública em PDF
    print("\n--- 1. Criando Consulta de Regimento com Upload de PDF ---")
    mock_pdf_bytes = b"%PDF-1.4 Mock Regimento Interno - Live Deploy Test on LXC 1"
    fields = {
        'title': 'Revisão Participativa do Regimento 2026',
        'document_type': 'regimento',
        'description': 'Caros condôminos, participem indicando ajustes nas normas internas.',
    }
    files = {
        'pdf_file': ('Regimento_Oficial_2026.pdf', mock_pdf_bytes, 'application/pdf')
    }
    status, body, _ = http_post_multipart(f"{BASE_URL}/api/v1/condominiums/{condo_id}/consultations", fields, files)
    assert status == 201
    consultation = json.loads(body.decode('utf-8'))
    token = consultation['public_token']
    consultation_id = consultation['id']
    print(f"[OK] Consulta criada! ID: {consultation_id}")
    print(f"[OK] Token de acesso público: {token}")
    print(f"[OK] Link de participação do morador: {BASE_URL}/participar/{token}")

    # 4. Acesso público via token
    print("\n--- 2. Acesso Público do Morador via Token (Zero Fricção) ---")
    status, body, _ = http_get(f"{BASE_URL}/api/v1/public/consultations/{token}")
    assert status == 200
    pub_data = json.loads(body.decode('utf-8'))
    assert pub_data['title'] == 'Revisão Participativa do Regimento 2026'
    assert pub_data['status'] == 'aberta'
    print(f"[OK] Dados da consulta carregados publicamente com sucesso: '{pub_data['title']}'")

    # 5. Visualizador de PDF (streaming inline)
    print("\n--- 3. Verificando Streaming do Arquivo PDF ---")
    status, body, headers = http_get(f"{BASE_URL}/api/v1/public/consultations/{token}/pdf")
    assert status == 200
    content_type = headers.get('Content-Type', '')
    content_disp = headers.get('Content-Disposition', '')
    assert 'application/pdf' in content_type
    assert 'inline' in content_disp
    print(f"[OK] PDF entregue com sucesso via streaming ({len(body)} bytes).")

    # 6. Envio de sugestão pelo morador
    print("\n--- 4. Envio de Sugestão pelo Morador (Sem Senha/Login) ---")
    suggestion_payload = {
        'resident_name': 'Juliana Paes',
        'resident_phone': '(11) 98765-4321',
        'resident_email': 'juliana@condoc.com.br',
        'block_tower': 'Torre B',
        'unit_code': '604',
        'target_reference': 'Artigo 18, Parágrafo 3º',
        'action_type': 'alterar',
        'suggestion_text': 'Ampliar o horário de silêncio aos domingos para início às 22h e término às 9h.',
        'justification': 'Proporcionar maior descanso aos vizinhos com crianças e idosos.',
    }
    status, body, _ = http_post_json(f"{BASE_URL}/api/v1/public/consultations/{token}/suggestions", suggestion_payload)
    assert status == 201
    sug_data = json.loads(body.decode('utf-8'))
    protocol = sug_data['protocol']
    print(f"[OK] Sugestão registrada com sucesso!")
    print(f"[OK] Número de Protocolo gerado: {protocol}")
    assert protocol.startswith('SUG-')

    # 7. Consulta de histórico pelo morador
    print("\n--- 5. Consulta de Histórico pelo Morador ---")
    query = urllib.parse.urlencode({'phone': '(11) 98765-4321', 'unit': '604'})
    status, body, _ = http_get(f"{BASE_URL}/api/v1/public/consultations/{token}/my-suggestions?{query}")
    assert status == 200
    my_list = json.loads(body.decode('utf-8'))
    assert len(my_list) >= 1
    assert my_list[0]['protocol'] == protocol
    print(f"[OK] Morador visualiza seu próprio envio com protocolo {protocol}.")

    # 8. Exportação para Excel (CSV com BOM UTF-8)
    print("\n--- 6. Exportação para Excel (CSV com BOM UTF-8) pelo Síndico ---")
    status, body, headers = http_get(f"{BASE_URL}/api/v1/condominiums/{condo_id}/consultations/{consultation_id}/export")
    assert status == 200
    csv_text = body.decode('utf-8')
    assert csv_text.startswith('\ufeff'), "Faltou BOM UTF-8"
    assert protocol in csv_text
    assert 'Juliana Paes' in csv_text
    assert 'Artigo 18, Parágrafo 3º' in csv_text
    assert 'Alterar Redação' in csv_text
    print(f"[OK] CSV de exportação validado! Contém BOM UTF-8, protocolo {protocol} e formatação amigável para Excel.")

    print("\n=======================================================")
    print("[SUCESSO TOTAL] TODOS OS 6 TESTES E2E EM PRODUCAO (LXC 1) APROVADOS!")
    print("=======================================================")

if __name__ == '__main__':
    try:
        run_test()
    except Exception as e:
        print(f"\n[ERRO NO TESTE E2E]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
