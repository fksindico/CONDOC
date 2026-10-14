#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

def main():
    url = "https://condoc.fk.adm.br/participar/vtF2RgpJUoj7xMqbDta8"
    print(f"Testando Flipbook Centralizado e Ajustado em: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Teste Desktop Split View (Tela Padrão)
        page = browser.new_page(viewport={"width": 1366, "height": 820})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3500)
        page.screenshot(path="f:/CONDOC/test_screenshots/01_flipbook_split_centered.png")
        print("Salvo: 01_flipbook_split_centered.png")

        # 2. Teste Folheando para a Página 2
        next_btn = page.locator("button[title*='Próxima']")
        if next_btn.first.is_visible():
            next_btn.first.click()
            page.wait_for_timeout(1500)
        page.screenshot(path="f:/CONDOC/test_screenshots/02_flipbook_split_page2.png")
        print("Salvo: 02_flipbook_split_page2.png")

        # 3. Teste Modo 2 Páginas (clicando no botão 2 Págs)
        double_btn = page.locator("button:has-text('2 Págs')")
        if double_btn.is_visible():
            double_btn.click()
            page.wait_for_timeout(1500)
        page.screenshot(path="f:/CONDOC/test_screenshots/03_flipbook_double_mode.png")
        print("Salvo: 03_flipbook_double_mode.png")

        # 4. Teste Expandir Livro (Foco no Documento)
        expand_btn = page.locator("button:has-text('Expandir Livro')")
        if expand_btn.is_visible():
            expand_btn.click()
            page.wait_for_timeout(1500)
        page.screenshot(path="f:/CONDOC/test_screenshots/04_flipbook_expanded.png")
        print("Salvo: 04_flipbook_expanded.png")

        # 5. Teste Modo Rolagem Vertical Contínua
        scroll_btn = page.locator("button:has-text('Rolagem')")
        if scroll_btn.is_visible():
            scroll_btn.click()
            page.wait_for_timeout(1500)
        page.screenshot(path="f:/CONDOC/test_screenshots/06_flipbook_scroll_mode.png")
        print("Salvo: 06_flipbook_scroll_mode.png")

        # 6. Teste Mobile (Smartphone 390x844) - Aba Ver Documento
        page_mobile = browser.new_page(viewport={"width": 390, "height": 844})
        page_mobile.goto(url, wait_until="networkidle")
        page_mobile.wait_for_timeout(3500)
        doc_tab = page_mobile.locator("button:has-text('1. Ver Documento (PDF)')")
        if doc_tab.is_visible():
            doc_tab.click()
            page_mobile.wait_for_timeout(1500)
        page_mobile.screenshot(path="f:/CONDOC/test_screenshots/05_flipbook_mobile_doc.png")
        print("Salvo: 05_flipbook_mobile_doc.png")

        browser.close()

if __name__ == '__main__':
    main()
