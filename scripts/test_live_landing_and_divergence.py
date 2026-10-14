"""
Script de Validação E2E Live da Landing Page, Ciclos de Acesso,
Divergência Cadastral e Múltiplas Sugestões com Confirmação Personalizada.
"""
import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://192.168.10.200"

def log_step(name, passed=True, detail=""):
    status = "[PASSOU]" if passed else "[FALHOU]"
    print(f"{status} {name}")
    if detail:
        print(f"       -> {detail}")
    if not passed:
        sys.exit(1)

def http_get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def http_post_json(url, data_dict):
    payload = json.dumps(data_dict).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def main():
    print("=" * 70)
    print("VALIDAÇÃO E2E LIVE — LANDING PAGE, DIVERGÊNCIA & CONFIRMAÇÃO")
    print("=" * 70)

    # 1. Testar Endpoint Público da Landing Page
    print("\n1. Verificando /api/v1/public/landing-info...")
    status, landing_data = http_get(f"{BASE_URL}/api/v1/public/landing-info")
    log_step(
        "Endpoint Público de Apresentação (Landing Page)",
        status == 200 and "name" in landing_data and "open_consultations" in landing_data,
        f"Condomínio: {landing_data.get('name')}, "
        f"Título: {landing_data.get('landing_title') or '(Padrão do Sistema)'}, "
        f"Consultas Abertas: {len(landing_data.get('open_consultations', []))}"
    )

    consultations = landing_data.get('open_consultations', [])
    if not consultations:
        print("Nenhuma consulta ativa encontrada no condomínio.")
        sys.exit(1)

    consultation = consultations[0]
    token = consultation['public_token']
    print(f"\n2. Verificando Consulta Pública (Token: {token})...")
    status, consult_detail = http_get(f"{BASE_URL}/api/v1/public/consultations/{token}")
    log_step(
        "Detalhes da Consulta Pública",
        status == 200 and "title" in consult_detail and "structure" in consult_detail,
        f"Título: {consult_detail.get('title')}, Condomínio: {consult_detail.get('condominium_name')}"
    )

    # Obter estrutura de torres e unidades
    structure = consult_detail.get('structure', {})
    buildings = structure.get('buildings', [])
    log_step(
        "Estrutura Predial com Torres/Blocos",
        len(buildings) > 0,
        f"Torres disponíveis: {[b['name'] for b in buildings]}"
    )

    first_building = buildings[0]
    building_name = first_building['name']
    first_unit = first_building['units'][0]
    unit_code = first_unit['code']

    # 3. Submissão Inicial de Sugestão (Cadastro do Titular)
    print(f"\n3. Submetendo 1ª Sugestão (Titular: titular.ap101@exemplo.com - Torre: {building_name}, Unidade: {unit_code})...")
    sub1_payload = {
        "resident_name": "Ana Paula Rezende",
        "resident_email": "titular.ap101@exemplo.com",
        "resident_phone": "(11) 98888-1111",
        "block_tower": building_name,
        "unit_code": unit_code,
        "action_type": "alterar",
        "target_reference": "Página 2 - Artigo 5º",
        "suggestion_text": "Primeira sugestão de teste: ajustar o horário de silêncio para 22h nos finais de semana.",
        "justification": "Garantir o descanso das famílias com crianças pequenas."
    }
    status, sub1_resp = http_post_json(f"{BASE_URL}/api/v1/public/consultations/{token}/suggestions", sub1_payload)
    log_step(
        "Envio de Sugestão pelo Titular",
        status == 201 and "protocol" in sub1_resp and not sub1_resp.get('has_divergence'),
        f"Protocolo: {sub1_resp.get('protocol')} (Divergência: {sub1_resp.get('has_divergence')})"
    )

    # 4. Submissão com Divergência Cadastral (mesma unidade, e-mail diferente)
    print(f"\n4. Submetendo 2ª Sugestão com E-mail Divergente (outro.morador@exemplo.com - Mesma Unidade: {unit_code})...")
    sub2_payload = {
        "resident_name": "Roberto Falsário ou Convivente",
        "resident_email": "outro.morador@exemplo.com",
        "resident_phone": "(11) 97777-2222",
        "block_tower": building_name,
        "unit_code": unit_code,
        "action_type": "incluir",
        "target_reference": "Página 4 - Artigo 12",
        "suggestion_text": "Segunda sugestão enviada com e-mail divergente: inclusão de regras para animais de grande porte.",
        "justification": "Segurança nas áreas comuns."
    }
    status, sub2_resp = http_post_json(f"{BASE_URL}/api/v1/public/consultations/{token}/suggestions", sub2_payload)
    log_step(
        "Detecção de Divergência Cadastral (Segurança Anti-Falsidade)",
        status == 201 and sub2_resp.get('has_divergence') is True,
        f"Protocolo: {sub2_resp.get('protocol')} | Divergência: {sub2_resp.get('has_divergence')} | Titular Preservado: {sub2_resp.get('registered_email')}"
    )

    # 5. Validação da Tela de Confirmação & Mensagem de Agradecimento
    print("\n5. Verificando Dados para Tela de Confirmação...")
    thank_msg = sub2_resp.get('thank_you_message')
    log_step(
        "Retorno de Agradecimento e Dados da Confirmação",
        bool(sub2_resp.get('protocol')) and bool(thank_msg),
        f"Mensagem entregue ao morador: '{thank_msg[:60]}...'"
    )

    print("\n" + "=" * 70)
    print("TODAS AS VALIDAÇÕES DE API LIVE FORAM BEM-SUCEDIDAS!")
    print("=" * 70)

if __name__ == "__main__":
    main()
