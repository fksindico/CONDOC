#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

def main():
    url = "https://condoc.fk.adm.br/participar/vtF2RgpJUoj7xMqbDta8"
    print(f"Testando virada de página em: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3500)

        # Clica no botão de próxima página
        next_btn = page.locator("button[title='Próxima página']")
        if next_btn.is_visible():
            print("Clicando em Próxima Página...")
            next_btn.click()
            page.wait_for_timeout(1500)

        page.screenshot(path="f:/CONDOC/test_screenshots/https_flipbook_paginas_abertas.png")
        print("Screenshot salvo em f:/CONDOC/test_screenshots/https_flipbook_paginas_abertas.png")
        browser.close()

if __name__ == '__main__':
    main()
