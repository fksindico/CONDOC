#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

def main():
    url = "https://condoc.fk.adm.br/participar/vtF2RgpJUoj7xMqbDta8"
    print(f"Testando Flipbook e Rolagem Isolada em: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ----------------------------------------------------
        # 1. TESTE DESKTOP: MODO ROLAGEM COM FORMULÁRIO FIXO
        # ----------------------------------------------------
        page = browser.new_page(viewport={"width": 1366, "height": 820})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3500)

        # Clica no modo Rolagem
        scroll_btn = page.locator("button:has-text('Rolagem')")
        if scroll_btn.is_visible():
            scroll_btn.click()
            page.wait_for_timeout(1000)

        # Verifica se o formulário está visível
        form_visible = page.locator("h2:has-text('Formulário de Sugestão')").is_visible()
        scroll_y_before = page.evaluate("() => window.scrollY")
        print(f"[Desktop Rolagem Inicial] Formulário visível: {form_visible}, window.scrollY: {scroll_y_before}")
        page.screenshot(path="f:/CONDOC/test_screenshots/06_flipbook_scroll_mode.png")
        print("Salvo: 06_flipbook_scroll_mode.png")

        # Clica no seletor de próxima página no modo rolagem
        next_btn = page.locator("button[title*='Próxima']")
        if next_btn.first.is_visible():
            next_btn.first.click()
            page.wait_for_timeout(1200)

        scroll_y_after = page.evaluate("() => window.scrollY")
        form_visible_after = page.locator("h2:has-text('Formulário de Sugestão')").is_visible()
        print(f"[Desktop Rolagem Pág 2] Formulário visível: {form_visible_after}, window.scrollY: {scroll_y_after}")
        assert scroll_y_after == 0, f"Erro: window.scrollY mudou para {scroll_y_after}!"
        page.screenshot(path="f:/CONDOC/test_screenshots/07_scroll_page2_form_visible.png")
        print("Salvo: 07_scroll_page2_form_visible.png")

        # ----------------------------------------------------
        # 2. TESTE TABLET EM PAISAGEM (1024x768)
        # ----------------------------------------------------
        page_tablet_land = browser.new_page(viewport={"width": 1024, "height": 768})
        page_tablet_land.goto(url, wait_until="networkidle")
        page_tablet_land.wait_for_timeout(3000)
        page_tablet_land.screenshot(path="f:/CONDOC/test_screenshots/08_tablet_landscape.png")
        print("Salvo: 08_tablet_landscape.png")

        # ----------------------------------------------------
        # 3. TESTE TABLET EM RETRATO (768x1024)
        # ----------------------------------------------------
        page_tablet_port = browser.new_page(viewport={"width": 768, "height": 1024})
        page_tablet_port.goto(url, wait_until="networkidle")
        page_tablet_port.wait_for_timeout(3000)
        page_tablet_port.screenshot(path="f:/CONDOC/test_screenshots/09_tablet_portrait.png")
        print("Salvo: 09_tablet_portrait.png")

        # ----------------------------------------------------
        # 4. TESTE SMARTPHONE (390x844)
        # ----------------------------------------------------
        page_mobile = browser.new_page(viewport={"width": 390, "height": 844})
        page_mobile.goto(url, wait_until="networkidle")
        page_mobile.wait_for_timeout(3000)

        # Abre aba Documento
        doc_tab = page_mobile.locator("button:has-text('1. Ver Documento (PDF)')")
        if doc_tab.is_visible():
            doc_tab.click()
            page_mobile.wait_for_timeout(1000)
        page_mobile.screenshot(path="f:/CONDOC/test_screenshots/10_mobile_document_view.png")
        print("Salvo: 10_mobile_document_view.png")

        # Clica no botão inferior para ir ao formulário
        go_form_btn = page_mobile.locator("button:has-text('2. Fazer Minha Sugestão')")
        if go_form_btn.is_visible():
            go_form_btn.click()
            page_mobile.wait_for_timeout(1000)
        page_mobile.screenshot(path="f:/CONDOC/test_screenshots/11_mobile_suggestion_view.png")
        print("Salvo: 11_mobile_suggestion_view.png")

        browser.close()
        print("[SUCESSO] Todos os testes de rolagem e responsividade concluídos com êxito!")

if __name__ == '__main__':
    main()
