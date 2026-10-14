#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

def main():
    url = "https://condoc.fk.adm.br/participar/vtF2RgpJUoj7xMqbDta8"
    print(f"Testando URL de produção HTTPS: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.on("console", lambda m: print(f"  [CONSOLE] {m.type}: {m.text}"))
        page.on("pageerror", lambda e: print(f"  [PAGEERROR] {e}"))
        page.on("requestfailed", lambda req: print(f"  [REQ FAILED] {req.url} -> {req.failure}"))

        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3000)

        err = page.locator("text='Não foi possível carregar o PDF'")
        print(f"Erro 'Não foi possível carregar o PDF' visível: {err.count() > 0}")

        err_detail = page.locator("div:has-text('Não foi possível carregar o PDF') p").all_inner_texts()
        print(f"Detalhe do erro na tela: {err_detail}")

        page.screenshot(path="f:/CONDOC/test_screenshots/https_condoc_error.png")
        browser.close()

if __name__ == '__main__':
    main()
