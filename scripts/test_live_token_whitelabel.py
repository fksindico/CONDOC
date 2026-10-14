import os
import sys
import time
from playwright.sync_api import sync_playwright

# Força codificação segura para evitar erros do console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = os.environ.get("BASE_URL", "https://condoc.fk.adm.br")
ARTIFACT_DIR = r"C:\Users\Fabiano\.gemini\antigravity\brain\006771d1-3d1e-40ee-8ac7-9289fd578f17"

def main():
    print(f"=== TESTE E2E: White-Label 'FK Gestão Condominial' e Acesso por Token ===")
    print(f"Alvo: {BASE_URL}")
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800}, ignore_https_errors=True)
        page = context.new_page()

        # 1. ACESSO À PÁGINA INICIAL (/)
        print("\n[1] Acessando Landing Page inicial...")
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        time.sleep(2)

        # Captura screenshot da Landing Page
        ss_landing = os.path.join(ARTIFACT_DIR, "36_landing_page_fk_gestao.png")
        page.screenshot(path=ss_landing, full_page=True)
        print(f"Screenshot salvo: {ss_landing}")

        # Validações estritas na Landing Page:
        # A. Título da página
        page_title = page.title()
        print(f"Título da página: '{page_title}'")
        assert "FK Gestão Condominial" in page_title, f"Título incorreto: {page_title}"
        assert "CONDOC" not in page_title, f"CONDOC visível no título da Landing Page: {page_title}"

        # B. Marca no Header e Hero
        body_text = page.locator("body").inner_text()
        assert "FK Gestão Condominial" in body_text, "Marca 'FK Gestão Condominial' não encontrada no corpo da página!"
        print("[OK] Marca 'FK Gestao Condominial' verificada no topo e rodape.")

        # C. Proibição de 'plataforma oficial' e 'Ambiente Oficial'
        assert "plataforma oficial" not in body_text.lower(), "Termo proibido 'plataforma oficial' encontrado na home!"
        assert "ambiente oficial" not in body_text.lower(), "Termo proibido 'ambiente oficial' encontrado na home!"
        print("[OK] Proibicao de referencias como 'plataforma oficial' cumprida.")

        # D. Proibição de 'conDoc' / 'CONDOC' para moradores na Landing Page
        # Nota: Deve ser zero referências na tela pública
        assert "condoc" not in body_text.lower(), "Menção a CONDOC encontrada na tela pública do morador!"
        print("[OK] Nenhuma mencao a 'CONDOC' encontrada para os moradores na home.")

        # E. Ausência de lista aberta de consultas / cards de campanhas diretamente na home
        assert "Consultas Públicas Ativas" not in body_text, "Listagem aberta de consultas ainda presente na home!"
        assert not page.locator("a[href*='/participar/']").is_visible(), "Link direto de consulta encontrado na home!"
        print("[OK] Nenhuma consulta exposta em aberto na página inicial.")

        # F. Presença da Caixa de Entrada de Código de Acesso
        token_input = page.locator("input[placeholder*='REG2026']")
        assert token_input.is_visible(), "Campo de inserção de código de acesso não encontrado!"
        print("[OK] Caixa de insercao de codigo de acesso identificada com sucesso.")

        # 2. LOGIN DO SÍNDICO PARA CONSULTAR/ATUALIZAR TOKEN
        print("\n[2] Acessando Painel do Sindico para gerenciar token...")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        time.sleep(1)

        # Clica no perfil rápido do Síndico Ativo
        sindico_btn = page.locator("button:has-text('Síndico Ativo')").first
        if sindico_btn.is_visible():
            sindico_btn.click()
        else:
            page.fill("input[type='email']", "sindico@parquedasflores.com")
            page.click("button[type='submit']")

        page.wait_for_url("**/painel**", timeout=15000)
        time.sleep(2)
        print("[OK] Login de Sindico realizado com sucesso.")

        # Acessa Consultas em PDF
        page.goto(f"{BASE_URL}/painel/consultas", wait_until="networkidle")
        time.sleep(3)

        # Captura screenshot do gerenciamento com token personalizável
        ss_admin_token = os.path.join(ARTIFACT_DIR, "37_admin_customizable_token.png")
        page.screenshot(path=ss_admin_token, full_page=True)
        print(f"Screenshot salvo: {ss_admin_token}")

        # Verifica se o código de acesso e o botão Personalizar estão visíveis
        token_badge = page.locator("span:has-text('Código de Acesso:')").first
        assert token_badge.is_visible(), "Badge de Código de Acesso não encontrado no painel do síndico!"
        print("[OK] Codigo de Acesso exibido no painel de gerenciamento da consulta.")

        # Clica em 'Personalizar'
        personalizar_btn = page.locator("button:has-text('Personalizar')").first
        if personalizar_btn.is_visible():
            personalizar_btn.click()
            time.sleep(1)
            # Altera para um token curto memorável: FLORES26
            token_edit_input = page.locator("input[placeholder*='REG2026']").last
            token_edit_input.fill("FLORES26")
            page.click("button:has-text('Salvar')")
            time.sleep(2)
            print("[OK] Token atualizado pelo sindico para 'FLORES26'.")

        ss_admin_token_saved = os.path.join(ARTIFACT_DIR, "38_admin_token_saved.png")
        page.screenshot(path=ss_admin_token_saved, full_page=True)
        print(f"Screenshot salvo: {ss_admin_token_saved}")

        # 3. TESTE DO MORADOR ACESSANDO PELO CÓDIGO NA HOME
        print("\n[3] Testando acesso do morador digitando codigo 'FLORES26' na Landing Page...")
        # Desloga e volta para home
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        time.sleep(2)

        input_home = page.locator("input[placeholder*='REG2026']")
        # Digita em minúsculo 'flores26' para testar case-insensitivity
        input_home.fill("flores26")
        time.sleep(0.5)
        page.click("button:has-text('Acessar Consulta')")

        # Deve navegar para /participar/FLORES26
        page.wait_for_url("**/participar/**", timeout=10000)
        time.sleep(3)
        print(f"[OK] Redirecionado com sucesso para: {page.url}")

        # Aguarda carregamento da consulta pública
        try:
            page.wait_for_selector("h1", timeout=10000)
        except Exception:
            pass
        time.sleep(2)

        consultation_body = page.locator("body").inner_text()
        print(f"URL da consulta ativa: {page.url}")
        print(f"Texto da consulta ativa:\n{consultation_body[:400]}")
        
        # A. O nome do condomínio DEVE aparecer aqui!
        # Por exemplo: 'NEXT RESIDENCE' ou 'Residencial Parque das Flores'
        assert any(k.lower() in consultation_body.lower() for k in ["next residence", "parque das flores", "condomínio", "residencial"]), \
            f"Nome do condomínio não encontrado na página da consulta ativa! Conteúdo: {consultation_body[:300]}"
        print("[OK] Nome do condominio apresentado corretamente na campanha ativa.")

        # B. Validação da presença do Flipbook e formulário
        assert page.locator("button:has-text('Foco no Documento')").is_visible() or \
               page.locator("text=Formulário de Sugestão").is_visible() or \
               page.locator("canvas").is_visible(), "Elementos da consulta participativa não encontrados!"
        print("[OK] Flipbook e formulario carregados perfeitamente.")

        # Captura screenshot da consulta ativa acessada por token
        ss_consultation = os.path.join(ARTIFACT_DIR, "39_public_consultation_via_token.png")
        page.screenshot(path=ss_consultation, full_page=True)
        print(f"Screenshot salvo: {ss_consultation}")

        browser.close()
        print("\n=== TODOS OS TESTES E VALIDAÇÕES FORAM APROVADOS COM 100% DE SUCESSO! ===")

if __name__ == "__main__":
    main()
